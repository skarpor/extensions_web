"""
日志模型
"""
from sqlalchemy import Column, String, Text, Integer
from .base import BaseModel

class Log(BaseModel):
    __tablename__ = "logs"

    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line = Column(Integer, nullable=True)
    stack_trace = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)  # 可选的用户ID 