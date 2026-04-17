"""记忆管理路由"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.database import get_db, MemoryModel

router = APIRouter()


class MemoryCreate(BaseModel):
    title: Optional[str] = ""
    content: str
    category: Optional[str] = ""
    tags: Optional[List[str]] = []
    importance: Optional[int] = 5
    source: Optional[str] = "manual"


class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: Optional[int] = None
    source: Optional[str] = None


def model_to_dict(mem: MemoryModel) -> dict:
    """转换记忆模型"""
    return {
        "id": mem.id,
        "title": mem.title,
        "content": mem.content,
        "category": mem.category,
        "tags": mem.tags or [],
        "importance": mem.importance,
        "source": mem.source,
        "accessCount": mem.access_count,
        "createdAt": mem.created_at.timestamp() * 1000 if mem.created_at else 0,
        "updatedAt": mem.updated_at.timestamp() * 1000 if mem.updated_at else 0,
        "lastAccessedAt": mem.last_accessed_at.timestamp() * 1000 if mem.last_accessed_at else 0,
    }


@router.get("")
async def list_memories(db: Session = Depends(get_db)):
    """获取所有记忆"""
    memories = db.query(MemoryModel).order_by(MemoryModel.created_at.desc()).all()
    return [model_to_dict(m) for m in memories]


@router.get("/{memory_id}")
async def get_memory(memory_id: str, db: Session = Depends(get_db)):
    """获取单个记忆"""
    mem = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="记忆不存在")
    mem.access_count = (mem.access_count or 0) + 1
    db.commit()
    return model_to_dict(mem)


@router.post("")
async def create_memory(data: MemoryCreate, db: Session = Depends(get_db)):
    """创建记忆"""
    mem = MemoryModel(
        id=str(uuid.uuid4()),
        title=data.title,
        content=data.content,
        category=data.category,
        tags=data.tags or [],
        importance=data.importance,
        source=data.source,
    )
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return model_to_dict(mem)


@router.put("/{memory_id}")
async def update_memory(memory_id: str, data: MemoryUpdate, db: Session = Depends(get_db)):
    """更新记忆"""
    mem = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="记忆不存在")
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(mem, key, value)
    db.commit()
    db.refresh(mem)
    return model_to_dict(mem)


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """删除记忆"""
    mem = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="记忆不存在")
    db.delete(mem)
    db.commit()
    return {"success": True}


@router.post("/search")
async def search_memories(payload: dict, db: Session = Depends(get_db)):
    """搜索记忆"""
    query = payload.get("query", "")
    limit = payload.get("limit", 10)
    memories = db.query(MemoryModel).filter(
        MemoryModel.content.contains(query)
    ).limit(limit).all()
    return [model_to_dict(m) for m in memories]
