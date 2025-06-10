"""
数据迁移脚本
用于将旧数据库的数据迁移到新数据库
"""

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from new_app.db.session import AsyncSessionLocal
from new_app.models import User, File, Extension, Setting, Chat, Message, Log

async def migrate_users(old_conn: sqlite3.Connection, session: AsyncSession):
    """迁移用户数据"""
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    for user_data in users:
        user = User(
            id=user_data[0],
            username=user_data[1],
            email=user_data[2],
            hashed_password=user_data[3],
            is_active=bool(user_data[4]),
            is_superuser=bool(user_data[5]),
            created_at=datetime.fromisoformat(user_data[6]),
            updated_at=datetime.fromisoformat(user_data[7])
        )
        session.add(user)
    
    await session.commit()

async def migrate_files(old_conn: sqlite3.Connection, session: AsyncSession):
    """迁移文件数据"""
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM files")
    files = cursor.fetchall()
    
    for file_data in files:
        file = File(
            id=file_data[0],
            filename=file_data[1],
            filepath=file_data[2],
            filetype=file_data[3],
            filesize=file_data[4],
            owner_id=file_data[5],
            created_at=datetime.fromisoformat(file_data[6]),
            updated_at=datetime.fromisoformat(file_data[7])
        )
        session.add(file)
    
    await session.commit()

async def migrate_extensions(old_conn: sqlite3.Connection, session: AsyncSession):
    """迁移扩展数据"""
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM extensions")
    extensions = cursor.fetchall()
    
    for ext_data in extensions:
        extension = Extension(
            id=ext_data[0],
            name=ext_data[1],
            description=ext_data[2],
            version=ext_data[3],
            enabled=bool(ext_data[4]),
            creator_id=ext_data[5],
            created_at=datetime.fromisoformat(ext_data[6]),
            updated_at=datetime.fromisoformat(ext_data[7])
        )
        session.add(extension)
    
    await session.commit()

async def migrate_settings(old_conn: sqlite3.Connection, session: AsyncSession):
    """迁移设置数据"""
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM settings")
    settings = cursor.fetchall()
    
    for setting_data in settings:
        setting = Setting(
            id=setting_data[0],
            key=setting_data[1],
            value=setting_data[2],
            user_id=setting_data[3],
            created_at=datetime.fromisoformat(setting_data[4]),
            updated_at=datetime.fromisoformat(setting_data[5])
        )
        session.add(setting)
    
    await session.commit()

async def migrate_chats(old_conn: sqlite3.Connection, session: AsyncSession):
    """迁移聊天数据"""
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM chats")
    chats = cursor.fetchall()
    
    for chat_data in chats:
        chat = Chat(
            id=chat_data[0],
            title=chat_data[1],
            user_id=chat_data[2],
            created_at=datetime.fromisoformat(chat_data[3]),
            updated_at=datetime.fromisoformat(chat_data[4])
        )
        session.add(chat)
    
    await session.commit()

async def migrate_messages(old_conn: sqlite3.Connection, session: AsyncSession):
    """迁移消息数据"""
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM messages")
    messages = cursor.fetchall()
    
    for msg_data in messages:
        message = Message(
            id=msg_data[0],
            content=msg_data[1],
            chat_id=msg_data[2],
            user_id=msg_data[3],
            created_at=datetime.fromisoformat(msg_data[4]),
            updated_at=datetime.fromisoformat(msg_data[5])
        )
        session.add(message)
    
    await session.commit()

async def migrate_logs(old_conn: sqlite3.Connection, session: AsyncSession):
    """迁移日志数据"""
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM logs")
    logs = cursor.fetchall()
    
    for log_data in logs:
        log = Log(
            id=log_data[0],
            level=log_data[1],
            message=log_data[2],
            created_at=datetime.fromisoformat(log_data[3])
        )
        session.add(log)
    
    await session.commit()

async def main():
    """主迁移函数"""
    # 连接旧数据库
    old_db_path = Path("database.sqlite")
    if not old_db_path.exists():
        print("错误：找不到旧数据库文件")
        return
    
    old_conn = sqlite3.connect(str(old_db_path))
    
    # 获取新数据库会话
    async with AsyncSessionLocal() as session:
        try:
            # 按顺序迁移数据
            print("开始迁移用户数据...")
            await migrate_users(old_conn, session)
            
            print("开始迁移文件数据...")
            await migrate_files(old_conn, session)
            
            print("开始迁移扩展数据...")
            await migrate_extensions(old_conn, session)
            
            print("开始迁移设置数据...")
            await migrate_settings(old_conn, session)
            
            print("开始迁移聊天数据...")
            await migrate_chats(old_conn, session)
            
            print("开始迁移消息数据...")
            await migrate_messages(old_conn, session)
            
            print("开始迁移日志数据...")
            await migrate_logs(old_conn, session)
            
            print("数据迁移完成！")
            
        except Exception as e:
            print(f"迁移过程中出错：{str(e)}")
            await session.rollback()
        finally:
            old_conn.close()

if __name__ == "__main__":
    asyncio.run(main()) 