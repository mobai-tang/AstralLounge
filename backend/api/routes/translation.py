"""翻译路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx

from backend.config.settings import settings

router = APIRouter()


class TranslationRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"
    target_lang: str = "zh"
    provider: Optional[str] = None  # auto, google, deepseek, openai


SUPPORTED_LANGS = {
    "zh": "中文", "en": "英语", "ja": "日语", "ko": "韩语",
    "fr": "法语", "de": "德语", "es": "西班牙语", "ru": "俄语",
    "ar": "阿拉伯语", "pt": "葡萄牙语", "it": "意大利语",
    "nl": "荷兰语", "pl": "波兰语", "vi": "越南语", "th": "泰语",
}


@router.post("/translate")
async def translate_text(payload: TranslationRequest):
    """翻译文本"""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="翻译文本不能为空")

    target_lang = payload.target_lang.lower()
    if target_lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail=f"不支持的目标语言: {target_lang}")

    # 自动选择提供商
    provider = payload.provider or "auto"

    if provider == "auto":
        # 优先使用 DeepSeek（如果配置了）
        if settings.deepseek_api_key:
            provider = "deepseek"
        elif settings.openai_api_key:
            provider = "openai"
        else:
            provider = "google"

    try:
        if provider == "deepseek":
            return await translate_with_deepseek(text, payload.source_lang, target_lang)
        elif provider == "openai":
            return await translate_with_openai(text, payload.source_lang, target_lang)
        elif provider == "google":
            return await translate_with_google(text, payload.source_lang, target_lang)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的翻译提供商: {provider}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


async def translate_with_deepseek(text: str, source: str, target: str):
    """使用 DeepSeek API 翻译"""
    lang_map = {
        "zh": "中文", "en": "英文", "ja": "日文", "ko": "韩文",
        "fr": "法文", "de": "德文", "es": "西班牙文"
    }

    source_lang = lang_map.get(source, source) if source != "auto" else source
    target_lang = lang_map.get(target, target)

    system_prompt = f"""你是一个专业的翻译助手。请将以下文本翻译成{target_lang}。
规则：
1. 保持原文的语气和风格
2. 对于专有名词，保留原文并在括号中标注翻译
3. 只返回翻译结果，不要添加任何解释
4. 如果 source_lang 不是 auto，则从{source_lang}翻译
"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            }
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="DeepSeek 翻译失败")

        data = resp.json()
        translated = data["choices"][0]["message"]["content"]

        return {
            "original": text,
            "translated": translated.strip(),
            "source_lang": source,
            "target_lang": target,
            "provider": "deepseek",
        }


async def translate_with_openai(text: str, source: str, target: str):
    """使用 OpenAI API 翻译"""
    lang_map = {
        "zh": "Chinese", "en": "English", "ja": "Japanese", "ko": "Korean",
        "fr": "French", "de": "German", "es": "Spanish"
    }

    target_lang = lang_map.get(target, target)

    system_prompt = f"""You are a professional translator. Translate the following text to {target_lang}.
Rules:
1. Maintain the tone and style of the original text
2. For proper nouns, keep the original and add translation in brackets
3. Only return the translation, no explanations
"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            }
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="OpenAI 翻译失败")

        data = resp.json()
        translated = data["choices"][0]["message"]["content"]

        return {
            "original": text,
            "translated": translated.strip(),
            "source_lang": source,
            "target_lang": target,
            "provider": "openai",
        }


async def translate_with_google(text: str, source: str, target: str):
    """使用 Google Translate API 翻译"""
    # 注意：Google Translate API 需要 API Key
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="未配置 Google Translate API Key")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            "https://translation.googleapis.com/language/translate/v2",
            params={
                "key": settings.google_api_key,
                "q": text,
                "source": source if source != "auto" else None,
                "target": target,
                "format": "text",
            }
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Google 翻译失败")

        data = resp.json()
        translated = data["data"]["translations"][0]["translatedText"]

        return {
            "original": text,
            "translated": translated,
            "source_lang": source,
            "target_lang": target,
            "provider": "google",
        }


@router.get("/languages")
async def get_supported_languages():
    """获取支持的语言列表"""
    return SUPPORTED_LANGS


@router.post("/detect")
async def detect_language(text: str):
    """检测文本语言"""
    # 简单的语言检测（基于字符集）
    import re

    # 检测中文
    if re.search(r'[\u4e00-\u9fff]', text):
        return {"language": "zh", "confidence": 0.95}

    # 检测日语
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
        return {"language": "ja", "confidence": 0.9}

    # 检测韩语
    if re.search(r'[\uac00-\ud7af]', text):
        return {"language": "ko", "confidence": 0.9}

    # 检测俄语
    if re.search(r'[\u0400-\u04ff]', text):
        return {"language": "ru", "confidence": 0.9}

    # 默认返回英语
    return {"language": "en", "confidence": 0.5}
