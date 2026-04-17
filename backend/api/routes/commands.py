"""聊天命令路由"""
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Callable

router = APIRouter()


# ============ 内置命令定义 ============

COMMANDS: Dict[str, Dict[str, Any]] = {
    # 角色相关命令
    "char": {
        "name": "char",
        "description": "切换当前角色",
        "usage": "/char <角色名>",
        "aliases": ["character", "角色"],
        "category": "character",
        "handler": "change_character",
    },
    "reset": {
        "name": "reset",
        "description": "重置当前对话",
        "usage": "/reset",
        "aliases": ["重置"],
        "category": "session",
        "handler": "reset_conversation",
    },
    "retry": {
        "name": "retry",
        "description": "重新生成上一个回复",
        "usage": "/retry",
        "aliases": ["重试"],
        "category": "session",
        "handler": "retry_last_response",
    },

    # 记忆相关命令
    "remember": {
        "name": "remember",
        "description": "保存内容到记忆",
        "usage": "/remember <内容>",
        "aliases": ["记忆", "记住"],
        "category": "memory",
        "handler": "save_to_memory",
    },
    "forget": {
        "name": "forget",
        "description": "从记忆中删除内容",
        "usage": "/forget <关键词>",
        "aliases": ["遗忘"],
        "category": "memory",
        "handler": "remove_from_memory",
    },
    "recall": {
        "name": "recall",
        "description": "搜索记忆内容",
        "usage": "/recall <关键词>",
        "aliases": ["回忆", "搜索记忆"],
        "category": "memory",
        "handler": "search_memory",
    },

    # 生成相关命令
    "img": {
        "name": "img",
        "description": "生成图片",
        "usage": "/img <提示词>",
        "aliases": ["图片", "生成图片"],
        "category": "generation",
        "handler": "generate_image",
    },
    "translate": {
        "name": "translate",
        "description": "翻译文本",
        "usage": "/translate <文本>",
        "aliases": ["翻译"],
        "category": "utility",
        "handler": "translate_text",
    },
    "summarize": {
        "name": "summarize",
        "description": "总结当前对话",
        "usage": "/summarize",
        "aliases": ["总结", "摘要"],
        "category": "utility",
        "handler": "summarize_chat",
    },

    # 设置相关命令
    "model": {
        "name": "model",
        "description": "切换 AI 模型",
        "usage": "/model <模型名>",
        "aliases": ["模型"],
        "category": "settings",
        "handler": "switch_model",
    },
    "temp": {
        "name": "temp",
        "description": "设置温度参数",
        "usage": "/temp <0.0-2.0>",
        "aliases": ["温度"],
        "category": "settings",
        "handler": "set_temperature",
    },
    "maxlen": {
        "name": "maxlen",
        "description": "设置最大回复长度",
        "usage": "/maxlen <token数>",
        "aliases": ["最大长度"],
        "category": "settings",
        "handler": "set_max_length",
    },

    # 快捷回复
    "quick": {
        "name": "quick",
        "description": "使用快捷回复",
        "usage": "/quick <编号或名称>",
        "aliases": ["快捷"],
        "category": "quickreply",
        "handler": "use_quick_reply",
    },
    "quickadd": {
        "name": "quickadd",
        "description": "添加快捷回复",
        "usage": "/quickadd <名称>|<内容>",
        "aliases": ["添加快捷回复"],
        "category": "quickreply",
        "handler": "add_quick_reply",
    },

    # 系统命令
    "help": {
        "name": "help",
        "description": "显示帮助信息",
        "usage": "/help [命令名]",
        "aliases": ["帮助", "?"],
        "category": "system",
        "handler": "show_help",
    },
    "status": {
        "name": "status",
        "description": "显示当前状态",
        "usage": "/status",
        "aliases": ["状态"],
        "category": "system",
        "handler": "show_status",
    },
    "history": {
        "name": "history",
        "description": "显示对话历史",
        "usage": "/history [条数]",
        "aliases": ["历史"],
        "category": "session",
        "handler": "show_history",
    },
}


class CommandExecuteRequest(BaseModel):
    command: str
    args: str = ""
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class QuickReplyCreate(BaseModel):
    name: str
    content: str
    category: Optional[str] = "default"


