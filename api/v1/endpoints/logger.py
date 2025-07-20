"""
在线查看日志
仅支持查看日志，不支持修改日志
"""

import asyncio
from datetime import datetime
import io
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import os
from pathlib import Path
from config import settings
import logging
from schemas.user import User
from core.permissions import manage_logs
router = APIRouter()

# 设置日志
logger = logging.getLogger(__name__)

class LogFile(BaseModel):
    name: str
    size: str
    last_modified: datetime

@router.get("/", response_model=List[LogFile])
async def get_logs(current_user: User = Depends(manage_logs)):
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

async def tail_log_file1(filepath: str) -> AsyncGenerator[str, None]:
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


async def tail_log_file(filepath: str) -> AsyncGenerator[str, None]:
    """跟踪日志文件变化并生成内容"""
    try:
        # 发送一个初始消息确认连接已建立
        yield "data: SSE连接已建立\n\n"
        
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
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
                    await asyncio.sleep(1.0)  # 增加等待时间，减少CPU使用
                    f.seek(where)
                else:
                    yield f"data: {line}\n\n"
    except FileNotFoundError:
        yield "event: error\ndata: 日志文件不存在\n\n"
    except UnicodeDecodeError:
        # 尝试使用其他编码
        try:
            with open(filepath, "r", encoding="gbk", errors="replace") as f:
                # 读取内容...
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
                        await asyncio.sleep(1.0)
                        f.seek(where)
                    else:
                        yield f"data: {line}\n\n"
        except Exception as e:
            yield f"event: error\ndata: 读取日志文件失败: {str(e)}\n\n"
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
    lines: Optional[int] = Query(100, gt=0, le=10000, description="获取最后多少行日志"),
    current_user: User = Depends(manage_logs)
):
    """获取日志文件的部分内容"""

    try:
        file_path = validate_log_file(file_name)

        # 尝试多种编码格式
        encodings = ['utf-8', 'gbk', 'latin-1']  # 常见编码尝试顺序

        for encoding in encodings:
            try:
                with open(file_path, "rb") as f:
                    # 高效读取最后N行
                    lines_found: List[str] = []
                    buffer_size = 4096

                    try:
                        f.seek(0, os.SEEK_END)
                        file_size = f.tell()
                        position = f.tell()
                        remaining_lines = lines

                        while position > 0 and remaining_lines > 0:
                            # 计算本次读取的位置和大小
                            chunk_size = min(buffer_size, position)
                            position -= chunk_size
                            f.seek(position)

                            chunk = f.read(chunk_size)
                            decoded_chunk = chunk.decode(encoding, errors='replace')

                            # 分割行并反转顺序
                            chunk_lines = decoded_chunk.splitlines()
                            lines_found = chunk_lines + lines_found

                            # 更新剩余需要读取的行数
                            remaining_lines = lines - len(lines_found)

                        # 获取最后N行
                        result = lines_found[-lines:]
                        return {"content": result}

                    except io.UnsupportedOperation:
                        # 不能seek的情况，直接读取整个文件
                        f.seek(0)
                        content = f.read().decode(encoding, errors='replace')
                        return {"content": content.splitlines()[-lines:]}

                # 如果成功则跳出循环
                break

            except UnicodeDecodeError:
                # 当前编码失败，尝试下一个
                continue

        # 所有编码尝试都失败
        raise HTTPException(
            status_code=500,
            detail="无法解码日志文件，尝试了多种编码格式"
        )

    except Exception as e:
        logger.error(f"获取日志内容失败: {file_name}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{file_name}")
async def stream_logs(file_name: str):
    """SSE流式传输日志内容"""
    try:
        file_path = validate_log_file(file_name)
        # print(file_path)
                # 添加CORS相关头信息
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }

        return StreamingResponse(
            tail_log_file(file_path),
            media_type="text/event-stream",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        # raise
        logger.error(f"SSE流式传输失败: {file_name}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))