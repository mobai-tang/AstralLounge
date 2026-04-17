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


# ============ 模型提供商相关接口 ============

# 提供商定义信息（中文名称、描述等）
PROVIDER_INFO: Dict[str, Dict[str, Any]] = {
    "ollama": {
        "name": "Ollama",
        "description": "本地开源大模型运行框架，支持 Llama、Mistral 等模型",
        "category": "local",
        "requiresApiKey": False,
        "defaultUrl": "http://localhost:11434",
        "defaultModel": "llama3.2",
        "color": "#ff6b35",
        "models": ["llama3.2", "llama3.1", "mistral", "mixtral", "qwen2.5", "phi3", "gemma2"],
    },
    "openai": {
        "name": "OpenAI",
        "description": "OpenAI 官方 API（GPT-4、GPT-3.5）",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.openai.com/v1",
        "defaultModel": "gpt-3.5-turbo",
        "color": "#10a37f",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "description": "DeepSeek 官方 API（性价比高）",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.deepseek.com/v1",
        "defaultModel": "deepseek-chat",
        "color": "#0066cc",
        "models": ["deepseek-chat", "deepseek-coder"],
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "description": "Anthropic Claude 系列模型（强推理能力）",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.anthropic.com/v1",
        "defaultModel": "claude-3-5-haiku-20241022",
        "color": "#cc785c",
        "models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
        ],
    },
    "azure": {
        "name": "Azure OpenAI",
        "description": "微软 Azure 云上的 OpenAI 模型",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "",
        "defaultModel": "gpt-4",
        "color": "#0078d4",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-35-turbo"],
    },
    "openrouter": {
        "name": "OpenRouter",
        "description": "聚合多个 AI 提供商，一站式访问 Llama、Claude 等",
        "category": "aggregate",
        "requiresApiKey": True,
        "defaultUrl": "https://openrouter.ai/api/v1",
        "defaultModel": "openai/gpt-3.5-turbo",
        "color": "#a855f7",
        "models": [
            "openai/gpt-4o",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3-70b-instruct",
        ],
    },
    "groq": {
        "name": "Groq",
        "description": "免费高速 API，支持 Llama、Mistral 等",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.groq.com/openai/v1",
        "defaultModel": "llama-3.1-8b-instant",
        "color": "#00d4aa",
        "models": [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "llama-3.1-405b-reasoning",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
        ],
    },
    "together": {
        "name": "Together AI",
        "description": "开源模型聚合平台，支持 Llama、Mistral 等",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.together.xyz/v1",
        "defaultModel": "meta-llama/Llama-3-8B-Instruct-Turbo",
        "color": "#c800a0",
        "models": [
            "meta-llama/Llama-3-8B-Instruct-Turbo",
            "meta-llama/Llama-3-70B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "Qwen/Qwen2-72B-Instruct",
        ],
    },
    "fireworks": {
        "name": "Fireworks AI",
        "description": "高速推理平台，支持多种开源模型",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.fireworks.ai/inference/v1",
        "defaultModel": "accounts/fireworks/models/llama-v3-8b-instruct",
        "color": "#ff4500",
        "models": [
            "accounts/fireworks/models/llama-v3-8b-instruct",
            "accounts/fireworks/models/llama-v3-70b-instruct",
            "accounts/fireworks/models/mixtral-8x22b-instruct",
            "accounts/fireworks/models/qwen2-72b-instruct",
        ],
    },
    "novita": {
        "name": "Novita AI",
        "description": "提供开源模型 API 服务",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.novita.ai/v3",
        "defaultModel": "meta-llama/llama-3.1-8b-instruct",
        "color": "#7c3aed",
        "models": [
            "meta-llama/llama-3.1-8b-instruct",
            "meta-llama/llama-3.1-70b-instruct",
            "mistralai/mistral-7b-instruct",
            "qwen/qwen2-72b-instruct",
        ],
    },
    "siliconflow": {
        "name": "SiliconFlow 硅基流动",
        "description": "国内平价 API，支持 Qwen、GLM、DeepSeek 等",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.siliconflow.cn/v1",
        "defaultModel": "Qwen/Qwen2.5-7B-Instruct",
        "color": "#06b6d4",
        "models": [
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct",
            "deepseek-ai/DeepSeek-V2.5",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "THUDM/glm-4-9b-chat",
        ],
    },
    "lmstudio": {
        "name": "LM Studio",
        "description": "本地桌面应用，支持加载 GGUF 模型",
        "category": "local",
        "requiresApiKey": False,
        "defaultUrl": "http://localhost:1234",
        "defaultModel": "local-model",
        "color": "#f59e0b",
        "models": [],
    },
    "koboldcpp": {
        "name": "KoboldCpp",
        "description": "本地 GGUF 模型服务，支持 Kobold 格式",
        "category": "local",
        "requiresApiKey": False,
        "defaultUrl": "http://localhost:5000",
        "defaultModel": "local-model",
        "color": "#84cc16",
        "models": [],
    },
    "custom": {
        "name": "自定义 OpenAI 兼容",
        "description": "连接任意 OpenAI 兼容的 API 端点",
        "category": "custom",
        "requiresApiKey": False,
        "defaultUrl": "https://your-api.example.com/v1",
        "defaultModel": "your-model",
        "color": "#6b7280",
        "models": [],
    },
    "mistral": {
        "name": "Mistral AI",
        "description": "欧洲 AI 公司开源模型，支持 Mistral、Mixtral 等",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.mistral.ai/v1",
        "defaultModel": "mistral-small-latest",
        "color": "#ff6b35",
        "models": [
            "mistral-small-latest",
            "mistral-medium-latest",
            "mistral-large-latest",
            "mistral-nemo",
            "mistral-7b-instruct",
            "mixtral-8x7b-instruct",
            "mixtral-8x22b-instruct",
        ],
    },
    "gemini": {
        "name": "Google Gemini",
        "description": "Google 强大的多模态 AI 模型",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://generativelanguage.googleapis.com/v1beta",
        "defaultModel": "gemini-1.5-flash",
        "color": "#4285f4",
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
        ],
    },
    "cohere": {
        "name": "Cohere",
        "description": "加拿大 AI 公司，支持 Command-R 系列",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.cohere.ai/v1",
        "defaultModel": "command-r-plus",
        "color": "#ff6b9d",
        "models": [
            "command-r-plus",
            "command-r",
            "command",
            "command-light",
        ],
    },
    "ai21": {
        "name": "AI21 Jurassic",
        "description": "AI21 Labs Jurassic 系列模型",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.ai21.com/studio/v1",
        "defaultModel": "j2-ultra",
        "color": "#f97316",
        "models": [
            "j2-ultra",
            "j2-mid",
            "j2-light",
        ],
    },
    "perplexity": {
        "name": "Perplexity",
        "description": "AI 搜索助手，支持实时网络搜索",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.perplexity.ai",
        "defaultModel": "llama-3.1-sonar-large-128k-online",
        "color": "#22c55e",
        "models": [
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online",
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct",
        ],
    },
    "xai": {
        "name": "xAI Grok",
        "description": "Elon Musk 创立的 xAI 推出的 Grok 模型",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.x.ai/v1",
        "defaultModel": "grok-2-1212",
        "color": "#a855f7",
        "models": [
            "grok-2-1212",
            "grok-2-v1212",
            "grok-1",
            "grok-1.5",
        ],
    },
    "tencent": {
        "name": "腾讯云混元",
        "description": "腾讯云混元大模型 API",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://hunyuan.cloud.tencent.com",
        "defaultModel": "hunyuan-pro",
        "color": "#07c160",
        "models": [
            "hunyuan-pro",
            "hunyuan-standard",
            "hunyuan-lite",
        ],
    },
    "baichuan": {
        "name": "百川 AI",
        "description": "百川智能大模型 API",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://api.baichuan-ai.com/v1",
        "defaultModel": "baichuan4",
        "color": "#06a0ff",
        "models": [
            "baichuan4",
            "baichuan3-turbo",
            "baichuan3-turbo-128k",
        ],
    },
    "zhipu": {
        "name": "智谱 GLM",
        "description": "智谱 AI GLM 大模型 API",
        "category": "cloud",
        "requiresApiKey": True,
        "defaultUrl": "https://open.bigmodel.cn/api/paas/v4",
        "defaultModel": "glm-4",
        "color": "#7c3aed",
        "models": [
            "glm-4",
            "glm-4-plus",
            "glm-4-air",
            "glm-4-flashx",
            "glm-4-airx",
            "glm-3-turbo",
        ],
    },
}


