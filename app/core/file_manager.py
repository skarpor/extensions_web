"""
文件管理器模块

负责管理用户生成的文件，提供文件存储、获取和管理功能。
"""
import mimetypes
import os
import uuid
import shutil
import datetime
import json
from typing import Dict, List, Optional, Union, BinaryIO
from pathlib import Path

from .logger import get_logger
from .database import Database

logger = get_logger("file_manager")

class FileManager:
    """
    文件管理器类
    
    负责存储和管理用户生成的文件，提供文件存储、获取和列表功能
    """
    
    def __init__(self, files_dir: str, db: Database = None):
        """
        初始化文件管理器
        
        Args:
            files_dir: 文件存储目录
            db: 数据库实例，如果为None则继续使用JSON文件存储
        """
        self.files_dir = files_dir
        self.files_meta_path = os.path.join(files_dir, "files_meta.json")
        self.db = db
        
        # 确保目录存在
        os.makedirs(files_dir, exist_ok=True)
        
        # 加载文件元数据（如果没有数据库实例）
        if not self.db:
            self.files_meta = self._load_meta()
            logger.info(f"文件管理器初始化完成，使用JSON存储。文件目录: {files_dir}")
        else:
            # 如果使用数据库，尝试从JSON迁移数据
            self._migrate_json_to_db()
            logger.info(f"文件管理器初始化完成，使用数据库存储。文件目录: {files_dir}")

    def _load_meta(self) -> Dict:
        """
        加载文件元数据（从JSON文件）
        
        Returns:
            文件元数据字典
        """
        if os.path.exists(self.files_meta_path):
            try:
                with open(self.files_meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载文件元数据失败: {str(e)}")
                return {"files": {}}
        else:
            return {"files": {}}
    
    def _save_meta(self):
        """保存文件元数据到JSON文件（仅在没有数据库时使用）"""
        if self.db:
            return
            
        try:
            with open(self.files_meta_path, "w", encoding="utf-8") as f:
                json.dump(self.files_meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文件元数据失败: {str(e)}")
    
    def _migrate_json_to_db(self):
        """将JSON文件中的元数据迁移到数据库"""
        if not os.path.exists(self.files_meta_path):
            return
            
        try:
            # 加载JSON数据
            with open(self.files_meta_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            
            # 迁移到数据库
            migrated_count = 0
            for file_id, file_meta in json_data.get("files", {}).items():
                if self.db.save_file_metadata(file_meta):
                    migrated_count += 1
            
            if migrated_count > 0:
                logger.info(f"成功将 {migrated_count} 个文件元数据从JSON迁移到数据库")
                
                # 备份JSON文件
                backup_path = f"{self.files_meta_path}.bak"
                shutil.copy2(self.files_meta_path, backup_path)
                logger.info(f"已备份原JSON文件到 {backup_path}")
        except Exception as e:
            logger.error(f"迁移文件元数据到数据库失败: {str(e)}")
    
    def save_file(self, 
                  file_content: Union[bytes, BinaryIO], 
                  filename: str, 
                  content_type: str = None,
                  extension_id: str = None,
                  description: str = None) -> Dict:
        """
        保存文件
        
        Args:
            file_content: 文件内容（二进制数据或文件对象）
            filename: 原始文件名
            content_type: 文件MIME类型
            extension_id: 生成文件的扩展ID
            description: 文件描述
            
        Returns:
            文件元数据字典，包含文件ID、名称、路径等信息
        """
        # 生成唯一文件ID，短一点的

        file_id = str(uuid.uuid4())[:8]
        
        # 如果当前extension_id为空，则使用当前执行的python文件的名称
        if not extension_id:
            extension_id = os.path.basename(__file__).split(".")[0]
        # 确保文件名唯一
        # 使用唯一id+文件后缀名
        # 获取文件后缀名
        file_extension = os.path.splitext(filename)[1]
        safe_filename = f"{file_id}{file_extension}"
        
        # 文件存储路径
        file_path = os.path.join(self.files_dir, safe_filename)
        # print(file_path,safe_filename)
        # 保存文件
        try:
            if isinstance(file_content, bytes):
                with open(file_path, "wb") as f:
                    f.write(file_content)
            else:
                # 如果是文件对象，复制内容
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file_content, f)
            if not content_type:
                # 根据文件后缀名设置content_type
                content_type = mimetypes.guess_type(file_path)[0]

            # 创建文件元数据
            now = datetime.datetime.now().isoformat()
            file_meta = {
                "id": file_id,
                "filename": filename,
                "safe_filename": safe_filename,
                "content_type": content_type,
                "path": file_path,
                "extension_id": extension_id,
                "description": description,
                "created_at": now,
                "size": os.path.getsize(file_path)
            }
            
            # 保存元数据
            if self.db:
                # 使用数据库存储
                self.db.save_file_metadata(file_meta)
            else:
                # 使用JSON文件存储
                self.files_meta["files"][file_id] = file_meta
                self._save_meta()
            
            logger.info(f"文件保存成功: {filename} (ID: {file_id})")
            return file_meta
        
        except Exception as e:
            logger.error(f"保存文件失败: {filename}, {str(e)}")
            raise
    
    def get_file(self, file_id: str) -> Optional[Dict]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件元数据字典，如果文件不存在则返回None
        """
        if self.db:
            # 从数据库获取
            file_meta = self.db.get_file_metadata(file_id)
        else:
            # 从JSON获取
            file_meta = self.files_meta["files"].get(file_id)
            
        if file_meta and os.path.exists(file_meta["path"]):
            return file_meta
        return None
    
    def get_file_content(self, file_id: str) -> Optional[bytes]:
        """
        获取文件内容
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件二进制内容，如果文件不存在则返回None
        """
        file_meta = self.get_file(file_id)
        if file_meta:
            try:
                with open(file_meta["path"], "rb") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"读取文件内容失败: {file_id}, {str(e)}")
        return None
    
    def list_files(self, 
                   extension_id: str = None, 
                   limit: int = 100, 
                   offset: int = 0) -> List[Dict]:
        """
        列出文件
        
        Args:
            extension_id: 可选，按扩展ID筛选
            limit: 返回的最大文件数
            offset: 结果起始位置
            
        Returns:
            文件元数据列表
        """
        if self.db:
            # 从数据库获取
            files = self.db.list_file_metadata(extension_id, limit, offset)
        else:
            # 从JSON获取
            files = list(self.files_meta["files"].values())
            
            # 按扩展ID过滤
            if extension_id:
                files = [f for f in files if f.get("extension_id") == extension_id]
            
            # 按创建时间排序（新的在前）
            files.sort(key=lambda x: x["created_at"], reverse=True)
            
            # 应用分页
            files = files[offset:offset+limit]
        
        # 检查文件是否存在
        return [f for f in files if os.path.exists(f["path"])]
    
    def delete_file(self, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            删除是否成功
        """
        # 获取文件元数据
        if self.db:
            file_meta = self.db.get_file_metadata(file_id)
        else:
            file_meta = self.files_meta["files"].get(file_id)
            
        if not file_meta:
            return False
        
        try:
            # 删除文件
            if os.path.exists(file_meta["path"]):
                os.remove(file_meta["path"])
            
            # 更新元数据
            if self.db:
                self.db.delete_file_metadata(file_id)
            else:
                del self.files_meta["files"][file_id]
                self._save_meta()
            
            logger.info(f"文件删除成功: {file_meta['filename']} (ID: {file_id})")
            return True
        
        except Exception as e:
            logger.error(f"删除文件失败: {file_id}, {str(e)}")
            return False
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """
        清理旧文件
        
        Args:
            days: 文件保留天数，超过此天数的文件将被删除
            
        Returns:
            清理的文件数量
        """
        count = 0
        
        if self.db:
            # 使用数据库查找旧文件
            file_ids = self.db.cleanup_old_files(days)
            
            # 删除文件
            for file_id in file_ids:
                if self.delete_file(file_id):
                    count += 1
        else:
            # 使用JSON数据
            now = datetime.datetime.now()
            
            for file_id, file_meta in list(self.files_meta["files"].items()):
                try:
                    created_at = datetime.datetime.fromisoformat(file_meta["created_at"])
                    age = now - created_at
                    
                    if age.days > days:
                        if self.delete_file(file_id):
                            count += 1
                except Exception as e:
                    logger.error(f"处理文件时出错: {file_id}, {str(e)}")
        
        logger.info(f"清理了 {count} 个超过 {days} 天的文件")
        return count 