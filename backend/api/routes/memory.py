"""记忆管理路由"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.database import get_db, MemoryModel
from backend.services import redis_manager as redis_m

router = APIRouter(prefix="/api/memory", tags=["memory"])


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


class MemorySearch(BaseModel):
    query: str = ""
    category: str = ""
    limit: int = 20
    sort_by: str = "heat"


def model_to_dict(mem) -> dict:
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


# ============================================================
# 核心 CRUD（Redis 优先，SQLite 写穿透）
# ============================================================

@router.get("")
async def list_memories(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("newest", regex="^(newest|oldest|heat)$"),
    db: Session = Depends(get_db),
):
    """获取记忆列表"""
    if redis_m.is_redis_available():
        mems = await redis_m.mem_list_all(limit=limit, offset=offset, sort=sort)
        if mems:
            return mems
        # Redis 为空时从 SQLite 同步
        db_mems = db.query(MemoryModel).order_by(
            MemoryModel.created_at.desc() if sort == "newest"
            else MemoryModel.created_at.asc()
        ).offset(offset).limit(limit).all()
        for m in db_mems:
            await redis_m.mem_save(model_to_dict(m))
        return [model_to_dict(m) for m in db_mems]

    db_mems = db.query(MemoryModel).order_by(
        MemoryModel.created_at.desc() if sort == "newest"
        else MemoryModel.created_at.asc()
    ).offset(offset).limit(limit).all()
    return [model_to_dict(m) for m in db_mems]


@router.get("/stats")
async def get_memory_stats():
    """获取记忆统计"""
    if redis_m.is_redis_available():
        return await redis_m.mem_get_stats()

    db: Session = next(get_db())
    total = db.query(MemoryModel).count()
    manual = db.query(MemoryModel).filter(
        (MemoryModel.source == "manual") | (MemoryModel.source == None)
    ).count()
    auto = db.query(MemoryModel).filter(MemoryModel.source == "auto").count()
    summarized = db.query(MemoryModel).filter(MemoryModel.source == "summarized").count()
    return {"total": total, "manual": manual, "auto": auto, "summarized": summarized}


@router.get("/for-ai")
async def get_memories_for_ai(
    query: str = "",
    category: str = "",
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("heat", regex="^(heat|newest|relevance)$"),
    db: Session = Depends(get_db),
):
    """
    AI 读取记忆的专用接口。
    返回按热度排序的高相关性记忆，减少 AI 上下文噪音。
    """
    if redis_m.is_redis_available():
        return await redis_m.mem_get_for_ai(
            query=query, category=category, limit=limit, sort_by=sort_by
        )

    # SQLite 回退
    q = db.query(MemoryModel)
    if query:
        q = q.filter(MemoryModel.content.contains(query))
    if category:
        q = q.filter(MemoryModel.category == category)

    mems = q.order_by(MemoryModel.access_count.desc()).limit(limit).all()
    return [model_to_dict(m) for m in mems]


@router.get("/category/{category}")
async def get_memories_by_category(category: str, db: Session = Depends(get_db)):
    """按类别获取记忆"""
    if redis_m.is_redis_available():
        mems = await redis_m.mem_list_by_category(category)
        if mems:
            return mems

    db_mems = db.query(MemoryModel).filter(MemoryModel.category == category).all()
    return [model_to_dict(m) for m in db_mems]


@router.get("/tag/{tag}")
async def get_memories_by_tag(tag: str, db: Session = Depends(get_db)):
    """按标签获取记忆"""
    if redis_m.is_redis_available():
        mems = await redis_m.mem_list_by_tag(tag)
        if mems:
            return mems

    db_mems = db.query(MemoryModel).filter(MemoryModel.tags.any(tag)).all()
    return [model_to_dict(m) for m in db_mems]


@router.get("/{memory_id}")
async def get_memory(memory_id: str, db: Session = Depends(get_db)):
    """获取单个记忆"""
    if redis_m.is_redis_available():
        mem = await redis_m.mem_get(memory_id)
        if mem:
            return mem

    mem = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="记忆不存在")
    mem.access_count = (mem.access_count or 0) + 1
    db.commit()
    return model_to_dict(mem)


@router.post("")
async def create_memory(data: MemoryCreate, db: Session = Depends(get_db)):
    """创建记忆（Redis + SQLite 双写）"""
    mem_id = str(uuid.uuid4())
    now_ms = int(uuid.uuid1().time * 1000)

    mem_data = {
        "id": mem_id,
        "title": data.title,
        "content": data.content,
        "category": data.category,
        "tags": data.tags or [],
        "importance": data.importance,
        "source": data.source,
        "createdAt": now_ms,
        "updatedAt": now_ms,
        "lastAccessedAt": 0,
        "accessCount": 0,
    }

    # Redis 优先写入
    if redis_m.is_redis_available():
        await redis_m.mem_save(mem_data)

    # SQLite 持久化
    mem = MemoryModel(
        id=mem_id,
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

    updates = data.model_dump(exclude_none=True)
    if "tags" in updates and updates["tags"] is None:
        updates.pop("tags")

    # Redis 更新
    if redis_m.is_redis_available():
        await redis_m.mem_update(memory_id, updates)

    # SQLite 更新
    for key, value in updates.items():
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

    # Redis 删除
    if redis_m.is_redis_available():
        await redis_m.mem_delete(memory_id)

    # SQLite 删除
    db.delete(mem)
    db.commit()
    return {"success": True}


@router.post("/search")
async def search_memories(
    payload: MemorySearch,
    db: Session = Depends(get_db),
):
    """搜索记忆"""
    if redis_m.is_redis_available():
        return await redis_m.mem_search(
            query=payload.query,
            category=payload.category,
            limit=payload.limit,
            sort_by=payload.sort_by,
        )

    q = db.query(MemoryModel)
    if payload.query:
        q = q.filter(MemoryModel.content.contains(payload.query))
    if payload.category:
        q = q.filter(MemoryModel.category == payload.category)
    mems = q.order_by(MemoryModel.access_count.desc()).limit(payload.limit).all()
    return [model_to_dict(m) for m in mems]


@router.post("/sync-from-sqlite")
async def sync_from_sqlite(db: Session = Depends(get_db)):
    """从 SQLite 同步所有记忆到 Redis（手动触发）"""
    if not redis_m.is_redis_available():
        return {"success": False, "message": "Redis 不可用"}

    mems = db.query(MemoryModel).all()
    count = await redis_m.mem_sync_from_sqlite([model_to_dict(m) for m in mems])
    return {"success": True, "count": count}
