"""
聊天相关的Pydantic模型
"""
from typing import Optional, List
from pydantic import BaseModel

from .base import BaseSchema
from .user import User

class ChatBase(BaseModel):
    """聊天基础模型"""
    title: Optional[str] = None

class ChatCreate(ChatBase):
    """聊天创建模型"""
    pass

class ChatUpdate(ChatBase):
    """聊天更新模型"""
    pass

class MessageBase(BaseModel):
    """消息基础模型"""
    content: str
    is_bot: bool = False

class MessageCreate(MessageBase):
    """消息创建模型"""
    pass

class MessageUpdate(MessageBase):
    """消息更新模型"""
    content: Optional[str] = None

class MessageInDBBase(MessageBase, BaseSchema):
    """数据库中的消息模型"""
    id: Optional[int] = None
    chat_id: int
    user_id: int

    class Config:
        from_attributes = True

class Message(MessageInDBBase):
    """API响应中的消息模型"""
    user: Optional[User] = None

class MessageInDB(MessageInDBBase):
    """数据库中的消息模型"""
    pass

class ChatInDBBase(ChatBase, BaseSchema):
    """数据库中的聊天模型"""
    id: Optional[int] = None
    user_id: int

    class Config:
        from_attributes = True

class Chat(ChatInDBBase):
    """API响应中的聊天模型"""
    user: Optional[User] = None
    messages: List[Message] = []

class ChatInDB(ChatInDBBase):
    """数据库中的聊天模型"""
    pass 