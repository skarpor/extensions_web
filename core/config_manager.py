#!/usr/bin/env python3
"""
配置管理器 - 负责配置的加密存储和读取
"""

import os
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.logger import get_logger
from config import settings

logger = get_logger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "app_config.enc"
        self.key_file = self.config_dir / ".key"
        self._ensure_config_dir()
        self._cipher = None
        
    def _get_config_dir(self) -> Path:
        """获取配置目录"""
        home = Path.home()
        config_dir = home / ".extensions_web"
        return config_dir
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(exist_ok=True)
        
    def _get_or_create_key(self) -> bytes:
        """获取或创建加密密钥"""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        
        # 生成新密钥
        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        
        # 设置文件权限（仅所有者可读写）
        if os.name != 'nt':  # 非Windows系统
            os.chmod(self.key_file, 0o600)
            
        logger.info("生成新的配置加密密钥")
        return key
    
    def _get_cipher(self) -> Fernet:
        """获取加密器"""
        if self._cipher is None:
            key = self._get_or_create_key()
            self._cipher = Fernet(key)
        return self._cipher
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        # 从当前settings获取默认值
        default_config = {
            # 基础配置
            "APP_NAME": getattr(settings, 'APP_NAME', 'Extensions Web'),
            "DEBUG": getattr(settings, 'DEBUG', False),
            "HOST": getattr(settings, 'HOST', '0.0.0.0'),
            "PORT": getattr(settings, 'PORT', 8000),
            
            # 安全配置
            "SECRET_KEY": getattr(settings, 'SECRET_KEY', ''),
            "ACCESS_TOKEN_EXPIRE_MINUTES": getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30),
            "ALGORITHM": getattr(settings, 'ALGORITHM', 'HS256'),
            
            # 数据库配置
            "DATABASE_URL": getattr(settings, 'DATABASE_URL', 'sqlite:///./data/db/app.db'),
            "DATABASE_TYPE": getattr(settings, 'DATABASE_TYPE', 'sqlite'),
            
            # 文件配置
            "UPLOAD_DIR": getattr(settings, 'UPLOAD_DIR', 'data/uploads'),
            "MAX_FILE_SIZE": getattr(settings, 'MAX_FILE_SIZE', 100 * 1024 * 1024),  # 100MB
            "ALLOWED_EXTENSIONS": getattr(settings, 'ALLOWED_EXTENSIONS', ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.png']),
            
            # 扩展配置
            "EXTENSIONS_DIR": getattr(settings, 'EXTENSIONS_DIR', 'data/extensions'),
            "ALLOW_EXTENSION_UPLOAD": getattr(settings, 'ALLOW_EXTENSION_UPLOAD', True),
            
            # 用户配置
            "ALLOW_REGISTER": getattr(settings, 'ALLOW_REGISTER', True),
            "DEFAULT_USER_ROLE": getattr(settings, 'DEFAULT_USER_ROLE', 'user'),
            
            # 日志配置
            "LOG_LEVEL": getattr(settings, 'LOG_LEVEL', 'INFO'),
            "LOG_FILE": getattr(settings, 'LOG_FILE', 'data/logs/app.log'),
            
            # 邮件配置
            "SMTP_HOST": getattr(settings, 'SMTP_HOST', ''),
            "SMTP_PORT": getattr(settings, 'SMTP_PORT', 587),
            "SMTP_USER": getattr(settings, 'SMTP_USER', ''),
            "SMTP_PASSWORD": getattr(settings, 'SMTP_PASSWORD', ''),
            "SMTP_TLS": getattr(settings, 'SMTP_TLS', True),
            
            # 系统配置
            "TIMEZONE": getattr(settings, 'TIMEZONE', 'Asia/Shanghai'),
            "LANGUAGE": getattr(settings, 'LANGUAGE', 'zh-CN'),
            
            # 过期时间（首次初始化时设置，不在页面显示）
            "EXPIRY_DATE": (datetime.now() + timedelta(days=90)).isoformat(),
            "INITIALIZED_AT": datetime.now().isoformat(),
        }
        
        return default_config
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if not self.config_file.exists():
                # 首次运行，创建默认配置
                default_config = self._get_default_config()
                self.save_config(default_config)
                logger.info("创建默认配置文件")
                return default_config
            
            # 读取加密配置
            encrypted_data = self.config_file.read_bytes()
            cipher = self._get_cipher()
            decrypted_data = cipher.decrypt(encrypted_data)
            config = json.loads(decrypted_data.decode('utf-8'))
            
            logger.info("成功加载配置文件")
            return config
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            # 返回默认配置
            return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        try:
            # 确保过期时间存在
            if "EXPIRY_DATE" not in config:
                config["EXPIRY_DATE"] = (datetime.now() + timedelta(days=90)).isoformat()
            
            # 更新修改时间
            config["UPDATED_AT"] = datetime.now().isoformat()
            
            # 加密并保存
            cipher = self._get_cipher()
            config_json = json.dumps(config, indent=2, ensure_ascii=False)
            encrypted_data = cipher.encrypt(config_json.encode('utf-8'))
            
            self.config_file.write_bytes(encrypted_data)
            
            # 设置文件权限
            if os.name != 'nt':  # 非Windows系统
                os.chmod(self.config_file, 0o600)
            
            logger.info("配置保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取单个配置值"""
        config = self.load_config()
        return config.get(key, default)
    
    def set_config_value(self, key: str, value: Any) -> bool:
        """设置单个配置值"""
        config = self.load_config()
        config[key] = value
        return self.save_config(config)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        try:
            expiry_date_str = self.get_config_value("EXPIRY_DATE")
            if not expiry_date_str:
                return True
            
            expiry_date = datetime.fromisoformat(expiry_date_str)
            return datetime.now() > expiry_date
            
        except Exception as e:
            logger.error(f"检查过期时间失败: {e}")
            return True
    
    def get_expiry_info(self) -> Dict[str, Any]:
        """获取过期信息"""
        try:
            expiry_date_str = self.get_config_value("EXPIRY_DATE")
            initialized_at_str = self.get_config_value("INITIALIZED_AT")
            
            if not expiry_date_str:
                return {"expired": True, "days_left": 0}
            
            expiry_date = datetime.fromisoformat(expiry_date_str)
            now = datetime.now()
            days_left = (expiry_date - now).days
            
            return {
                "expired": now > expiry_date,
                "expiry_date": expiry_date_str,
                "initialized_at": initialized_at_str,
                "days_left": max(0, days_left)
            }
            
        except Exception as e:
            logger.error(f"获取过期信息失败: {e}")
            return {"expired": True, "days_left": 0}
    
    def get_editable_config(self) -> Dict[str, Any]:
        """获取可编辑的配置（排除敏感和系统配置）"""
        config = self.load_config()
        
        # 排除不应在页面显示的配置
        excluded_keys = {
            "EXPIRY_DATE", "INITIALIZED_AT", "UPDATED_AT", 
            "SECRET_KEY"  # 密钥单独处理
        }
        
        editable_config = {k: v for k, v in config.items() if k not in excluded_keys}
        
        # 密钥特殊处理（只显示是否已设置）
        editable_config["SECRET_KEY_SET"] = bool(config.get("SECRET_KEY"))
        
        return editable_config

# 全局配置管理器实例
config_manager = ConfigManager()
