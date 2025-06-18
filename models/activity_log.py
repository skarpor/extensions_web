"""
活动日志模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import BaseModel

class ActivityLog(BaseModel):
    """活动日志模型"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    activity_type = Column(String(50), index=True)  # 活动类型：login, logout, file_upload, etc.
    description = Column(Text, nullable=True)  # 活动描述
    ip_address = Column(String(50), nullable=True)  # IP地址
    user_agent = Column(String(255), nullable=True)  # 用户代理
    resource_id = Column(Integer, nullable=True)  # 相关资源ID
    resource_type = Column(String(50), nullable=True)  # 相关资源类型
    
    # 关联关系
    user = relationship("User", back_populates="activities")
    
    def __init__(
        self,
        user_id: Optional[int] = None,
        activity_type: str = "",
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_type: Optional[str] = None,
    ):
        """初始化活动日志"""
        self.user_id = user_id
        self.activity_type = activity_type
        self.description = description
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.resource_id = resource_id
        self.resource_type = resource_type 