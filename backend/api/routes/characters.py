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