@router.get("/providers")
async def get_providers():
    """获取所有可用的模型提供商列表"""
    from backend.services.model_provider import get_provider_registry

    registry = get_provider_registry()
    registry.setup_from_settings(settings)

    result = []
    for pid, info in PROVIDER_INFO.items():
        config = registry.get_config(pid)
        result.append({
            "id": pid,
            "name": info["name"],
            "description": info["description"],
            "category": info["category"],
            "requiresApiKey": info["requiresApiKey"],
            "defaultUrl": info["defaultUrl"],
            "defaultModel": info["defaultModel"],
            "color": info["color"],
            "models": info["models"],
            "hasApiKey": bool(config and config.api_key) if info["requiresApiKey"] else True,
            "baseUrl": config.base_url if config else "",
            "currentModel": config.default_model if config else "",
        })
    return {"providers": result}


@router.post("/providers/test")
async def test_provider(payload: dict):
    """测试指定提供商的连接"""
    provider_id = payload.get("provider")
    if not provider_id:
        raise HTTPException(status_code=400, detail="缺少 provider 参数")

    from backend.services.model_provider import get_provider_registry
    registry = get_provider_registry()
    registry.setup_from_settings(settings)

    # 如果提供了新的配置，先更新
    if "apiKey" in payload or "baseUrl" in payload or "model" in payload:
        from backend.services.model_provider import ModelProviderConfig
        info = PROVIDER_INFO.get(provider_id, {})
        config = ModelProviderConfig(
            name=provider_id,
            api_key=payload.get("apiKey", ""),
            base_url=payload.get("baseUrl", info.get("defaultUrl", "")),
            default_model=payload.get("model", info.get("defaultModel", "")),
        )
        registry.update_config(provider_id, config)

    success, message = await registry.test_provider(provider_id)
    return {"success": success, "message": message}


@router.get("/providers/{provider_id}/models")
async def get_provider_models(provider_id: str):
    """获取指定提供商的可用模型列表"""
    from backend.services.model_provider import get_provider_registry
    registry = get_provider_registry()
    registry.setup_from_settings(settings)

    info = PROVIDER_INFO.get(provider_id, {})
    models = await registry.get_provider_models(provider_id)
    if not models:
        models = info.get("models", [])
    return {"models": models}


@router.get("/models/available")
async def get_available_models():
    """获取当前选中提供商的可用模型列表"""
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
