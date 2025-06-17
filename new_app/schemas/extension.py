"""
扩展相关的Pydantic模型
"""
from typing import Optional, List
from pydantic import BaseModel

from .base import BaseSchema
from .user import User

class ExtensionBase(BaseModel):
    """扩展基础模型"""
    name: str
    description: Optional[str] = None
    execution_mode: str = "manual"
    has_config_form: bool = False
    has_query_form: bool = False
    show_in_home: bool = False
    render_type: str = "html" # 渲染方式


class ExtensionCreate(ExtensionBase):
    """扩展创建模型"""
    pass

class ExtensionUpdate(BaseModel):
    """扩展更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[str] = None
    show_in_home: Optional[bool] = None
    render_type: Optional[str] = None

class ExtensionInDBBase(ExtensionBase, BaseSchema):
    """数据库中的扩展模型"""
    id: Optional[str] = None
    creator_id: int
    class Config:
        from_attributes = True

class Extension(ExtensionInDBBase):
    """API响应中的扩展模型"""
    # creator: Optional[User] = None
    enabled:bool
    pass
class ExtensionInDB(ExtensionInDBBase):
    """数据库中的扩展模型"""


