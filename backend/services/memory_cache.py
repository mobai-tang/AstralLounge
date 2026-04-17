"""
Redis 记忆服务
AI 通过 Redis 读取旧记忆，支持语义搜索和关键词搜索
"""
import json
import hashlib
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.services.redis_manager import get_redis, is_redis_available


MEMORY_KEY_PREFIX = "astral:memory:"
MEMORY_INDEX_KEY = "astral:memory:index"
MEMORY_ACCESS_KEY = "astral:memory:access:"
SESSION_CONTEXT_KEY = "astral:session:context:"
RECENT_MEMORIES_KEY = "astral:recent:memories"


class MemoryCache:
    """Redis 记忆缓存层，AI 直接读取旧记忆"""

    def __init__(self):
        self.redis = None

    async def ensure_connected(self):
        if self.redis is None:
            self.redis = await get_redis()

    def _memory_key(self, memory_id: str) -> str:
        return f"{MEMORY_KEY_PREFIX}{memory_id}"

    def _generate_id(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()[:16]

    async def store_memory(self, memory_id: str, data: Dict[str, Any], ttl: int = 0) -> bool:
        """存储单条记忆到 Redis"""
        await self.ensure_connected()
        if not self.redis:
            return False

        try:
            key = self._memory_key(memory_id)
            value = json.dumps(data, ensure_ascii=False)

            if ttl > 0:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)

            await self.redis.sadd(MEMORY_INDEX_KEY, memory_id)
            logger.debug(f"记忆已存入 Redis: {memory_id}")
            return True
        except Exception as e:
            logger.warning(f"Redis 存储记忆失败: {e}")
            return False

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """读取单条记忆"""
        await self.ensure_connected()
        if not self.redis:
            return None

        try:
            key = self._memory_key(memory_id)
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis 读取记忆失败: {e}")
            return None

    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        await self.ensure_connected()
        if not self.redis:
            return False

        try:
            await self.redis.delete(self._memory_key(memory_id))
            await self.redis.srem(MEMORY_INDEX_KEY, memory_id)
            return True
        except Exception as e:
            logger.warning(f"Redis 删除记忆失败: {e}")
            return False

    async def search_by_keywords(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """关键词搜索记忆"""
        await self.ensure_connected()
        if not self.redis:
            return []

        try:
            memory_ids = await self.redis.smembers(MEMORY_INDEX_KEY)
            if not memory_ids:
                return []

            query_lower = query.lower()
            query_words = [w for w in query_lower.split() if len(w) >= 2]
            results = []

            for mem_id in memory_ids:
                mem = await self.get_memory(mem_id)
                if not mem:
                    continue

                content = (mem.get("content", "") or "").lower()
                title = (mem.get("title", "") or "").lower()
                tags = " ".join(mem.get("tags", []) or []).lower()
                combined = f"{title} {content} {tags}"

                score = 0
                for word in query_words:
                    if word in combined:
                        score += 1

                if score > 0:
                    mem["_search_score"] = score
                    results.append(mem)

            results.sort(key=lambda x: -x["_search_score"])

            importance_weight = 3
            for r in results:
                imp = r.get("importance", 5)
                r["_final_score"] = r["_search_score"] * importance_weight + imp
            results.sort(key=lambda x: -x["_final_score"])

            return results[:limit]
        except Exception as e:
            logger.warning(f"Redis 关键词搜索失败: {e}")
            return []

    async def get_all_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有记忆（按重要性/访问频率排序）"""
        await self.ensure_connected()
        if not self.redis:
            return []

        try:
            memory_ids = await self.redis.smembers(MEMORY_INDEX_KEY)
            if not memory_ids:
                return []

            memories = []
            for mem_id in memory_ids:
                mem = await self.get_memory(mem_id)
                if mem:
                    memories.append(mem)

            memories.sort(key=lambda x: (
                -(x.get("importance", 5)),
                -(x.get("access_count", 0)),
            ))
            return memories[:limit]
        except Exception as e:
            logger.warning(f"Redis 获取全部记忆失败: {e}")
            return []

    async def increment_access(self, memory_id: str) -> None:
        """增加记忆访问次数"""
        await self.ensure_connected()
        if not self.redis:
            return

        try:
            mem = await self.get_memory(memory_id)
            if mem:
                mem["access_count"] = mem.get("access_count", 0) + 1
                mem["last_accessed_at"] = self._now_ts()
                await self.store_memory(memory_id, mem)

            await self.redis.zincrby(MEMORY_ACCESS_KEY, 1, memory_id)
        except Exception:
            pass

    async def save_session_context(self, session_id: str, context: Dict[str, Any], ttl: int = 86400 * 7) -> bool:
        """保存会话上下文（用于 AI 读取之前的对话历史记忆）"""
        await self.ensure_connected()
        if not self.redis:
            return False

        try:
            key = f"{SESSION_CONTEXT_KEY}{session_id}"
            await self.redis.setex(key, ttl, json.dumps(context, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"Redis 保存会话上下文失败: {e}")
            return False

    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话上下文"""
        await self.ensure_connected()
        if not self.redis:
            return None

        try:
            key = f"{SESSION_CONTEXT_KEY}{session_id}"
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def append_to_recent(self, memory_id: str, ttl: int = 86400) -> None:
        """追加到最近访问列表"""
        await self.ensure_connected()
        if not self.redis:
            return

        try:
            await self.redis.lpush(RECENT_MEMORIES_KEY, memory_id)
            await self.redis.ltrim(RECENT_MEMORIES_KEY, 0, 99)
            await self.redis.expire(RECENT_MEMORIES_KEY, ttl)
        except Exception:
            pass

    async def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近访问的记忆"""
        await self.ensure_connected()
        if not self.redis:
            return []

        try:
            memory_ids = await self.redis.lrange(RECENT_MEMORIES_KEY, 0, limit - 1)
            results = []
            for mem_id in memory_ids:
                mem = await self.get_memory(mem_id)
                if mem:
                    results.append(mem)
            return results
        except Exception:
            return []

    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        await self.ensure_connected()
        if not self.redis:
            return {"total": 0, "categories": {}, "avg_importance": 0}

        try:
            memory_ids = await self.redis.smembers(MEMORY_INDEX_KEY)
            total = len(memory_ids)
            categories: Dict[str, int] = {}
            total_importance = 0

            for mem_id in memory_ids:
                mem = await self.get_memory(mem_id)
                if mem:
                    cat = mem.get("category", "未分类")
                    categories[cat] = categories.get(cat, 0) + 1
                    total_importance += mem.get("importance", 5)

            return {
                "total": total,
                "categories": categories,
                "avg_importance": round(total_importance / total, 1) if total > 0 else 0,
            }
        except Exception:
            return {"total": 0, "categories": {}, "avg_importance": 0}

    async def sync_from_sqlite(self, memories: List[Dict[str, Any]]) -> int:
        """从 SQLite 批量同步记忆到 Redis"""
        await self.ensure_connected()
        if not self.redis:
            return 0

        count = 0
        for mem in memories:
            memory_id = mem.get("id", "")
            if memory_id:
                if await self.store_memory(memory_id, mem):
                    count += 1
        logger.info(f"已同步 {count} 条记忆到 Redis")
        return count

    async def full_sync_to_sqlite(self) -> List[Dict[str, Any]]:
        """从 Redis 导出全部记忆（用于回写 SQLite）"""
        await self.ensure_connected()
        if not self.redis:
            return []

        try:
            memory_ids = await self.redis.smembers(MEMORY_INDEX_KEY)
            memories = []
            for mem_id in memory_ids:
                mem = await self.get_memory(mem_id)
                if mem:
                    mem["id"] = mem_id
                    memories.append(mem)
            return memories
        except Exception:
            return []

    @staticmethod
    def _now_ts() -> int:
        import time
        return int(time.time() * 1000)


memory_cache = MemoryCache()
