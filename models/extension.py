"""
扩展模型
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class Extension(BaseModel):
    __tablename__ = "extensions"
    id = Column(String, primary_key=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=False)
    execution_mode = Column(String(255), default="manual")  # 执行方式：立即执行、手动执行、定时执行
    show_in_home = Column(Boolean, default=False) # 是否显示在首页
    config = Column(JSON, nullable=True)  # 配置表单项
    has_query_form = Column(Boolean, default=False) # 是否显示查询表单
    has_config_form = Column(Boolean, default=False) # 是否显示配置表单
    entry_point = Column(String(255), nullable=True)  # 入口文件路径
    deleted = Column(Boolean, default=False)  # 是否删除
    creator_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="extensions") 
    render_type = Column(String(255), default="html") # 渲染方式
