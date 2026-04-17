"""
网络搜索插件
集成多种搜索引擎进行网络搜索
"""
from typing import Dict, Any, List, Optional
import httpx
from backend.plugins.plugin_manager import BaseSkill, SkillMetadata


class WebSearchSkill(BaseSkill):
    """网络搜索技能"""

    metadata = SkillMetadata(
        name="web-search",
        version="1.0.0",
        description="集成多种搜索引擎，支持 Google、Bing、Tavily、Searxng 等",
        author="AstralLounge",
        triggers=["search", "搜索", "查找"],
        enabled=True,
        category="tools",
        icon="🔍",
        config_schema={
            "type": "object",
            "properties": {
                "default_engine": {"type": "string", "default": "serper"},
                "engines": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["serper", "tavily", "searxng"]
                }
            }
        }
    )

    def __init__(self):
        super().__init__()
        self.search_engines = {
            "serper": self._search_serper,
            "tavily": self._search_tavily,
            "searxng": self._search_searxng,
        }

    async def on_load(self):
        """插件加载"""
        print("网络搜索插件已加载")

    async def on_message(self, text: str, context: Dict[str, Any]) -> Optional[str]:
        """拦截消息，处理搜索请求"""
        search_prefixes = ["搜索", "search", "查找", "找一下", "帮我搜索"]
        for prefix in search_prefixes:
            if text.startswith(prefix) or text.lower().startswith(prefix.lower()):
                query = text[len(prefix):].strip()
                if query:
                    return await self.perform_search(query, context)
        return None

    async def perform_search(self, query: str, context: Dict[str, Any]) -> str:
        """执行搜索"""
        engine = self.config.get("default_engine", "serper")

        if engine in self.search_engines:
            try:
                results = await self.search_engines[engine](query)
                return self.format_results(query, results)
            except Exception as e:
                return f"搜索失败: {str(e)}"

        return "未配置搜索引擎"

    async def _search_serper(self, query: str) -> List[Dict]:
        """Serper 搜索"""
        # 需要配置 SERPER_API_KEY
        return []

    async def _search_tavily(self, query: str) -> List[Dict]:
        """Tavily 搜索"""
        return []

    async def _search_searxng(self, query: str) -> List[Dict]:
        """Searxng 搜索"""
        return []

    def format_results(self, query: str, results: List[Dict]) -> str:
        """格式化搜索结果"""
        if not results:
            return f"未找到关于「{query}」的相关结果"

        response = f"关于「{query}」的搜索结果:\n\n"
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "无标题")
            snippet = r.get("snippet", r.get("description", ""))
            url = r.get("url", "")
            response += f"{i}. **{title}**\n   {snippet}\n   {url}\n\n"

        return response
