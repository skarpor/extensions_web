"""
迁移测试脚本
用于测试数据迁移是否成功
"""

import asyncio
from sqlalchemy import select
from new_app.db.session import AsyncSessionLocal
from new_app.models import User, File, Extension, Setting, Chat, Message, Log

async def test_users():
    """测试用户数据迁移"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"用户数量: {len(users)}")
        for user in users:
            print(f"用户ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")

async def test_files():
    """测试文件数据迁移"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(File))
        files = result.scalars().all()
        print(f"文件数量: {len(files)}")
        for file in files:
            print(f"文件ID: {file.id}, 文件名: {file.filename}, 所有者ID: {file.owner_id}")

async def test_extensions():
    """测试扩展数据迁移"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Extension))
        extensions = result.scalars().all()
        print(f"扩展数量: {len(extensions)}")
        for ext in extensions:
            print(f"扩展ID: {ext.id}, 名称: {ext.name}, 版本: {ext.version}")

async def test_settings():
    """测试设置数据迁移"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Setting))
        settings = result.scalars().all()
        print(f"设置数量: {len(settings)}")
        for setting in settings:
            print(f"设置ID: {setting.id}, 键: {setting.key}, 值: {setting.value}")

async def test_chats():
    """测试聊天数据迁移"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Chat))
        chats = result.scalars().all()
        print(f"聊天数量: {len(chats)}")
        for chat in chats:
            print(f"聊天ID: {chat.id}, 标题: {chat.title}, 用户ID: {chat.user_id}")

async def test_messages():
    """测试消息数据迁移"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Message))
        messages = result.scalars().all()
        print(f"消息数量: {len(messages)}")
        for msg in messages:
            print(f"消息ID: {msg.id}, 聊天ID: {msg.chat_id}, 用户ID: {msg.user_id}")

async def test_logs():
    """测试日志数据迁移"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Log))
        logs = result.scalars().all()
        print(f"日志数量: {len(logs)}")
        for log in logs:
            print(f"日志ID: {log.id}, 级别: {log.level}, 消息: {log.message}")

async def main():
    """主测试函数"""
    print("开始测试数据迁移结果...")
    
    print("\n=== 测试用户数据 ===")
    await test_users()
    
    print("\n=== 测试文件数据 ===")
    await test_files()
    
    print("\n=== 测试扩展数据 ===")
    await test_extensions()
    
    print("\n=== 测试设置数据 ===")
    await test_settings()
    
    print("\n=== 测试聊天数据 ===")
    await test_chats()
    
    print("\n=== 测试消息数据 ===")
    await test_messages()
    
    print("\n=== 测试日志数据 ===")
    await test_logs()
    
    print("\n数据迁移测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 