"""
文件管理API路由

提供文件管理相关的API路由，包括文件列表、下载和删除功能。
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.file_manager import FileManager
from app.core.logger import get_logger
from app.core.auth import get_current_user
from app.models.user import User
from app.utils import view_online
from config import TEMPLATE_DIR
logger = get_logger("file_routes")
router = APIRouter()
file_manager: Optional[FileManager] = None
templates = Jinja2Templates(directory=TEMPLATE_DIR)

def init_router(manager: FileManager):
    """
    初始化路由器
    
    Args:
        manager: 文件管理器实例
    """
    global file_manager
    file_manager = manager
    logger.info("文件路由初始化完成")


@router.get("/api/files", response_model=List[Dict])
async def list_files(
    extension_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    获取文件列表
    
    Args:
        extension_id: 可选，按扩展ID筛选
        limit: 每页文件数量，默认50
        offset: 起始位置，默认0
        current_user: 当前用户
        
    Returns:
        文件列表
    """
    if not file_manager:
        logger.error("文件管理器未初始化")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="文件管理系统未初始化")
    
    try:
        # logger.info(f"用户 {current_user.username} 请求文件列表")
        files = file_manager.list_files(extension_id=extension_id, limit=limit, offset=offset)
        
        # 移除敏感信息
        for file in files:
            file.pop("path", None)
        print(files)
        return files
    
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取文件列表失败: {str(e)}")
# 抽取文件管理页面中的数据，新增一个接口
@router.get("/api/file-manager-data", response_model=List[Dict])
async def file_manager_data(
    extension_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    获取文件管理页面中的数据
    """
    if not file_manager:
        logger.error("文件管理器未初始化")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="文件管理系统未初始化")
    
    try:
        files = file_manager.list_files(extension_id=extension_id, limit=limit, offset=offset)
        return files
    except Exception as e:
        logger.error(f"获取文件管理页面中的数据失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取文件管理页面中的数据失败: {str(e)}")




@router.get("/file-manager", response_class=HTMLResponse)
async def file_manager_page(
    request: Request,
    extension_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=5, le=100),
):
    """
    文件管理页面
    
    Args:
        request: 请求对象
        extension_id: 可选，按扩展ID筛选
        page: 页码，默认1
        limit: 每页文件数量，默认20
        current_user: 当前用户
        
    Returns:
        HTML页面
    """
    if not file_manager:
        logger.error("文件管理器未初始化")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="文件管理系统未初始化")
    
    try:
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 获取文件列表
        files = file_manager.list_files(extension_id=extension_id, limit=limit, offset=offset)
        
        # 获取所有扩展ID以便过滤
        extension_ids = set()
        for file in files:
            if file.get("extension_id"):
                extension_ids.add(file.get("extension_id"))
        
        # 格式化文件大小和日期
        for file in files:
            # 添加下载URL
            file["download_url"] = f"/api/files/{file['id']}"
            
            # 格式化文件大小
            size_bytes = file.get("size", 0)
            if size_bytes < 1024:
                file["size_formatted"] = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                file["size_formatted"] = f"{size_bytes/1024:.2f} KB"
            else:
                file["size_formatted"] = f"{size_bytes/(1024*1024):.2f} MB"
            
            # 尝试格式化日期
            try:
                import datetime
                created_at = datetime.datetime.fromisoformat(file.get("created_at", ""))
                file["created_at_formatted"] = created_at.strftime("%Y-%m-%d %H:%M:%S")
            except:
                file["created_at_formatted"] = file.get("created_at", "")
        
        # 计算总页数
        total_files = len(file_manager.list_files(extension_id=extension_id))
        total_pages = (total_files + limit - 1) // limit
        
        # 渲染模板
        return templates.TemplateResponse(
            "file_manager.html",
            {
                "request": request,
                "files": files,
                "current_page": page,
                "limit": limit,
                "extension_id": extension_id,
                "extension_ids": sorted(list(extension_ids)),
                "title": "文件管理",
                "nav_active": "file-manager",
                "total_pages": total_pages
            }
        )
    
    except Exception as e:
        logger.error(f"渲染文件管理页面失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"渲染文件管理页面失败: {str(e)}")

@router.get("/api/files/{file_id}")
async def download_file(
    file_id: str = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_user)
):
    """
    下载文件
    
    Args:
        file_id: 文件ID
        current_user: 当前用户
        
    Returns:
        文件响应
    """
    if not file_manager:
        logger.error("文件管理器未初始化")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="文件管理系统未初始化")
    
    try:
        logger.info(f"用户 {current_user.username} 下载文件 {file_id}")
        file_meta = file_manager.get_file(file_id)
        
        if not file_meta:
            logger.warning(f"文件不存在: {file_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
        
        return FileResponse(
            path=file_meta["path"],
            filename=file_meta["filename"],
            media_type=file_meta.get("content_type")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {file_id}, {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"下载文件失败: {str(e)}")

@router.delete("/api/files/{file_id}")
async def delete_file(
    file_id: str = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_user)
):
    """
    删除文件
    
    Args:
        file_id: 文件ID
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    if not file_manager:
        logger.error("文件管理器未初始化")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="文件管理系统未初始化")
    
    try:
        logger.info(f"用户 {current_user.username} 删除文件 {file_id}")
        
        # 检查权限，只有管理员可以删除文件
        if current_user.role != "admin":
            logger.warning(f"非管理员用户 {current_user.username} 尝试删除文件")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以删除文件")
        
        success = file_manager.delete_file(file_id)
        
        if not success:
            logger.warning(f"文件不存在或删除失败: {file_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在或删除失败")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {file_id}, {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除文件失败: {str(e)}")

@router.post("/api/files/cleanup")
async def cleanup_files(
    days: int = Query(30, ge=1, le=365, description="文件保留天数"),
    current_user: User = Depends(get_current_user)
):
    """
    清理旧文件
    
    Args:
        days: 文件保留天数，超过此天数的文件将被删除
        current_user: 当前用户
        
    Returns:
        清理结果
    """
    if not file_manager:
        logger.error("文件管理器未初始化")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="文件管理系统未初始化")
    
    try:
        # 检查权限，只有管理员可以清理文件
        if current_user.role != "admin":
            logger.warning(f"非管理员用户 {current_user.username} 尝试清理文件")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以清理文件")
        
        logger.info(f"用户 {current_user.username} 清理超过 {days} 天的文件")
        count = file_manager.cleanup_old_files(days)
        
        return {"success": True, "deleted_count": count}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理文件失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"清理文件失败: {str(e)}") 



