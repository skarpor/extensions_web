#!/usr/bin/env python3
"""
系统设置API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from core.config_manager import config_manager
from core.auth import manage_system
from core.logger import get_logger
from db.session import get_db
from models.user import User as DBUser

router = APIRouter()
logger = get_logger("settings")

class SystemSettings(BaseModel):
    """系统设置模型"""
    # 基础配置
    APP_NAME: str = Field(..., description="应用名称")
    DEBUG: bool = Field(False, description="调试模式")
    HOST: str = Field("0.0.0.0", description="监听地址")
    PORT: int = Field(8000, description="监听端口")
    
    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="访问令牌过期时间(分钟)")
    ALGORITHM: str = Field("HS256", description="加密算法")
    SECRET_KEY_SET: bool = Field(False, description="密钥是否已设置")
    
    # 数据库配置
    DATABASE_URL: str = Field(..., description="数据库连接URL")
    DATABASE_TYPE: str = Field("sqlite", description="数据库类型")
    
    # 文件配置
    UPLOAD_DIR: str = Field("data/uploads", description="上传目录")
    MAX_FILE_SIZE: int = Field(104857600, description="最大文件大小(字节)")
    ALLOWED_EXTENSIONS: list = Field(default_factory=list, description="允许的文件扩展名")
    
    # 扩展配置
    EXTENSIONS_DIR: str = Field("data/extensions", description="扩展目录")
    ALLOW_EXTENSION_UPLOAD: bool = Field(True, description="允许上传扩展")
    
    # 用户配置
    ALLOW_REGISTER: bool = Field(True, description="允许用户注册")
    DEFAULT_USER_ROLE: str = Field("user", description="默认用户角色")
    
    # 日志配置
    LOG_LEVEL: str = Field("INFO", description="日志级别")
    LOG_FILE: str = Field("data/logs/app.log", description="日志文件路径")
    
    # 邮件配置
    SMTP_HOST: str = Field("", description="SMTP服务器地址")
    SMTP_PORT: int = Field(587, description="SMTP端口")
    SMTP_USER: str = Field("", description="SMTP用户名")
    SMTP_PASSWORD: str = Field("", description="SMTP密码")
    SMTP_TLS: bool = Field(True, description="启用TLS")
    
    # 系统配置
    TIMEZONE: str = Field("Asia/Shanghai", description="时区")
    LANGUAGE: str = Field("zh-CN", description="语言")

class SecretKeyUpdate(BaseModel):
    """密钥更新模型"""
    secret_key: str = Field(..., min_length=32, description="新的密钥(至少32位)")

class ExpiryInfo(BaseModel):
    """过期信息模型"""
    expired: bool = Field(..., description="是否已过期")
    expiry_date: Optional[str] = Field(None, description="过期日期")
    initialized_at: Optional[str] = Field(None, description="初始化时间")
    days_left: int = Field(0, description="剩余天数")

@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db)
):
    """获取系统设置"""
    try:
        config = config_manager.get_editable_config()
        logger.info(f"用户 {current_user.username} 获取系统设置")
        return SystemSettings(**config)
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统设置失败"
        )

@router.put("/settings", response_model=Dict[str, str])
async def update_system_settings(
    settings: SystemSettings,
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db)
):
    """更新系统设置"""
    try:
        # 转换为字典，排除不需要保存的字段
        settings_dict = settings.dict()
        settings_dict.pop("SECRET_KEY_SET", None)  # 移除密钥设置状态字段
        
        # 保存配置
        success = config_manager.save_config(settings_dict)
        
        if success:
            logger.info(f"用户 {current_user.username} 更新系统设置成功")
            return {"message": "系统设置更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存系统设置失败"
            )
            
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新系统设置失败"
        )

@router.put("/settings/secret-key", response_model=Dict[str, str])
async def update_secret_key(
    key_update: SecretKeyUpdate,
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db)
):
    """更新系统密钥"""
    try:
        success = config_manager.set_config_value("SECRET_KEY", key_update.secret_key)
        
        if success:
            logger.info(f"用户 {current_user.username} 更新系统密钥成功")
            return {"message": "系统密钥更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存系统密钥失败"
            )
            
    except Exception as e:
        logger.error(f"更新系统密钥失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新系统密钥失败"
        )

@router.get("/expiry-info", response_model=ExpiryInfo)
async def get_expiry_info():
    """获取系统过期信息（无需认证）"""
    try:
        expiry_info = config_manager.get_expiry_info()
        return ExpiryInfo(**expiry_info)
    except Exception as e:
        logger.error(f"获取过期信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取过期信息失败"
        )

@router.get("/config-status", response_model=Dict[str, Any])
async def get_config_status(
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db)
):
    """获取配置状态信息"""
    try:
        config = config_manager.load_config()
        expiry_info = config_manager.get_expiry_info()
        
        status_info = {
            "config_file_exists": config_manager.config_file.exists(),
            "config_dir": str(config_manager.config_dir),
            "initialized_at": config.get("INITIALIZED_AT"),
            "updated_at": config.get("UPDATED_AT"),
            "expiry_info": expiry_info,
            "total_config_items": len(config)
        }
        
        logger.info(f"用户 {current_user.username} 获取配置状态")
        return status_info
        
    except Exception as e:
        logger.error(f"获取配置状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置状态失败"
        )
