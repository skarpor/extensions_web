"""
用户相关的API端点
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    current_user: UserModel = Depends(manage_users),
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

@router.get("/search/users")
async def search_users(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="返回数量限制"),
    current_user: UserModel = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索用户"""
    try:
        if not q or len(q.strip()) < 2:
            return []

        from sqlalchemy import select, and_, or_

        search_term = f"%{q.strip()}%"

        # 简化搜索逻辑，避免复杂的条件表达式
        query = select(UserModel).where(
            and_(
                or_(
                    UserModel.username.ilike(search_term),
                    UserModel.nickname.ilike(search_term)
                ),
                UserModel.is_active == True,
                UserModel.id != current_user.id  # 排除当前用户
            )
        ).order_by(UserModel.username).limit(limit)

        result = await db.execute(query)
        users = result.scalars().all()

        # 转换为响应格式
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar": getattr(user, 'avatar', None),
                "is_active": user.is_active
            })

        return user_list

    except Exception as e:
        logger.error(f"搜索用户失败: {e}")
        raise HTTPException(status_code=500, detail="搜索用户失败")

@router.get("/contacts/recent")
async def get_recent_contacts(
    limit: int = Query(10, description="返回数量限制"),
    current_user: UserModel = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取最近联系人"""
    try:
        # 简单返回一些活跃用户作为最近联系人
        from sqlalchemy import select, desc, and_

        query = select(UserModel).where(
            and_(
                UserModel.is_active == True,
                UserModel.id != current_user.id
            )
        ).order_by(desc(UserModel.created_at)).limit(limit)

        result = await db.execute(query)
        users = result.scalars().all()

        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar": getattr(user, 'avatar', None),
                "is_active": user.is_active
            })

        return user_list

    except Exception as e:
        logger.error(f"获取最近联系人失败: {e}")
        return []  # 失败时返回空列表