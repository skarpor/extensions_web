"""
文件相关的Pydantic模型
"""
from typing import Optional
from pydantic import BaseModel

from .base import BaseSchema
from .user import User

class FileBase(BaseModel):
    """文件基础模型"""
    filename: str
    filepath: str
    filetype: Optional[str] = None
    filesize: int
    hash: Optional[str] = None
    # metadata: Optional[str] = None
    path: str


class FileCreate(FileBase):
    """文件创建模型"""
    pass

class FileUpdate(FileBase):
    """文件更新模型"""
    filename: Optional[str] = None
    filepath: Optional[str] = None
    filesize: Optional[int] = None

class FileInDBBase(FileBase, BaseSchema):
    """数据库中的文件模型"""
    id: Optional[int] = None
    owner_id: int

    class Config:
        from_attributes = True

class File(FileInDBBase):
    """API响应中的文件模型"""
    owner: Optional[User] = None

class FileInDB(FileInDBBase):
    """数据库中的文件模型"""
    pass 