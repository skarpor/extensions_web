"""
数据库管理模块

提供SQLite数据库连接和操作功能，用于存储配置和文件元数据。
"""
import os
import sqlite3
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import threading
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError

from app.models.extension import UpdateExtension
from app.models.user import User, UserCreate, UserInDB, UserUpdate
from app.db.models import User

from .logger import get_logger

logger = get_logger("database")

# 线程本地存储，确保每个线程使用独立的数据库连接
_local = threading.local()

class Database:
    """
    数据库管理类
    
    提供SQLite数据库连接和操作，支持配置和文件元数据的存储和检索
    """
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_db()
        logger.info(f"数据库初始化完成。路径: {db_path}")
    
    def _get_connection(self):
        """获取当前线程的数据库连接"""
        if not hasattr(_local, 'connection'):
            _local.connection = sqlite3.connect(self.db_path)
            # 启用外键约束
            _local.connection.execute("PRAGMA foreign_keys = ON")
            # 设置行工厂为字典
            _local.connection.row_factory = sqlite3.Row
        return _local.connection
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nickname TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            email TEXT,
            avatar TEXT,
            last_login TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # 创建聊天室表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_private INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        ''')
        
        # 创建聊天室成员表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_room_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL,
            FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE (room_id, user_id)
        )
        ''')
        
        # 创建聊天消息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            has_image INTEGER NOT NULL DEFAULT 0,
            image_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建系统设置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # 创建扩展配置表,扩展配置表要百分百和json一样
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS extension_configs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            endpoint TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 0,
            config TEXT NOT NULL,
            has_config_form INTEGER NOT NULL DEFAULT 0,
            has_query_form INTEGER NOT NULL DEFAULT 0,
            showinindex INTEGER NOT NULL DEFAULT 0,
            return_type TEXT NOT NULL DEFAULT 'text',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # 创建文件元数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_metadata (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            safe_filename TEXT NOT NULL,
            content_type TEXT,
            path TEXT NOT NULL,
            extension_id TEXT,
            description TEXT,
            created_at TEXT NOT NULL,
            size INTEGER NOT NULL
        )
        ''')
        
        # 创建权限表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            resource TEXT NOT NULL,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (role, resource, action)
        )
        ''')
        
        conn.commit()
        
        # 初始化默认用户
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查是否已存在用户
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            # 如果没有用户，创建默认管理员用户
            if user_count == 0:
                now = self._now_iso()
                # 默认密码: 123
                hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # bcrypt加密的"123"
                
                cursor.execute(
                    """
                    INSERT INTO users (username, password, nickname, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("admin", hashed_password, "管理员", "admin", now, now)
                )
                
                cursor.execute(
                    """
                    INSERT INTO users (username, password, nickname, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("test", hashed_password, "测试用户", "user", now, now)
                )
                
                # 创建默认聊天室
                cursor.execute(
                    """
                    INSERT INTO chat_rooms (name, description, created_by, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("公共聊天室", "所有用户可见的公共聊天室", 1, now, now)
                )
                
                # 将两个用户添加到默认聊天室
                cursor.execute(
                    """
                    INSERT INTO chat_room_members (room_id, user_id, joined_at)
                    VALUES (?, ?, ?)
                    """,
                    (1, 1, now)
                )
                
                cursor.execute(
                    """
                    INSERT INTO chat_room_members (room_id, user_id, joined_at)
                    VALUES (?, ?, ?)
                    """,
                    (1, 2, now)
                )
                
                # 创建默认系统设置
                default_settings = [
                    ("enable_chat", "true", "启用聊天功能"),
                    ("enable_extensions", "true", "启用扩展管理"),
                    ("enable_logs", "true", "启用日志管理"),
                    ("enable_files", "true", "启用文件管理"),
                    ("enable_settings", "true", "启用系统设置")
                ]
                
                for key, value, desc in default_settings:
                    cursor.execute(
                        """
                        INSERT INTO system_settings (setting_key, setting_value, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (key, value, desc, now, now)
                    )
                
                # 创建默认权限
                default_permissions = [
                    ("admin", "*", "*"),  # 管理员可以访问所有资源的所有操作
                    ("user", "chat", "read"),
                    ("user", "chat", "write"),
                    ("user", "files", "read"),
                    ("user", "files", "upload")
                ]
                
                for role, resource, action in default_permissions:
                    cursor.execute(
                        """
                        INSERT INTO permissions (role, resource, action, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (role, resource, action, now, now)
                    )
                
                conn.commit()
                logger.info("已创建默认用户和系统设置")
            
        except Exception as e:
            logger.error(f"初始化默认数据失败: {str(e)}")
    
    def get_extension_config(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        获取扩展配置
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            扩展配置字典，如果不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM extension_configs WHERE id = ?",
            (extension_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # 转换为字典并解析JSON配置
        config = dict(row)
        config['config'] = json.loads(config['config'])
        config['enabled'] = bool(config['enabled'])
        config['has_config_form'] = bool(config['has_config_form'])
        config['has_query_form'] = bool(config['has_query_form'])
        config['showinindex'] = bool(config['showinindex'])
        config['return_type'] = config['return_type']
        return config
    
    def save_extension_config(self, extension_id: str,updateExtension: UpdateExtension) -> bool:
        """
        保存扩展配置
        
        Args:
            extension_id: 扩展ID
            config: 配置字典
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 转换配置为JSON
            config_json = json.dumps(updateExtension.get('config', {}), ensure_ascii=False)
            
            # 检查是否存在
            cursor.execute(
                "SELECT 1 FROM extension_configs WHERE id = ?",
                (extension_id,)
            )
            
            now = updateExtension.get('updated_at') or updateExtension.get('created_at') or self._now_iso()
            
            if cursor.fetchone():
                # 更新
                cursor.execute(
                    """
                    UPDATE extension_configs
                    SET name = ?, description = ?, endpoint = ?, enabled = ?, config = ?, showinindex = ?, return_type = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        updateExtension.get('name'),
                        updateExtension.get('description', '无描述'),
                        updateExtension.get('endpoint'),
                        1 if updateExtension.get('enabled', False) else 0,
                        config_json,
                        1 if updateExtension.get('showinindex', False) else 0,
                        updateExtension.get('return_type', 'text'),
                        now,
                        extension_id
                    )
                )
            else:
                # 插入
                cursor.execute(
                    """
                    INSERT INTO extension_configs
                    (id, name, description, endpoint, enabled, config, has_config_form, has_query_form, showinindex, return_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        extension_id,
                        updateExtension.get('name', extension_id),
                        updateExtension.get('description', '无描述'),
                        updateExtension.get('endpoint'),
                        1 if updateExtension.get('enabled', False) else 0,
                        config_json,
                        1 if updateExtension.get('has_config_form', False) else 0,
                        1 if updateExtension.get('has_query_form', False) else 0,
                        1 if updateExtension.get('showinindex', False) else 0,
                        updateExtension.get('return_type', 'text'),
                        now,
                        now
                    )
                )
            
            conn.commit()
            logger.info(f"保存扩展配置成功: {extension_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存扩展配置失败: {extension_id}, {str(e)}")
            return False
    
    def delete_extension_config(self, extension_id: str) -> bool:
        """
        删除扩展配置
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM extension_configs WHERE id = ?",
                (extension_id,)
            )
            
            conn.commit()
            logger.info(f"数据库 删除扩展配置成功: {extension_id}")
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"数据库 删除扩展配置失败: {extension_id}, {str(e)}")
            return False
    
    def list_extension_configs(self) -> List[Dict[str, Any]]:
        """
        列出所有扩展配置
        
        Returns:
            扩展配置列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM extension_configs ORDER BY updated_at DESC")
        
        configs = []
        for row in cursor.fetchall():
            config = dict(row)
            config['config'] = json.loads(config['config'])
            config['enabled'] = bool(config['enabled'])
            config['has_config_form'] = bool(config['has_config_form'])
            config['has_query_form'] = bool(config['has_query_form'])
            config['showinindex'] = bool(config['showinindex'])
            config['return_type'] = config['return_type']
            config['id'] = config['id']
            config['name'] = config['name']
            config['description'] = config['description']
            config['endpoint'] = config['endpoint']
            config['created_at'] = config['created_at']
            config['updated_at'] = config['updated_at']
            configs.append(config)
        return configs
    
    def save_file_metadata(self, file_meta: Dict[str, Any]) -> bool:
        """
        保存文件元数据
        
        Args:
            file_meta: 文件元数据字典
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查是否存在
            cursor.execute(
                "SELECT 1 FROM file_metadata WHERE id = ?",
                (file_meta['id'],)
            )
            
            if cursor.fetchone():
                # 更新
                cursor.execute(
                    """
                    UPDATE file_metadata
                    SET filename = ?, safe_filename = ?, content_type = ?, path = ?,
                        extension_id = ?, description = ?, size = ?
                    WHERE id = ?
                    """,
                    (
                        file_meta['filename'],
                        file_meta['safe_filename'],
                        file_meta.get('content_type'),
                        file_meta['path'],
                        file_meta.get('extension_id'),
                        file_meta.get('description'),
                        file_meta['size'],
                        file_meta['id']
                    )
                )
            else:
                # 插入
                cursor.execute(
                    """
                    INSERT INTO file_metadata
                    (id, filename, safe_filename, content_type, path, extension_id, description, created_at, size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_meta['id'],
                        file_meta['filename'],
                        file_meta['safe_filename'],
                        file_meta.get('content_type'),
                        file_meta['path'],
                        file_meta.get('extension_id'),
                        file_meta.get('description'),
                        file_meta.get('created_at', self._now_iso()),
                        file_meta['size']
                    )
                )
            
            conn.commit()
            logger.info(f"保存文件元数据成功: {file_meta['id']}")
            return True
            
        except Exception as e:
            logger.error(f"保存文件元数据失败: {file_meta['id']}, {str(e)}")
            return False
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件元数据字典，如果不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM file_metadata WHERE id = ?",
            (file_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return dict(row)
    
    def delete_file_metadata(self, file_id: str) -> bool:
        """
        删除文件元数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM file_metadata WHERE id = ?",
                (file_id,)
            )
            
            conn.commit()
            logger.info(f"删除文件元数据成功: {file_id}")
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"删除文件元数据失败: {file_id}, {str(e)}")
            return False
    
    def list_file_metadata(self, extension_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出文件元数据
        
        Args:
            extension_id: 可选，按扩展ID筛选
            limit: 返回的最大记录数
            offset: 结果起始位置
            
        Returns:
            文件元数据列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if extension_id:
            cursor.execute(
                """
                SELECT * FROM file_metadata 
                WHERE extension_id = ? 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (extension_id, limit, offset)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM file_metadata 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """
        查找超过指定天数的文件元数据
        
        Args:
            days: 文件保留天数
            
        Returns:
            符合条件的文件ID列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 计算截止日期
        cutoff_date = self._days_ago_iso(days)
        
        cursor.execute(
            """
            SELECT id FROM file_metadata
            WHERE created_at < ?
            """,
            (cutoff_date,)
        )
        
        file_ids = [row['id'] for row in cursor.fetchall()]
        return file_ids
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(_local, 'connection'):
            _local.connection.close()
            delattr(_local, 'connection')
    
    def _now_iso(self) -> str:
        """获取当前时间的ISO格式字符串"""
        return datetime.now().isoformat()
    
    def _days_ago_iso(self, days: int) -> str:
        """获取指定天数前的ISO格式字符串"""
        return (datetime.now() - datetime.timedelta(days=days)).isoformat()
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典，如果不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return dict(row)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典，如果不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return dict(row)
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """
        创建新用户
        
        Args:
            user_data: 用户数据字典
            
        Returns:
            新用户的ID，如果创建失败则返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = self._now_iso()
            
            cursor.execute(
                """
                INSERT INTO users (username, password, nickname, role, email, avatar, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_data.get("username"),
                    user_data.get("password"),
                    user_data.get("nickname") or user_data.get("username"),
                    user_data.get("role", "user"),
                    user_data.get("email"),
                    user_data.get("avatar"),
                    now,
                    now
                )
            )
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return None
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 用户数据字典
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 构建更新字段
            update_fields = []
            params = []
            
            for field in ["nickname", "role", "email", "avatar"]:
                if field in user_data and user_data[field] is not None:
                    update_fields.append(f"{field} = ?")
                    params.append(user_data[field])
            
            # 如果有密码，单独处理
            if "password" in user_data and user_data["password"]:
                update_fields.append("password = ?")
                params.append(user_data["password"])
            
            # 添加更新时间
            update_fields.append("updated_at = ?")
            params.append(self._now_iso())
            
            # 添加用户ID
            params.append(user_id)
            
            if update_fields:
                cursor.execute(
                    f"""
                    UPDATE users
                    SET {", ".join(update_fields)}
                    WHERE id = ?
                    """,
                    params
                )
                
                conn.commit()
                return cursor.rowcount > 0
            
            return False
            
        except Exception as e:
            logger.error(f"更新用户失败: {str(e)}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM users WHERE id = ?",
                (user_id,)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return False
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM users
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_user_last_login(self, user_id: int) -> bool:
        """
        更新用户最后登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE users
                SET last_login = ?
                WHERE id = ?
                """,
                (self._now_iso(), user_id)
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新用户最后登录时间失败: {str(e)}")
            return False
    
    # 聊天室相关方法
    def create_chat_room(self, room_data: Dict[str, Any]) -> Optional[int]:
        """
        创建聊天室
        
        Args:
            room_data: 聊天室数据
            
        Returns:
            新聊天室的ID，如果创建失败则返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = self._now_iso()
            
            cursor.execute(
                """
                INSERT INTO chat_rooms (name, description, is_private, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    room_data.get("name"),
                    room_data.get("description"),
                    1 if room_data.get("is_private", False) else 0,
                    room_data.get("created_by"),
                    now,
                    now
                )
            )
            
            room_id = cursor.lastrowid
            
            # 如果创建成功，将创建者添加为成员
            if room_id and room_data.get("created_by"):
                cursor.execute(
                    """
                    INSERT INTO chat_room_members (room_id, user_id, joined_at)
                    VALUES (?, ?, ?)
                    """,
                    (room_id, room_data.get("created_by"), now)
                )
            
            conn.commit()
            return room_id
            
        except Exception as e:
            logger.error(f"创建聊天室失败: {str(e)}")
            return None
    
    def get_chat_room(self, room_id: int) -> Optional[Dict[str, Any]]:
        """
        获取聊天室信息
        
        Args:
            room_id: 聊天室ID
            
        Returns:
            聊天室信息，如果不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT r.*, u.username as creator_username, u.nickname as creator_nickname
            FROM chat_rooms r
            LEFT JOIN users u ON r.created_by = u.id
            WHERE r.id = ?
            """,
            (room_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        room_data = dict(row)
        room_data["is_private"] = bool(room_data["is_private"])
        return room_data
    
    def list_chat_rooms(self, user_id: Optional[int] = None, include_private: bool = False) -> List[Dict[str, Any]]:
        """
        列出聊天室
        
        Args:
            user_id: 用户ID，如果提供，则只返回该用户可见的聊天室
            include_private: 是否包含私有聊天室
            
        Returns:
            聊天室列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if user_id is not None:
            # 返回用户可见的聊天室（公共聊天室 + 用户所在的私有聊天室）
            cursor.execute(
                """
                SELECT r.*, u.username as creator_username, u.nickname as creator_nickname,
                       (SELECT COUNT(*) FROM chat_room_members WHERE room_id = r.id) as member_count
                FROM chat_rooms r
                LEFT JOIN users u ON r.created_by = u.id
                WHERE r.is_private = 0 OR r.id IN (
                    SELECT room_id FROM chat_room_members WHERE user_id = ?
                )
                ORDER BY r.updated_at DESC
                """,
                (user_id,)
            )
        else:
            # 返回所有聊天室或仅公共聊天室
            if include_private:
                cursor.execute(
                    """
                    SELECT r.*, u.username as creator_username, u.nickname as creator_nickname,
                           (SELECT COUNT(*) FROM chat_room_members WHERE room_id = r.id) as member_count
                    FROM chat_rooms r
                    LEFT JOIN users u ON r.created_by = u.id
                    ORDER BY r.updated_at DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT r.*, u.username as creator_username, u.nickname as creator_nickname,
                           (SELECT COUNT(*) FROM chat_room_members WHERE room_id = r.id) as member_count
                    FROM chat_rooms r
                    LEFT JOIN users u ON r.created_by = u.id
                    WHERE r.is_private = 0
                    ORDER BY r.updated_at DESC
                    """
                )
        
        rooms = []
        for row in cursor.fetchall():
            room_data = dict(row)
            room_data["is_private"] = bool(room_data["is_private"])
            rooms.append(room_data)
        
        return rooms
    
    def delete_chat_room(self, room_id: int) -> bool:
        """
        删除聊天室
        
        Args:
            room_id: 聊天室ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 删除聊天室（成员和消息会通过外键约束自动删除）
            cursor.execute(
                "DELETE FROM chat_rooms WHERE id = ?",
                (room_id,)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"删除聊天室失败: {str(e)}")
            return False
    
    # 聊天室成员相关方法
    def add_room_member(self, room_id: int, user_id: int) -> bool:
        """
        添加聊天室成员
        
        Args:
            room_id: 聊天室ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查用户是否已经是成员
            cursor.execute(
                "SELECT 1 FROM chat_room_members WHERE room_id = ? AND user_id = ?",
                (room_id, user_id)
            )
            
            if cursor.fetchone():
                return True  # 用户已经是成员
            
            # 添加成员
            cursor.execute(
                """
                INSERT INTO chat_room_members (room_id, user_id, joined_at)
                VALUES (?, ?, ?)
                """,
                (room_id, user_id, self._now_iso())
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"添加聊天室成员失败: {str(e)}")
            return False
    
    def remove_room_member(self, room_id: int, user_id: int) -> bool:
        """
        移除聊天室成员
        
        Args:
            room_id: 聊天室ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM chat_room_members WHERE room_id = ? AND user_id = ?",
                (room_id, user_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"移除聊天室成员失败: {str(e)}")
            return False
    
    def list_room_members(self, room_id: int) -> List[Dict[str, Any]]:
        """
        列出聊天室成员
        
        Args:
            room_id: 聊天室ID
            
        Returns:
            成员列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT m.*, u.username, u.nickname, u.avatar, u.role
            FROM chat_room_members m
            JOIN users u ON m.user_id = u.id
            WHERE m.room_id = ?
            ORDER BY m.joined_at
            """,
            (room_id,)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def is_room_member(self, room_id: int, user_id: int) -> bool:
        """
        检查用户是否是聊天室成员
        
        Args:
            room_id: 聊天室ID
            user_id: 用户ID
            
        Returns:
            是否是成员
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM chat_room_members WHERE room_id = ? AND user_id = ?",
            (room_id, user_id)
        )
        
        return cursor.fetchone() is not None
    
    # 聊天消息相关方法
    def save_chat_message(self, message_data: Dict[str, Any]) -> Optional[int]:
        """
        保存聊天消息
        
        Args:
            message_data: 消息数据
            
        Returns:
            新消息的ID，如果保存失败则返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO chat_messages (room_id, user_id, message, has_image, image_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message_data.get("room_id"),
                    message_data.get("user_id"),
                    message_data.get("message"),
                    1 if message_data.get("has_image", False) else 0,
                    message_data.get("image_path"),
                    message_data.get("created_at") or self._now_iso()
                )
            )
            
            # 更新聊天室的更新时间
            cursor.execute(
                """
                UPDATE chat_rooms
                SET updated_at = ?
                WHERE id = ?
                """,
                (self._now_iso(), message_data.get("room_id"))
            )
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"保存聊天消息失败: {str(e)}")
            return None
    
    def get_chat_messages(self, room_id: int, limit: int = 50, before_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取聊天消息
        
        Args:
            room_id: 聊天室ID
            limit: 限制数量
            before_id: 获取指定ID之前的消息
            
        Returns:
            消息列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if before_id:
            cursor.execute(
                """
                SELECT m.*, u.username, u.nickname, u.avatar
                FROM chat_messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.room_id = ? AND m.id < ?
                ORDER BY m.id DESC
                LIMIT ?
                """,
                (room_id, before_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT m.*, u.username, u.nickname, u.avatar
                FROM chat_messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.room_id = ?
                ORDER BY m.id DESC
                LIMIT ?
                """,
                (room_id, limit)
            )
        
        messages = []
        for row in cursor.fetchall():
            message = dict(row)
            message["has_image"] = bool(message["has_image"])
            messages.append(message)
        
        # 返回按时间正序排列的消息
        return list(reversed(messages))
    
    # 系统设置相关方法
    def get_system_settings(self) -> Dict[str, str]:
        """
        获取所有系统设置
        
        Returns:
            系统设置字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM system_settings")
        # cursor.execute("SELECT setting_key, setting_value FROM system_settings")

        settings = {}
        for row in cursor.fetchall():
            settings[row["key"]] = row["value"]
        
        return settings
    
    def update_system_setting(self, key: str, value: str) -> bool:
        """
        更新系统设置
        
        Args:
            key: 设置键
            value: 设置值
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = self._now_iso()
            
            # 检查设置是否存在
            cursor.execute(
                "SELECT 1 FROM system_settings WHERE setting_key = ?",
                (key,)
            )
            
            if cursor.fetchone():
                # 更新设置
                cursor.execute(
                    """
                    UPDATE system_settings
                    SET setting_value = ?, updated_at = ?
                    WHERE setting_key = ?
                    """,
                    (value, now, key)
                )
            else:
                # 创建设置
                cursor.execute(
                    """
                    INSERT INTO system_settings (setting_key, setting_value, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, value, now, now)
                )
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新系统设置失败: {str(e)}")
            return False
    
    # 权限相关方法
    def get_permissions_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        获取角色权限
        
        Args:
            role: 角色名
            
        Returns:
            权限列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 获取角色的直接权限
        cursor.execute(
            "SELECT * FROM permissions WHERE role = ?",
            (role,)
        )
        
        permissions = [dict(row) for row in cursor.fetchall()]
        
        # 如果角色是admin，添加通配符权限
        if role == "admin":
            cursor.execute(
                "SELECT * FROM permissions WHERE role = ? AND resource = '*' AND action = '*'",
                ("admin",)
            )
            
            if not cursor.fetchone():
                # 如果没有通配符权限，添加一个
                now = self._now_iso()
                cursor.execute(
                    """
                    INSERT INTO permissions (role, resource, action, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("admin", "*", "*", now, now)
                )
                
                conn.commit()
                
                # 重新获取权限
                cursor.execute(
                    "SELECT * FROM permissions WHERE role = ?",
                    (role,)
                )
                
                permissions = [dict(row) for row in cursor.fetchall()]
        
        return permissions
    
    def check_permission(self, role: str, resource: str, action: str) -> bool:
        """
        检查权限
        
        Args:
            role: 角色名
            resource: 资源名
            action: 操作名
            
        Returns:
            是否有权限
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 检查直接权限
        cursor.execute(
            """
            SELECT 1 FROM permissions 
            WHERE role = ? AND (resource = ? OR resource = '*') AND (action = ? OR action = '*')
            """,
            (role, resource, action)
        )
        
        return cursor.fetchone() is not None
    
    def add_permission(self, role: str, resource: str, action: str) -> bool:
        """
        添加权限
        
        Args:
            role: 角色名
            resource: 资源名
            action: 操作名
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = self._now_iso()
            
            # 检查权限是否已存在
            cursor.execute(
                """
                SELECT 1 FROM permissions 
                WHERE role = ? AND resource = ? AND action = ?
                """,
                (role, resource, action)
            )
            
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO permissions (role, resource, action, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (role, resource, action, now, now)
                )
                
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"添加权限失败: {str(e)}")
            return False
    
    def remove_permission(self, role: str, resource: str, action: str) -> bool:
        """
        移除权限
        
        Args:
            role: 角色名
            resource: 资源名
            action: 操作名
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                DELETE FROM permissions 
                WHERE role = ? AND resource = ? AND action = ?
                """,
                (role, resource, action)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"移除权限失败: {str(e)}")
            return False
    
    # 异步数据库操作方法
    async def get_user(self, db: AsyncSession, user_id: int) -> Optional[UserInDB]:
        """
        通过ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            result = await db.execute(select(User).where(User.c.id == user_id))
            user_row = result.fetchone()
            if not user_row:
                return None
            
            return UserInDB(
                id=user_row.id,
                username=user_row.username,
                hashed_password=user_row.password,
                nickname=user_row.nickname,
                email=user_row.email,
                role=user_row.role,
                avatar=user_row.avatar,
                last_login=user_row.last_login,
                created_at=user_row.created_at,
                updated_at=user_row.updated_at
            )
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def get_user_by_username_db(self, db: AsyncSession, username: str) -> Optional[UserInDB]:
        """
        通过用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            result = await db.execute(select(User).where(User.c.username == username))
            user_row = result.fetchone()
            if not user_row:
                return None
            
            return UserInDB(
                id=user_row.id,
                username=user_row.username,
                hashed_password=user_row.password,
                nickname=user_row.nickname,
                email=user_row.email,
                role=user_row.role,
                avatar=user_row.avatar,
                last_login=user_row.last_login,
                created_at=user_row.created_at,
                updated_at=user_row.updated_at
            )
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def get_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        """
        获取用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            用户对象列表
        """
        from app.db.models import User
        try:
            result = await db.execute(
                select(User)
                .order_by(User.id)
                .offset(skip)
                .limit(limit)
            )
            user_rows = result.scalars().fetchall()
            print(user_rows)
            # for row in user_rows:
            #     print(row[0])
            #
            # # 返回值是错误的，fetchall()返回的是一个元组，而不是一个列表
            # # 需要将元组转换为列表
            # user_rows = [list(row) for row in user_rows]
            # print(user_rows) # row是元组，没有id和其他属性
            #
            
            return [
                UserInDB(
                    id=row.id,
                    username=row.username,
                    # hashed_password=row.password,
                    nickname=row.nickname,
                    email=row.email,
                    role=row.role,
                    # avatar=row.avatar,
                    last_login=row.last_login,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                for row in user_rows
            ]
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return []

    async def create_user_db(self, db: AsyncSession, user: UserCreate) -> UserInDB:
        """
        创建新用户
        
        Args:
            db: 数据库会话
            user: 用户创建对象
            
        Returns:
            创建的用户对象
            
        Raises:
            IntegrityError: 如果用户名已存在
        """
        now = datetime.now().isoformat()
        
        user_values = {
            "username": user.username,
            "password": user.hashed_password,
            "nickname": user.nickname or user.username,
            "email": user.email,
            "role": user.role,
            "created_at": now,
            "updated_at": now
        }
        
        stmt = insert(User).values(**user_values)
        await db.execute(stmt)
        await db.commit()
        
        # 获取创建的用户
        return await self.get_user_by_username_db(db, user.username)

    async def update_user(self, db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[UserInDB]:
        """
        更新用户信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            user_update: 用户更新对象
            
        Returns:
            更新后的用户对象，如果用户不存在则返回None
            
        Raises:
            IntegrityError: 如果更新的用户名已存在
        """
        # 首先检查用户是否存在
        user = await self.get_user(db, user_id)
        if not user:
            return None
        
        # 准备更新数据
        update_data = user_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now().isoformat()
        
        # 如果有哈希密码，需要更新密码字段
        if "hashed_password" in update_data:
            update_data["password"] = update_data.pop("hashed_password")
        
        # 执行更新
        stmt = update(User).where(User.c.id == user_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        
        # 返回更新后的用户
        return await self.get_user(db, user_id)

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            是否成功删除
        """
        stmt = delete(User).where(User.c.id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0

    async def update_last_login(self, db: AsyncSession, user_id: int) -> bool:
        """
        更新用户最后登录时间
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            是否成功更新
        """
        now = datetime.now().isoformat()
        stmt = update(User).where(User.c.id == user_id).values(last_login=now)
        await db.execute(stmt)
        await db.commit()
        
        return True

    async def get_system_settingsxx(self, db: AsyncSession) -> dict:
        """
        获取所有系统设置
        
        Args:
            db: 数据库会话
            
        Returns:
            包含所有系统设置的字典
        """
        from sqlalchemy import select
        from app.db.models import SystemSetting
        
        try:
            result = await db.execute(select(SystemSetting))
            settings_rows = result.fetchall()
            
            settings = {}
            for row in settings_rows:
                settings[row.setting_key] = row.setting_value
            
            return settings
        except Exception as e:
            logger.error(f"获取系统设置失败: {str(e)}")
            return {}
            
    async def get_permissions_by_role(self, db: AsyncSession, role: str) -> list:
        """
        获取指定角色的所有权限
        
        Args:
            db: 数据库会话
            role: 角色名称
            
        Returns:
            权限列表
        """
        from sqlalchemy import select
        from app.db.models import Permission
        
        try:
            result = await db.execute(
                select(Permission).where(Permission.c.role == role)
            )
            permission_rows = result.fetchall()
            
            return [
                {
                    "id": row.id,
                    "role": row.role,
                    "resource": row.resource,
                    "action": row.action,
                    "created_at": row.created_at
                }
                for row in permission_rows
            ]
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            return [] 