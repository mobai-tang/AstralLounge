"""
配置管理
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
import json


class Settings(BaseSettings):
    app_name: str = "AstralLounge"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    host: str = "0.0.0.0"
    port: int = 8000

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [s.strip() for s in v.split(",") if s.strip()]
        return v

    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])

    data_dir: Path = Field(default=Path("./data"))
    models_dir: Path = Field(default=Path("./models"))
    plugins_dir: Path = Field(default=Path("./backend/plugins/skills"))

    vector_db_type: str = "chroma"
    vector_db_path: Path = Field(default=Path("./data/vector_db"))
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    default_model_type: str = Field(default="ollama", validation_alias="DEFAULT_MODEL_TYPE")
    default_model_name: str = Field(default="llama3.2", validation_alias="DEFAULT_MODEL_NAME")
    ollama_base_url: str = "http://localhost:11434"

    frontend_path: str = Field(default="", validation_alias="FRONTEND_PATH")

    @property
    def frontend_path_resolved(self) -> str:
        """返回实际存在的前端路径，不存在则返回空"""
        if not self.frontend_path:
            return ""
        p = Path(self.frontend_path)
        if p.exists() and p.is_dir():
            return str(p)
        return ""

    max_token_limit: int = 4096
    default_max_tokens: int = 512
    default_temperature: float = 0.7

    session_ttl: int = 86400
    memory_enabled: bool = True

    # Redis 配置
    redis_host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    redis_port: int = Field(default=6379, validation_alias="REDIS_PORT")
    redis_password: str = Field(default="", validation_alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0)
    redis_enabled: bool = Field(default=True, validation_alias="REDIS_ENABLED")

    # 模型 API Keys
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    claude_api_key: str = ""
    claude_base_url: str = "https://api.anthropic.com/v1"
    anthropic_api_version: str = "2023-06-01"
    azure_api_key: str = ""
    azure_endpoint: str = ""
    azure_api_version: str = "2024-02-01"
    azure_deployment: str = ""
    openrouter_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # 额外模型 API Keys
    groq_api_key: str = ""
    together_api_key: str = ""
    fireworks_api_key: str = ""
    novita_api_key: str = ""
    siliconflow_api_key: str = ""

    # 更多模型 API Keys
    mistral_api_key: str = ""
    gemini_api_key: str = ""
    cohere_api_key: str = ""
    ai21_api_key: str = ""
    perplexity_api_key: str = ""
    xai_api_key: str = ""
    baichuan_api_key: str = ""
    zhipu_api_key: str = ""
    tencent_secret_id: str = ""
    tencent_secret_key: str = ""

    # 本地模型服务
    lmstudio_base_url: str = "http://localhost:1234"
    lmstudio_model: str = "local-model"
    koboldcpp_base_url: str = "http://localhost:5000"
    koboldcpp_model: str = "local-model"

    # 图片生成
    sd_api_url: str = ""

    # 搜索引擎 API Keys
    google_api_key: str = ""
    bing_api_key: str = ""
    tavily_api_key: str = ""
    brave_api_key: str = ""
    serper_api_key: str = ""
    searxng_url: str = "http://localhost:8888"

    # TTS 配置
    tts_enabled: bool = Field(default=False, validation_alias="TTS_ENABLED")
    tts_provider: str = Field(default="cosyvoice", validation_alias="TTS_PROVIDER")
    cosyvoice_url: str = Field(default="http://localhost:5000", validation_alias="COSYVOICE_URL")
    gptsovits_url: str = Field(default="http://localhost:5001", validation_alias="GPTSOVITS_URL")

    # 目录配置
    characters_dir: Path = Field(default=Path("./data/characters"))
    world_info_dir: Path = Field(default=Path("./data/world_info"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
