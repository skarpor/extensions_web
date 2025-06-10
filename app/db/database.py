"""
SQLAlchemy异步数据库连接模块

提供异步数据库会话和连接管理
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from config import settings

# 创建异步数据库引擎
# 使用SQLite作为数据库，支持异步操作
DATABASE_URL = f"sqlite+aiosqlite:///{settings.DATABASE_PATH}"

# 确保数据库目录存在
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # 在调试模式下输出SQL语句
    poolclass=NullPool,  # 对于SQLite，禁用连接池
    connect_args={"check_same_thread": False}  # SQLite特有的设置，允许多线程访问
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话
    
    用作FastAPI的依赖项，提供数据库会话
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    初始化数据库
    
    创建所有表和初始数据
    """
    from app.db.models import Base
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    # 初始化默认数据
    await init_default_data()

async def init_default_data():
    """
    初始化默认数据
    
    创建默认用户、权限等数据
    """
    from datetime import datetime
    from sqlalchemy import select, insert
    from app.db.models import User, Permission, ChatRoom, ChatRoomMember, SystemSetting
    from app.core.auth import get_password_hash
    
    async with AsyncSessionLocal() as db:
        # 检查是否已有用户
        result = await db.execute(select(User))
        if result.first() is not None:
            # 已有用户，不需要初始化
            return
        
        now = datetime.now()
        
        # 创建默认管理员用户
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("123"),  # 默认密码: 123
            nickname="管理员",
            role="ADMIN",
            created_at=now,
            updated_at=now
        )
        db.add(admin)
        await db.flush()
        
        # 创建默认测试用户
        test_user = User(
            username="test",
            email="test@example.com",
            hashed_password=get_password_hash("123"),  # 默认密码: 123
            nickname="测试用户",
            role="USER",
            created_at=now,
            updated_at=now
        )
        db.add(test_user)
        await db.flush()
        
        # 创建默认聊天室
        chat_room = ChatRoom(
            name="公共聊天室",
            description="所有用户可见的公共聊天室",
            created_by=admin.id,
            created_at=now,
            updated_at=now
        )
        db.add(chat_room)
        await db.flush()
        
        # 将用户添加到聊天室
        admin_member = ChatRoomMember(
            room_id=chat_room.id,
            user_id=admin.id,
            created_at=now
        )
        db.add(admin_member)
        
        test_member = ChatRoomMember(
            room_id=chat_room.id,
            user_id=test_user.id,
            created_at=now
        )
        db.add(test_member)
        
        # 创建默认系统设置
        default_settings = [
            ("enable_chat", "true", "启用聊天功能"),
            ("enable_extensions", "true", "启用扩展管理"),
            ("enable_logs", "true", "启用日志管理"),
            ("enable_files", "true", "启用文件管理"),
            ("enable_settings", "true", "启用系统设置"),
            ("enable_email", "false", "启用邮件通知")
        ]
        
        for key, value, desc in default_settings:
            setting = SystemSetting(
                key=key,
                value=value,
                description=desc,
                updated_at=now
            )
            db.add(setting)
        
        # 创建默认权限
        default_permissions = [
            # 管理员权限
            ("admin", "system", "manage"),
            ("admin", "users", "manage"),
            ("admin", "chat", "manage"),
            ("admin", "extensions", "manage"),
            ("admin", "files", "manage"),
            ("admin", "logs", "view"),
            
            # 管理员权限
            ("manager", "users", "view"),
            ("manager", "users", "create"),
            ("manager", "users", "edit"),
            ("manager", "chat", "manage"),
            ("manager", "files", "manage"),
            
            # 普通用户权限
            ("user", "chat", "use"),
            ("user", "files", "upload"),
            ("user", "files", "download"),
            ("user", "profile", "edit")
        ]
        
        # 注意：这里需要创建一个新的权限模型，但由于我们没有完整的权限模型，
        # 暂时跳过这部分，等应用程序稳定后再添加
        
        await db.commit() 