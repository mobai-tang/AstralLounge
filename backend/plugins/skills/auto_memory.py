"""
自动记忆插件
自动将对话中的重要内容提取并保存到记忆系统
"""
from typing import Dict, Any, List, Optional
from backend.plugins.plugin_manager import BaseSkill, SkillMetadata


class AutoMemorySkill(BaseSkill):
    """自动记忆技能 - 自动提取对话中的重要信息"""

    metadata = SkillMetadata(
        name="auto-memory",
        version="1.0.0",
        description="自动将对话中的重要内容提取并保存到记忆系统",
        author="AstralLounge",
        triggers=["memory", "自动记忆", "important"],
        enabled=True,
        category="memory",
        icon="🧠",
        config_schema={
            "type": "object",
            "properties": {
                "auto_extract": {"type": "boolean", "default": True},
                "importance_threshold": {"type": "number", "default": 0.7}
            }
        }
    )

    async def on_load(self):
        """插件加载时初始化"""
        print(f"自动记忆插件已加载 - 阈值: {self.config.get('importance_threshold', 0.7)}")

    async def process_output(self, text: str, context: Dict[str, Any]) -> str:
        """处理输出，检测是否需要保存到记忆"""
        if not self.config.get("auto_extract", True):
            return text

        # 检测是否包含重要信息
        importance_keywords = [
            "记住", "请记住", "重要的是", "关键",
            "我最喜欢的", "我不喜欢", "我的爱好是",
            "我的名字是", "我住在"
        ]

        for keyword in importance_keywords:
            if keyword in text:
                # 这里可以触发记忆保存逻辑
                print(f"检测到重要信息: {keyword}")
                break

        return text
