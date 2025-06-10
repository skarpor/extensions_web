"""
文件管理器
负责文件的上传、下载和管理
"""
import os
import shutil
import hashlib
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, Depends

from new_app.models import File
from new_app.core.config import settings
from new_app.core.logger import get_logger
from new_app.db.session import get_db

logger = get_logger(__name__)

class FileManager:
    def __init__(self, db: AsyncSession=Depends(get_db)):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        sha256_hash = hashlib.sha256()
        with open(str(file_path), "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_safe_filename(self, filename: str) -> str:
        """获取安全的文件名"""
        # 移除不安全的字符
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        return filename

    async def save_file(self, file: UploadFile, owner_id: int, metadata: Optional[Dict[str, Any]] = None) -> Optional[File]:
        """保存上传的文件"""
        try:
            # 生成安全的文件名
            safe_filename = self._get_safe_filename(file.filename)
            
            # 创建用户目录
            user_dir = self.upload_dir / str(owner_id)
            user_dir.mkdir(parents=True, exist_ok=True)

            # 生成唯一的文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = user_dir / f"{timestamp}_{safe_filename}"

            # 保存文件
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # 计算文件大小和哈希值
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)

            # 创建文件记录
            db_file = File(
                filename=safe_filename,
                filepath=str(file_path.relative_to(self.upload_dir)),
                filetype=file.content_type,
                filesize=file_size,
                hash=file_hash,
                metadata=json.dumps(metadata) if metadata else None,
                owner_id=owner_id
            )

            self.db.add(db_file)
            await self.db.commit()
            await self.db.refresh(db_file)

            return db_file

        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            await self.db.rollback()
            return None

    async def get_file(self, file_id: int) -> Optional[File]:
        """获取文件信息"""
        try:
            result = await self.db.execute(
                select(File).where(File.id == file_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取文件失败: {str(e)}")
            return None

    async def delete_file(self, file_id: int) -> bool:
        """删除文件"""
        try:
            file = await self.get_file(file_id)
            if not file:
                return False

            # 删除物理文件
            file_path = self.upload_dir / file.filepath
            if file_path.exists():
                file_path.unlink()

            # 删除数据库记录
            await self.db.delete(file)
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            await self.db.rollback()
            return False

    async def get_user_files(self, user_id: int) -> List[File]:
        """获取用户的所有文件"""
        try:
            result = await self.db.execute(
                select(File).where(File.owner_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取用户文件失败: {str(e)}")
            return []

    def get_file_path(self, file: File) -> Path:
        """获取文件的完整路径"""
        return self.upload_dir / file.filepath

    async def update_file_metadata(self, file_id: int, metadata: Dict[str, Any]) -> Optional[File]:
        """更新文件元数据"""
        try:
            file = await self.get_file(file_id)
            if not file:
                return None

            # 更新元数据
            current_metadata = json.loads(file.metadata) if file.metadata else {}
            current_metadata.update(metadata)
            file.metadata = json.dumps(current_metadata)

            await self.db.commit()
            await self.db.refresh(file)

            return file

        except Exception as e:
            logger.error(f"更新文件元数据失败: {str(e)}")
            await self.db.rollback()
            return None 