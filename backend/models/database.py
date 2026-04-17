"""
数据库模型
"""
import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Table
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path

from backend.config.settings import settings

DB_PATH = Path("./data/astral.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=settings.debug
)

Base = declarative_base()


class CharacterModel(Base):
    """角色模型"""
    __tablename__ = "characters"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    personality = Column(Text, default="")
    scenario = Column(Text, default="")
    greeting = Column(Text, default="")
    avatar = Column(Text, default="")
    tags = Column(JSON, default=list)
    examples = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatSessionModel(Base):
    """对话会话模型"""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    character_id = Column(String, ForeignKey("characters.id"), nullable=True)
    character_name = Column(String, default="")
    model = Column(String, default="llama3.2")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    pinned = Column(Boolean, default=False)
    group_id = Column(String, nullable=True)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan")


class MessageModel(Base):
    """消息模型"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, default="")
    character_id = Column(String, nullable=True)
    timestamp = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSessionModel", back_populates="messages")


class GroupModel(Base):
    """会话分组模型"""
    __tablename__ = "chat_groups"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    color = Column(String, default="#667eea")
    created_at = Column(DateTime, default=datetime.utcnow)


class LorebookModel(Base):
    """世界设定模型"""
    __tablename__ = "lorebooks"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    scan_depth = Column(Integer, default=2)
    context_length = Column(Integer, default=2048)
    insert_mode = Column(String, default="append")
    force_activation = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entries = relationship("LorebookEntryModel", back_populates="lorebook", cascade="all, delete-orphan")


class LorebookEntryModel(Base):
    """世界设定条目模型"""
    __tablename__ = "lorebook_entries"

    id = Column(String, primary_key=True)
    lorebook_id = Column(String, ForeignKey("lorebooks.id"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, default="")
    keywords = Column(JSON, default=list)
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lorebook = relationship("LorebookModel", back_populates="entries")


class MemoryModel(Base):
    """记忆模型"""
    __tablename__ = "memories"

    id = Column(String, primary_key=True)
    title = Column(String, default="")
    content = Column(Text, nullable=False)
    category = Column(String, default="")
    tags = Column(JSON, default=list)
    importance = Column(Integer, default=5)
    source = Column(String, default="manual")  # auto, manual
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PluginConfigModel(Base):
    """插件配置模型"""
    __tablename__ = "plugin_configs"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PersonaModel(Base):
    """用户人设模型"""
    __tablename__ = "personas"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    avatar = Column(Text, default="")
    system_prompt = Column(Text, default="")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GroupChatGroupModel(Base):
    """群聊分组模型"""
    __tablename__ = "group_chat_groups"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    members = Column(JSON, default=list)
    chat_mode = Column(String, default="rotation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    """获取数据库会话"""
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
