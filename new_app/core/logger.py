"""
日志管理器
提供统一的日志记录功能
"""
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from new_app.models import Log
from new_app.core.config import settings

# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 配置文件日志
file_handler = logging.FileHandler(settings.LOG_FILE)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

# 配置控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 避免重复添加处理器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

class DatabaseLogger:
    """数据库日志记录器"""
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = get_logger(__name__)

    async def log(
        self,
        level: str,
        message: str,
        module: Optional[str] = None,
        function: Optional[str] = None,
        line: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Optional[Log]:
        """记录日志到数据库"""
        try:
            # 获取调用栈信息
            if not module or not function or not line:
                stack = traceback.extract_stack()
                caller = stack[-2]  # -1 是当前函数，-2 是调用者
                module = module or caller.filename
                function = function or caller.name
                line = line or caller.lineno

            # 创建日志记录
            log = Log(
                level=level,
                message=message,
                module=module,
                function=function,
                line=line,
                user_id=user_id,
                created_at=datetime.utcnow()
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            # 同时记录到文件
            self.logger.log(
                getattr(logging, level),
                f"[{module}:{function}:{line}] {message}"
            )

            return log

        except Exception as e:
            self.logger.error(f"记录数据库日志失败: {str(e)}")
            await self.db.rollback()
            return None

    async def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        return await self.log("INFO", message, **kwargs)

    async def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        return await self.log("WARNING", message, **kwargs)

    async def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        return await self.log("ERROR", message, **kwargs)

    async def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        return await self.log("DEBUG", message, **kwargs)

    async def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        return await self.log("CRITICAL", message, **kwargs) 