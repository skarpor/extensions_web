"""
用户相关的Pydantic模型
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from .base import BaseSchema

class UserBase(BaseModel):
    """用户基础模型"""
    username:str
    nickname:str
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    avatar: Optional[str] = None
    # is_superuser: bool = False
    # full_name: Optional[str] = None

class UserCreate(UserBase):
    """用户创建模型"""
    username: str
    email: EmailStr
    password: str

class UserUpdate(UserBase):
    """用户更新模型"""
    password: Optional[str] = None

class UserInDBBase(UserBase, BaseSchema):
    """数据库中的用户模型"""
    id: Optional[int] = None
    is_superuser: bool = False
    class Config:
        from_attributes = True

class User(UserInDBBase):
    """API响应中的用户模型"""
    pass

class UserInDB(UserInDBBase):
    """数据库中的用户模型（包含哈希密码）"""
    hashed_password: str
from .token import Token
class LoginResponse(Token):
    user:User

# 新增权限和角色相关模型
class PermissionBase(BaseModel):
    """权限基础模型"""
    code: str
    name: str
    url: Optional[str] = None
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    """权限创建模型"""
    pass

class PermissionUpdate(PermissionBase):
    """权限更新模型"""
    code: Optional[str] = None
    name: Optional[str] = None

class Permission(PermissionBase, BaseSchema):
    """API响应中的权限模型"""
    id: int
    
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """角色创建模型"""
    permission_ids: List[int] = []

class RoleUpdate(RoleBase):
    """角色更新模型"""
    name: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class Role(RoleBase, BaseSchema):
    """API响应中的角色模型"""
    id: int
    permissions: List[Permission] = []
    
    class Config:
        from_attributes = True

class UserWithRoles(User):
    """带有角色信息的用户模型"""
    roles: List[Role] = []
    
    class Config:
        from_attributes = True

class AssignRoleRequest(BaseModel):
    """分配角色请求模型"""
    user_id: int
    role_ids: List[int]