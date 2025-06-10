from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    READONLY = "readonly"


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(BaseModel):
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    role: str = "user"
    avatar: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class User(UserBase):
    id: int
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    username: str
    password: str


class ChatRoom(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_private: bool = False
    created_by: int
    created_at: datetime
    updated_at: datetime


class ChatRoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class ChatMessage(BaseModel):
    id: int
    room_id: int
    user_id: int
    message: str
    has_image: bool = False
    image_path: Optional[str] = None
    created_at: datetime
    
    # 这些字段不在数据库中，但会在API响应中填充
    username: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class ChatMessageCreate(BaseModel):
    room_id: int
    message: str
    has_image: bool = False
    image_path: Optional[str] = None
