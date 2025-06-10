"""
示例和文档API路由

提供示例文件和文档的展示功能，包括示例列表和文档内容查看。
"""
import os
from fastapi.templating import Jinja2Templates
import markdown
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Path, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from app.core.example import get_file_list
from config import TEMPLATE_DIR
from app.core.logger import get_logger
from app.core.auth import get_current_user
from app.models.user import User
from config import EXAMPLE_DIR
logger = get_logger("example_routes")
router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)



@router.get("/example", response_class=HTMLResponse)
async def example_list(request: Request):
    """
    获取示例和文档文件列表
    
    Args:
        request: HTTP请求
        current_user: 当前登录用户
        
    Returns:
        HTML响应
    """
    try:
        examples = []
        if not os.path.exists(EXAMPLE_DIR):
            os.makedirs(EXAMPLE_DIR, exist_ok=True)
            logger.info(f"创建示例目录: {EXAMPLE_DIR}")
        
        examples = get_file_list(EXAMPLE_DIR)

        return templates.TemplateResponse(
            "example_list.html", 
            {
                "request": request, 
                "title": "示例和文档", 
                "examples": examples,
                "nav_active": "example",
                # "user": current_user
            }
        )
    except Exception as e:
        logger.error(f"获取示例列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取示例列表失败: {str(e)}")


@router.get("/example/view/{filename}", response_class=HTMLResponse)
async def view_example(
    request: Request, 
    filename: str = Path(..., description="文件名"), 
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
        filepath = os.path.join(EXAMPLE_DIR, filename)
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
            
        # 读取文件内容
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='gbk') as f:
                content = f.read()

        # 根据内容类型处理
        if content_type == "markdown":
            # 将Markdown转换为HTML
            content = markdown.markdown(
                content, 
                extensions=['extra', 'codehilite', 'tables', 'fenced_code']
            )
        
        return templates.TemplateResponse(
            "view_example.html", 
            {
                "request": request, 
                "title": filename,
                "filename": filename,
                "file_type": file_type,
                "content_type": content_type,
                "content": content,
                "modified_time": modified_time_str,
                "nav_active": "example",
                # "user": current_user,
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"查看文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查看文档失败: {str(e)}")
    
# 添加一个路由，用于上传示例文件
@router.post("/example/upload", response_class=JSONResponse)
async def upload_example(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_user)):
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
            if os.path.exists(os.path.join(EXAMPLE_DIR, file.filename)):
                failed_files.append(file.filename)
                continue
            # 保存文件到示例目录
            save_path = os.path.join(EXAMPLE_DIR, file.filename)
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
@router.post("/example/delete", response_class=JSONResponse)
async def delete_example(filename: Dict, current_user: User = Depends(get_current_user)):
    """
    删除示例文件
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限删除示例文件")
    try:
        os.remove(os.path.join(EXAMPLE_DIR, filename['filename']))
        return JSONResponse(
            {
                "detail": "删除成功",
                "filename": filename['filename']
            }
        )
    except Exception as e:
        logger.error(f"删除示例文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除示例文件失败: {str(e)}")

# 添加一个路由，用于下载示例文件
@router.get("/example/download/{filename}", response_class=FileResponse)
async def download_example(filename: str, current_user: User = Depends(get_current_user)):
    """
    下载示例文件
    """
    try:
        return FileResponse(os.path.join(EXAMPLE_DIR, filename))
    except Exception as e:
        logger.error(f"下载示例文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载示例文件失败: {str(e)}")

# 添加一个路由，用于获取示例文件列表
@router.get("/example/list", response_class=JSONResponse)
async def get_example_list():
    """
    获取示例文件列表,返回和/example接口中examples一样的格式
    """
    try:
        files = []
        files = get_file_list(EXAMPLE_DIR)

        return JSONResponse(
            {
                "detail": "获取示例文件列表成功",
                "files": files
            }
        )
    except Exception as e:
        logger.error(f"获取示例文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取示例文件列表失败: {str(e)}")
