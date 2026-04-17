"""群聊路由"""
import uuid
import json
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.database import get_db, GroupChatGroupModel, MessageModel
from backend.config.settings import settings

router = APIRouter()


class GroupChatCreate(BaseModel):
    name: str


class MessageCreate(BaseModel):
    content: str
    mode: Optional[str] = "rotation"


def model_to_dict(group) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "members": group.members or [],
        "chatMode": group.chat_mode,
        "createdAt": group.created_at.timestamp() * 1000 if group.created_at else 0,
        "updatedAt": group.updated_at.timestamp() * 1000 if group.updated_at else 0,
    }


@router.get("/groups")
async def list_groups(db: Session = Depends(get_db)):
    """获取所有群聊组"""
    groups = db.query(GroupChatGroupModel).order_by(GroupChatGroupModel.updated_at.desc()).all()
    return [model_to_dict(g) for g in groups]


@router.post("/groups")
async def create_group(data: GroupChatCreate, db: Session = Depends(get_db)):
    """创建群聊组"""
    group = GroupChatGroupModel(
        id=str(uuid.uuid4()),
        name=data.name,
        members=[],
        chat_mode="rotation",
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return model_to_dict(group)


@router.get("/{group_id}")
async def get_group(group_id: str, db: Session = Depends(get_db)):
    """获取群聊组"""
    group = db.query(GroupChatGroupModel).filter(GroupChatGroupModel.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群聊组不存在")
    return model_to_dict(group)


@router.delete("/{group_id}")
async def delete_group(group_id: str, db: Session = Depends(get_db)):
    """删除群聊组"""
    group = db.query(GroupChatGroupModel).filter(GroupChatGroupModel.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群聊组不存在")
    db.delete(group)
    db.commit()
    return {"success": True}


@router.get("/{group_id}/messages")
async def get_messages(group_id: str, db: Session = Depends(get_db)):
    """获取群聊消息"""
    messages = db.query(MessageModel).filter(
        MessageModel.session_id == group_id
    ).order_by(MessageModel.timestamp).all()
    return [
        {
            "role": m.role,
            "content": m.content,
            "characterId": m.character_id,
            "timestamp": m.timestamp,
        }
        for m in messages
    ]


@router.post("/{group_id}/members")
async def add_member(group_id: str, payload: dict, db: Session = Depends(get_db)):
    """添加成员"""
    group = db.query(GroupChatGroupModel).filter(GroupChatGroupModel.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群聊组不存在")
    member = {"id": payload.get("characterId"), "name": payload.get("name", "")}
    if member not in group.members:
        group.members = group.members + [member] if group.members else [member]
    db.commit()
    return model_to_dict(group)


@router.delete("/{group_id}/members/{member_id}")
async def remove_member(group_id: str, member_id: str, db: Session = Depends(get_db)):
    """移除成员"""
    group = db.query(GroupChatGroupModel).filter(GroupChatGroupModel.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群聊组不存在")
    if group.members:
        group.members = [m for m in group.members if m.get("id") != member_id]
    db.commit()
    return model_to_dict(group)


@router.post("/{group_id}/messages")
async def send_group_message(group_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    """在群聊中发送消息（流式响应，轮流以各角色回复）"""
    group = db.query(GroupChatGroupModel).filter(GroupChatGroupModel.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群聊组不存在")

    members = group.members or []
    if not members:
        raise HTTPException(status_code=400, detail="群聊中没有任何角色")

    # 保存用户消息
    user_msg = MessageModel(
        id=str(uuid.uuid4()),
        session_id=group_id,
        role="user",
        content=payload.content,
        character_id=None,
        timestamp=0
    )
    db.add(user_msg)
    db.commit()

    async def generate():
        all_messages = []
        try:
            # 轮流以每个角色回复
            for i, member in enumerate(members):
                member_name = member.get("name", "未知角色")
                char_id = member.get("id", "")

                # 构建上下文：用户消息 + 之前的 AI 回复
                context_lines = [f"用户: {payload.content}"]
                for prev in all_messages:
                    context_lines.append(prev)

                system_prompt = (
                    f"你是角色「{member_name}」。"
                    f"群聊中共有 {len(members)} 个角色，依次轮流发言。"
                    f"请以 {member_name} 的视角和性格，简短自然地回复。"
                    f"回复内容仅输出角色的话，不需要额外描述动作或心理。"
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "\n".join(context_lines[-6:])}  # 限制上下文
                ]

                model_type = settings.default_model_type
                full_response = ""

                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        if model_type == "deepseek" and settings.deepseek_api_key:
                            async with client.stream(
                                "POST",
                                f"{settings.deepseek_base_url}/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "model": "deepseek-chat",
                                    "messages": messages,
                                    "stream": True,
                                    "temperature": 0.8,
                                    "max_tokens": 512,
                                }
                            ) as resp:
                                async for line in resp.aiter_lines():
                                    if line and line.startswith("data:"):
                                        if line.strip() == "data: [DONE]":
                                            break
                                        try:
                                            data = json.loads(line[5:])
                                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                            if content:
                                                full_response += content
                                                yield f"[{member_name}]:{content}"
                                        except json.JSONDecodeError:
                                            continue

                        elif model_type == "openai" and settings.openai_api_key:
                            async with client.stream(
                                "POST",
                                f"{settings.openai_base_url}/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {settings.openai_api_key}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "model": "gpt-3.5-turbo",
                                    "messages": messages,
                                    "stream": True,
                                    "temperature": 0.8,
                                    "max_tokens": 512,
                                }
                            ) as resp:
                                async for line in resp.aiter_lines():
                                    if line and line.startswith("data:"):
                                        if line.strip() == "data: [DONE]":
                                            break
                                        try:
                                            data = json.loads(line[5:])
                                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                            if content:
                                                full_response += content
                                                yield f"[{member_name}]:{content}"
                                        except json.JSONDecodeError:
                                            continue

                        else:
                            # 默认 Ollama
                            async with client.stream(
                                "POST",
                                f"{settings.ollama_base_url}/api/chat",
                                json={
                                    "model": settings.default_model_name,
                                    "messages": messages,
                                    "stream": True,
                                    "options": {
                                        "temperature": 0.8,
                                        "num_predict": 512,
                                    }
                                }
                            ) as resp:
                                async for line in resp.aiter_lines():
                                    if line:
                                        try:
                                            data = json.loads(line)
                                            content = data.get("message", {}).get("content", "")
                                            if content:
                                                full_response += content
                                                yield f"[{member_name}]:{content}"
                                            if data.get("done"):
                                                break
                                        except json.JSONDecodeError:
                                            continue

                except Exception as e:
                    yield f"[{member_name}]:（无法连接 AI 服务: {str(e)}）"
                    full_response = f"（无法连接 AI 服务）"

                # 保存角色消息
                if full_response:
                    char_msg = MessageModel(
                        id=str(uuid.uuid4()),
                        session_id=group_id,
                        role="assistant",
                        content=full_response,
                        character_id=char_id,
                        timestamp=i + 1
                    )
                    db.add(char_msg)
                    db.commit()
                    all_messages.append(f"{member_name}: {full_response}")

        except Exception as e:
            yield f"错误: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")
