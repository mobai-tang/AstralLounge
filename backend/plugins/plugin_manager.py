"""
插件管理器 - BaseSkill 基类和插件加载系统
"""
import os
import sys
import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from loguru import logger

import asyncio


@dataclass
class SkillMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    triggers: List[str]
    enabled: bool = True
    category: str = "tools"
    icon: str = ""
    config_schema: Dict = field(default_factory=dict)
    dependencies: List = field(default_factory=list)


class BaseSkill:
    """所有插件的基类"""

    metadata: SkillMetadata

    def __init__(self):
        self.config: Dict[str, Any] = {}

    async def on_load(self):
        """插件加载时调用，用于初始化资源"""
        pass

    async def on_unload(self):
        """插件卸载时调用，用于清理资源"""
        pass

    async def on_config_change(self, new_config: Dict[str, Any]):
        """配置变更时调用"""
        self.config = new_config

    async def process_input(self, text: str, context: Dict[str, Any]) -> str:
        """处理输入消息"""
        return text

    async def process_output(self, text: str, context: Dict[str, Any]) -> str:
        """处理输出消息"""
        return text

    async def on_message(self, text: str, context: Dict[str, Any]) -> Optional[str]:
        """拦截消息，返回 None 则继续传递"""
        return None


class PluginManager:
    """插件管理器"""

    def __init__(self, plugins_dir: Optional[Path] = None):
        if plugins_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            plugins_dir = base_dir / "backend" / "plugins" / "skills"
        self.plugins_dir = Path(plugins_dir)
        self.skills: Dict[str, BaseSkill] = {}
        self._check_tasks: Dict[str, asyncio.Task] = {}

    def _find_skill_modules(self) -> List[Path]:
        """查找所有插件模块"""
        if not self.plugins_dir.exists():
            logger.warning(f"插件目录不存在: {self.plugins_dir}")
            return []

        modules = []
        for file_path in self.plugins_dir.glob("*.py"):
            if file_path.stem not in ("__init__", "__pycache__"):
                modules.append(file_path)
        return modules

    async def load_plugins(self):
        """加载所有插件"""
        logger.info("正在初始化插件管理器...")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        modules = self._find_skill_modules()
        loaded_count = 0

        for module_path in modules:
            try:
                module_name = module_path.stem
                spec = importlib.util.spec_from_file_location(
                    f"backend.plugins.skills.{module_name}", module_path
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"backend.plugins.skills.{module_name}"] = module
                    spec.loader.exec_module(module)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseSkill)
                            and attr is not BaseSkill
                        ):
                            skill = attr()
                            skill_name = skill.metadata.name

                            if skill_name in self.skills:
                                logger.warning(f"插件 {skill_name} 已存在，将被覆盖")

                            self.skills[skill_name] = skill
                            await skill.on_load()
                            logger.info(f"  - 加载技能 {skill_name} v{skill.metadata.version}")
                            loaded_count += 1

            except Exception as e:
                logger.error(f"加载插件 {module_path.name} 失败: {e}")

        logger.info(f"插件管理器初始化完成，已加载 {loaded_count} 个技能")

    async def unload_plugins(self):
        """卸载所有插件"""
        for name, skill in self.skills.items():
            try:
                if self._check_tasks.get(name):
                    self._check_tasks[name].cancel()
                    try:
                        await self._check_tasks[name]
                    except asyncio.CancelledError:
                        pass
                await skill.on_unload()
                logger.info(f"插件 {name} 已卸载")
            except Exception as e:
                logger.error(f"卸载插件 {name} 失败: {e}")

    def get_plugin(self, name: str) -> Optional[BaseSkill]:
        """获取指定插件"""
        return self.skills.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        return [
            {
                "name": s.metadata.name,
                "version": s.metadata.version,
                "description": s.metadata.description,
                "author": s.metadata.author,
                "triggers": s.metadata.triggers,
                "enabled": s.metadata.enabled,
                "category": s.metadata.category,
                "icon": s.metadata.icon,
            }
            for s in self.skills.values()
        ]

    async def reload_plugin(self, name: str):
        """重新加载指定插件"""
        if name in self.skills:
            await self.skills[name].on_unload()
            del self.skills[name]

        module_path = self.plugins_dir / f"{name}.py"
        if module_path.exists():
            try:
                module_name = name
                spec = importlib.util.spec_from_file_location(
                    f"backend.plugins.skills.{module_name}", module_path
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"backend.plugins.skills.{module_name}"] = module
                    spec.loader.exec_module(module)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseSkill)
                            and attr is not BaseSkill
                        ):
                            skill = attr()
                            self.skills[name] = skill
                            await skill.on_load()
                            logger.info(f"插件 {name} 已重新加载")
                            return True
            except Exception as e:
                logger.error(f"重新加载插件 {name} 失败: {e}")
        return False

    async def process_input(self, text: str, context: Dict[str, Any]) -> str:
        """处理输入，按优先级传递"""
        result = text
        for skill in self.skills.values():
            if skill.metadata.enabled:
                try:
                    result = await skill.process_input(result, context)
                except Exception as e:
                    logger.error(f"处理输入失败 [{skill.metadata.name}]: {e}")
        return result

    async def process_output(self, text: str, context: Dict[str, Any]) -> str:
        """处理输出"""
        result = text
        for skill in self.skills.values():
            if skill.metadata.enabled:
                try:
                    result = await skill.process_output(result, context)
                except Exception as e:
                    logger.error(f"处理输出失败 [{skill.metadata.name}]: {e}")
        return result


_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        base_dir = Path(__file__).parent.parent.parent
        plugins_dir = base_dir / "backend" / "plugins" / "skills"
        _plugin_manager = PluginManager(plugins_dir)
    return _plugin_manager
