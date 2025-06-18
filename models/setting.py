"""
设置模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Setting(BaseModel):
    __tablename__ = "settings"

    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    # user_id = Column(Integer, ForeignKey("users.id"))
    
    # 关联关系
    # user = relationship("User", back_populates="settings")