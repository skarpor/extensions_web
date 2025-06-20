"""
文件模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class File(BaseModel):
    __tablename__ = "files"

    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    filetype = Column(String(50), nullable=True)
    filesize = Column(BigInteger, nullable=False)
    hash = Column(String(64), nullable=True)  # 文件哈希值
    path = Column(String(512), nullable=False)
# filemeta = Column(String(1024), nullable=True)  # JSON格式的元数据
    owner_id = Column(Integer, ForeignKey("users.id"))
    # 关联关系
    owner = relationship("User", back_populates="files") 
    # 目录
    
