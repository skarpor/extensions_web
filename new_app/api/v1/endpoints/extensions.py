"""
扩展相关的API端点
"""
from datetime import datetime
from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core.config import settings
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
    logger.info("扩展程序初始化完成")

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
    return await extension_manager.list_extensions(db)


@router.post("", response_model=ExtensionSchema)
async def create_extension(
    *,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str = Form(...),
    execution_mode: str = Form(...),
    render_type: str = Form(...),
    show_in_home: bool = Form(...),
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
    print(show_in_home)
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
        entry_point=settings.EXTENSIONS_ENTRY_POINT_PREFIX+extension_id
    )
    print(extension)
    db.add(extension)
    await db.commit()
    await db.refresh(extension)
    # 加载
    extension_ext = await extension_manager.load_extension(extension_id,db)
    # # 二次保存
    # # module = extension_ext.module
    # extension.has_config_form = extension_ext.get("has_config_form")
    # extension.has_query_form = extension_ext.get("has_query_form")
    # # 更新数据库
    # await db.add(extension)
    # await db.commit()
    #
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
    extension.document = extension_manager.get_extension_document(extension_id)
    return extension

@router.put("/{extension_id}", response_model=ExtensionSchema)
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
    
    success = await extension_manager.delete_extension(extension_id,db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展卸载失败"
        )
    return {"message": "扩展已删除"}