"""
SQLAlchemy数据库模型定义

定义了应用程序使用的所有数据库表结构
"""
from sqlalchemy import (
    Table, Column, Integer, String, Text, Boolean, 
    ForeignKey, MetaData, DateTime, UniqueConstraint, Float, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# 创建元数据对象
metadata = MetaData()

# 用户表
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    nickname = Column(String(50))
    role = Column(String(20), default="USER")  # USER, MANAGER, ADMIN
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime, default=datetime.now,nullable=True)
    # 关联关系
    permissions = relationship("Permission", secondary="user_permissions", back_populates="users")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    query_records = relationship("QueryRecord", back_populates="user")
    chat_rooms = relationship("ChatRoom", foreign_keys="ChatRoom.created_by", back_populates="creator")
    chat_room_memberships = relationship("ChatRoomMember", back_populates="user")
    sent_messages = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender")
    received_messages = relationship("ChatMessage", foreign_keys="ChatMessage.receiver_id", back_populates="receiver")


# 权限表
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50),unique=True,index=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(200))
    
    # 关联关系
    users = relationship("User", secondary="user_permissions", back_populates="permissions")


# 用户权限关联表
class UserPermission(Base):
    __tablename__ = "user_permissions"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


# API密钥表
class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    key = Column(String(100), unique=True, index=True)
    name = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)
    
    # 关联关系
    user = relationship("User", back_populates="api_keys")


# 系统设置表
class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True)
    value = Column(Text)
    description = Column(String(200))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# 查询记录表
class QueryRecord(Base):
    __tablename__ = "query_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    query_text = Column(Text)
    response_text = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    user = relationship("User", back_populates="query_records")


# 聊天室表
class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    is_private = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    creator = relationship("User", foreign_keys=[created_by], back_populates="chat_rooms")
    members = relationship("ChatRoomMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")


# 聊天室成员表
class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"
    
    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系
    room = relationship("ChatRoom", back_populates="members")
    user = relationship("User", back_populates="chat_room_memberships")


# 聊天消息表
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    message_type = Column(String(10), default="text")  # text, image
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    room = relationship("ChatRoom", back_populates="messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")


# 插件表
class Plugin(Base):
    __tablename__ = "plugins"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    version = Column(String(20))
    enabled = Column(Boolean, default=True)
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# 文件元数据表
file_metadata = Table(
    "file_metadata",
    metadata,
    Column("id", String, primary_key=True),
    Column("filename", String, nullable=False),
    Column("safe_filename", String, nullable=False),
    Column("content_type", String),
    Column("path", String, nullable=False),
    Column("extension_id", String, ForeignKey("extension_configs.id", ondelete="SET NULL")),
    Column("description", Text),
    Column("created_at", String, nullable=False),
    Column("size", Integer, nullable=False)
)

# 扩展配置表
extension_configs = Table(
    "extension_configs",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("endpoint", String, nullable=False),
    Column("enabled", Boolean, default=False, nullable=False),
    Column("config", Text, nullable=False),
    Column("has_config_form", Boolean, default=False, nullable=False),
    Column("has_query_form", Boolean, default=False, nullable=False),
    Column("showinindex", Boolean, default=False, nullable=False),
    Column("return_type", String, default="text", nullable=False),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False)
) 