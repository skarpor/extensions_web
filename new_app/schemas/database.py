"""
数据库模型Schema模块

定义与统一数据库管理相关的所有数据模型。
包括表结构、列定义和数据操作等相关模型。
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """列信息模型"""
    name: str = Field(..., description="列名")
    type: str = Field(..., description="数据类型")
    primary_key: bool = Field(False, description="是否为主键")
    nullable: bool = Field(True, description="是否可为空")
    unique: bool = Field(False, description="是否唯一")
    default: Optional[Any] = Field(None, description="默认值")
    comment: Optional[str] = Field(None, description="列注释")
    length: Optional[int] = Field(None, description="字符串长度")
    precision: Optional[int] = Field(None, description="数值精度")
    auto_increment: Optional[bool] = Field(None, description="是否自增")


class TableSchema(BaseModel):
    """表结构模型"""
    columns: List[ColumnInfo] = Field(..., description="列定义列表")
    description: Optional[str] = Field(None, description="表描述")


class TableInfo(BaseModel):
    """表信息模型"""
    name: str = Field(..., description="表名")
    display_name: str = Field(..., description="显示名称（不包含前缀）")
    # original_name: str = Field(..., description="原始名称（不包含扩展前缀）")
    description: Optional[str] = Field(None, description="表描述")
    extension_id: Optional[str] = Field(None, description="所属扩展ID")
    extension_name: Optional[str] = Field(None, description="所属扩展名称")
    record_count: int = Field(0, description="记录数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")


class TableDataResponse(BaseModel):
    """表数据响应模型"""
    items: List[Dict[str, Any]] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页记录数")
    pages: int = Field(..., description="总页数")


class TableDataCreate(BaseModel):
    """表数据创建模型"""
    data: Dict[str, Any] = Field(..., description="要创建的数据")


class TableDataUpdate(BaseModel):
    """表数据更新模型"""
    data: Dict[str, Any] = Field(..., description="要更新的数据")


class QueryCondition(BaseModel):
    """查询条件模型"""
    field: str = Field(..., description="字段名")
    operator: str = Field(..., description="操作符 (eq, neq, gt, lt, gte, lte, like, in)")
    value: Any = Field(..., description="值")


class QueryRequest(BaseModel):
    """查询请求模型"""
    conditions: List[QueryCondition] = Field([], description="查询条件列表")
    fields: Optional[List[str]] = Field(None, description="要返回的字段")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_desc: bool = Field(False, description="是否降序排序")
    page: int = Field(1, description="页码")
    per_page: int = Field(10, description="每页记录数")
    group_by: Optional[List[str]] = Field(None, description="分组字段")
    having: Optional[List[QueryCondition]] = Field(None, description="HAVING条件") 