"""
AstralLounge - FastAPI 主应用入口
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend.config.settings import settings
from backend.models.database import engine, Base, get_db


def setup_logging():
    """配置日志"""
    logger.remove()
    log_level = "DEBUG" if settings.debug else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    log_dir = Path("./data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "astral_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"AstralLounge 启动中...")

    # 初始化数据库
    logger.info("初始化数据库...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成")

    # 确保数据目录存在
    settings.characters_dir.mkdir(parents=True, exist_ok=True)
    settings.world_info_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_db_path.mkdir(parents=True, exist_ok=True)

    # 加载插件
    from backend.plugins.plugin_manager import get_plugin_manager
    plugin_manager = get_plugin_manager()
    await plugin_manager.load_plugins()

    logger.info(f"✅ AstralLounge 启动完成 | 版本: 1.0.0")
    yield

    # 关闭时卸载插件
    logger.info("正在关闭...")
    await plugin_manager.unload_plugins()
    logger.info("再见！")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title="AstralLounge API",
        description="本地 AI 对话平台 API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    from backend.api.routes import chat, characters, lorebooks, memory, config, plugins, health, group_chat, tts, summarize, image_gen

    app.include_router(health.router, prefix="/api", tags=["健康检查"])
    app.include_router(config.router, prefix="/api/config", tags=["配置"])
    app.include_router(characters.router, prefix="/api/characters", tags=["角色"])
    app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
    app.include_router(group_chat.router, prefix="/api/group-chat", tags=["群聊"])
    app.include_router(lorebooks.router, prefix="/api/lorebooks", tags=["世界设定"])
    app.include_router(memory.router, prefix="/api/memory", tags=["记忆"])
    app.include_router(plugins.router, prefix="/api/plugins", tags=["插件"])
    app.include_router(tts.router, prefix="/api/tts", tags=["语音合成"])
    app.include_router(summarize.router, prefix="/api/summarize", tags=["摘要"])
    app.include_router(image_gen.router, prefix="/api/image", tags=["图片生成"])

    # 挂载前端静态文件
    frontend_path = settings.frontend_path_resolved
    if frontend_path:
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
        logger.info(f"前端已挂载: {frontend_path}")
    else:
        @app.get("/")
        async def root():
            return {"message": "AstralLounge API", "version": "1.0.0", "docs": "/docs"}

    return app


app = create_app()


if __name__ == "__main__":
    setup_logging()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
