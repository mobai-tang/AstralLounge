"""角色管理路由"""
import json
import base64
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.database import get_db, CharacterModel
from backend.config.settings import settings

router = APIRouter()


class CharacterCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    personality: Optional[str] = ""
    scenario: Optional[str] = ""
    greeting: Optional[str] = ""
    avatar: Optional[str] = ""
    tags: Optional[List[str]] = []
    examples: Optional[List[str]] = []


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    scenario: Optional[str] = None
    greeting: Optional[str] = None
    avatar: Optional[str] = None
    tags: Optional[List[str]] = None
    examples: Optional[List[str]] = None


def model_to_dict(char: CharacterModel) -> dict:
    """将模型转换为字典"""
    return {
        "id": char.id,
        "name": char.name,
        "description": char.description,
        "personality": char.personality,
        "scenario": char.scenario,
        "greeting": char.greeting,
        "avatar": char.avatar,
        "tags": char.tags or [],
        "examples": char.examples or [],
        "createdAt": char.created_at.timestamp() * 1000 if char.created_at else 0,
        "updatedAt": char.updated_at.timestamp() * 1000 if char.updated_at else 0,
    }


@router.get("")
async def list_characters(db: Session = Depends(get_db)):
    """获取所有角色"""
    chars = db.query(CharacterModel).order_by(CharacterModel.name).all()
    return [model_to_dict(c) for c in chars]


