"""
基础的Pydantic模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class BaseSchema(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 