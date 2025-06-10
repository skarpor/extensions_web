"""
聊天相关的数据模型schema
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class ChatRoomBase(BaseModel):
    """聊天室基础模型"""
    name: str = Field(..., max_length=50, description="聊天室名称")
    description: Optional[str] = Field(None, max_length=200, description="聊天室描述")
    is_private: bool = Field(False, description="是否是私有聊天室")


class ChatRoomCreate(ChatRoomBase):
    """创建聊天室请求模型"""
    pass


class ChatRoom(ChatRoomBase):
    """聊天室响应模型"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class ChatRoomResponse(BaseModel):
    """聊天室操作响应"""
    message: str
    room: ChatRoom


class ChatRoomList(BaseModel):
    """聊天室列表响应"""
    rooms: List[ChatRoom]


class ChatRoomMember(BaseModel):
    """聊天室成员模型"""
    id: int
    room_id: int
    user_id: int
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


class ChatRoomMemberInfo(BaseModel):
    """聊天室成员信息"""
    id: int
    username: str
    nickname: Optional[str]
    is_admin: bool
    joined_at: datetime
    online: bool


class ChatRoomMemberList(BaseModel):
    """聊天室成员列表响应"""
    members: List[ChatRoomMemberInfo]


class ChatMessageBase(BaseModel):
    """聊天消息基础模型"""
    message_type: str = Field(..., description="消息类型: text, image")
    message: str = Field(..., description="消息内容")


class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息请求模型"""
    room_id: Optional[int] = Field(None, description="聊天室ID，为空表示私聊")
    receiver_id: Optional[int] = Field(None, description="接收者ID，聊天室消息为空")


class ChatMessage(ChatMessageBase):
    """聊天消息响应模型"""
    id: int
    sender_id: int
    room_id: Optional[int]
    receiver_id: Optional[int]
    timestamp: datetime
    username: str
    nickname: Optional[str]
    
    class Config:
        orm_mode = True


class ChatMessageResponse(BaseModel):
    """聊天消息操作响应"""
    message: str
    chat_message: Optional[ChatMessage] = None


class ChatMessageList(BaseModel):
    """聊天消息列表响应"""
    messages: List[ChatMessage]


class WebSocketMessage(BaseModel):
    """WebSocket消息基础模型"""
    type: str = Field(..., description="消息类型")


class ChatWebSocketMessage(WebSocketMessage):
    """聊天WebSocket消息"""
    message_type: str = "text"
    message: str
    room_id: Optional[int] = None
    receiver_id: Optional[int] = None


class UserInfoMessage(WebSocketMessage):
    """用户信息WebSocket消息"""
    nickname: Optional[str] = None


class RoomActionMessage(WebSocketMessage):
    """聊天室操作WebSocket消息"""
    room_id: int


class TypingMessage(WebSocketMessage):
    """正在输入WebSocket消息"""
    isTyping: bool
    room_id: Optional[int] = None
    receiver_id: Optional[int] = None


class ImageUploadResponse(BaseModel):
    """图片上传响应"""
    image_url: str 