"""
控制面板相关的API端点
"""
from typing import Any, Dict, List
from datetime import datetime, timedelta
import os
import psutil

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from new_app.core import auth
from new_app.db.session import get_db
from new_app.models.user import User as UserModel
from new_app.models.extension import Extension
from new_app.models.file import File
from new_app.models.chat import Chat, Message
from new_app.models.activity_log import ActivityLog
from new_app.core.config import settings

router = APIRouter()

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Dict[str, Any]:
    """
    获取系统统计信息
    """
    # 获取用户总数
    users_count = await db.scalar(select(func.count()).select_from(UserModel))
    
    # 获取扩展总数
    extensions_count = await db.scalar(select(func.count()).select_from(Extension))
    
    # 获取文件总数，过滤文件夹
    files_count = await db.scalar(select(func.count()).select_from(File).where(File.filetype != "directory"))
    
    # 获取消息总数
    messages_count = await db.scalar(select(func.count()).select_from(Message))
    
    return {
        "users_count": users_count,
        "extensions_count": extensions_count,
        "files_count": files_count,
        "messages_count": messages_count
    }

@router.get("/system")
async def get_system_info(
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Dict[str, Any]:
    """
    获取系统信息
    """
    # 检查是否为管理员
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问系统信息"
        )
    
    try:
        # 获取CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 获取内存使用情况
        memory = psutil.virtual_memory()
        memory_usage = memory.used
        
        # 获取磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_usage = disk.used
        
        # 获取系统启动时间
        boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
        
        return {
            "version": settings.VERSION,
            "start_time": boot_time,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage
        }
    except Exception as e:
        return {
            "version": settings.VERSION,
            "start_time": datetime.now().isoformat(),
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "error": str(e)
        }

@router.get("/activity")
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_active_user),
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    获取最近活动记录
    """
    # 如果不是管理员，只获取自己的活动
    if current_user.is_superuser:
        # 管理员可以看到所有活动
        query = select(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit)
    else:
        # 普通用户只能看到自己的活动
        query = select(ActivityLog).where(
            ActivityLog.user_id == current_user.id
        ).order_by(ActivityLog.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    activity_list = []
    for activity in activities:
        # 获取用户名
        user = None
        if activity.user_id:
            user_query = select(UserModel).where(UserModel.id == activity.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
        
        activity_list.append({
            "id": activity.id,
            "timestamp": activity.timestamp.isoformat(),
            "user_id": activity.user_id,
            "username": user.username if user else "系统",
            "type": activity.activity_type,
            "description": activity.description,
            "ip_address": activity.ip_address
        })
    
    return activity_list 