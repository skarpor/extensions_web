"""
Token相关的Pydantic模型
"""
from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    """Token模型"""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Token载荷模型"""
    sub: Optional[int] = None 