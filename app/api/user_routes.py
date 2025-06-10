"""用户管理相关的API路由处理。

提供用户的CRUD操作，包括：
- 获取用户列表
- 获取单个用户信息
- 创建用户
- 更新用户信息
- 删除用户
"""
from datetime import datetime
from logging import getLogger
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user, get_password_hash, verify_password
from app.core.database import Database
from app.db.database import get_db
from app.models.user import User, UserCreate, UserInDB, UserRole, UserUpdate

# 全局变量
router = APIRouter(prefix="/api/users", tags=["users"])
db_instance:Database = None
logger = getLogger("user_routes")

def init_router(db):
    """初始化路由，设置数据库实例"""
    global db_instance
    db_instance = db
    return router

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    role: str
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    username: str
    password: str
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    role: str = UserRole.USER.value
    
    @validator('role')
    def validate_role(cls, v):
        if v not in [role.value for role in UserRole]:
            raise ValueError(f"角色必须是以下之一: {', '.join([role.value for role in UserRole])}")
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("用户名长度必须至少为3个字符")
        if not v.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("密码长度必须至少为6个字符")
        return v

class UserUpdateRequest(BaseModel):
    """用户更新请求模型"""
    password: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in [role.value for role in UserRole]:
            raise ValueError(f"角色必须是以下之一: {', '.join([role.value for role in UserRole])}")
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError("密码长度必须至少为6个字符")
        return v

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """获取用户列表"""
    # 检查权限
    # print(current_user.role,UserRole.ADMIN.value,UserRole.MANAGER.value)
    if current_user.role.lower() not in [UserRole.ADMIN.value, UserRole.MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 获取用户列表
    users = await db_instance.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """获取单个用户信息"""
    # 检查权限
    if current_user.role not in [UserRole.ADMIN.value, UserRole.MANAGER.value] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 获取用户信息
    user = await db_instance.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreateRequest,
    # db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """创建新用户"""
    # 检查权限
    if current_user.role not in [UserRole.ADMIN.value, UserRole.MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 如果不是管理员，不能创建管理员账户
    if current_user.role != UserRole.ADMIN.value and user.role == UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以创建管理员账户"
        )
    
    # 创建用户
    try:
        hashed_password = get_password_hash(user.password)
        user_data = UserCreate(
            username=user.username,
            hashed_password=hashed_password,
            nickname=user.nickname or user.username,
            email=user.email,
            role=user.role
        )
        
        created_user = await db_instance.create_user(user=user_data)
        return created_user
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """更新用户信息"""
    # 检查权限
    if current_user.role not in [UserRole.ADMIN.value, UserRole.MANAGER.value] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 获取要更新的用户
    db_user = await db_instance.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    
    # 特殊权限检查
    if user_update.role:
        # 只有管理员可以修改角色
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有超级管理员可以修改用户角色"
            )
        
        # 不能修改管理员的角色
        if db_user.role == UserRole.ADMIN.value and user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能修改其他管理员的角色"
            )
    
    # 准备更新数据
    update_data = user_update.dict(exclude_unset=True)
    
    # 如果有密码，需要哈希处理
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # 更新用户
    try:
        updated_user = await db_instance.update_user(
            db, 
            user_id=user_id, 
            user_update=UserUpdate(**update_data)
        )
        return updated_user
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """删除用户"""
    # 检查权限
    if current_user.role not in [UserRole.ADMIN.value, UserRole.MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录的用户"
        )
    
    # 获取要删除的用户
    db_user = await db_instance.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    
    # 只有管理员可以删除管理员
    if db_user.role == UserRole.ADMIN.value and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以删除管理员账户"
        )
    
    # 删除用户
    await db_instance.delete_user(db, user_id=user_id)
    return None 