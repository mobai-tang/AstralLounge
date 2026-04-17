"""
自动记忆插件
自动将对话中的重要内容提取并保存到记忆系统
"""
import re
import uuid
import time
from typing import Dict, Any, List
from backend.plugins.plugin_manager import BaseSkill, SkillMetadata


class AutoMemorySkill(BaseSkill):
    """自动记忆技能 - 自动提取对话中的重要信息，写入 Redis"""

    metadata = SkillMetadata(
        name="auto-memory",
        version="2.0.0",
        description="自动将对话中的重要内容提取并保存到记忆系统（Redis 存储）",
        author="AstralLounge",
        triggers=["memory", "自动记忆", "important"],
        enabled=True,
        category="memory",
        icon="🧠",
        config_schema={
            "type": "object",
            "properties": {
                "auto_extract": {"type": "boolean", "default": True},
                "importance_threshold": {"type": "number", "default": 0.7},
                "max_memories_per_session": {"type": "integer", "default": 10},
                "min_content_length": {"type": "integer", "default": 10},
                "duplicate_check": {"type": "boolean", "default": True},
            }
        }
    )

    IMPORTANCE_PATTERNS = [
        (r"请记住[：:](.+?)(?=$|\n)", "important"),
        (r"记住[：:](.+?)(?=$|\n)", "important"),
        (r"重要的是[：:](.+?)(?=$|\n)", "important"),
        (r"关键[是点]([：:].+?)(?=$|\n)", "important"),
        (r"我最喜欢的[是](.+?)(?=[。\n]|$)", "preference"),
        (r"我不喜欢[的是](.+?)(?=[。\n]|$)", "preference"),
        (r"我的爱好[是](.+?)(?=[。\n]|$)", "preference"),
        (r"我的名字[是叫](.+?)(?=[。\n]|$)", "identity"),
        (r"我住在[](.+?)(?=[。\n]|$)", "identity"),
        (r"我的(.+?)是(.+?)(?=[。\n]|$)", "fact"),
    ]

    _recent_hashes: Dict[str, int] = {}

    async def on_load(self):
        threshold = self.config.get("importance_threshold", 0.7)
        auto_extract = self.config.get("auto_extract", True)
        print(f"[自动记忆] 插件已加载 - 阈值: {threshold}, 自动提取: {auto_extract}")

    async def process_output(self, text: str, context: Dict[str, Any]) -> str:
        """处理输出，检测是否需要保存到记忆"""
        if not self.config.get("auto_extract", True):
            return text
        if not text or len(text) < self.config.get("min_content_length", 10):
            return text

        session_id = context.get("session_id", "")
        character = context.get("character", "")

        extractions = self._extract_important_info(text)
        if not extractions:
            return text

        from backend.services import redis_manager as redis_m
        from backend.models.database import get_db, MemoryModel

        saved_count = 0
        max_memories = self.config.get("max_memories_per_session", 10)

        for content, category, importance in extractions:
            if saved_count >= max_memories:
                break

            if self.config.get("duplicate_check", True):
                content_hash = hash(content.strip())
                cache_key = f"{session_id}:{content_hash}"
                if cache_key in self._recent_hashes:
                    continue
                self._recent_hashes[cache_key] = 1

            # 检查是否已存在（先查 Redis）
            if redis_m.is_redis_available():
                exists = await redis_m.mem_search(query=content.strip(), limit=1)
                if exists:
                    continue
            else:
                db = next(get_db())
                try:
                    existing = db.query(MemoryModel).filter(
                        MemoryModel.content == content.strip()
                    ).first()
                    if existing:
                        continue
                finally:
                    db.close()

            # 构建记忆数据
            now_ms = int(time.time() * 1000)
            mem_data = {
                "id": str(uuid.uuid4()),
                "title": self._generate_title(content),
                "content": content.strip(),
                "category": category,
                "tags": self._generate_tags(content, category, character),
                "importance": int(importance * 10),
                "source": "auto",
                "createdAt": now_ms,
                "updatedAt": now_ms,
                "lastAccessedAt": 0,
                "accessCount": 0,
            }

            # 写入 Redis（优先）
            if redis_m.is_redis_available():
                await redis_m.mem_save(mem_data)
                print(f"  [自动记忆] Redis保存: {mem_data['title']} ({category})")
            else:
                # Redis 不可用时，写入 SQLite
                db = next(get_db())
                try:
                    mem = MemoryModel(
                        id=mem_data["id"],
                        title=mem_data["title"],
                        content=mem_data["content"],
                        category=mem_data["category"],
                        tags=mem_data["tags"],
                        importance=mem_data["importance"],
                        source="auto",
                    )
                    db.add(mem)
                    db.commit()
                    print(f"  [自动记忆] SQLite保存: {mem_data['title']} ({category})")
                except Exception as e:
                    print(f"  [自动记忆] SQLite保存失败: {e}")
                    db.rollback()
                finally:
                    db.close()

            saved_count += 1

        if saved_count > 0:
            print(f"  [自动记忆] 本次共保存 {saved_count} 条")

        # 定期清理缓存
        if len(self._recent_hashes) > 1000:
            keys = list(self._recent_hashes.keys())[:500]
            for k in keys:
                del self._recent_hashes[k]

        return text

    def _extract_important_info(self, text: str) -> List:
        """从文本中提取重要信息"""
        results = []
        for pattern, category in self.IMPORTANCE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    content = "".join(match).strip()
                else:
                    content = match.strip()
                if len(content) < 5:
                    continue
                importance = self._calculate_importance(content, category)
                if importance >= self.config.get("importance_threshold", 0.7):
                    results.append((content, category, importance))

        fact_patterns = [
            r"(?:顺便一提|对了|另外)[，,]([^。\n]{10,100}?)(?=[。\n]|$)",
        ]
        for pattern in fact_patterns:
            matches = re.findall(pattern, text)
            for content in matches:
                if len(content) >= 10:
                    importance = self._calculate_importance(content, "fact")
                    if importance >= self.config.get("importance_threshold", 0.7):
                        results.append((content.strip(), "fact", importance))

        seen = set()
        unique_results = []
        for item in results:
            key = item[0].strip()
            if key not in seen:
                seen.add(key)
                unique_results.append(item)
        return unique_results

    def _calculate_importance(self, content: str, category: str) -> float:
        """计算内容重要性分数"""
        category_weights = {
            "identity": 0.9,
            "important": 0.85,
            "preference": 0.8,
            "fact": 0.7,
        }
        base = category_weights.get(category, 0.6)
        length = len(content)
        if length < 10:
            base -= 0.2
        elif length > 200:
            base -= 0.1
        elif 20 <= length <= 100:
            base += 0.1
        return min(1.0, max(0.0, base))

    def _generate_title(self, content: str) -> str:
        if len(content) <= 20:
            return content
        return content[:20] + "..."

    def _generate_tags(self, content: str, category: str, character: str) -> List[str]:
        tags = [category]
        if character:
            tags.append(f"角色:{character}")
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]{2,5}', content)
        for word in words[:3]:
            if len(word) >= 2 and word not in tags:
                tags.append(word)
        return tags

    async def on_unload(self):
        self._recent_hashes.clear()
        print("[自动记忆] 插件已卸载")
