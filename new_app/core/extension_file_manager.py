"""
扩展程序文件管理器

负责管理扩展程序产生或依赖的文件数据。
"""
import os
import shutil
from typing import Dict, Optional, List, BinaryIO
from datetime import datetime
import hashlib
from pathlib import Path

from fastapi import UploadFile
from new_app.core.logger import get_logger

logger = get_logger("extension_file_manager")

class ExtensionFileManager:
    """扩展程序文件管理器"""
    
    def __init__(self, base_dir: str):
        """初始化扩展程序文件管理器
        
        Args:
            base_dir: 基础目录路径
        """
        self.base_dir = base_dir
        self._ensure_dirs()
        logger.info(f"扩展程序文件管理器初始化完成，基础目录：{base_dir}")
    
    def _ensure_dirs(self):
        """确保必要的目录存在"""
        os.makedirs(self.base_dir, exist_ok=True)
        
    def _get_extension_dir(self, extension_id: str) -> str:
        """获取扩展程序的文件目录
        
        Args:
            extension_id: 扩展程序ID
            
        Returns:
            扩展程序文件目录路径
        """
        ext_dir = os.path.join(self.base_dir, extension_id)
        os.makedirs(ext_dir, exist_ok=True)
        return ext_dir
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件哈希值
        
        Args:
            file_content: 文件内容
            
        Returns:
            文件的SHA256哈希值
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def _get_safe_filename(self, filename: str) -> str:
        """获取安全的文件名
        
        Args:
            filename: 原始文件名
            
        Returns:
            安全的文件名
        """
        # 移除不安全的字符
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        return filename
    
    async def save_file(self, extension_id: str, file: UploadFile, description: Optional[str] = None) -> Dict:
        """保存文件
        
        Args:
            extension_id: 扩展程序ID
            file: 上传的文件
            description: 文件描述
            
        Returns:
            文件信息字典
        """
        try:
            content = await file.read()
            await file.seek(0)
            
            # 获取安全的文件名
            safe_filename = self._get_safe_filename(file.filename)
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(content)
            
            # 构建文件路径
            ext_dir = self._get_extension_dir(extension_id)
            file_path = os.path.join(ext_dir, safe_filename)
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(content)
            
            # 返回文件信息
            file_info = {
                "filename": safe_filename,
                "original_filename": file.filename,
                "content_type": file.content_type,
                "hash": file_hash,
                "size": len(content),
                "path": file_path,
                "description": description,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"扩展程序 {extension_id} 保存文件成功：{safe_filename}")
            return file_info
            
        except Exception as e:
            logger.error(f"扩展程序 {extension_id} 保存文件失败：{str(e)}")
            raise
    
    def get_file(self, extension_id: str, filename: str) -> Optional[str]:
        """获取文件路径
        
        Args:
            extension_id: 扩展程序ID
            filename: 文件名
            
        Returns:
            文件完整路径，如果文件不存在则返回None
        """
        ext_dir = self._get_extension_dir(extension_id)
        file_path = os.path.join(ext_dir, filename)
        return file_path if os.path.exists(file_path) else None
    
    def delete_file(self, extension_id: str, filename: str) -> bool:
        """删除文件
        
        Args:
            extension_id: 扩展程序ID
            filename: 文件名
            
        Returns:
            是否删除成功
        """
        try:
            file_path = self.get_file(extension_id, filename)
            if file_path:
                os.remove(file_path)
                logger.info(f"扩展程序 {extension_id} 删除文件成功：{filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"扩展程序 {extension_id} 删除文件失败：{str(e)}")
            return False
    
    def list_files(self, extension_id: str) -> List[Dict]:
        """列出扩展程序的所有文件
        
        Args:
            extension_id: 扩展程序ID
            
        Returns:
            文件信息列表
        """
        try:
            ext_dir = self._get_extension_dir(extension_id)
            files = []
            
            for filename in os.listdir(ext_dir):
                file_path = os.path.join(ext_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return files
        except Exception as e:
            logger.error(f"扩展程序 {extension_id} 列出文件失败：{str(e)}")
            return []
    
    def clean_files(self, extension_id: str):
        """清理扩展程序的所有文件
        
        Args:
            extension_id: 扩展程序ID
        """
        try:
            ext_dir = self._get_extension_dir(extension_id)
            if os.path.exists(ext_dir):
                shutil.rmtree(ext_dir)
            logger.info(f"扩展程序 {extension_id} 清理文件成功")
        except Exception as e:
            logger.error(f"扩展程序 {extension_id} 清理文件失败：{str(e)}")
            raise 