@router.get("/{char_id}")
async def get_character(char_id: str, db: Session = Depends(get_db)):
    """获取单个角色"""
    char = db.query(CharacterModel).filter(CharacterModel.id == char_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    return model_to_dict(char)


@router.post("")
async def create_character(char_data: CharacterCreate, db: Session = Depends(get_db)):
    """创建角色"""
    char = CharacterModel(
        id=str(uuid.uuid4()),
        name=char_data.name,
        description=char_data.description,
        personality=char_data.personality,
        scenario=char_data.scenario,
        greeting=char_data.greeting,
        avatar=char_data.avatar,
        tags=char_data.tags or [],
        examples=char_data.examples or [],
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return model_to_dict(char)


@router.put("/{char_id}")
async def update_character(char_id: str, char_data: CharacterUpdate, db: Session = Depends(get_db)):
    """更新角色"""
    char = db.query(CharacterModel).filter(CharacterModel.id == char_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    for key, value in char_data.model_dump(exclude_none=True).items():
        setattr(char, key, value)
    db.commit()
    db.refresh(char)
    return model_to_dict(char)


@router.delete("/{char_id}")
async def delete_character(char_id: str, db: Session = Depends(get_db)):
    """删除角色"""
    char = db.query(CharacterModel).filter(CharacterModel.id == char_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.delete(char)
    db.commit()
    return {"success": True}


@router.get("/{char_id}/avatar")
async def get_avatar(char_id: str, db: Session = Depends(get_db)):
    """获取角色头像"""
    char = db.query(CharacterModel).filter(CharacterModel.id == char_id).first()
    if not char or not char.avatar:
        raise HTTPException(status_code=404, detail="头像不存在")
    avatar_data = char.avatar
    if avatar_data.startswith("data:image"):
        parts = avatar_data.split(",")
        if len(parts) == 2:
            mime, data = parts
            media_type = mime.split(";")[0].split(":")[1]
            binary_data = base64.b64decode(data)
            return Response(content=binary_data, media_type=media_type)
    return Response(content=avatar_data, media_type="image/png")


@router.post("/import")
async def import_characters(payload: dict, db: Session = Depends(get_db)):
    """导入角色（支持多种格式）"""
    imported = []
    data = payload.get("data", "")
    filename = payload.get("filename", "")

    def parse_and_save(char_data: dict, name: str = ""):
        char = CharacterModel(
            id=str(uuid.uuid4()),
            name=char_data.get("name") or name or "Unnamed",
            description=char_data.get("description", ""),
            personality=char_data.get("personality", ""),
            scenario=char_data.get("scenario", ""),
            greeting=char_data.get("greeting", ""),
            avatar=char_data.get("avatar", ""),
            tags=char_data.get("tags", []),
            examples=char_data.get("examples", []) or char_data.get("example_dialogue", "").split("\n") if char_data.get("example_dialogue") else [],
        )
        db.add(char)
        imported.append(char)

    # 尝试解析 JSON
    try:
        # PNG 嵌入格式（简化的 SillyTavern）
        if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".webp"):
            # 暂时跳过二进制解析
            pass
        else:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                for item in parsed:
                    parse_and_save(item)
            elif isinstance(parsed, dict):
                parse_and_save(parsed)
    except json.JSONDecodeError:
        # 可能是 SillyTavern JSON 格式
        try:
            # 尝试提取 JSON 部分
            json_start = data.find("{")
            if json_start != -1:
                json_text = data[json_start:]
                parsed = json.loads(json_text)
                if isinstance(parsed, list):
                    for item in parsed:
                        parse_and_save(item)
                else:
                    parse_and_save(parsed)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="无效的角色数据格式")

    db.commit()
    return [model_to_dict(c) for c in imported]


@router.get("/{char_id}/export/{format}")
async def export_character(char_id: str, format: str, db: Session = Depends(get_db)):
    """导出角色"""
    char = db.query(CharacterModel).filter(CharacterModel.id == char_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")

    char_dict = model_to_dict(char)

    if format == "sillytavern":
        return char_dict
    elif format == "tavernai":
        return char_dict
    elif format == "ooba":
        return {
            "name": char.name,
            "description": char.description,
            "personality": char.personality,
            "scenario": char.scenario,
            "greeting": char.greeting,
            "example_dialogue": "\n".join(char.examples or [])
        }
    else:
        return char_dict


class AIGenerateRequest(BaseModel):
    """AI 生成角色请求"""
    description: str
    style: Optional[str] = "creative"  # creative, formal, casual
    language: Optional[str] = "zh"  # zh, en


@router.post("/generate")
async def generate_character(payload: AIGenerateRequest, db: Session = Depends(get_db)):
    """
    通过对话描述 AI 生成角色
    用户输入一段描述，AI 根据描述生成完整的角色卡
    """
    try:
        # 构建提示词
        style_instructions = {
            "creative": "用富有创意和细节的方式描述角色性格和场景",
            "formal": "用正式、严谨的方式描述角色性格和场景",
            "casual": "用轻松、口语化的方式描述角色性格和场景"
        }
        style = style_instructions.get(payload.style, style_instructions["creative"])

        system_prompt = """你是一个专业的角色设计师。根据用户提供的描述，生成一个完整的角色卡。

请严格按照以下 JSON 格式返回，不要包含任何其他内容：
{
    "name": "角色名称",
    "description": "角色描述（简短介绍）",
    "personality": "性格特征（详细描述角色的性格、说话风格、行为特点）",
    "scenario": "场景设定（角色所在的背景环境）",
    "greeting": "开场白（角色主动说的第一句话，要自然）",
    "tags": ["标签1", "标签2", "标签3"],
    "examples": ["User: 用户的对话\\nCharacter: 角色的回复", "..."]
}

注意事项：
- name: 2-20个字符
- personality: 50-500个字符，详细描述性格
- greeting: 10-100个字符，要符合角色性格
- examples: 提供2-3个示例对话，展示角色的典型说话方式
- 所有内容使用中文"""

        user_prompt = f"""请根据以下描述生成一个角色：

描述：{payload.description}

要求：{style}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 使用 model_provider 调用 AI
        from backend.services.model_provider import chat_with_provider, ChatMessage, get_provider_registry
        from backend.config.settings import settings

        registry = get_provider_registry()
        registry.setup_from_settings(settings)

        provider_name = settings.default_model_type
        model_name = settings.default_model_name

        # 收集 AI 回复
        full_response = ""
        async for chunk in chat_with_provider(
            provider_name=provider_name,
            messages=[ChatMessage(role=m["role"], content=m["content"]) for m in messages],
            model=model_name,
            temperature=0.8,
            max_tokens=2048,
            stream=False
        ):
            full_response += chunk

        # 解析 JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', full_response)
        if not json_match:
            raise HTTPException(status_code=500, detail="AI 生成的格式无效")

        char_data = json.loads(json_match.group())

        # 创建角色
        char = CharacterModel(
            id=str(uuid.uuid4()),
            name=char_data.get("name", "未命名角色"),
            description=char_data.get("description", ""),
            personality=char_data.get("personality", ""),
            scenario=char_data.get("scenario", ""),
            greeting=char_data.get("greeting", ""),
            avatar="",
            tags=char_data.get("tags", []),
            examples=char_data.get("examples", []),
        )
        db.add(char)
        db.commit()
        db.refresh(char)

        return model_to_dict(char)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成角色失败: {str(e)}")


@router.post("/generate/preview")
async def preview_character_description(payload: AIGenerateRequest):
    """
    预览角色描述（不保存，只返回 AI 生成的预览）
    """
    try:
        system_prompt = """你是一个专业的角色设计师。根据用户提供的描述，生成一个完整的角色预览。

请严格按照以下 JSON 格式返回，不要包含任何其他内容：
{
    "name": "角色名称",
    "description": "角色描述（简短介绍）",
    "personality": "性格特征（详细描述角色的性格、说话风格、行为特点）",
    "scenario": "场景设定（角色所在的背景环境）",
    "greeting": "开场白（角色主动说的第一句话，要自然）",
    "tags": ["标签1", "标签2", "标签3"],
    "examples": ["User: 用户的对话\\nCharacter: 角色的回复", "..."]
}"""

        user_prompt = f"""请根据以下描述生成一个角色预览：

描述：{payload.description}

要求：生成符合描述的角色"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        from backend.services.model_provider import chat_with_provider, ChatMessage, get_provider_registry
        from backend.config.settings import settings

        registry = get_provider_registry()
        registry.setup_from_settings(settings)

        full_response = ""
        async for chunk in chat_with_provider(
            provider_name=settings.default_model_type,
            messages=[ChatMessage(role=m["role"], content=m["content"]) for m in messages],
            model=settings.default_model_name,
            temperature=0.8,
            max_tokens=2048,
            stream=False
        ):
            full_response += chunk

        import re
        json_match = re.search(r'\{[\s\S]*\}', full_response)
        if not json_match:
            return {"success": False, "preview": None, "raw": full_response}

        return {"success": True, "preview": json.loads(json_match.group())}

    except Exception as e:
        return {"success": False, "error": str(e)}
