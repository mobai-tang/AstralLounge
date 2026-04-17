"""TTS 语音合成路由"""
import base64
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.config.settings import settings

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: str = "female_zh"
    speed: float = 1.0


@router.post("/synthesize")
async def synthesize_speech(payload: TTSRequest):
    """合成语音"""
    try:
        # 如果未启用 TTS，返回提示
        if not settings.tts_enabled:
            raise HTTPException(status_code=503, detail="TTS 未启用")

        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="文本不能为空")

        # 根据配置的 TTS 类型调用不同的服务
        if settings.tts_provider == "cosyvoice":
            # CosyVoice TTS
            return await cosyvoice_tts(payload)
        elif settings.tts_provider == "gptsovits":
            # GPT-SoVITS TTS
            return await gptsovits_tts(payload)
        else:
            raise HTTPException(status_code=400, detail="未知的 TTS 提供商")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 合成失败: {str(e)}")


async def cosyvoice_tts(payload: TTSRequest):
    """CosyVoice TTS 合成"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.cosyvoice_url}/tts",
                json={
                    "text": payload.text,
                    "voice": payload.voice,
                    "speed": payload.speed
                }
            )
            if resp.status_code == 200:
                return Response(content=resp.content, media_type="audio/wav")
            else:
                raise HTTPException(status_code=500, detail="CosyVoice 服务返回错误")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="无法连接到 CosyVoice 服务")


async def gptsovits_tts(payload: TTSRequest):
    """GPT-SoVITS TTS 合成"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.gptsovits_url}/tts",
                json={
                    "text": payload.text,
                    "voice": payload.voice,
                    "speed": payload.speed
                }
            )
            if resp.status_code == 200:
                return Response(content=resp.content, media_type="audio/wav")
            else:
                raise HTTPException(status_code=500, detail="GPT-SoVITS 服务返回错误")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="无法连接到 GPT-SoVITS 服务")


@router.get("/voices")
async def list_voices():
    """获取可用音色列表"""
    return {
        "voices": [
            {"id": "female_zh", "name": "女声-中文", "lang": "zh"},
            {"id": "male_zh", "name": "男声-中文", "lang": "zh"},
            {"id": "female_en", "name": "女声-英文", "lang": "en"},
            {"id": "male_en", "name": "男声-英文", "lang": "en"},
        ]
    }


@router.get("/status")
async def tts_status():
    """获取 TTS 服务状态"""
    return {
        "enabled": settings.tts_enabled,
        "provider": settings.tts_provider,
        "cosyvoice_url": settings.cosyvoice_url,
        "gptsovits_url": settings.gptsovits_url,
    }
