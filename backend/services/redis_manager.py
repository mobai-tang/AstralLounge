"""
Redis 连接与记忆管理
"""
import json
import uuid
import time
from typing import Optional, List, Dict, Any
import redis.asyncio as redis
from loguru import logger

_redis_client: Optional[redis.Redis] = None


def is_redis_available() -> bool:
    """检查 Redis 是否可用"""
    return _redis_client is not None


async def get_redis() -> Optional[redis.Redis]:
    """获取 Redis 客户端"""
    return _redis_client


async def init_redis(host: str, port: int, password: str, db: int, enabled: bool) -> None:
    """初始化 Redis 连接"""
    global _redis_client

    if not enabled:
        logger.info("Redis 已禁用，跳过连接")
        return

    try:
        _redis_client = redis.Redis(
            host=host,
            port=port,
            password=password or None,
            db=db,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        await _redis_client.ping()
        logger.info(f"Redis 连接成功: {host}:{port}")
    except redis.ConnectionError as e:
        logger.warning(f"Redis 连接失败: {e}，记忆将使用 SQLite 回退")
        _redis_client = None
    except Exception as e:
        logger.warning(f"Redis 初始化异常: {e}，记忆将使用 SQLite 回退")
        _redis_client = None


async def close_redis() -> None:
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("Redis 连接已关闭")
        except Exception:
            pass
        _redis_client = None


# ============================================================
# 记忆键前缀
# ============================================================
MEM_KEY = "mem:"                          # 单条记忆 Hash: mem:{id}
MEM_ALL = "mem:all"                       # 所有记忆 ID 的 Set
MEM_CAT_PREFIX = "mem:cat:"               # 按类别: mem:cat:{category}
MEM_TAG_PREFIX = "mem:tag:"              # 按标签: mem:tag:{tag}
MEM_IMP_PREFIX = "mem:imp:"              # 按重要性: mem:imp:{n}
MEM_RECENT = "mem:recent"                 # 按时间排序的 ZSet
MEM_HEAT = "mem:heat"                    # 热度 ZSet（访问次数 + 时间衰减）


def _mem_key(mem_id: str) -> str:
    return f"{MEM_KEY}{mem_id}"


def _cat_key(cat: str) -> str:
    return f"{MEM_CAT_PREFIX}{cat}"


def _tag_key(tag: str) -> str:
    return f"{MEM_TAG_PREFIX}{tag}"


def _imp_key(n: int) -> str:
    return f"{MEM_IMP_PREFIX}{n}"


def _now_ts() -> float:
    return time.time()


# ============================================================
# 记忆 CRUD
# ============================================================

async def mem_save(mem: Dict[str, Any]) -> Dict[str, Any]:
    """保存单条记忆到 Redis，返回完整记忆数据"""
    r = await get_redis()
    if not r:
        return mem

    mem_id = mem.get("id") or str(uuid.uuid4())
    now = _now_ts()

    # 构建存储数据
    data = {
        "id": mem_id,
        "title": mem.get("title") or "",
        "content": mem.get("content", ""),
        "category": mem.get("category") or "",
        "tags": json.dumps(mem.get("tags") or [], ensure_ascii=False),
        "importance": mem.get("importance") or 5,
        "source": mem.get("source") or "manual",
        "accessCount": mem.get("accessCount") or 0,
        "createdAt": mem.get("createdAt") or int(now * 1000),
        "updatedAt": int(now * 1000),
        "lastAccessedAt": mem.get("lastAccessedAt") or 0,
    }

    pipe = r.pipeline()

    # 主数据
    pipe.hset(_mem_key(mem_id), mapping=data)

    # 加入各索引
    pipe.sadd(MEM_ALL, mem_id)
    pipe.zadd(MEM_RECENT, {mem_id: data["createdAt"]})

    cat = data["category"]
    if cat:
        pipe.sadd(_cat_key(cat), mem_id)

    imp = data["importance"]
    pipe.sadd(_imp_key(imp), mem_id)

    tags: List[str] = mem.get("tags") or []
    for tag in tags:
        pipe.sadd(_tag_key(tag), mem_id)

    await pipe.execute()
    logger.debug(f"[Redis Memory] 保存: {mem_id} - {data['title'] or data['content'][:20]}")
    return data


async def mem_get(mem_id: str) -> Optional[Dict[str, Any]]:
    """读取单条记忆，并增加热度"""
    r = await get_redis()
    if not r:
        return None

    data = await r.hgetall(_mem_key(mem_id))
    if not data:
        return None

    # 解析 tags
    if "tags" in data and data["tags"]:
        try:
            data["tags"] = json.loads(data["tags"])
        except Exception:
            data["tags"] = []
    else:
        data["tags"] = []

    # 类型转换
    data["importance"] = int(data.get("importance", 5))
    data["accessCount"] = int(data.get("accessCount", 0))
    data["createdAt"] = int(data.get("createdAt", 0))
    data["updatedAt"] = int(data.get("updatedAt", 0))
    data["lastAccessedAt"] = int(data.get("lastAccessedAt", 0))

    # 增加热度 & 更新时间戳
    await r.zincrby(MEM_HEAT, 1, mem_id)
    await r.hset(_mem_key(mem_id), "lastAccessedAt", int(_now_ts() * 1000))
    await r.hincrby(_mem_key(mem_id), "accessCount", 1)

    return data


async def mem_update(mem_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新记忆"""
    r = await get_redis()
    if not r:
        return None

    existing = await r.hgetall(_mem_key(mem_id))
    if not existing:
        return None

    now = int(_now_ts() * 1000)

    # 处理 tags 序列化
    if "tags" in updates:
        updates["tags"] = json.dumps(updates["tags"] or [], ensure_ascii=False)

    updates["updatedAt"] = now
    await r.hset(_mem_key(mem_id), mapping=updates)

    # 如果 importance 变了，更新索引
    new_imp = updates.get("importance")
    old_imp = existing.get("importance")
    if new_imp is not None and str(new_imp) != str(old_imp):
        await r.srem(_imp_key(int(old_imp)), mem_id)
        await r.sadd(_imp_key(int(new_imp)), mem_id)

    return await mem_get(mem_id)


async def mem_delete(mem_id: str) -> bool:
    """删除记忆"""
    r = await get_redis()
    if not r:
        return False

    data = await r.hgetall(_mem_key(mem_id))
    if not data:
        return False

    pipe = r.pipeline()
    pipe.delete(_mem_key(mem_id))
    pipe.srem(MEM_ALL, mem_id)
    pipe.zrem(MEM_RECENT, mem_id)
    pipe.zrem(MEM_HEAT, mem_id)

    cat = data.get("category")
    if cat:
        pipe.srem(_cat_key(cat), mem_id)

    imp = data.get("importance")
    if imp:
        pipe.srem(_imp_key(int(imp)), mem_id)

    try:
        tags = json.loads(data.get("tags") or "[]")
    except Exception:
        tags = []
    for tag in tags:
        pipe.srem(_tag_key(tag), mem_id)

    await pipe.execute()
    logger.debug(f"[Redis Memory] 删除: {mem_id}")
    return True


# ============================================================
# 批量读取
# ============================================================

async def mem_list_all(
    limit: int = 100,
    offset: int = 0,
    sort: str = "newest"
) -> List[Dict[str, Any]]:
    """列出所有记忆，按指定顺序"""
    r = await get_redis()
    if not r:
        return []

    if sort == "newest":
        mem_ids = await r.zrevrange(MEM_RECENT, offset, offset + limit - 1)
    elif sort == "oldest":
        mem_ids = await r.zrange(MEM_RECENT, offset, offset + limit - 1)
    elif sort == "heat":
        mem_ids = await r.zrevrange(MEM_HEAT, offset, offset + limit - 1)
    else:
        mem_ids = await r.srandmember(MEM_ALL, limit)

    results = []
    for mid in mem_ids:
        mem = await mem_get(mid)
        if mem:
            results.append(mem)
    return results


async def mem_list_by_category(category: str) -> List[Dict[str, Any]]:
    """按类别读取"""
    r = await get_redis()
    if not r:
        return []

    mem_ids = await r.smembers(_cat_key(category))
    results = []
    for mid in mem_ids:
        mem = await mem_get(mid)
        if mem:
            results.append(mem)
    return results


async def mem_list_by_tag(tag: str) -> List[Dict[str, Any]]:
    """按标签读取"""
    r = await get_redis()
    if not r:
        return []

    mem_ids = await r.smembers(_tag_key(tag))
    results = []
    for mid in mem_ids:
        mem = await mem_get(mid)
        if mem:
            results.append(mem)
    return results


async def mem_search(
    query: str,
    limit: int = 10,
    category: str = "",
    min_importance: int = 1,
    sort_by: str = "relevance"
) -> List[Dict[str, Any]]:
    """搜索记忆（关键词匹配 + 热度排序）"""
    r = await get_redis()
    if not r:
        return []

    q = query.lower()

    # 取候选集：全量 or 按类别
    if category:
        mem_ids = await r.smembers(_cat_key(category))
    else:
        mem_ids = await r.smembers(MEM_ALL)

    # 过滤 + 排序
    scored = []
    for mid in mem_ids:
        mem = await r.hgetall(_mem_key(mid))
        if not mem:
            continue
        content = mem.get("content", "").lower()
        title = mem.get("title", "").lower()

        if q not in content and q not in title:
            continue

        imp = int(mem.get("importance", 5))
        if imp < min_importance:
            continue

        # 简单相关性评分
        score = 0
        if q in title:
            score += 10
        if q in content:
            score += 5
        score += imp * 2

        if sort_by == "heat":
            heat = await r.zscore(MEM_HEAT, mid) or 0
            score += heat

        scored.append((score, mid))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for _, mid in scored[:limit]:
        m = await mem_get(mid)
        if m:
            results.append(m)
    return results


async def mem_get_for_ai(
    query: str = "",
    category: str = "",
    limit: int = 20,
    sort_by: str = "heat"
) -> List[Dict[str, Any]]:
    """AI 读取记忆的专用接口，按热度优先返回"""
    r = await get_redis()
    if not r:
        return []

    if query:
        return await mem_search(query=query, limit=limit, category=category, sort_by=sort_by)

    if category:
        return await mem_list_by_category(category)

    # 默认按热度 + 重要性返回
    if sort_by == "heat":
        mem_ids = await r.zrevrange(MEM_HEAT, 0, limit - 1)
    else:
        mem_ids = await r.zrevrange(MEM_RECENT, 0, limit - 1)

    results = []
    for mid in mem_ids:
        mem = await mem_get(mid)
        if mem:
            results.append(mem)
    return results


async def mem_count() -> int:
    """统计记忆总数"""
    r = await get_redis()
    if not r:
        return 0
    return await r.scard(MEM_ALL)


async def mem_get_stats() -> Dict[str, Any]:
    """获取记忆统计"""
    r = await get_redis()
    if not r:
        return {"total": 0, "manual": 0, "auto": 0, "summarized": 0, "categories": []}

    total = await r.scard(MEM_ALL)
    cats = []
    for cat in await r.keys(f"{MEM_CAT_PREFIX}*"):
        cat_name = cat.replace(MEM_CAT_PREFIX, "")
        cats.append({"name": cat_name, "count": await r.scard(cat)})

    return {
        "total": total,
        "categories": cats,
    }


async def mem_sync_from_sqlite(memories: List[Dict[str, Any]]) -> int:
    """从 SQLite 同步记忆到 Redis（启动时调用）"""
    r = await get_redis()
    if not r:
        return 0

    count = 0
    for mem in memories:
        await mem_save(mem)
        count += 1

    logger.info(f"[Redis Memory] 从 SQLite 同步了 {count} 条记忆")
    return count
