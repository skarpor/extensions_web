"""
聊天和消息模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel

class Chat(BaseModel):
    __tablename__ = "chats"

    title = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 关联关系
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(BaseModel):
    __tablename__ = "messages"

    content = Column(Text, nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_bot = Column(Boolean, default=False)
    
    # 关联关系
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User")




# 聊天室表
class ChatRoom(BaseModel):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    is_private = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    creator = relationship("User", back_populates="chat_rooms")
    members = relationship("ChatRoomMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")


# 聊天室成员表
class ChatRoomMember(BaseModel):
    __tablename__ = "chat_room_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系
    room = relationship("ChatRoom", back_populates="members")
    user = relationship("User", back_populates="chat_room_memberships")


# 聊天消息表
class ChatMessage(BaseModel):
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
