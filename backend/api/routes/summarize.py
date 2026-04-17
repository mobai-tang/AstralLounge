"""自动摘要路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx

from backend.config.settings import settings

router = APIRouter()


class SummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 200
    style: Optional[str] = "concise"  # concise, detailed, bullet_points
    provider: Optional[str] = None


class ChatSummaryRequest(BaseModel):
    session_id: str
    max_length: Optional[int] = 200
    force: bool = False


@router.post("/summarize")
async def summarize_text(payload: SummarizeRequest):
    """总结文本"""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="要总结的文本不能为空")

    style = payload.style or "concise"
    max_length = payload.max_length or 200

    # 选择提供商
    if settings.deepseek_api_key:
        return await summarize_with_deepseek(text, max_length, style)
    elif settings.openai_api_key:
        return await summarize_with_openai(text, max_length, style)
    else:
        raise HTTPException(status_code=503, detail="未配置 AI 翻译服务")


async def summarize_with_deepseek(text: str, max_length: int, style: str):
    """使用 DeepSeek 总结"""
    style_prompts = {
        "concise": "简洁地总结，保留关键信息",
        "detailed": "详细总结，保留重要细节",
        "bullet_points": "用要点列表形式总结"
    }

    system_prompt = f"""你是一个专业的文本摘要助手。请将以下文本进行总结。
规则：
1. {style_prompts.get(style, style_prompts['concise'])}
2. 总结长度不超过 {max_length} 字
3. 只返回总结内容，不要添加任何解释
"""

    async with httpx.AsyncClient(timeout=60.0) as client:
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
                "max_tokens": 500,
            }
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="DeepSeek 总结失败")

        data = resp.json()
        summary = data["choices"][0]["message"]["content"]

        return {
            "original": text,
            "summary": summary.strip(),
            "style": style,
            "original_length": len(text),
            "summary_length": len(summary),
            "provider": "deepseek",
        }


async def summarize_with_openai(text: str, max_length: int, style: str):
    """使用 OpenAI 总结"""
    style_prompts = {
        "concise": "Summarize concisely, keeping key information",
        "detailed": "Summarize in detail, preserving important details",
        "bullet_points": "Summarize in bullet point format"
    }

    system_prompt = f"""You are a professional text summarizer. Summarize the following text.
Rules:
1. {style_prompts.get(style, style_prompts['concise'])}
2. Keep summary under {max_length} characters
3. Only return the summary, no explanations
"""

    async with httpx.AsyncClient(timeout=60.0) as client:
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
                "max_tokens": 500,
            }
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="OpenAI 总结失败")

        data = resp.json()
        summary = data["choices"][0]["message"]["content"]

        return {
            "original": text,
            "summary": summary.strip(),
            "style": style,
            "original_length": len(text),
            "summary_length": len(summary),
            "provider": "openai",
        }


@router.post("/chat")
async def summarize_chat(payload: ChatSummaryRequest):
    """总结对话历史"""
    # 从数据库获取对话历史
    from backend.models.database import get_db, ChatSessionModel, MessageModel

    db = next(get_db())
    try:
        session = db.query(ChatSessionModel).filter(
            ChatSessionModel.id == payload.session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 获取所有消息
        messages = db.query(MessageModel).filter(
            MessageModel.session_id == payload.session_id
        ).order_by(MessageModel.timestamp).all()

        # 组合对话文本
        chat_text = "\n".join([
            f"{'用户' if m.role == 'user' else 'AI'}: {m.content}"
            for m in messages
        ])

        if not chat_text:
            return {
                "summary": "对话为空",
                "message_count": 0,
            }

        # 限制文本长度（取最后的消息）
        if len(chat_text) > 4000:
            chat_text = chat_text[-4000:]

        # 生成摘要
        if settings.deepseek_api_key:
            result = await summarize_with_deepseek(chat_text, payload.max_length or 200, "concise")
        elif settings.openai_api_key:
            result = await summarize_with_openai(chat_text, payload.max_length or 200, "concise")
        else:
            # 如果没有 AI 服务，返回简单的前几条消息
            return {
                "summary": f"对话共 {len(messages)} 条消息",
                "message_count": len(messages),
                "provider": "simple",
            }

        return {
            "summary": result["summary"],
            "message_count": len(messages),
            "original_length": result["original_length"],
            "provider": result["provider"],
        }

    finally:
        db.close()


@router.get("/formats")
async def get_summary_formats():
    """获取可用的摘要格式"""
    return {
        "formats": [
            {"id": "concise", "name": "简洁摘要", "description": "简短总结关键信息"},
            {"id": "detailed", "name": "详细摘要", "description": "保留更多细节的总结"},
            {"id": "bullet_points", "name": "要点列表", "description": "以要点列表形式呈现"},
        ]
    }
