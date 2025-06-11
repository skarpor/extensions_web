"""
应用配置模块
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import validator
from pydantic import BaseSettings
from pydantic.networks import AnyHttpUrl

class Settings(BaseSettings):
    PROJECT_NAME: str = "Data Query System"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # BACKEND_CORS_ORIGINS is a comma-separated list of origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:5173"]

    # @validator("BACKEND_CORS_ORIGINS", pre=True)
    # def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
    #     if isinstance(v, str) and not v.startswith("["):
    #         return [i.strip() for i in v.split(",")]
    #     elif isinstance(v, (list, str)):
    #         return v
    #     raise ValueError(v)

    # Database configuration
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./database.sqlite"
    )

    # JWT configuration
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    # 允许的图片类型
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

    # 创建上传目录
    CHAT_UPLOAD_DIR = os.path.join("static", "uploads", "chat")

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 1024 * 1024 * 50  # 50MB

    # Templates
    TEMPLATES_DIR: str = "templates"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # Extension settings
    EXTENSIONS_DIR: str = "extensions"
    CONFIG_DIR: str = os.path.join(os.path.expanduser("~"), ".config", "data_query_system")

    # Application expiry
    EXPIRE_TIME: Optional[str] = None

    # New fields from the code block
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    DATA_DIR: str = "./data"
    EXTENSION_DB_TYPE: str = "sqlite"  # 可选: sqlite, postgres, mysql
    
    # 统一数据库配置
    DB_TYPE: str = "sqlite"  # 数据库类型: sqlite, postgres, mysql
    DB_PATH: str = "./data/extension_db.db"  # 统一扩展数据库路径
    # TABLE_PREFIX: str = "ext_"  # 表名前缀，用于区分不同扩展的表

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 

# Ensure necessary directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXTENSIONS_DIR, exist_ok=True)
os.makedirs(settings.CONFIG_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
# os.makedirs(os.path.join(settings.DATA_DIR, "extension_dbs"), exist_ok=True)