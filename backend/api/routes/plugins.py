"""插件管理路由"""
import asyncio
import shutil
import zipfile
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.plugins.plugin_manager import get_plugin_manager
from backend.config.settings import settings

router = APIRouter()

# 本地插件列表（模拟）
LOCAL_PLUGINS: List[Dict[str, Any]] = [
    {
        "id": "web-search",
        "name": "web-search",
        "displayName": "网络搜索",
        "version": "1.0.0",
        "author": "AstralLounge",
        "description": "集成多种搜索引擎，支持 Google、Bing、Tavily 等",
        "category": "tools",
        "enabled": True,
        "installed": True,
        "metadata": {"url": "built-in"}
    },
    {
        "id": "image-gen",
        "name": "image-gen",
        "displayName": "图片生成",
        "version": "1.0.0",
        "author": "AstralLounge",
        "description": "调用 Stable Diffusion 生成图片",
        "category": "tools",
        "enabled": False,
        "installed": False,
        "metadata": {"url": "built-in"}
    },
    {
        "id": "auto-memory",
        "name": "auto-memory",
        "displayName": "自动记忆",
        "version": "1.0.0",
        "author": "AstralLounge",
        "description": "自动将重要对话内容提取保存到记忆系统",
        "category": "memory",
        "enabled": True,
        "installed": True,
        "metadata": {"url": "built-in"}
    }
]

FEATURED_PLUGINS = [
    {
        "id": "github-integration",
        "name": "github-integration",
        "displayName": "GitHub 集成",
        "version": "1.0.0",
        "author": "AstralLounge",
        "description": "与 GitHub 集成，支持代码片段分享和仓库搜索",
        "category": "integration",
        "installed": False
    },
    {
        "id": "latex-renderer",
        "name": "latex-renderer",
        "displayName": "LaTeX 渲染",
        "version": "1.0.0",
        "author": "AstralLounge",
        "description": "在对话中渲染 LaTeX 数学公式",
        "category": "render",
        "installed": False
    }
]


class PluginInstall(BaseModel):
    url: str


@router.get("")
async def list_plugins():
    """获取所有插件（包括本地和已安装）"""
    pm = get_plugin_manager()
    skills = pm.list_plugins()

    # 合并技能和本地插件
    plugins = LOCAL_PLUGINS.copy()
    for skill in skills:
        existing = next((p for p in plugins if p["id"] == skill["name"]), None)
        if not existing:
            plugins.append({
                "id": skill["name"],
                "name": skill["name"],
                "displayName": skill.get("description", skill["name"]),
                "version": skill.get("version", "1.0.0"),
                "author": skill.get("author", ""),
                "description": skill.get("description", ""),
                "category": skill.get("category", "skill"),
                "enabled": skill.get("enabled", True),
                "installed": True
            })

    return plugins


@router.get("/skills")
async def list_skills():
    """获取所有技能"""
    pm = get_plugin_manager()
    return pm.list_plugins()


@router.get("/featured")
async def get_featured_plugins():
    """获取推荐插件列表"""
    return FEATURED_PLUGINS


@router.get("/{name}")
async def get_plugin(name: str):
    """获取指定插件"""
    pm = get_plugin_manager()
    skill = pm.get_plugin(name)
    if skill:
        return {
            "name": skill.metadata.name,
            "version": skill.metadata.version,
            "description": skill.metadata.description,
            "author": skill.metadata.author,
            "triggers": skill.metadata.triggers,
            "enabled": skill.metadata.enabled,
            "category": skill.metadata.category,
        }

    # 检查本地插件
    for p in LOCAL_PLUGINS:
        if p["id"] == name or p["name"] == name:
            return p

    raise HTTPException(status_code=404, detail="插件不存在")


@router.post("/{name}/reload")
async def reload_plugin(name: str):
    """重新加载插件"""
    pm = get_plugin_manager()
    success = await pm.reload_plugin(name)
    if not success:
        raise HTTPException(status_code=404, detail="插件重新加载失败")
    return {"success": True}


@router.post("/reload-all")
async def reload_all_plugins():
    """重新加载所有插件"""
    pm = get_plugin_manager()
    await pm.unload_plugins()
    await pm.load_plugins()
    return {"success": True}


@router.post("/install")
async def install_plugin(payload: PluginInstall):
    """安装插件（从 GitHub URL）"""
    url = payload.url.strip()

    try:
        # 模拟安装过程
        # 实际实现可以从 GitHub 下载插件
        plugin_name = url.split("/")[-1].replace(".git", "") if "/" in url else url

        new_plugin = {
            "id": plugin_name,
            "name": plugin_name,
            "displayName": plugin_name,
            "version": "1.0.0",
            "author": "Community",
            "description": f"从 {url} 安装的插件",
            "category": "external",
            "enabled": True,
            "installed": True
        }

        return {"success": True, "plugin": new_plugin}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"安装失败: {str(e)}")


@router.delete("/{name}")
async def uninstall_plugin(name: str):
    """卸载插件"""
    # 实际实现应该删除插件文件
    return {"success": True}
