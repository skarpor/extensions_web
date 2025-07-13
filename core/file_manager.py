"""
文件管理器
负责文件的上传、下载和管理
"""
from __future__ import annotations
import os
import shutil
import hashlib
import json
from typing import Optional, Dict, Any, List, Union, Sequence
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from fastapi import UploadFile, Depends, HTTPException,status

from models import File
from config import settings
from core.logger import get_logger
from db.session import get_db

logger = get_logger(__name__)

class FileManager:
    def __init__(self, db: AsyncSession=Depends(get_db)):
        self.db = db
        self.upload_dir = settings.FILE_UPLOAD_DIR + "/"
        # self.upload_dir.mkdir(parents=True, exist_ok=True)

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

    
    def _generate_safe_filename(self, filename: str) -> str:
        """生成安全的文件名"""
        # 提取文件扩展名
        ext = "".join(Path(filename).suffixes)
        # 生成随机文件名部分
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_str = hashlib.md5(filename.encode()).hexdigest()[:8]
        # 清理基本名称
        base_name = Path(filename).stem
        safe_base = "".join(c for c in base_name if c.isalnum() or c in "._- ")
        return f"{timestamp}_{random_str}_{safe_base}{ext}"

    async def save_file(
            self,
            file: UploadFile,
            owner_id: int,
            path: str = "/",  # 默认根目录
            # metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[File]:
        """保存上传的文件"""
        try:
            # 确保上传目录是绝对路径
            upload_dir = os.path.abspath(settings.FILE_UPLOAD_DIR)
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            # 规范化路径
            # safe_path = self._normalize_path(path)
            target_dir = os.path.abspath(upload_dir+path)
            # 路径安全验证
            if not self.is_vaild_path(target_dir):
                raise HTTPException(status_code=400, detail="非法路径")
            # try:
            #     target_dir.relative_to(upload_dir)
            # except ValueError:
            #     logger.error(f"非法路径: {target_dir} 不在 {upload_dir} 下")
            #     raise ValueError("非法路径")

            # 创建目录（如果不存在）
            os.makedirs(target_dir, exist_ok=True)

            # 生成安全文件名
            safe_filename = self._generate_safe_filename(file.filename)
            file_path = os.path.abspath(os.path.join(target_dir, safe_filename))
            print(file_path,'file_path')
            # 保存文件
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # 计算文件哈希值
            file_hash = self._calculate_file_hash(file_path)
            print(file_hash,'创建文件记录')
            # 创建文件记录
            db_file = File(
                filename=safe_filename,
                filepath=str(target_dir[len(upload_dir):]).replace("\\","/") + "/",
                filetype=file.content_type,
                filesize=os.path.getsize(file_path),
                hash=file_hash,
                # filemeta=json.dumps(metadata) if metadata else None,
                owner_id=owner_id,
                path=str(path)
            )

            self.db.add(db_file)
            await self.db.commit()
            await self.db.refresh(db_file)

            return db_file

        except HTTPException:
            raise
        except Exception as e:
            
            logger.error(f"保存文件失败: {str(e)}", exc_info=True)
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文件上传失败"
            )
    async def get_file(self, file_id: int,path: str) -> Optional[File]:
        """获取文件信息"""
        try:
            result = await self.db.execute(
                select(File).where(File.id == file_id,File.filepath.startswith(path))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取文件失败: {str(e)}")
            return None

    async def delete_file(self, file_id: int,path: str) -> bool:
        """删除文件"""
        try:
            file = await self.get_file(file_id,path)
            if not file:
                return False

            # 删除物理文件
            file_path = self.upload_dir + file.filepath + "/" + file.filename
            if os.path.exists(file_path):
                os.remove(file_path)

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

    def get_file_path(self, file: str,path: str) -> str:
        """获取文件的完整路径"""

        return os.path.abspath(self.upload_dir + path + file)

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
    # 获取用户文件列表
    async def get_file_list(self, user_id: int, path: str) -> List[File]:
        """获取用户文件列表"""
        try:
            result = await self.db.execute(
                select(File).where(File.owner_id == user_id, File.filepath.startswith(path))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取用户文件列表失败: {str(e)}")
            return []
    # 获取目录下所有文件
    async def get_dir_files(self,  path: str) -> Union[list[Any], Sequence[File]]: # -> Union[list[Any], Sequence[File]]
        """获取目录下所有文件"""
        try:
            # 如果没有/结尾，则添加/
            if not path.endswith("/"):
                path += "/"
            result = await self.db.execute(
                select(File).where(File.filepath == path)
            )
            # print(result.fetchall())
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取目录下所有文件失败: {str(e)}")
            return []
    def is_vaild_path(self, path: str) -> bool:
        return path.startswith(os.path.abspath(self.upload_dir))

    # 创建目录,可能为多级
    async def create_dir(self, path: str,owner_id: int,name: str) -> bool:
        """创建目录"""
        try:
            target_dir = os.path.abspath(self.upload_dir + "/" + path + "/" + name)
            if not self.is_vaild_path(target_dir):
                raise HTTPException(status_code=400, detail="非法路径")
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            else:
                raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED,detail="目录已存在")
            # 保存到数据库中,多级目录需要递归保存
            path_list = name.split("/")
            i_path = path
            for i in path_list:
                if i == "":
                    continue
                db_dir = File(
                    filename=i,
                    filepath=i_path,
                    filetype="directory",
                    filesize=0,
                    hash="",
                    owner_id=owner_id,
                    path=i_path+i+"/"
                )
                i_path+=i+"/"
                self.db.add(db_dir)
            await self.db.commit()
            await self.db.refresh(db_dir)
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}", exc_info=True)
            await self.db.rollback()
            return False

    # 删除目录
    async def delete_dir(self,db: AsyncSession, path: str) -> bool:
        """删除目录"""
        try:
            # 删除目录
            target_dir = os.path.abspath(self.upload_dir + "/" + path)
            # if not os.path.exists(target_dir):
            #     return False
            try:
                shutil.rmtree(target_dir)
            except FileNotFoundError:
                pass

            # 删除数据库记录,递归删除
            if not path.endswith("/"):
                path += "/"
            # 正确方式：先构建查询，再执行删除
            stmt = delete(File).where(File.filepath.startswith(path))
            await db.execute(stmt)
            stmt = delete(File).where(File.path==path and File.filetype=="directory")
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:

            logger.error(f"删除目录失败: {str(e)}", exc_info=True)
            return False

