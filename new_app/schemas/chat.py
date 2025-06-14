"""
聊天相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

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
        from_attributes = True


# class ChatRoomResponse(BaseModel):
#     """聊天室操作响应"""
#     message: str
#     room: ChatRoom


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
        from_attributes = True


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
        from_attributes = True

# class ChatMessageResponse(BaseModel):
#     """聊天消息操作响应"""
#     message: str
#     chat_message: Optional[ChatMessage] = None


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

# ===== 聊天室相关模型 =====

class ChatRoomResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_private: bool
    created_by: int
    creator_username: str
    creator_nickname: Optional[str] = None
    member_count: int
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    username: str
    nickname: Optional[str] = None
    message: str
    has_image: bool
    image_path: Optional[str] = None
    created_at: str


# class ChatMessageCreate(BaseModel):
#     room_id: int
#     message: str
