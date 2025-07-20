"""
示例和文档API路由

提供示例文件和文档的展示功能，包括示例列表和文档内容查看。
"""
import os
import markdown
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Path, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from core.help import get_file_list
from core.logger import get_logger
from core.auth import get_current_user
from schemas.user import User
from config import settings
logger = get_logger("help")
router = APIRouter()
from core.permissions import delete_help,upload_help,download_help,view_help

@router.get("/view/{filename}")
async def view_example(
    request: Request, 
    filename: str = Path(..., description="文件名"), 
    current_user: User = Depends(view_help)
):
    """
    查看示例文件内容
    
    Args:
        request: HTTP请求
        filename: 文件名
        current_user: 当前登录用户
        
    Returns:
        HTML响应
    """
    try:
        filepath = os.path.join(settings.HELP_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
        
        # 获取修改时间
        modified_time = os.path.getmtime(filepath)
        from datetime import datetime
        modified_time_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
        
        # 确定文件类型和内容类型
        file_type = "其他"
        content_type = "text"
        
        if filename.endswith('.md'):
            file_type = "文档"
            content_type = "markdown"
        elif filename.endswith('.py'):
            file_type = "示例扩展"
            content_type = "python"
        elif filename.endswith('.html'):
            file_type = "示例页面"
            content_type = "html"
        elif filename.endswith(".txt"):
            file_type = "文本文档"
            content_type = "text"
        elif filename.endswith(".js"):
            file_type = "JavaScript"
            content_type = "javascript"
        elif filename.endswith(".java"):
            file_type = "Java"
            content_type = "java"
        elif filename.endswith(".css"):
            file_type = "CSS"
            content_type = "css"
        elif filename.endswith(".php"):
            file_type = "PHP"
            content_type = "php"
        elif filename.endswith(".sql"):
            file_type = "SQL"
            content_type = "sql"
        elif filename.endswith(".yaml"):
            file_type = "YAML"
            content_type = "yaml"
        elif filename.endswith(".toml"):
            file_type = "TOML"
            content_type = "toml"
        elif filename.endswith(".ini"):
            file_type = "INI"
            content_type = "ini"
        elif filename.endswith(".xlsx") \
              or filename.endswith(".xls")\
              or filename.endswith(".csv")\
              or filename.endswith(".doc")\
              or filename.endswith(".docx")\
              or filename.endswith(".ppt")\
              or filename.endswith(".pptx")\
              or filename.endswith(".pdf"):
            file_type = "office"
            content_type = "office"
        
        # 读取文件内容
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                pass

        # 根据内容类型处理
        if content_type == "markdown":
            # 将Markdown转换为HTML
            content = markdown.markdown(
                content, 
                extensions=['extra', 'codehilite', 'tables', 'fenced_code']
            )
        elif content_type == "office":
            # md = markitdown.MarkItDown(enable_plugins=False)
            # content = md.convert(filepath).text_content
            content_type = "markdown"
            content = "暂不支持在线预览"
        return {
                "title": filename,
                "filename": filename,
                "file_type": file_type,
                "content_type": content_type,
                "content": content,
                "modified_time": modified_time_str,
                "user": current_user,
            }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"查看文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查看文档失败: {str(e)}")
    
# 添加一个路由，用于上传示例文件
@router.post("/upload", response_class=JSONResponse)
async def upload_example(files: List[UploadFile] = File(..., alias="files[]"), current_user: User = Depends(upload_help)):
    """
    上传示例文件
    
    Args:
        request: HTTP请求
        current_user: 当前登录用户
        
    Returns:
        JSON响应
    """
    try:
        # 遍历上传的文件，保存到示例目录，把失败的文件记录到返回结果
        failed_files = []
        success_files = []
        for file in files:
            # 检查文件是否存在
            if os.path.exists(os.path.join(settings.HELP_DIR, file.filename)):
                failed_files.append(file.filename)
                continue
            # 保存文件到示例目录
            save_path = os.path.join(settings.HELP_DIR, file.filename)
            with open(save_path, "wb") as f:
                f.write(file.file.read())
            success_files.append(file.filename)
        return JSONResponse(
            {
                "detail": "上传成功",
                "failed_files": failed_files,
                "success_files": success_files,
            }
        )
    except Exception as e:
        logger.error(f"上传示例文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传示例文件失败: {str(e)}")

# 添加一个路由，用于删除示例文件
@router.delete("/delete/{filename}", response_class=JSONResponse)
async def delete_example(filename: str, current_user: User = Depends(delete_help)):
    """
    删除示例文件
    """
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="无权限删除示例文件")
    try:
        os.remove(os.path.join(settings.HELP_DIR, filename))
        return JSONResponse(
            {
                "detail": "删除成功",
                "filename": filename
            }
        )
    except Exception as e:
        logger.error(f"删除示例文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除示例文件失败: {str(e)}")

# 添加一个路由，用于下载示例文件
@router.get("/download/{filename}", response_class=FileResponse)
async def download_example(filename: str, current_user: User = Depends(download_help)):
    """
    下载示例文件
    """
    try:
        return FileResponse(os.path.join(settings.HELP_DIR, filename))
    except Exception as e:
        logger.error(f"下载示例文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载示例文件失败: {str(e)}")

# 添加一个路由，用于获取示例文件列表
@router.get("/list", response_class=JSONResponse)
async def get_example_list(current_user: User = Depends(get_current_user)):
    """
    获取示例文件列表,返回和/example接口中examples一样的格式
    """
    try:
        files = []
        files = get_file_list(settings.HELP_DIR)

        return JSONResponse(
            {
                "detail": "获取示例文件列表成功",
                "files": files
            }
        )
    except Exception as e:
        logger.error(f"获取示例文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取示例文件列表失败: {str(e)}")
