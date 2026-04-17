"""对话管理路由"""
import uuid
import json
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.database import get_db, ChatSessionModel, MessageModel, GroupModel, CharacterModel, LorebookModel, MemoryModel
from backend.config.settings import settings
from backend.plugins.plugin_manager import get_plugin_manager

router = APIRouter()


class MessageCreate(BaseModel):
    content: str
    role: Optional[str] = "user"


class SessionCreate(BaseModel):
    name: Optional[str] = None
    characterId: Optional[str] = None
    characterName: Optional[str] = None
    modelType: Optional[str] = "ollama"  # ollama, openai, deepseek


class GroupCreate(BaseModel):
    name: str
    color: Optional[str] = "#667eea"


def model_to_session(s: ChatSessionModel) -> dict:
    """转换会话模型"""
    return {
        "id": s.id,
        "name": s.name,
        "characterId": s.character_id,
        "characterName": s.character_name,
        "model": s.model,
        "temperature": s.temperature,
        "maxTokens": s.max_tokens,
        "pinned": s.pinned,
        "groupId": s.group_id,
        "tokenCount": s.token_count,
        "createdAt": s.created_at.timestamp() * 1000 if s.created_at else 0,
        "updatedAt": s.updated_at.timestamp() * 1000 if s.updated_at else 0,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "characterId": m.character_id,
                "timestamp": m.timestamp
            }
            for m in sorted(s.messages, key=lambda x: x.timestamp or 0)
        ]
    }


def model_to_group(g: GroupModel) -> dict:
    """转换分组模型"""
    return {
        "id": g.id,
        "name": g.name,
        "color": g.color,
        "createdAt": g.created_at.timestamp() * 1000 if g.created_at else 0
    }


# ============ 会话路由 ============

@router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db)):
    """获取所有会话"""
    sessions = db.query(ChatSessionModel).order_by(ChatSessionModel.updated_at.desc()).all()
    return {"sessions": [model_to_session(s) for s in sessions]}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """获取单个会话"""
    session = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return model_to_session(session)


