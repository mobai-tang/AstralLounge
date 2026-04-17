"""API 路由包"""
from backend.api.routes import health, config, chat, characters, lorebooks, memory, plugins, group_chat

__all__ = ["health", "config", "chat", "characters", "lorebooks", "memory", "plugins", "group_chat"]
