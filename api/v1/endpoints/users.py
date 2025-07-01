"""
用户相关的API端点
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core import auth
from db.session import get_db
from schemas.user import User, UserUpdate, UserCreate
from models.user import User as UserModel
from core.logger import get_logger
from core.auth import PermissionChecker

router = APIRouter()
logger = get_logger("users")
# 定义权限检查器
view_users = PermissionChecker(["user:read"])
manage_users = PermissionChecker(["user:create", "user:update", "user:delete"])
manage_roles = PermissionChecker(["role:manage"])

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取当前用户信息
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    更新当前用户信息
    """
    user = await auth.update_user(db, db_obj=current_user, obj_in=user_in)
    return user

@router.get("", response_model=List[User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(auth.get_current_superuser),
) -> Any:
    """
    获取用户列表（仅超级管理员）
    """
    users = await auth.get_users(db, skip=skip, limit=limit)
    return users

@router.post("", response_model=User)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    current_user: UserModel = Depends(auth.get_current_superuser),
) -> Any:
    """
    创建新用户（仅超级管理员）
    """
    user = await auth.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已注册"
        )
    user = await auth.create_user(db, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=User)
async def read_user_by_id(
    user_id: int,
    current_user: UserModel = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    通过ID获取用户信息
    """
    user = await auth.get_user_by_id(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: UserModel = Depends(auth.get_current_superuser),
) -> Any:
    """
    更新用户信息（仅超级管理员）
    """
    user = await auth.get_user_by_id(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    user = await auth.update_user(db, db_obj=user, obj_in=user_in)
    return user 