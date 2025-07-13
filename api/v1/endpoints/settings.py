"""
设置相关的API端点
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core import auth
from db.session import get_db
from schemas.setting import Setting as SettingSchema
from schemas.setting import SettingCreate, SettingUpdate
from config import settings
from models.user import User
from core.auth import view_settings,update_settings

router = APIRouter()

@router.get("", response_model=List[SettingSchema])
async def read_settings(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(view_settings),
) -> Any:
    """
    获取当前用户的设置列表
    """
    settings = await settings.get_user_settings(current_user.id)
    return settings

@router.post("", response_model=SettingSchema)
async def create_setting(
    *,
    db: AsyncSession = Depends(get_db),
    setting_in: SettingCreate,
    current_user: User = Depends(update_settings),
) -> Any:
    """
    创建新设置
    """
    # 检查设置是否已存在
    existing_setting = await settings.get_by_key(
        db,
        key=setting_in.key,
        user_id=current_user.id
    )
    if existing_setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="设置已存在"
        )
    
    setting = await settings.create_setting(
        db=db,
        key=setting_in.key,
        value=setting_in.value,
        user_id=current_user.id
    )
    return setting

@router.get("/{setting_id}", response_model=SettingSchema)
async def read_setting(
    *,
    db: AsyncSession = Depends(get_db),
    setting_id: int,
    current_user: User = Depends(view_setting),
) -> Any:
    """
    获取设置信息
    """
    setting = await settings.get_setting(setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设置不存在"
        )
    if setting.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return setting

@router.put("/{setting_id}", response_model=SettingSchema)
async def update_setting(
    *,
    db: AsyncSession = Depends(get_db),
    setting_id: int,
    setting_in: SettingUpdate,
    current_user: User = Depends(update_settings),
) -> Any:
    """
    更新设置
    """
    setting = await settings.get_setting(setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设置不存在"
        )
    if setting.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    setting = await settings.update_setting(
        db=db,
        db_obj=setting,
        obj_in=setting_in
    )
    return setting

