"""世界设定管理路由"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.database import get_db, LorebookModel, LorebookEntryModel

router = APIRouter()


class EntryCreate(BaseModel):
    name: str
    content: Optional[str] = ""
    keywords: Optional[List[str]] = []
    priority: Optional[int] = 0
    enabled: Optional[bool] = True
    strategy: Optional[str] = "keyword"  # constant, keyword, chain
    probability: Optional[int] = 100     # 0-100
    insert_position: Optional[str] = "system"  # system, user, assistant
    exclusion_keywords: Optional[List[str]] = []
    exclusion_logic: Optional[str] = "none"  # none, and_any, and_all, not_any, not_all


class EntryUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    strategy: Optional[str] = None
    probability: Optional[int] = None
    insert_position: Optional[str] = None
    exclusion_keywords: Optional[List[str]] = None
    exclusion_logic: Optional[str] = None


class LorebookCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    scan_depth: Optional[int] = 2
    context_length: Optional[int] = 2048
    insert_mode: Optional[str] = "append"
    force_activation: Optional[bool] = False
    enabled: Optional[bool] = True
    max_recursion: Optional[int] = 3


class LorebookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scan_depth: Optional[int] = None
    context_length: Optional[int] = None
    insert_mode: Optional[str] = None
    force_activation: Optional[bool] = None
    enabled: Optional[bool] = None
    max_recursion: Optional[int] = None


def model_to_dict(book: LorebookModel) -> dict:
    """转换世界设定模型"""
    return {
        "id": book.id,
        "name": book.name,
        "description": book.description,
        "scanDepth": book.scan_depth,
        "contextLength": book.context_length,
        "insertMode": book.insert_mode,
        "forceActivation": book.force_activation,
        "enabled": book.enabled,
        "maxRecursion": book.max_recursion,
        "createdAt": book.created_at.timestamp() * 1000 if book.created_at else 0,
        "updatedAt": book.updated_at.timestamp() * 1000 if book.updated_at else 0,
        "entries": [
            {
                "id": e.id,
                "name": e.name,
                "content": e.content,
                "keywords": e.keywords or [],
                "priority": e.priority,
                "enabled": e.enabled,
                "strategy": e.strategy,
                "probability": e.probability,
                "insertPosition": e.insert_position,
                "exclusionKeywords": e.exclusion_keywords or [],
                "exclusionLogic": e.exclusion_logic,
                "createdAt": e.created_at.timestamp() * 1000 if e.created_at else 0,
                "updatedAt": e.updated_at.timestamp() * 1000 if e.updated_at else 0,
            }
            for e in sorted(book.entries, key=lambda x: -x.priority)
        ]
    }


# ============ 世界设定路由 ============

@router.get("")
async def list_lorebooks(db: Session = Depends(get_db)):
    """获取所有世界设定"""
    books = db.query(LorebookModel).order_by(LorebookModel.name).all()
    return [model_to_dict(b) for b in books]


@router.get("/{book_id}")
async def get_lorebook(book_id: str, db: Session = Depends(get_db)):
    """获取单个世界设定"""
    book = db.query(LorebookModel).filter(LorebookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="世界设定不存在")
    return model_to_dict(book)


@router.post("")
async def create_lorebook(data: LorebookCreate, db: Session = Depends(get_db)):
    """创建世界设定"""
    book = LorebookModel(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        scan_depth=data.scan_depth,
        context_length=data.context_length,
        insert_mode=data.insert_mode,
        force_activation=data.force_activation,
        enabled=data.enabled,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return model_to_dict(book)


@router.put("/{book_id}")
async def update_lorebook(book_id: str, data: LorebookUpdate, db: Session = Depends(get_db)):
    """更新世界设定"""
    book = db.query(LorebookModel).filter(LorebookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="世界设定不存在")
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return model_to_dict(book)


@router.delete("/{book_id}")
async def delete_lorebook(book_id: str, db: Session = Depends(get_db)):
    """删除世界设定"""
    book = db.query(LorebookModel).filter(LorebookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="世界设定不存在")
    db.delete(book)
    db.commit()
    return {"success": True}


# ============ 条目路由 ============

@router.post("/{book_id}/entries")
async def create_entry(book_id: str, data: EntryCreate, db: Session = Depends(get_db)):
    """添加条目"""
    book = db.query(LorebookModel).filter(LorebookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="世界设定不存在")
    entry = LorebookEntryModel(
        id=str(uuid.uuid4()),
        lorebook_id=book_id,
        name=data.name,
        content=data.content,
        keywords=data.keywords or [],
        priority=data.priority,
        enabled=data.enabled,
        strategy=data.strategy or "keyword",
        probability=data.probability or 100,
        insert_position=data.insert_position or "system",
        exclusion_keywords=data.exclusion_keywords or [],
        exclusion_logic=data.exclusion_logic or "none",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "id": entry.id,
        "name": entry.name,
        "content": entry.content,
        "keywords": entry.keywords or [],
        "priority": entry.priority,
        "enabled": entry.enabled,
        "strategy": entry.strategy,
        "probability": entry.probability,
        "insertPosition": entry.insert_position,
        "exclusionKeywords": entry.exclusion_keywords or [],
        "exclusionLogic": entry.exclusion_logic,
        "createdAt": entry.created_at.timestamp() * 1000 if entry.created_at else 0,
        "updatedAt": entry.updated_at.timestamp() * 1000 if entry.updated_at else 0,
    }


@router.put("/{book_id}/entries/{entry_id}")
async def update_entry(book_id: str, entry_id: str, data: EntryUpdate, db: Session = Depends(get_db)):
    """更新条目"""
    entry = db.query(LorebookEntryModel).filter(
        LorebookEntryModel.id == entry_id,
        LorebookEntryModel.lorebook_id == book_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return {
        "id": entry.id,
        "name": entry.name,
        "content": entry.content,
        "keywords": entry.keywords or [],
        "priority": entry.priority,
        "enabled": entry.enabled,
        "strategy": entry.strategy,
        "probability": entry.probability,
        "insertPosition": entry.insert_position,
        "exclusionKeywords": entry.exclusion_keywords or [],
        "exclusionLogic": entry.exclusion_logic,
        "createdAt": entry.created_at.timestamp() * 1000 if entry.created_at else 0,
        "updatedAt": entry.updated_at.timestamp() * 1000 if entry.updated_at else 0,
    }


@router.delete("/{book_id}/entries/{entry_id}")
async def delete_entry(book_id: str, entry_id: str, db: Session = Depends(get_db)):
    """删除条目"""
    entry = db.query(LorebookEntryModel).filter(
        LorebookEntryModel.id == entry_id,
        LorebookEntryModel.lorebook_id == book_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    db.delete(entry)
    db.commit()
    return {"success": True}
