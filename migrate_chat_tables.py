#!/usr/bin/env python3
"""
聊天室数据库迁移脚本
"""

import asyncio
import sqlite3
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from config import settings
from core.logger import get_logger

logger = get_logger(__name__)

async def migrate_chat_tables():
    """迁移聊天室相关表结构"""
    
    print("🚀 开始迁移聊天室数据库表结构...\n")
    
    # 创建异步引擎
    engine = create_async_engine(
        settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///"),
        echo=False
    )
    
    async with engine.begin() as conn:
        try:
            # 1. 检查现有表结构
            print("🔄 检查现有表结构...")
            
            # 检查chat_rooms表是否存在
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_rooms'"
            ))
            chat_rooms_exists = result.fetchone() is not None
            
            if chat_rooms_exists:
                print("✅ 发现现有chat_rooms表")
                
                # 获取现有表结构
                result = await conn.execute(text("PRAGMA table_info(chat_rooms)"))
                existing_columns = {row[1] for row in result.fetchall()}
                print(f"   现有字段: {', '.join(sorted(existing_columns))}")
                
                # 需要添加的新字段
                new_columns = {
                    'room_type': 'TEXT DEFAULT "group"',
                    'avatar': 'TEXT',
                    'allow_member_invite': 'BOOLEAN DEFAULT 1',
                    'allow_member_modify_info': 'BOOLEAN DEFAULT 0',
                    'message_history_visible': 'BOOLEAN DEFAULT 1',
                    'last_message_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
                }
                
                # 添加缺失的字段
                for column_name, column_def in new_columns.items():
                    if column_name not in existing_columns:
                        print(f"🔄 添加字段: {column_name}")
                        await conn.execute(text(f"ALTER TABLE chat_rooms ADD COLUMN {column_name} {column_def}"))
                        print(f"✅ 字段 {column_name} 添加成功")
                
                # 重命名is_private为is_public（需要特殊处理）
                if 'is_private' in existing_columns and 'is_public' not in existing_columns:
                    print("🔄 转换is_private字段为is_public...")
                    await conn.execute(text("ALTER TABLE chat_rooms ADD COLUMN is_public BOOLEAN DEFAULT 1"))
                    await conn.execute(text("UPDATE chat_rooms SET is_public = NOT is_private"))
                    print("✅ is_public字段转换完成")
            
            else:
                print("⚠️ chat_rooms表不存在，将创建新表")
                
                # 创建新的chat_rooms表
                create_chat_rooms_sql = """
                CREATE TABLE chat_rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    room_type TEXT DEFAULT 'group',
                    avatar VARCHAR(255),
                    is_public BOOLEAN DEFAULT 1,
                    max_members INTEGER DEFAULT 500,
                    created_by INTEGER,
                    last_message_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    allow_member_invite BOOLEAN DEFAULT 1,
                    allow_member_modify_info BOOLEAN DEFAULT 0,
                    message_history_visible BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
                """
                await conn.execute(text(create_chat_rooms_sql))
                print("✅ chat_rooms表创建成功")
            
            # 2. 创建新的聊天室成员关联表
            print("\n🔄 处理聊天室成员关联表...")
            
            # 检查新的关联表是否存在
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_room_members_new'"
            ))
            new_members_table_exists = result.fetchone() is not None
            
            if not new_members_table_exists:
                # 创建新的成员关联表
                create_members_sql = """
                CREATE TABLE chat_room_members_new (
                    room_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role VARCHAR(20) DEFAULT 'member',
                    is_muted BOOLEAN DEFAULT 0,
                    last_read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    nickname VARCHAR(50),
                    PRIMARY KEY (room_id, user_id),
                    FOREIGN KEY (room_id) REFERENCES chat_rooms(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
                await conn.execute(text(create_members_sql))
                print("✅ chat_room_members_new表创建成功")
                
                # 迁移旧的成员数据（如果存在）
                result = await conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_room_members'"
                ))
                old_members_table_exists = result.fetchone() is not None
                
                if old_members_table_exists:
                    print("🔄 迁移旧的成员数据...")
                    
                    # 获取旧表结构
                    result = await conn.execute(text("PRAGMA table_info(chat_room_members)"))
                    old_columns = {row[1] for row in result.fetchall()}
                    
                    if 'room_id' in old_columns and 'user_id' in old_columns:
                        # 迁移数据
                        migrate_sql = """
                        INSERT INTO chat_room_members_new (room_id, user_id, role, joined_at)
                        SELECT 
                            room_id, 
                            user_id, 
                            CASE WHEN is_admin = 1 THEN 'admin' ELSE 'member' END as role,
                            COALESCE(created_at, CURRENT_TIMESTAMP) as joined_at
                        FROM chat_room_members
                        """
                        await conn.execute(text(migrate_sql))
                        print("✅ 成员数据迁移完成")
            else:
                print("✅ chat_room_members_new表已存在")
            
            # 3. 更新chat_messages表结构
            print("\n🔄 更新chat_messages表结构...")
            
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'"
            ))
            messages_table_exists = result.fetchone() is not None
            
            if messages_table_exists:
                # 获取现有字段
                result = await conn.execute(text("PRAGMA table_info(chat_messages)"))
                existing_msg_columns = {row[1] for row in result.fetchall()}
                
                # 需要添加的新字段
                new_msg_columns = {
                    'reply_to_id': 'INTEGER',
                    'file_url': 'VARCHAR(500)',
                    'file_name': 'VARCHAR(255)',
                    'file_size': 'INTEGER',
                    'is_edited': 'BOOLEAN DEFAULT 0',
                    'is_deleted': 'BOOLEAN DEFAULT 0',
                    'is_pinned': 'BOOLEAN DEFAULT 0',
                    'edit_count': 'INTEGER DEFAULT 0'
                }
                
                for column_name, column_def in new_msg_columns.items():
                    if column_name not in existing_msg_columns:
                        print(f"🔄 添加消息字段: {column_name}")
                        await conn.execute(text(f"ALTER TABLE chat_messages ADD COLUMN {column_name} {column_def}"))
                        print(f"✅ 消息字段 {column_name} 添加成功")
            
            # 4. 创建新的辅助表
            print("\n🔄 创建辅助表...")
            
            # 消息已读回执表
            read_receipts_sql = """
            CREATE TABLE IF NOT EXISTS message_read_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES chat_messages(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(message_id, user_id)
            )
            """
            await conn.execute(text(read_receipts_sql))
            print("✅ message_read_receipts表创建成功")
            
            # 消息表情反应表
            reactions_sql = """
            CREATE TABLE IF NOT EXISTS message_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                emoji VARCHAR(10) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES chat_messages(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(message_id, user_id, emoji)
            )
            """
            await conn.execute(text(reactions_sql))
            print("✅ message_reactions表创建成功")
            
            # 用户输入状态表
            typing_sql = """
            CREATE TABLE IF NOT EXISTS user_typing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES chat_rooms(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(room_id, user_id)
            )
            """
            await conn.execute(text(typing_sql))
            print("✅ user_typing表创建成功")
            
            print("\n🎉 聊天室数据库迁移完成!")
            
        except Exception as e:
            print(f"❌ 迁移过程中发生错误: {e}")
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_chat_tables())
