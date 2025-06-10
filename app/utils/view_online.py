import os
from fastapi.templating import Jinja2Templates
import markdown
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from app.core.example import get_file_list
from config import TEMPLATE_DIR
from app.core.logger import get_logger
from app.core.auth import get_current_user
from app.models.user import User
templates = Jinja2Templates(directory=TEMPLATE_DIR)

async def view_example(
        request: Request,
    filename: str = Path(..., description="文件名"), 
    file_path: Optional[str] = None,
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
        if file_path:
            filepath = os.path.join(file_path, filename)
        else:
            filepath = filename
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
                "title": os.path.basename(filepath),
                "filename": os.path.basename(filepath),
                "file_type": file_type,
                "content_type": content_type,
                "content": content,
                "modified_time": modified_time_str,
                "nav_active": "example",
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查看文档失败: {str(e)}")
