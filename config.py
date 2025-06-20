"""
应用配置模块
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pydantic import validator
from pydantic_settings import BaseSettings
from pydantic.networks import AnyHttpUrl

class Settings(BaseSettings):
    PROJECT_NAME: str = "Data Query System"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATA_DIR:str = "data" # 数据根目录，不要以/开头，否则会出现在盘符根目录下
    # BACKEND_CORS_ORIGINS is a comma-separated list of origins
    # BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:5173"]

    # @validator("BACKEND_CORS_ORIGINS", pre=True)
    # def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
    #     if isinstance(v, str) and not v.startswith("["):
    #         return [i.strip() for i in v.split(",")]
    #     elif isinstance(v, (list, str)):
    #         return v
    #     raise ValueError(v)

    # Database configuration
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///database.sqlite"
    )
    SYNC_SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv(
        "DATABASE_URL", "sqlite:///database.sqlite"
    )

    # JWT configuration
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    # 允许的图片类型
    ALLOWED_IMAGE_TYPES:List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]

    # 创建上传目录
    CHAT_UPLOAD_DIR:str = os.path.join("static", "chat", "img")

    # File storage
    FILE_UPLOAD_DIR: str = os.path.join(DATA_DIR,"file")
    MAX_UPLOAD_SIZE: int = 1024 * 1024 * 50  # 50MB

    # Templates
    TEMPLATES_DIR: str = "templates"

    # Logging
    LOG_DIR:str = os.path.join(DATA_DIR,"logs")

    # Extension settings
    EXTENSIONS_DIR: str =os.path.join(DATA_DIR,"extensions")
    EXTENSIONS_ENTRY_POINT_PREFIX: str = "/query/"

    # 数据库目录，非系统数据库
    EXT_DB_DIR:str = os.path.join(DATA_DIR,"db")

    # Config directory
    CONFIG_DIR: str = os.path.join(os.path.expanduser("~"), ".config", "data_query_system")

    # Token name for cookies
    TOKEN_NAME: str = "access_token"

    # Application expiry time
    EXPIRE_TIME: Optional[str] = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")

    # external DB configuration,异步数据库配置
    EXT_DB_TYPE: str = "sqlite"
    EXT_DB_CONFIG: Dict[str, Dict[str, str]] = {
        "sqlite": {
            "db_url": "sqlite+aiosqlite:///./database.sqlite"
        },
        "postgresql": {
            "db_url": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
        },
        "mysql": {
            "db_url": "mysql+aiomysql://root:root@localhost:3306/mysql"
        },
        "mssql": {
            "db_url": "mssql+pyodbc://sa:123456@localhost:1433/test?driver=ODBC+Driver+17+for+SQL+Server"
        }
    }
    # 是否允许注册
    ALLOW_REGISTER: bool = True
    class Config:
        case_sensitive = True
        env_file = ".env"


# 创建设置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.FILE_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHAT_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXTENSIONS_DIR, exist_ok=True)
os.makedirs(settings.CONFIG_DIR, exist_ok=True)
os.makedirs(settings.EXT_DB_DIR, exist_ok=True)
