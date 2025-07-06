"""
二维码文件模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, Boolean, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class QRFile(BaseModel):
    """二维码文件模型，用于跟踪生成的二维码文件"""
    __tablename__ = "qr_files"

    # 文件信息
    filename = Column(String(255), nullable=False, comment="文件名")
    filepath = Column(String(512), nullable=False, comment="文件路径")
    filetype = Column(String(50), nullable=True, comment="文件类型")
    filesize = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    
    # 二维码信息
    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")
    mode = Column(String(20), nullable=False, comment="模式(region/file)")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    
    # 原始文件信息
    original_filename = Column(String(255), nullable=True, comment="原始文件名")
    original_filesize = Column(BigInteger, nullable=True, comment="原始文件大小")
    
    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 其他信息
    description = Column(Text, nullable=True, comment="描述")
    is_deleted = Column(Boolean, default=False, comment="是否已删除")
    
    # 关联关系
    user = relationship("User", back_populates="qr_files") 