# ============ 快捷回复存储（内存中，实际应存数据库）===========
QUICK_REPLIES: List[Dict[str, str]] = [
    {"id": "1", "name": "打招呼", "content": "你好！", "category": "greeting"},
    {"id": "2", "name": "继续", "content": "然后呢？", "category": "continue"},
    {"id": "3", "name": "详细点", "content": "能详细说说吗？", "category": "detail"},
]


@router.get("/commands")
async def list_commands():
    """获取所有可用命令"""
    return {
        "commands": list(COMMANDS.values()),
        "categories": list(set(c["category"] for c in COMMANDS.values())),
    }


@router.get("/commands/{command_name}")
async def get_command(command_name: str):
    """获取指定命令详情"""
    cmd = COMMANDS.get(command_name)
    if not cmd:
        # 检查别名
        for c in COMMANDS.values():
            if command_name in c.get("aliases", []):
                return c
        raise HTTPException(status_code=404, detail="命令不存在")
    return cmd


@router.post("/execute")
async def execute_command(payload: CommandExecuteRequest):
    """执行命令"""
    command = payload.command.lstrip("/").lower()
    cmd = COMMANDS.get(command)

    # 检查别名
    if not cmd:
        for c in COMMANDS.values():
            if command in c.get("aliases", []):
                cmd = c
                break

    if not cmd:
        return {
            "success": False,
            "error": f"未知命令: /{command}",
            "hint": "输入 /help 查看可用命令",
        }

    # 返回命令执行信息（实际处理由前端或专门的处理器完成）
    return {
        "success": True,
        "command": cmd,
        "args": payload.args,
        "handler": cmd["handler"],
        "message": f"执行命令: {cmd['name']} {payload.args}",
    }


@router.post("/parse")
async def parse_message(message: str):
    """解析消息中的命令"""
    commands_found = []
    remaining_text = message

    # 匹配命令（以 / 开头）
    pattern = r'/(\w+)(?:\s+(.+))?(?=\s*/|\s*$|$)'
    matches = re.finditer(pattern, message)

    for match in matches:
        cmd_name = match.group(1).lower()
        args = match.group(2) or ""

        cmd = COMMANDS.get(cmd_name)
        if not cmd:
            for c in COMMANDS.values():
                if cmd_name in c.get("aliases", []):
                    cmd = c
                    break

        if cmd:
            commands_found.append({
                "command": cmd,
                "args": args,
                "raw": match.group(0),
            })

    # 如果找到命令，返回解析结果和纯文本
    if commands_found:
        # 移除命令部分，只保留普通文本
        for cmd_info in commands_found:
            remaining_text = remaining_text.replace(cmd_info["raw"], "")

        return {
            "has_commands": True,
            "commands": commands_found,
            "text": remaining_text.strip(),
        }

    return {
        "has_commands": False,
        "commands": [],
        "text": message,
    }


# ============ 快捷回复路由 ============

@router.get("/quick-replies")
async def list_quick_replies():
    """获取所有快捷回复"""
    return QUICK_REPLIES


@router.post("/quick-replies")
async def add_quick_reply(data: QuickReplyCreate):
    """添加快捷回复"""
    quick_reply = {
        "id": str(len(QUICK_REPLIES) + 1),
        "name": data.name,
        "content": data.content,
        "category": data.category or "default",
    }
    QUICK_REPLIES.append(quick_reply)
    return quick_reply


@router.delete("/quick-replies/{reply_id}")
async def delete_quick_reply(reply_id: str):
    """删除快捷回复"""
    global QUICK_REPLIES
    original_len = len(QUICK_REPLIES)
    QUICK_REPLIES = [r for r in QUICK_REPLIES if r["id"] != reply_id]
    if len(QUICK_REPLIES) == original_len:
        raise HTTPException(status_code=404, detail="快捷回复不存在")
    return {"success": True}


@router.get("/quick-replies/categories")
async def list_quick_reply_categories():
    """获取快捷回复分类"""
    categories = list(set(r["category"] for r in QUICK_REPLIES))
    return categories
