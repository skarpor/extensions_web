"""
文件相关的API端点
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core import auth
from new_app.core.file_manager import FileManager
from new_app.db.session import get_db
from new_app.schemas.file import File as FileSchema
from new_app.models.user import User as UserModel

router = APIRouter()

@router.post("/upload", response_model=FileSchema)
async def upload_file(
    *,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    上传文件
    """
    file_manager = FileManager(db)
    db_file = await file_manager.save_file(
        file=file,
        owner_id=current_user.id
    )
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件上传失败"
        )
    return db_file

# @router.get("/my-files", response_model=List[FileSchema])
# async def read_user_files(
#     *,
#     db: AsyncSession = Depends(get_db),
#     current_user: UserModel = Depends(auth.get_current_active_user),
# ) -> Any:
#     """
#     获取当前用户的文件列表
#     """
#     file_manager = FileManager(db)
#     return await file_manager.get_user_files(current_user.id)

@router.get("/{file_id}", response_model=FileSchema)
async def read_file(
    *,
    db: AsyncSession = Depends(get_db),
    file_id: int,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取文件信息
    """
    file_manager = FileManager(db)
    file = await file_manager.get_file(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    if file.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return file

@router.delete("/{file_id}")
async def delete_file(
    *,
    db: AsyncSession = Depends(get_db),
    file_id: int,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    删除文件
    """
    file_manager = FileManager(db)
    file = await file_manager.get_file(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    if file.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    success = await file_manager.delete_file(file_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件删除失败"
        )
    return {"message": "文件已删除"} 