@router.post("/sessions")
async def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    """创建新会话"""
    name = data.name or f"新对话 {uuid.uuid4().hex[:6]}"
    session = ChatSessionModel(
        id=str(uuid.uuid4()),
        name=name,
        character_id=data.characterId,
        character_name=data.characterName or "",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return model_to_session(session)


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, payload: dict, db: Session = Depends(get_db)):
    """更新会话"""
    session = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    for key, value in payload.items():
        if hasattr(session, key):
            setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return model_to_session(session)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    session = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(session)
    db.commit()
    return {"success": True}


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    """发送消息（流式响应）"""
    session = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 保存用户消息
    user_msg = MessageModel(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=payload.content,
        timestamp=0
    )
    db.add(user_msg)
    db.commit()

    # 获取角色信息
    char = None
    if session.character_id:
        char = db.query(CharacterModel).filter(CharacterModel.id == session.character_id).first()

    # 获取世界设定条目（关键词匹配）
    lorebook_content = _get_lorebook_context(db, payload.content)

    # 获取相关记忆
    memory_content = _get_relevant_memory(db, payload.content)

    async def generate():
        full_response = ""
        try:
            # 构建系统提示词
            system_parts = []

            if char:
                char_desc = []
                if char.name:
                    char_desc.append(f"角色名称: {char.name}")
                if char.personality:
                    char_desc.append(f"性格特征: {char.personality}")
                if char.scenario:
                    char_desc.append(f"场景设定: {char.scenario}")
                if char.greeting:
                    char_desc.append(f"开场白风格: {char.greeting}")
                if char_desc:
                    system_parts.append("【角色设定】\n" + "\n".join(char_desc))

            if lorebook_content:
                system_parts.append("【世界设定】\n" + lorebook_content)

            if memory_content:
                system_parts.append("【相关记忆】\n" + memory_content)

            if system_parts:
                system_prompt = "\n\n".join(system_parts)
            else:
                system_prompt = "你是一个有帮助的AI助手。"

            # 构建消息历史
            messages = [{"role": "system", "content": system_prompt}]
            for m in session.messages:
                messages.append({"role": m.role, "content": m.content})
            messages.append({"role": "user", "content": payload.content})

            model_type = session.model or settings.default_model_type

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
                            "temperature": session.temperature or 0.7,
                            "max_tokens": session.max_tokens or 4096,
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
                                        yield content
                                except json.JSONDecodeError:
                                    continue

                elif model_type in ("anthropic", "claude") and settings.claude_api_key:
                    # Anthropic Claude API (非流式，因为Claude的streaming格式不同)
                    sync_messages = [{"role": m["role"], "content": m["content"]} for m in messages[1:]]
                    resp = await client.post(
                        f"{settings.claude_base_url}/messages",
                        headers={
                            "x-api-key": settings.claude_api_key,
                            "anthropic-version": settings.antropic_api_version,
                            "content-type": "application/json"
                        },
                        json={
                            "model": "claude-3-5-haiku-20241022",
                            "max_tokens": session.max_tokens or 4096,
                            "system": messages[0]["content"],
                            "messages": sync_messages,
                            "stream": True,
                        }
                    )
                    async for line in resp.aiter_lines():
                        if line and line.startswith("data:"):
                            if line.strip() == "data: [DONE]":
                                break
                            try:
                                data = json.loads(line[5:])
                                delta = data.get("delta", {})
                                if delta.get("type") == "content_block_delta":
                                    content = delta.get("text", "")
                                    if content:
                                        full_response += content
                                        yield content
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
                            "model": session.model or "gpt-3.5-turbo",
                            "messages": messages,
                            "stream": True,
                            "temperature": session.temperature or 0.7,
                            "max_tokens": session.max_tokens or 4096,
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
                                        yield content
                                except json.JSONDecodeError:
                                    continue

                else:
                    # 默认 Ollama
                    async with client.stream(
                        "POST",
                        f"{settings.ollama_base_url}/api/chat",
                        json={
                            "model": session.model or settings.default_model_name,
                            "messages": messages,
                            "stream": True,
                            "options": {
                                "temperature": session.temperature or 0.7,
                                "num_predict": session.max_tokens or 4096,
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
                                        yield content
                                    if data.get("done"):
                                        break
                                except json.JSONDecodeError:
                                    continue

            # 保存助手消息
            assistant_msg = MessageModel(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="assistant",
                content=full_response,
                timestamp=0
            )
            db.add(assistant_msg)
            session.token_count = (session.token_count or 0) + len(full_response)
            db.commit()

            # 触发自动记忆（异步，不阻塞响应）
            if settings.memory_enabled:
                try:
                    from backend.plugins.plugin_manager import get_plugin_manager
                    plugin_mgr = get_plugin_manager()
                    auto_mem = plugin_mgr.get_plugin("auto-memory")
                    if auto_mem and auto_mem.metadata.enabled:
                        await auto_mem.process_output(full_response, {
                            "session_id": session_id,
                            "user_message": payload.content,
                            "character": char.name if char else None,
                        })
                except Exception:
                    pass

        except Exception as e:
            error_msg = f"错误: {str(e)}"
            yield error_msg

    return StreamingResponse(generate(), media_type="text/plain")


def _get_lorebook_context(db, query: str) -> str:
    """根据查询内容获取匹配的世界设定条目"""
    try:
        lorebooks = db.query(LorebookModel).filter(LorebookModel.enabled == True).all()
        matched = []
        for book in lorebooks:
            for entry in book.entries:
                if not entry.enabled:
                    continue
                keywords = entry.keywords or []
                # 检查关键词是否出现在查询中
                query_lower = query.lower()
                for kw in keywords:
                    if kw.lower() in query_lower:
                        matched.append({
                            "content": entry.content,
                            "priority": entry.priority,
                            "name": entry.name,
                        })
                        break

        # 按优先级排序，取前3个
        matched.sort(key=lambda x: -x["priority"])
        if matched:
            lines = [f"- {m['name']}: {m['content']}" for m in matched[:3]]
            return "\n".join(lines)
        return ""
    except Exception:
        return ""


def _get_relevant_memory(db, query: str) -> str:
    """获取相关记忆"""
    try:
        memories = db.query(MemoryModel).filter(
            MemoryModel.content.contains(query)
        ).limit(3).all()
        if memories:
            lines = [m.content for m in memories]
            return "\n".join(f"- {l}" for l in lines)
        return ""
    except Exception:
        return ""


# ============ 分组路由 ============

@router.get("/groups")
async def list_groups(db: Session = Depends(get_db)):
    """获取所有分组"""
    groups = db.query(GroupModel).order_by(GroupModel.name).all()
    return [model_to_group(g) for g in groups]


@router.post("/groups")
async def create_group(data: GroupCreate, db: Session = Depends(get_db)):
    """创建分组"""
    group = GroupModel(
        id=str(uuid.uuid4()),
        name=data.name,
        color=data.color,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return model_to_group(group)


@router.delete("/groups/{group_id}")
async def delete_group(group_id: str, db: Session = Depends(get_db)):
    """删除分组"""
    group = db.query(GroupModel).filter(GroupModel.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    db.delete(group)
    db.commit()
    return {"success": True}
