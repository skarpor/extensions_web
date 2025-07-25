"""
文件上传下载相关的API端点
文件不仅仅归属与个人，也归属与团队
"""
from typing import Any, List

from dotenv.cli import stream_file
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request,Path,Security
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession

from core import auth
from core.permissions import upload_files, download_files, view_files, delete_files, manage_files, create_dir, delete_dir
from core.file_manager import FileManager
from db.session import get_db
from schemas.file import File as FileSchema
from models.user import User as UserModel
from core.logger import get_logger
from urllib.parse import quote

logger = get_logger(__name__)

router = APIRouter()


@router.post("/upload/{file_path:path}",response_model=List[FileSchema])
async def upload_file(
        *,
        db: AsyncSession = Depends(get_db),
        files: List[UploadFile] = File(...),
        current_user: UserModel = Depends(upload_files),
        file_path: str = Path(..., description="文件存储路径")
) -> Any:
    """
    上传文件
    参数:
    - file_path: 文件存储路径，如 /docs 或 /images/2023
    """
    file_manager = FileManager(db)
    db_files = []

    for file in files:
        db_file = await file_manager.save_file(
            file=file,
            owner_id=current_user.id,
            path=file_path  # 直接使用路径参数
        )
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件上传失败"
            )
        db_file.owner = current_user
        db_files.append(db_file)
    logger.info(f"{current_user.username}, 上传文件成功: {db_files}")
    return db_files
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

@router.get("/download/{file_id}")
async def download_file(
    *,
    db: AsyncSession = Depends(get_db),
    file_id: int,
    request: Request,
    current_user: UserModel = Depends(download_files),
) -> Any:
    """
    下载文件
    """
    file_manager = FileManager(db)
    file = await file_manager.get_file(file_id,request.query_params.get("path"))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    

    file_path = file.filepath+'/'+file.filename
    file_path = file_manager.get_file_path(file_path,request.query_params.get("path"))
    logger.info(f"{current_user.username}, 下载文件: {file_path}")
    # 生成文件流
    def file_stream():
        with open(file_path, "rb") as f:
            yield from f
    # 对文件名进行URL编码
    encoded_filename = quote(file.filename)
    # 返回文件流
    return StreamingResponse(file_stream(), media_type='application/octet-stream',headers={"Content-Disposition": f"attachment; filename={encoded_filename}"})

@router.delete("/file/{file_id}")
async def delete_file(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    file_id: int,
    current_user: UserModel = Depends(delete_files),
) -> Any:
    """
    删除文件
    """
    file_manager = FileManager(db)
    file = await file_manager.get_file(file_id,request.query_params.get("path"))
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
    success = await file_manager.delete_file(file_id,request.query_params.get("path"))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件删除失败"
        )
    logger.info(f"{current_user.username}, 删除文件: {file_id}成功")
    return {"message": "文件已删除"} 
@router.get("/",response_model=List[FileSchema])
async def get_files(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(view_files),
    request: Request,

) -> Any:
    """
    获取当前用户的文件列表
    """
    logger.info(f"{current_user.username}, 获取文件列表")
    # 获取请求参数path
    path = request.query_params.get("path") or "/"
    file_manager = FileManager(db)
    files = await file_manager.get_dir_files(path)
    for file in files:
        user = await auth.get_user_by_id(db,file.owner_id)
        file.owner = user
        file.owner_id = user.id
    return files

# 获取文件列表
@router.get("/list/{path:path}")
async def get_files_by_path(
    path: str = Path(..., description="目录路径"),
    current_user: UserModel = Depends(view_files),
    db: AsyncSession = Depends(get_db)
):
    file_manager = FileManager(db)
    files = await file_manager.get_dir_files(path)
    logger.info(f"{current_user.username}, 获取文件列表: {files}")
    return files

# 创建目录
@router.post("/mkdir/{name:path}")
async def create_directory(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(create_dir),
    request: Request,
    name: str = Path(..., description="目录名称")
):
    if '\\' in name or ':' in name or '*' in name or '?' in name or '"' in name or '<' in name or '>' in name or '|' in name or ' ' in name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目录名称不能包含/\\:*?"
        )
    file_manager = FileManager(db)
    success = await file_manager.create_dir(request.query_params.get("path"),current_user.id,name)
    # 保存到数据库中
    logger.info(f"{current_user.username}, 创建目录: {name}成功")
    if not success:
        raise HTTPException(status_code=400, detail="目录创建失败")
    return {"message": "目录创建成功"}


@router.delete("/dir")
async def delete_dir(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(delete_dir),
    request: Request,
    # security_scopes: SecurityScopes = Security(auth.has_permission,scopes = ["file:manager"]),
) -> Any:
    """
    删除目录
    """
    logger.info(f"{current_user.username}, 删除目录")
    # 如果不是超级管理员，不可删除
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    path = request.query_params.get("path")
    if not path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目录路径不能为空"
        )
    file_manager = FileManager(db)
    success = await file_manager.delete_dir(db,path)
    if not success:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目录删除失败"
        )
    logger.info(f"{current_user.username}, 删除目录: {path}成功")
    return {"message": "目录已删除"}
