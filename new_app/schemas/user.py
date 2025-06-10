"""
用户相关的Pydantic模型
"""
from typing import Optional
from pydantic import BaseModel, EmailStr

from .base import BaseSchema

class UserBase(BaseModel):
    """用户基础模型"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    # is_superuser: bool = False
    # full_name: Optional[str] = None

class UserCreate(UserBase):
    """用户创建模型"""
    username: str
    email: EmailStr
    password: str

class UserUpdate(UserBase):
    """用户更新模型"""
    password: Optional[str] = None

class UserInDBBase(UserBase, BaseSchema):
    """数据库中的用户模型"""
    id: Optional[int] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    """API响应中的用户模型"""
    pass

class UserInDB(UserInDBBase):
    """数据库中的用户模型（包含哈希密码）"""
    hashed_password: str 