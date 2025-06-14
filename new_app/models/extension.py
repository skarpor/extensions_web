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
    enabled = Column(Boolean, default=True)
    config = Column(Text, nullable=True)  # JSON格式的配置
    entry_point = Column(String(255), nullable=False)  # 入口文件路径
    creator_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="extensions") 

    def __repr__(self):
        return f"<Extension(name='{self.name}', enabled={self.enabled})>"
    
