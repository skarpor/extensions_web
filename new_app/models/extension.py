"""
扩展模型
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Extension(BaseModel):
    __tablename__ = "extensions"

    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(Text, nullable=True)  # JSON格式的配置
    entry_point = Column(String(255), nullable=False)  # 入口文件路径
    requirements = Column(Text, nullable=True)  # 依赖列表，JSON格式
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    # 关联关系
    creator = relationship("User", back_populates="extensions") 