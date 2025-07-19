"""
Markdown文件管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import os
import aiofiles
from pathlib import Path
import logging

from db.session import get_db
from core.auth import get_current_user
from models.user import User as DBUser
from core.config_manager import ConfigManager
from config import settings
logger = logging.getLogger(__name__)
router = APIRouter()

class MarkdownContent(BaseModel):
    content: str
    file_path: Optional[str] = None

class LoadFileRequest(BaseModel):
    file_path: str

class CreateFileRequest(BaseModel):
    file_name: str
    template: str = "blank"

class FilePathRequest(BaseModel):
    file_path: str

# 文档模板
TEMPLATES = {
    "blank": "",
    "readme": """# 项目名称

## 简介
项目简介...

## 安装
```bash
# 安装命令
```

## 使用方法
使用说明...

## 贡献
贡献指南...

## 许可证
许可证信息...
""",
    "api": """# API 文档

## 概述
API概述...

## 认证
认证方式...

## 端点

### GET /api/example
描述...

**参数:**
- `param1` (string): 参数描述

**响应:**
```json
{
  "status": "success",
  "data": {}
}
```

## 错误码
| 错误码 | 描述 |
|--------|------|
| 400    | 请求错误 |
| 401    | 未授权 |
| 500    | 服务器错误 |
""",
    "project": """# 项目文档

## 项目概述
项目概述...

## 技术栈
- 前端: Vue.js
- 后端: FastAPI
- 数据库: SQLite

## 项目结构
```
project/
├── api/          # 后端API
├── fr/           # 前端代码
├── models/       # 数据模型
└── README.md     # 项目说明
```

## 开发指南
开发指南...

## 部署说明
部署说明...
"""
}

def get_markdown_folder_path() -> str:
    """获取配置的Markdown文件夹路径"""
    try:
        return settings.MARKDOWN_FOLDER_PATH
    except Exception as e:
        raise
        logger.warning(f"获取Markdown文件夹路径失败: {e}")
        return "data/docs"

def ensure_file_directory(file_path: str):
    """确保文件目录存在"""
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

@router.post("/load")
async def load_markdown_file(
    request: LoadFileRequest,
    current_user: DBUser = Depends(get_current_user)
):
    """加载指定Markdown文件内容"""
    try:
        file_path = request.file_path

        # 安全检查：确保文件路径在允许的目录内
        abs_file_path = os.path.abspath(file_path)
        project_root = os.path.abspath(".")

        if not abs_file_path.startswith(project_root):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件路径不在允许的目录内"
            )

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )

        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()

        logger.info(f"加载Markdown文件: {file_path}")

        return {
            "content": content,
            "file_path": file_path,
            "message": "文件加载成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载Markdown文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"加载文件失败: {str(e)}"
        )

@router.post("/save")
async def save_markdown_file(
    request: MarkdownContent,
    current_user: DBUser = Depends(get_current_user)
):
    """保存Markdown文件内容"""
    try:
        file_path = request.file_path

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件路径不能为空"
            )
        
        # 安全检查：确保文件路径在允许的目录内
        abs_file_path = os.path.abspath(file_path)
        project_root = os.path.abspath(".")
        
        if not abs_file_path.startswith(project_root):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件路径不在允许的目录内"
            )
        
        ensure_file_directory(file_path)
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(request.content)
        
        logger.info(f"保存Markdown文件: {file_path}")
        
        return {
            "message": "文件保存成功",
            "file_path": file_path,
            "content_length": len(request.content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存Markdown文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败: {str(e)}"
        )

@router.post("/create")
async def create_markdown_file(
    request: CreateFileRequest,
    current_user: DBUser = Depends(get_current_user)
):
    """在配置的文件夹中创建新的Markdown文件"""
    try:
        folder_path = get_markdown_folder_path()
        file_name = request.file_name

        # 确保文件名以.md结尾
        if not file_name.endswith('.md'):
            file_name += '.md'

        file_path = os.path.join(folder_path, file_name)

        # 安全检查
        abs_file_path = os.path.abspath(file_path)
        project_root = os.path.abspath(".")

        if not abs_file_path.startswith(project_root):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件路径不在允许的目录内"
            )

        # 检查文件是否已存在
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件已存在"
            )

        # 获取模板内容
        template_content = TEMPLATES.get(request.template, TEMPLATES["blank"])

        ensure_file_directory(file_path)

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(template_content)

        logger.info(f"创建Markdown文件: {file_path}, 模板: {request.template}")

        return {
            "message": "文件创建成功",
            "file_path": file_path,
            "file_name": file_name,
            "template": request.template,
            "content": template_content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建Markdown文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建文件失败: {str(e)}"
        )

@router.delete("/delete")
async def delete_markdown_file(
    request: FilePathRequest,
    current_user: DBUser = Depends(get_current_user)
):
    """删除Markdown文件"""
    try:
        file_path = request.file_path
        
        # 安全检查
        abs_file_path = os.path.abspath(file_path)
        project_root = os.path.abspath(".")
        
        if not abs_file_path.startswith(project_root):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件路径不在允许的目录内"
            )
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        os.remove(file_path)
        
        logger.info(f"删除Markdown文件: {file_path}")
        
        return {
            "message": "文件删除成功",
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Markdown文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}"
        )

@router.get("/list")
async def list_markdown_files(
    current_user: DBUser = Depends(get_current_user)
):
    """列出配置文件夹中的Markdown文件"""
    try:
        folder_path = get_markdown_folder_path()
        markdown_files = []

        # 确保文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"创建Markdown文件夹: {folder_path}")

        # 遍历文件夹中的所有.md文件
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.md', '.markdown')):
                    file_path = os.path.join(root, file)
                    try:
                        file_stat = os.stat(file_path)
                        # 计算相对于文件夹的路径
                        rel_path = os.path.relpath(file_path, folder_path)
                        markdown_files.append({
                            "path": file_path,
                            "name": file,
                            "relative_path": rel_path,
                            "size": file_stat.st_size,
                            "modified": file_stat.st_mtime
                        })
                    except OSError:
                        continue

        # 按文件名排序
        markdown_files.sort(key=lambda x: x["name"])

        return {
            "files": markdown_files,
            "folder_path": folder_path,
            "total_files": len(markdown_files)
        }

    except Exception as e:
        logger.error(f"列出Markdown文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出文件失败: {str(e)}"
        )


