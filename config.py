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

def _load_config_from_file() -> Dict[str, Any]:
    """从配置文件加载配置"""
    try:
        # 直接实现配置加载逻辑，避免循环导入
        import json
        from pathlib import Path
        from cryptography.fernet import Fernet

        # 获取配置目录
        home = Path.home()
        config_dir = home / ".extensions_web"
        config_file = config_dir / "app_config.enc"
        key_file = config_dir / ".key"

        if not config_file.exists():
            return {}

        if not key_file.exists():
            return {}

        # 读取密钥
        key = key_file.read_bytes()
        cipher = Fernet(key)

        # 读取并解密配置
        encrypted_data = config_file.read_bytes()
        decrypted_data = cipher.decrypt(encrypted_data)
        config = json.loads(decrypted_data.decode('utf-8'))

        return config

    except Exception as e:
        print(f"加载配置文件失败，使用默认配置: {e}")
        return {}

class Settings(BaseSettings):
    # 从配置文件加载配置
    _config_data = _load_config_from_file()

    # 基础配置 - 从配置文件读取
    PROJECT_NAME: str = _config_data.get("PROJECT_NAME", "Data Query System")
    VERSION: str = _config_data.get("VERSION", "2.0.0")
    API_V1_STR: str = "/api/v1"
    APP_NAME: str = _config_data.get("APP_NAME", "Extensions Web")
    DEBUG: bool = _config_data.get("DEBUG", False)

    # 服务器配置 - 从配置文件读取
    HOST: str = _config_data.get("HOST", "0.0.0.0")
    PORT: int = _config_data.get("PORT", 8000)
    DATA_DIR: str = _config_data.get("DATA_DIR", "data")

    # 数据库配置 - 从配置文件读取
    DATABASE_URL: str = _config_data.get("DATABASE_URL", "sqlite:///./data/db/app.db")
    DATABASE_TYPE: str = _config_data.get("DATABASE_TYPE", "sqlite")
    SQLALCHEMY_DATABASE_URI: Optional[str] = _config_data.get("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.sqlite")
    SYNC_SQLALCHEMY_DATABASE_URI: Optional[str] = _config_data.get("SYNC_SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL", "sqlite:///database.sqlite")

    # JWT配置 - 从配置文件读取
    SECRET_KEY: str = _config_data.get("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = _config_data.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _config_data.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8)

    # 文件配置 - 从配置文件读取
    UPLOAD_DIR: str = _config_data.get("UPLOAD_DIR", "data/uploads")
    MAX_FILE_SIZE: int = _config_data.get("MAX_FILE_SIZE", 100 * 1024 * 1024)
    ALLOWED_EXTENSIONS: List[str] = _config_data.get("ALLOWED_EXTENSIONS", ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.png'])
    MARKDOWN_FOLDER_PATH:str = _config_data.get("MARKDOWN_FOLDER_PATH", "data/docs")
    # 动态计算的目录路径
    @property
    def FILE_UPLOAD_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "file")

    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        return self.MAX_FILE_SIZE

    # 聊天图片配置 - 从配置文件读取
    ALLOWED_IMAGE_TYPES: List[str] = _config_data.get("ALLOWED_IMAGE_TYPES", ["image/jpeg", "image/png", "image/gif", "image/webp"])
    ALLOWED_IMAGE_EXTENSIONS: List[str] = _config_data.get("ALLOWED_IMAGE_EXTENSIONS", [".jpg", ".jpeg", ".png", ".gif", ".webp"])
    MAX_IMAGE_SIZE: int = _config_data.get("MAX_IMAGE_SIZE", 10 * 1024 * 1024)
    CHAT_UPLOAD_DIR: str = _config_data.get("CHAT_UPLOAD_DIR", "static/chat/img")
    CHAT_IMAGE_URL_PREFIX: str = _config_data.get("CHAT_IMAGE_URL_PREFIX", "/static/chat/img")

    # 模板目录 - 从配置文件读取
    TEMPLATES_DIR: str = _config_data.get("TEMPLATES_DIR", "templates")

    # 日志配置 - 从配置文件读取
    LOG_LEVEL: str = _config_data.get("LOG_LEVEL", "INFO")

    @property
    def LOG_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "logs")

    # 扩展配置 - 从配置文件读取
    EXTENSIONS_DIR: str = _config_data.get("EXTENSIONS_DIR", "data/extensions")
    EXTENSIONS_ENTRY_POINT_PREFIX: str = _config_data.get("EXTENSIONS_ENTRY_POINT_PREFIX", "/query/")
    ALLOW_EXTENSION_UPLOAD: bool = _config_data.get("ALLOW_EXTENSION_UPLOAD", True)

    # 动态计算的目录路径
    @property
    def EXT_DB_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "db")

    @property
    def HELP_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "help")

    CONFIG_DIR: str = _config_data.get("CONFIG_DIR", os.path.join(os.path.expanduser("~"), ".config", "data_query_system"))

    # Token配置 - 从配置文件读取
    TOKEN_NAME: str = _config_data.get("TOKEN_NAME", "access_token")

    # 应用过期时间 - 从配置文件读取
    EXPIRE_TIME: Optional[str] = _config_data.get("EXPIRE_TIME", (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S"))

    # 外部数据库配置 - 从配置文件读取
    EXT_DB_TYPE: str = _config_data.get("EXT_DB_TYPE", "sqlite")
    EXT_DB_CONFIG: Dict[str, Dict[str, str]] = _config_data.get("EXT_DB_CONFIG", {
        "sqlite": {"db_url": "sqlite+aiosqlite:///./database.sqlite"},
        "postgresql": {"db_url": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"},
        "mysql": {"db_url": "mysql+aiomysql://root:root@localhost:3306/mysql"},
        "mssql": {"db_url": "mssql+pyodbc://sa:123456@localhost:1433/test?driver=ODBC+Driver+17+for+SQL+Server"}
    })

    # 用户配置 - 从配置文件读取
    ALLOW_REGISTER: bool = _config_data.get("ALLOW_REGISTER", True)
    DEFAULT_USER_ROLE: str = _config_data.get("DEFAULT_USER_ROLE", "普通用户")

    @property
    def DEFAULT_ROLE(self) -> str:
        return self.DEFAULT_USER_ROLE

    # 邮件配置 - 从配置文件读取
    SMTP_HOST: str = _config_data.get("SMTP_HOST", "")
    SMTP_PORT: int = _config_data.get("SMTP_PORT", 587)
    SMTP_USER: str = _config_data.get("SMTP_USER", "")
    SMTP_PASSWORD: str = _config_data.get("SMTP_PASSWORD", "")
    SMTP_TLS: bool = _config_data.get("SMTP_TLS", True)

    # 模块启用配置
    FILE_ENABLE: bool = _config_data.get("FILE_ENABLE", False)
    CHAT_ENABLE: bool = _config_data.get("CHAT_ENABLE", False)
    QR_ENABLE: bool = _config_data.get("QR_ENABLE", False)
    SCHEDULER_ENABLE: bool = _config_data.get("SCHEDULER_ENABLE", False)
    LOG_ENABLE: bool = _config_data.get("LOG_ENABLE", False)
    DATABASE_ENABLE: bool = _config_data.get("DATABASE_ENABLE", False)
    
    # 国际化配置 - 从配置文件读取
    TIMEZONE: str = _config_data.get("TIMEZONE", "Asia/Shanghai")
    LANGUAGE: str = _config_data.get("LANGUAGE", "zh-CN")

    class Config:
        case_sensitive = True
        env_file = ".env"
def create_settings() -> Settings:
    """创建设置实例并确保目录存在"""
    # 创建设置实例
    settings_instance = Settings()

    # 确保必要的目录存在
    os.makedirs(settings_instance.DATA_DIR, exist_ok=True)
    os.makedirs(settings_instance.FILE_UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings_instance.CHAT_UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings_instance.EXTENSIONS_DIR, exist_ok=True)
    os.makedirs(settings_instance.CONFIG_DIR, exist_ok=True)
    os.makedirs(settings_instance.EXT_DB_DIR, exist_ok=True)
    os.makedirs(settings_instance.HELP_DIR, exist_ok=True)

    return settings_instance

# 创建全局设置实例
settings = create_settings()
