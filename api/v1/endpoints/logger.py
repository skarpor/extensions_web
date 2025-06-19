"""
在线查看日志
仅支持查看日志，不支持修改日志
"""

import asyncio
from datetime import datetime
import io
import time
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import os
from pathlib import Path
from config import settings
import logging

router = APIRouter()

# 设置日志
logger = logging.getLogger(__name__)

class LogFile(BaseModel):
    name: str
    size: str
    last_modified: datetime

@router.get("/", response_model=List[LogFile])
async def get_logs():
    """获取日志文件列表及基本信息"""
    try:
        files = []
        for filename in os.listdir(settings.LOG_DIR):
            filepath = os.path.join(settings.LOG_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                size = stat.st_size
                # 格式化文件大小
                size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"
                files.append(LogFile(
                    name=filename,
                    size=size_str,
                    last_modified=datetime.fromtimestamp(stat.st_mtime)
                ))
        return sorted(files, key=lambda x: x.last_modified, reverse=True)
    except Exception as e:
        logger.error(f"获取日志列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="无法获取日志列表")

async def tail_log_file(filepath: str) -> AsyncGenerator[str, None]:
    """跟踪日志文件变化并生成内容"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            # 先读取已有内容
            while True:
                line = f.readline()
                if not line:
                    break
                yield f"data: {line}\n\n"
            
            # 然后跟踪新内容
            while True:
                where = f.tell()
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    f.seek(where)
                else:
                    yield f"data: {line}\n\n"
    except FileNotFoundError:
        yield "event: error\ndata: 日志文件不存在\n\n"
    except Exception as e:
        yield f"event: error\ndata: {str(e)}\n\n"

def validate_log_file(file_name: str) -> str:
    """验证日志文件名并返回完整路径"""
    try:
        # 防止目录遍历攻击
        file_path = Path(settings.LOG_DIR) / file_name
        file_path = file_path.resolve()
        
        # 验证路径是否在允许的目录内
        if not file_path.is_relative_to(Path(settings.LOG_DIR).resolve()):
            raise ValueError("非法文件路径")
            
        if not file_path.exists():
            raise FileNotFoundError("文件不存在")
            
        if not file_path.is_file():
            raise ValueError("不是有效的文件")
            
        return str(file_path)
    except Exception as e:
        logger.error(f"日志文件验证失败: {file_name}, 错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{file_name}")
async def get_log_content(
    file_name: str,
    lines: Optional[int] = Query(100, gt=0, le=10000, description="获取最后多少行日志")
):
    """获取日志文件的部分内容"""
    try:
        file_path = validate_log_file(file_name)
        
        # 读取文件最后N行
        with open(file_path, "rb") as f:  # 使用二进制模式
            # 高效读取最后N行
            lines_found = []
            buffer = 4096
            
            try:
                # 尝试seek到文件末尾
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                
                block = -1
                while len(lines_found) < lines and abs(block * buffer) < file_size:
                    try:
                        f.seek(block * buffer, os.SEEK_END)
                    except io.UnsupportedOperation:
                        # 如果seek失败，回退到直接读取整个文件
                        f.seek(0)
                        lines_found = f.read().decode('utf-8').splitlines()
                        break
                        
                    data = f.read(buffer).decode('utf-8')
                    lines_found = data.splitlines() + lines_found
                    block -= 1
                
                result = lines_found[-lines:]
            except io.UnsupportedOperation:
                # 完全不能seek的情况，读取整个文件
                f.seek(0)
                lines_found = f.read().decode('utf-8').splitlines()
                result = lines_found[-lines:]
        
        return {"content": result}
    except Exception as e:
        logger.error(f"获取日志内容失败: {file_name}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/stream/{file_name}")
async def stream_logs(file_name: str):
    """SSE流式传输日志内容"""
    try:
        file_path = validate_log_file(file_name)
        
        return StreamingResponse(
            tail_log_file(file_path),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSE流式传输失败: {file_name}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))