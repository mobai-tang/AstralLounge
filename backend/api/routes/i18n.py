"""国际化路由"""
from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()


@router.get("/translations")
async def get_translations(lang: str = "zh"):
    """获取指定语言的翻译"""
    translations = {
        "zh": {
            "app": {"title": "AstralLounge", "version": "版本", "loading": "加载中..."},
            "nav": {"chat": "对话", "groupChat": "群聊", "characters": "角色", "lorebooks": "世界", "memory": "记忆", "plugins": "插件", "settings": "设置"},
            "chat": {"newSession": "新会话", "send": "发送"},
            "common": {"save": "保存", "cancel": "取消", "confirm": "确认"}
        },
        "en": {
            "app": {"title": "AstralLounge", "version": "Version", "loading": "Loading..."},
            "nav": {"chat": "Chat", "groupChat": "Group Chat", "characters": "Characters", "lorebooks": "Worlds", "memory": "Memory", "plugins": "Plugins", "settings": "Settings"},
            "chat": {"newSession": "New Session", "send": "Send"},
            "common": {"save": "Save", "cancel": "Cancel", "confirm": "Confirm"}
        }
    }
    return translations.get(lang, {})


@router.get("/languages")
async def get_languages():
    """获取支持的语言列表"""
    return [
        {"code": "zh", "name": "中文", "native": "简体中文", "flag": "🇨🇳"},
        {"code": "en", "name": "English", "native": "English", "flag": "🇺🇸"},
    ]


@router.post("/language")
async def set_language(payload: dict):
    """设置语言偏好"""
    return {"success": True}
