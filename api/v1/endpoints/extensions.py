"""
扩展相关的API端点
"""
from datetime import datetime
from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core import auth
from core.extension_manager import ExtensionManager
from db.session import get_db
from models.extension import Extension
from schemas.extension import ExtensionInDB, ExtensionUpdate
from models.user import User
from core.extension_manager import logger

router = APIRouter()
extension_manager: ExtensionManager


def init_manager(manager: ExtensionManager):
    """
    初始化路由器
    
    Args:
        manager: 扩展管理器实例
    """
    global extension_manager
    extension_manager = manager
    logger.info("扩展程序初始化完成")


@router.get("", response_model=List[ExtensionInDB])
async def get_extensions(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取扩展列表
    """
    extensions = await extension_manager.list_extensions(db)
    for extension in extensions:
        user =await db.execute(select(User).where(User.id == extension.creator_id))
        extension.creator = user.scalar_one_or_none()
    return extensions


@router.post("", response_model=ExtensionInDB)
async def create_extension(
        *,
        db: AsyncSession = Depends(get_db),
        name: str = Form(...),
        description: Optional[str] = Form(None),
        execution_mode: str = Form(...),
        render_type: str = Form(...),
        show_in_home: Optional[bool] = Form(None),
        file: UploadFile = File(...),
        current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    创建新扩展
    """
    if not extension_manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展管理器未初始化"
        )
    # 创建UUID
    extension_id = str(uuid.uuid4())
    # 直接写入到文件
    with open(f"{settings.EXTENSIONS_DIR}/{extension_id}.py", "wb") as f:
        f.write(file.file.read())
    # 先写入数据库
    extension = Extension(
        id=extension_id,
        name=name,
        description=description,
        enabled=False,
        execution_mode=execution_mode,
        show_in_home=bool(show_in_home),
        render_type=render_type,
        creator_id=current_user.id,
        created_at=datetime.now(),
        entry_point=settings.EXTENSIONS_ENTRY_POINT_PREFIX + extension_id
    )
    db.add(extension)
    await db.commit()
    await db.refresh(extension)
    # 加载
    extension_ext = await extension_manager.load_extension(extension_id, db)
    if not extension_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展安装失败"
        )
    return extension


@router.get("/{extension_id}", response_model=ExtensionInDB)
async def get_extension(
        *,
        db: AsyncSession = Depends(get_db),
        extension_id: str,
        current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取扩展信息
    """
    extension = await db.execute(select(Extension).where(Extension.id == extension_id))
    extension = extension.scalar_one_or_none()
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="扩展不存在"
        )
    extension.document =await extension_manager.get_extension_document(extension_id,db)
    return extension


@router.put("/{extension_id}", response_model=ExtensionInDB)
async def update_extension(
        *,
        db: AsyncSession = Depends(get_db),
        extension_id: str,
        extension_in: ExtensionUpdate,
        current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    更新扩展信息
    """
    extension = await db.execute(select(Extension).where(Extension.id == extension_id))
    extension = extension.scalar_one_or_none()
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="扩展不存在"
        )
    if extension.creator_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    extension = await extension_manager.update_extension(
        extension_id=extension_id,
        updateExtension=extension_in,
        db=db
    )
    return extension


@router.delete("/{extension_id}")
async def delete_extension(
        *,
        db: AsyncSession = Depends(get_db),
        extension_id: str,
        current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    删除扩展
    """
    extension = await db.execute(select(Extension).where(Extension.id == extension_id))
    extension = extension.scalar_one_or_none()
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="扩展不存在"
        )
    if extension.creator_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    success = await extension_manager.delete_extension(extension_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展卸载失败"
        )
    return {"message": "扩展已删除"}


@router.get("/{extension_id}/config")
async def get_extension_config(
        *,
        db: AsyncSession = Depends(get_db),
        extension_id: str,
        current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取扩展配置
    """
    extension = await db.execute(select(Extension).where(Extension.id == extension_id))
    extension = extension.scalar_one_or_none()
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="扩展不存在"
        )
    config_form = await extension_manager.get_extension_config(extension_id, db)
    return {"config_form": config_form, "config": extension.config}


