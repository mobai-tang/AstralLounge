"""图片生成路由"""
import base64
import io
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx

from backend.config.settings import settings

router = APIRouter()


class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    width: int = 512
    height: int = 512
    steps: int = 25
    seed: Optional[int] = None
    cfg_scale: float = 7.0
    model: Optional[str] = None
    sampler: Optional[str] = None


class VariationRequest(BaseModel):
    image: str  # base64
    strength: float = 0.5
    prompt: Optional[str] = ""


def model_to_image_response(image_data: str, seed: int = None) -> dict:
    """转换图片响应"""
    return {
        "image": f"data:image/png;base64,{image_data}" if not image_data.startswith("data:") else image_data,
        "seed": seed,
    }


@router.post("/generate")
async def generate_image(payload: ImageGenerationRequest):
    """生成图片（支持 Stable Diffusion / DALL-E）"""
    try:
        # 如果配置了 Stable Diffusion
        if settings.sd_api_url:
            return await generate_with_stable_diffusion(payload)

        # 如果配置了 OpenAI DALL-E
        if settings.openai_api_key and "dall-e" in (payload.model or "").lower():
            return await generate_with_dalle(payload)

        raise HTTPException(status_code=503, detail="未配置图片生成服务")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")


async def generate_with_stable_diffusion(payload: ImageGenerationRequest):
    """使用 Stable Diffusion API 生成图片"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        request_data = {
            "prompt": payload.prompt,
            "negative_prompt": payload.negative_prompt,
            "width": payload.width,
            "height": payload.height,
            "steps": payload.steps,
            "cfg_scale": payload.cfg_scale,
        }

        if payload.seed:
            request_data["seed"] = payload.seed
        if payload.sampler:
            request_data["sampler_name"] = payload.sampler

        resp = await client.post(
            f"{settings.sd_api_url}/sdapi/v1/txt2img",
            json=request_data
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Stable Diffusion 服务返回错误")

        data = resp.json()
        images = data.get("images", [])
        if not images:
            raise HTTPException(status_code=500, detail="未生成图片")

        return model_to_image_response(
            images[0],
            data.get("parameters", {}).get("seed")
        )


async def generate_with_dalle(payload: ImageGenerationRequest):
    """使用 DALL-E API 生成图片"""
    size_map = {
        (512, 512): "512x512",
        (1024, 1024): "1024x1024",
        (1792, 1024): "1792x1024",
        (1024, 1792): "1024x1792",
    }
    size = size_map.get((payload.width, payload.height), "1024x1024")

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.openai_base_url}/images/generations",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "prompt": payload.prompt,
                "n": 1,
                "size": size,
                "response_format": "b64_json",
            }
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="DALL-E 服务返回错误")

        data = resp.json()
        image_data = data["data"][0]["b64_json"]
        return model_to_image_response(image_data)


@router.post("/img2img")
async def image_to_image(payload: VariationRequest):
    """图生图（以图生图）"""
    if not settings.sd_api_url:
        raise HTTPException(status_code=503, detail="未配置 Stable Diffusion 服务")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.sd_api_url}/sdapi/v1/img2img",
            json={
                "init_images": [payload.image],
                "prompt": payload.prompt,
                "denoising_strength": 1 - payload.strength,
                "steps": 25,
            }
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="图生图失败")

        data = resp.json()
        images = data.get("images", [])
        if not images:
            raise HTTPException(status_code=500, detail="未生成图片")

        return model_to_image_response(images[0])


@router.get("/models")
async def list_image_models():
    """获取可用图片模型"""
    models = []

    if settings.sd_api_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{settings.sd_api_url}/sdapi/v1/sd-models")
                if resp.status_code == 200:
                    sd_models = resp.json()
                    models.extend([{"id": m["title"], "name": m["title"]} for m in sd_models])
        except:
            pass

    if settings.openai_api_key:
        models.append({"id": "dall-e-3", "name": "DALL-E 3"})
        models.append({"id": "dall-e-2", "name": "DALL-E 2"})

    return models


@router.get("/status")
async def image_service_status():
    """获取图片服务状态"""
    status = {
        "stable_diffusion": bool(settings.sd_api_url),
        "dalle": bool(settings.openai_api_key),
    }

    if settings.sd_api_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.sd_api_url}/sdapi/v1/options")
                status["sd_available"] = resp.status_code == 200
        except:
            status["sd_available"] = False

    return status
