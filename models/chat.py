"""
现代化聊天室系统模型
"""
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, DateTime, Table, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel

# 聊天室成员关联表
chat_room_members = Table(
    'chat_room_members_new',
    BaseModel.metadata,
    Column('room_id', Integer, ForeignKey('chat_rooms.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, default=func.now()),
    Column('role', String(20), default='member'),  # admin, member
    Column('is_muted', Boolean, default=False),
    Column('last_read_at', DateTime, default=func.now()),
    Column('nickname', String(50), nullable=True)  # 群内昵称
)

class MessageType(enum.Enum):
    """消息类型"""
    text = "text"
    image = "image"
    file = "file"
    system = "system"
    voice = "voice"
    video = "video"
    emoji = "emoji"

class RoomType(enum.Enum):
    """聊天室类型"""
    public = "public"    # 公开聊天室
    private = "private"  # 私聊
    group = "group"      # 私密聊天室
    channel = "channel"  # 频道

class MessageStatus(enum.Enum):
    """消息状态"""
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"




class ChatRoom(BaseModel):
    """现代化聊天室模型"""
    __tablename__ = "chat_rooms"

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    room_type = Column(Enum(RoomType), default=RoomType.group)
    avatar = Column(String(255), nullable=True)
    is_public = Column(Boolean, default=True)
    max_members = Column(Integer, default=500)
    created_by = Column(Integer, ForeignKey("users.id"))
    last_message_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # 群聊设置
    allow_member_invite = Column(Boolean, default=True)
    allow_member_modify_info = Column(Boolean, default=False)
    message_history_visible = Column(Boolean, default=True)

    # 私密房间设置
    allow_search = Column(Boolean, default=False)  # 是否允许被搜索（默认不允许）
    enable_invite_code = Column(Boolean, default=True)  # 是否启用邀请码（默认启用）
    invite_code = Column(String(32), nullable=True, unique=True)  # 邀请码
    invite_code_expires_at = Column(DateTime, nullable=True)  # 邀请码过期时间

    # 高级设置
    auto_delete_messages = Column(Boolean, default=False)  # 自动删除消息
    message_retention_days = Column(Integer, default=30)  # 消息保留天数
    allow_file_upload = Column(Boolean, default=True)  # 允许文件上传
    max_file_size = Column(Integer, default=10)  # 最大文件大小(MB)
    welcome_message = Column(Text, nullable=True)  # 欢迎消息
    rules = Column(Text, nullable=True)  # 聊天室规则

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("User", secondary=chat_room_members)
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")


class JoinRequestStatus(enum.Enum):
    """加入申请状态"""
    pending = "pending"    # 待处理
    approved = "approved"  # 已同意
    rejected = "rejected"  # 已拒绝
    expired = "expired"    # 已过期


class ChatRoomJoinRequest(BaseModel):
    """聊天室加入申请"""
    __tablename__ = "chat_room_join_requests"

    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(JoinRequestStatus), default=JoinRequestStatus.pending)
    message = Column(Text, nullable=True)  # 申请消息
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 处理人
    processed_at = Column(DateTime, nullable=True)  # 处理时间
    expires_at = Column(DateTime, nullable=False)  # 过期时间

    # 关系
    room = relationship("ChatRoom")
    user = relationship("User", foreign_keys=[user_id])
    processor = relationship("User", foreign_keys=[processed_by])


class ChatMessage(BaseModel):
    """聊天消息模型"""
    __tablename__ = "chat_messages"

    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.text)
    reply_to_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)

    # 文件相关
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)

    # 消息状态
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    edit_count = Column(Integer, default=0)

    # 系统消息数据
    system_data = Column(JSON, nullable=True)

    # 置顶相关
    pinned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    pinned_at = Column(DateTime, nullable=True)

    # 关系
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    pinner = relationship("User", foreign_keys=[pinned_by])
    reply_to = relationship("ChatMessage", remote_side="ChatMessage.id")
    read_receipts = relationship("MessageReadReceipt", back_populates="message", cascade="all, delete-orphan")
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")


class MessageReadReceipt(BaseModel):
    """消息已读回执"""
    __tablename__ = "message_read_receipts"

    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    read_at = Column(DateTime, default=func.now())

    # 关系
    message = relationship("ChatMessage", back_populates="read_receipts")
    user = relationship("User")

class MessageReaction(BaseModel):
    """消息表情回应"""
    __tablename__ = "message_reactions"

    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emoji = Column(String(10), nullable=False)  # 表情符号

    # 关系
    message = relationship("ChatMessage", back_populates="reactions")
    user = relationship("User")

class UserTyping(BaseModel):
    """用户正在输入状态"""
    __tablename__ = "user_typing"

    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=func.now())

    # 关系
    room = relationship("ChatRoom")
    user = relationship("User")

# 保持向后兼容的旧模型
class Chat(BaseModel):
    """旧版聊天模型（保持兼容性）"""
    __tablename__ = "chats"

    title = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # 关联关系
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(BaseModel):
    """旧版消息模型（保持兼容性）"""
    __tablename__ = "messages"

    content = Column(Text, nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_bot = Column(Boolean, default=False)

    # 关联关系
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User")
