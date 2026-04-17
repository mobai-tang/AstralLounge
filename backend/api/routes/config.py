"""配置管理路由"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.config.settings import settings
from backend.models.database import get_db

router = APIRouter()


class ModelConfig(BaseModel):
    provider: str = "ollama"
    model_name: str = "llama3.2"
    api_url: str = "http://localhost:11434"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    presence_penalty: float = 0
    frequency_penalty: float = 0
    stream: bool = True


class TTSSettings(BaseModel):
    enabled: bool = False
    provider: str = "cosyvoice"
    cosyvoice_url: str = "http://localhost:5000"
    gptsovits_url: str = "http://localhost:5001"
    default_voice: str = "female_zh"
    speech_speed: float = 1.0


class UISettings(BaseModel):
    theme: str = "dark"
    accent_color: str = "#667eea"
    typing_effect: bool = True
    stream_response: bool = True
    compact_mode: bool = False
    language: str = "zh"


class SafetySettings(BaseModel):
    enabled: bool = True
    block_enabled: bool = False
    log_enabled: bool = True
    sensitive_action: str = "warn"
    blocked_words: List[str] = []
    sensitive_words: List[str] = []


class SettingsPayload(BaseModel):
    model: ModelConfig
    tts: TTSSettings
    ui: UISettings
    safety: SafetySettings


SETTINGS_FILE = Path("./data/settings.json")


def load_settings() -> dict:
    """加载设置"""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(data: dict):
    """保存设置"""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/settings")
async def get_settings():
    """获取设置"""
    return load_settings()


@router.post("/settings")
async def save_settings_endpoint(payload: SettingsPayload):
    """保存设置"""
    data = {
        "model": payload.model.model_dump(),
        "tts": payload.tts.model_dump(),
        "ui": payload.ui.model_dump(),
        "safety": payload.safety.model_dump()
    }
    save_settings(data)
    return {"success": True}


@router.get("/models/available")
async def get_available_models():
    """获取可用模型列表"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return {"models": models}
    except Exception:
        pass
    return {"models": [settings.default_model_name]}


@router.post("/models/refresh")
async def refresh_models():
    """刷新模型列表"""
    return await get_available_models()


@router.post("/models/switch")
async def switch_model(payload: dict):
    """切换模型"""
    return {"success": True, "model": payload.get("model_name", settings.default_model_name)}
