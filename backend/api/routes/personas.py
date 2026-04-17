"""用户人设管理路由"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.database import get_db, PersonaModel

router = APIRouter()


class PersonaCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    avatar: Optional[str] = ""
    system_prompt: Optional[str] = ""


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    system_prompt: Optional[str] = None
    is_default: Optional[bool] = None


def model_to_dict(p: PersonaModel) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "avatar": p.avatar,
        "systemPrompt": p.system_prompt,
        "isDefault": p.is_default,
        "createdAt": p.created_at.timestamp() * 1000 if p.created_at else 0,
        "updatedAt": p.updated_at.timestamp() * 1000 if p.updated_at else 0,
    }


@router.get("")
async def list_personas(db: Session = Depends(get_db)):
    """获取所有用户人设"""
    personas = db.query(PersonaModel).order_by(PersonaModel.is_default.desc(), PersonaModel.name).all()
    return [model_to_dict(p) for p in personas]


@router.get("/{persona_id}")
async def get_persona(persona_id: str, db: Session = Depends(get_db)):
    """获取单个用户人设"""
    persona = db.query(PersonaModel).filter(PersonaModel.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="人设不存在")
    return model_to_dict(persona)


@router.get("/default")
async def get_default_persona(db: Session = Depends(get_db)):
    """获取默认用户人设"""
    persona = db.query(PersonaModel).filter(PersonaModel.is_default == True).first()
    if not persona:
        # 返回一个默认人设
        return {
            "id": "default",
            "name": "用户",
            "description": "默认用户人设",
            "avatar": "",
            "systemPrompt": "你是与 AI 角色对话的用户。",
            "isDefault": True,
            "createdAt": 0,
            "updatedAt": 0,
        }
    return model_to_dict(persona)


@router.post("")
async def create_persona(data: PersonaCreate, db: Session = Depends(get_db)):
    """创建用户人设"""
    # 检查是否已经有默认人设
    has_default = db.query(PersonaModel).filter(PersonaModel.is_default == True).count() > 0
    persona = PersonaModel(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        avatar=data.avatar,
        system_prompt=data.system_prompt,
        is_default=not has_default,  # 第一个设为默认
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return model_to_dict(persona)


@router.put("/{persona_id}")
async def update_persona(persona_id: str, data: PersonaUpdate, db: Session = Depends(get_db)):
    """更新用户人设"""
    persona = db.query(PersonaModel).filter(PersonaModel.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="人设不存在")

    # 如果设置为默认，先取消其他默认
    if data.is_default:
        db.query(PersonaModel).filter(PersonaModel.is_default == True).update({"is_default": False})

    for key, value in data.model_dump(exclude_none=True).items():
        setattr(persona, key.replace("_", "_"), value)
    db.commit()
    db.refresh(persona)
    return model_to_dict(persona)


@router.delete("/{persona_id}")
async def delete_persona(persona_id: str, db: Session = Depends(get_db)):
    """删除用户人设"""
    persona = db.query(PersonaModel).filter(PersonaModel.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="人设不存在")

    was_default = persona.is_default
    db.delete(persona)

    # 如果删除的是默认人设，将第一个设为默认
    if was_default:
        first = db.query(PersonaModel).first()
        if first:
            first.is_default = True

    db.commit()
    return {"success": True}
