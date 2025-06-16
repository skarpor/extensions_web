"""
扩展相关的API端点
"""
from datetime import datetime
from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.api.v1.endpoints import settings
from new_app.core import auth
from new_app.core.extension_manager import ExtensionManager
from new_app.db.session import get_db
from new_app.models.extension import Extension
from new_app.schemas.extension import Extension as ExtensionSchema
from new_app.schemas.extension import ExtensionCreate, ExtensionUpdate
from new_app.models.user import User
from new_app.core.logger import get_logger

logger = get_logger("extension")
router = APIRouter()
extension_manager: ExtensionManager = None

def init_manager(manager: ExtensionManager):
    """
    初始化路由器
    
    Args:
        manager: 扩展管理器实例
    """
    global extension_manager
    extension_manager = manager
    logger.info("扩展路由初始化完成")

@router.get("", response_model=List[ExtensionSchema])
async def read_extensions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取扩展列表
    """
    return await extension_manager.list_extensions(db=db)

@router.post("", response_model=ExtensionSchema)
async def create_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_in: ExtensionCreate,
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
    with open(f"{settings.EXTENSION_DIR}/{extension_id}.py", "w") as f:
        f.write(file.file.read())
    # 先写入数据库
    extension = Extension(
        id=extension_id,
        name=extension_in.name,
        description=extension_in.description,
        enabled=False,
        execution_mode=extension_in.execution_mode,
        show_in_home=extension_in.show_in_home,
        render_type=extension_in.render_type,
        creator_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(extension)
    await db.commit()
    # 加载
    extension_ext = extension_manager.load_extension(extension_id)
    # 二次保存
    # module = extension_ext.module
    extension.has_config_form = extension_ext.has_config_form
    extension.has_query_form = extension_ext.has_query_form
    # 更新数据库
    await db.add(extension)
    await db.commit()

    if not extension_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展安装失败"
        )
    return extension

@router.get("/{extension_id}", response_model=ExtensionSchema)
async def read_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_id: int,
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
    extension.document = extension_manager.get_extension_document(extension_id)
    return extension

@router.put("/{extension_id}", response_model=ExtensionSchema)
async def update_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_id: int,
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
        updateExtension=extension_in
    )
    return extension

@router.delete("/{extension_id}")
async def delete_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_id: int,
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
    
    success = await extension_manager.delete_extension(extension_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展卸载失败"
        )
    return {"message": "扩展已删除"}