"""
扩展相关的API端点
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core import auth
from new_app.core.extension_manager import ExtensionManager
from new_app.db.session import get_db
from new_app.schemas.extension import Extension as ExtensionSchema
from new_app.schemas.extension import ExtensionCreate, ExtensionUpdate
from new_app.models.user import User as UserModel

router = APIRouter()

@router.get("", response_model=List[ExtensionSchema])
async def read_extensions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取扩展列表
    """
    extension_manager = ExtensionManager(db)
    return await extension_manager.get_extensions(skip=skip, limit=limit)

@router.post("", response_model=ExtensionSchema)
async def create_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_in: ExtensionCreate,
    files: List[UploadFile] = File(...),
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    创建新扩展
    """
    extension_manager = ExtensionManager(db)
    extension = await extension_manager.install_extension(
        extension_data={
            **extension_in.dict(),
            "creator_id": current_user.id
        },
        files=files
    )
    if not extension:
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
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取扩展信息
    """
    extension_manager = ExtensionManager(db)
    extension = await extension_manager.get_extension(extension_id)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="扩展不存在"
        )
    return extension

@router.put("/{extension_id}", response_model=ExtensionSchema)
async def update_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_id: int,
    extension_in: ExtensionUpdate,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    更新扩展信息
    """
    extension_manager = ExtensionManager(db)
    extension = await extension_manager.get_extension(extension_id)
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
        data=extension_in.dict(exclude_unset=True)
    )
    return extension

@router.delete("/{extension_id}")
async def delete_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_id: int,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    删除扩展
    """
    extension_manager = ExtensionManager(db)
    extension = await extension_manager.get_extension(extension_id)
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
    
    success = await extension_manager.uninstall_extension(extension_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展卸载失败"
        )
    return {"message": "扩展已删除"}

@router.post("/{extension_id}/run")
async def run_extension(
    *,
    db: AsyncSession = Depends(get_db),
    extension_id: int,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    运行扩展
    """
    extension_manager = ExtensionManager(db)
    extension = await extension_manager.get_extension(extension_id)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="扩展不存在"
        )
    if not extension.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扩展未启用"
        )
    
    result = await extension_manager.run_extension(
        extension_id,
        user_id=current_user.id
    )
    return {"result": result} 