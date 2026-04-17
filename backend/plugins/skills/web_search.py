"""
网络搜索插件
集成多种搜索引擎进行网络搜索
"""
from typing import Dict, Any, List, Optional
import httpx
from backend.plugins.plugin_manager import BaseSkill, SkillMetadata
from backend.config.settings import settings


class WebSearchSkill(BaseSkill):
    """网络搜索技能"""

    metadata = SkillMetadata(
        name="web-search",
        version="1.0.0",
        description="集成多种搜索引擎，支持 Google Serper、Tavily、Searxng 等",
        author="AstralLounge",
        triggers=["search", "搜索", "查找", "search:"],
        enabled=False,
        category="tools",
        icon="🔍",
        config_schema={
            "type": "object",
            "properties": {
                "default_engine": {"type": "string", "default": "searxng"},
                "max_results": {"type": "integer", "default": 5},
                "engines": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["searxng", "serper", "tavily"]
                }
            }
        }
    )

    def __init__(self):
        super().__init__()
        self.search_engines = {
            "searxng": self._search_searxng,
            "serper": self._search_serper,
            "tavily": self._search_tavily,
        }

    async def on_load(self):
        default_engine = self.config.get("default_engine", "searxng")
        max_results = self.config.get("max_results", 5)
        print(f"网络搜索插件已加载 - 默认引擎: {default_engine}, 最大结果: {max_results}")

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
        engine = self.config.get("default_engine", "searxng")
        max_results = self.config.get("max_results", 5)

        if engine in self.search_engines:
            try:
                results = await self.search_engines[engine](query, max_results)
                return self.format_results(query, results)
            except Exception as e:
                return f"搜索失败: {str(e)}"

        return "未配置搜索引擎"

    async def _search_searxng(self, query: str, max_results: int = 5) -> List[Dict]:
        """Searxng 搜索"""
        searxng_url = settings.searxng_url
        if not searxng_url:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    searxng_url,
                    params={
                        "q": query,
                        "format": "json",
                        "engines": "google,bing,duckduckgo",
                        "categories": "general",
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for r in data.get("results", [])[:max_results]:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("content", r.get("description", "")),
                        })
                    return results
        except Exception as e:
            print(f"Searxng 搜索错误: {e}")
        return []

    async def _search_serper(self, query: str, max_results: int = 5) -> List[Dict]:
        """Serper 搜索"""
        api_key = settings.serper_api_key
        if not api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                    json={"q": query, "num": max_results}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("organic", [])[:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                        })
                    return results
        except Exception as e:
            print(f"Serper 搜索错误: {e}")
        return []

    async def _search_tavily(self, query: str, max_results: int = 5) -> List[Dict]:
        """Tavily 搜索"""
        api_key = settings.tavily_api_key
        if not api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    headers={"Content-Type": "application/json"},
                    json={
                        "api_key": api_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": max_results,
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("results", [])[:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", ""),
                        })
                    return results
        except Exception as e:
            print(f"Tavily 搜索错误: {e}")
        return []

    def format_results(self, query: str, results: List[Dict]) -> str:
        """格式化搜索结果"""
        if not results:
            return f"未找到关于「{query}」的相关结果"

        response = f"关于「{query}」的搜索结果:\n\n"
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "无标题")
            snippet = r.get("snippet", "")
            url = r.get("url", "")
            response += f"{i}. **{title}**\n   {snippet}\n   🔗 {url}\n\n"

        return response
