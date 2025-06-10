"""
聊天和消息模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
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