"""
设置相关的Pydantic模型
"""
from typing import Optional
from pydantic import BaseModel

from .base import BaseSchema
from .user import User

class SettingBase(BaseModel):
    """设置基础模型"""
    key: str
    value: Optional[str] = None
    description: Optional[str] = None

class SettingCreate(SettingBase):
    """设置创建模型"""
    pass

class SettingUpdate(BaseModel):
    """设置更新模型"""
    value: Optional[str] = None
    description: Optional[str] = None

class SettingInDBBase(SettingBase, BaseSchema):
    """数据库中的设置模型"""
    id: Optional[int] = None
    user_id: int

    class Config:
        from_attributes = True

class Setting(SettingInDBBase):
    """API响应中的设置模型"""
    user: Optional[User] = None

class SettingInDB(SettingInDBBase):
    """数据库中的设置模型"""
    pass 