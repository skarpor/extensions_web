"""
认证相关的API端点
"""
from datetime import timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Response, status, UploadFile, File
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from models.user import User as DBUser, Role as DBRole, Permission as DBPermission, PermissionGroup as DBPermissionGroup, user_role, role_permission
from config import settings
from db.session import get_db
from schemas.token import Token
from schemas.user import UserCreate, User, LoginResponse, UserUpdate, Role, RoleCreate, RoleUpdate, Permission, PermissionCreate, PermissionUpdate, UserWithRoles, AssignRoleRequest, PermissionGroup, PermissionGroupCreate, PermissionGroupUpdate, PermissionGroupWithPermissions
from core import auth
from core.auth import logger
from core.auth import PermissionChecker, get_password_hash, has_permission
import os
import uuid
from pathlib import Path

router = APIRouter()


# 定义权限检查器
view_users = PermissionChecker(["user:read"])
manage_users = PermissionChecker(["user:create", "user:update", "user:delete"])
manage_roles = PermissionChecker(["role:manage"])

@router.post("/login", response_model=LoginResponse)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录
    """
    user = await auth.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        logger.warning(f"用户登录失败: {form_data.username} - 无效凭证")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        logger.warning(f"用户登录失败: {form_data.username} - 用户未激活")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"用户登录成功: {form_data.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


# 添加一个支持JSON格式的登录端点
class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login-json", response_model=LoginResponse)
async def login_json(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    用户登录 - JSON格式
    """
    user = await auth.authenticate(
        db, username=login_data.username, password=login_data.password
    )
    if not user:
        logger.warning(f"用户登录失败: {login_data.username} - 无效凭证")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        logger.warning(f"用户登录失败: {login_data.username} - 用户未激活")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"用户登录成功: {login_data.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@router.post("/test-token", response_model=User)
async def test_token(
    current_user: User = Depends(auth.get_current_user)
) -> Any:
    """
    测试token
    """
    return current_user 


@router.post("/token", response_model=Token)
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    response: Response = None,
    db: AsyncSession = Depends(get_db),
    
    ):
    """
    用户登录并获取令牌
    
    Args:
        form_data: 包含用户名和密码的表单数据
        
    Returns:
        带有访问令牌的响应
        
    Raises:
        HTTPException: 如果凭证无效
    """
    logger.info(f"用户尝试登录: {form_data.username}")
    
    try:
        user =await auth.authenticate(db, form_data.username, form_data.password)

        if not user:
            logger.warning(f"用户登录失败: {form_data.username} - 无效凭证")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # 创建访问令牌
        access_token = auth.create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        # 设置cookie
        response.set_cookie(
            key=settings.TOKEN_NAME,
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,  # 生产环境应设为True，需要HTTPS
            samesite="lax"
        )

        logger.info(f"用户登录成功: {form_data.username}")
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "username": user.username,
            "email": user.email,
            # "role": user.roles,
            # "is_active": user.is_active,
            # "is_superuser": user.is_superuser,
            "nickname": user.nickname or user.username
        }
    except HTTPException as e:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户登录过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="登录处理过程中发生错误"
        )


@router.post("/logout")
async def logout(response: Response):
    """
    用户登出
    
    Args:
        response: HTTP响应对象
        
    Returns:
        成功消息
    """
    response.delete_cookie(key=settings.TOKEN_NAME)
    return {"status_code": status.HTTP_200_OK, "detail": "登出成功"}


@router.post("/register", response_model=User)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    注册新用户
    
    Args:
        user_data: 用户注册数据
        
    Returns:
        成功消息
        
    Raises:
        HTTPException: 如果用户名已存在或发生其他错误
    """
    try:
        # 查看系统设置中是否允许注册
        if not settings.ALLOW_REGISTER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统不允许注册"
            )
        # 检查用户名是否已存在
        existing_user = await auth.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        # 检查邮箱是否已存在
        existing_user = await auth.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        # 哈希密码
        # hashed_password = auth.get_password_hash(user_data.password)
        # # print(user_data.password,hashed_password)
#
        # plain_password = "123456"
        # hashed = auth.get_password_hash(plain_password)
        # print("验证结果:", auth.verify_password(plain_password, hashed))  # 应返回 True

        logger.info(f"用户注册成功: {user_data.username}")
        # 创建用户
        user = await auth.create_user(db, {
            "username": user_data.username,
            "password": user_data.password,
            "nickname": user_data.nickname or user_data.username,
            # "role": settings.DEFAULT_ROLE,  # 默认角色为普通用户
            "email": user_data.email,
            "avatar": user_data.avatar
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建用户失败"
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册用户时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册处理过程中发生错误"
        )


@router.get("/me")
async def get_me(current_user: User = Depends(auth.get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户，由依赖项提供
        
    Returns:
        当前用户信息
    """
    # print(current_user)
    # # 转字典或json
    # current_user_dict = current_user.model_dump()
    return current_user

# refresh
@router.post("/refresh")
async def refresh(response: Response, db: AsyncSession = Depends(get_db)):
    """
    刷新令牌
    """
    try:
        # 获取当前用户
        current_user = await auth.get_current_user(db)
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": current_user.username},
            expires_delta=access_token_expires
        )
        # 设置cookie
        response.set_cookie(
            key=settings.TOKEN_NAME,
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,  # 生产环境应设为True，需要HTTPS
            samesite="lax"
        )
        return {"status_code": status.HTTP_200_OK, "detail": "刷新成功"}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"刷新令牌时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌处理过程中发生错误"
        )

# 更新用户信息
@router.put("/me")
async def update_user(user_data: UserUpdate, db: AsyncSession = Depends(get_db),current_user: User = Depends(auth.get_current_user)):
    """
    更新当前用户信息
    """
    # 获取当前用户
    current_user = await db.execute(select(DBUser).filter(DBUser.id == current_user.id))
    user = current_user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return await auth.update_user(db, user, user_data)

# 更新用户密码
@router.put("/me/password")
async def update_password(password_data: Dict, db: AsyncSession = Depends(get_db),current_user: User = Depends(auth.get_current_user)):
    """
    更新当前用户密码
    """
    # 通过id及密码获取当前用户
    current_user = await db.execute(select(DBUser).filter(DBUser.id == current_user.id ))
    user = current_user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="验证失败")
    return await auth.update_password(db, user, password_data.get("new_password"))

# 获取用户列表
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    """
    获取所有用户列表
    """
    return await auth.get_users(db)

# 新增权限管理接口
@router.get("/permissions/all", response_model=List[Permission])
async def get_all_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(auth.get_current_superuser),
):
    """获取所有权限"""
    query = select(DBPermission).options(selectinload(DBPermission.group))
    result = await db.execute(query)
    permissions = result.scalars().all()
    return permissions

@router.get("/permission-groups", response_model=List[PermissionGroupWithPermissions])
async def get_permission_groups(
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """获取所有权限分组及其权限"""
    query = select(DBPermissionGroup).options(selectinload(DBPermissionGroup.permissions)).order_by(DBPermissionGroup.sort_order)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/permission-groups", response_model=PermissionGroup)
async def create_permission_group(
    group_in: PermissionGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """创建权限分组"""
    # 检查分组代码是否已存在
    query = select(DBPermissionGroup).where(DBPermissionGroup.code == group_in.code)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限分组代码已存在"
        )

    # 创建新权限分组
    db_group = DBPermissionGroup(
        code=group_in.code,
        name=group_in.name,
        description=group_in.description,
        sort_order=group_in.sort_order,
        icon=group_in.icon
    )
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    return db_group

@router.put("/permission-groups/{group_id}", response_model=PermissionGroup)
async def update_permission_group(
    group_id: int,
    group_in: PermissionGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """更新权限分组"""
    # 获取权限分组
    query = select(DBPermissionGroup).where(DBPermissionGroup.id == group_id)
    result = await db.execute(query)
    db_group = result.scalar_one_or_none()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限分组不存在"
        )

    # 更新权限分组
    if group_in.code is not None:
        db_group.code = group_in.code
    if group_in.name is not None:
        db_group.name = group_in.name
    if group_in.description is not None:
        db_group.description = group_in.description
    if group_in.sort_order is not None:
        db_group.sort_order = group_in.sort_order
    if group_in.icon is not None:
        db_group.icon = group_in.icon

    await db.commit()
    await db.refresh(db_group)
    return db_group

@router.delete("/permission-groups/{group_id}")
async def delete_permission_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """删除权限分组"""
    # 获取权限分组
    query = select(DBPermissionGroup).where(DBPermissionGroup.id == group_id)
    result = await db.execute(query)
    db_group = result.scalar_one_or_none()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限分组不存在"
        )

    # 删除权限分组（会级联删除相关权限）
    await db.delete(db_group)
    await db.commit()
    return {"detail": "权限分组已删除"}

@router.get("/permissions", response_model=Dict[str, List])
async def get_user_permissions(
    current_user: User = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    获取当前用户的权限
    """
    if current_user.is_superuser:
        # 超级用户拥有所有权限
        permissions_query = await db.execute(select(DBPermission))
        all_permissions = permissions_query.scalars().all()
        permissions = [p.code for p in all_permissions]

        roles_query = await db.execute(select(DBRole))
        all_roles = roles_query.scalars().all()
        roles = [r.name for r in all_roles]
    else:
        # 获取用户角色
        roles_query = await db.execute(
            select(DBRole).join(user_role, user_role.c.role_id == DBRole.id)
            .where(user_role.c.user_id == current_user.id)
        )
        user_roles = roles_query.scalars().all()
        roles = [r.name for r in user_roles]

        # 获取用户权限
        permissions = []
        for role in user_roles:
            role_permissions = await db.execute(
                select(DBPermission).join(role_permission, role_permission.c.permission_id == DBPermission.id)
                .where(role_permission.c.role_id == role.id)
            )
            for permission in role_permissions.scalars().all():
                if permission.code not in permissions:
                    permissions.append(permission.code)
    
    return {
        "permissions": permissions,
        "roles": roles
    }


@router.post("/permissions", response_model=Permission)
async def create_permission(
    permission_in: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """创建权限"""
    # 检查权限代码是否已存在
    query = select(DBPermission).where(DBPermission.code == permission_in.code)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限代码已存在"
        )

    # 创建新权限
    db_permission = DBPermission(
        code=permission_in.code,
        name=permission_in.name,
        url=permission_in.url,
        description=permission_in.description,
        group_id=permission_in.group_id
    )
    db.add(db_permission)
    await db.commit()
    await db.refresh(db_permission)

    # 重新查询权限以获取完整的关联数据
    query = select(DBPermission).options(selectinload(DBPermission.group)).where(DBPermission.id == db_permission.id)
    result = await db.execute(query)
    return result.scalar_one()

@router.put("/permissions/{permission_id}", response_model=Permission)
async def update_permission(
    permission_id: int,
    permission_in: PermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """更新权限"""
    # 获取权限
    query = select(DBPermission).where(DBPermission.id == permission_id)
    result = await db.execute(query)
    db_permission = result.scalar_one_or_none()
    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )

    # 检查权限代码是否已存在
    if permission_in.code and permission_in.code != db_permission.code:
        query = select(DBPermission).where(DBPermission.code == permission_in.code)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限代码已存在"
            )

    # 更新权限
    update_data = permission_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_permission, key, value)

    await db.commit()
    await db.refresh(db_permission)

    # 重新查询权限以获取完整的关联数据
    query = select(DBPermission).options(selectinload(DBPermission.group)).where(DBPermission.id == db_permission.id)
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """删除权限"""
    # 获取权限
    query = select(DBPermission).where(DBPermission.id == permission_id)
    result = await db.execute(query)
    db_permission = result.scalar_one_or_none()
    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )

    # 删除权限
    await db.execute(delete(role_permission).where(role_permission.c.permission_id == permission_id))
    await db.delete(db_permission)
    await db.commit()
    return {"detail": "权限已删除"}

# 角色管理接口
@router.get("/roles", response_model=List[Role])
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """获取所有角色"""
    query = select(DBRole).options(
        selectinload(DBRole.permissions).selectinload(DBPermission.group)
    )
    result = await db.execute(query)
    roles = result.scalars().all()
    return roles


@router.post("/roles", response_model=Role)
async def create_role(
        role_in: RoleCreate,
        db: AsyncSession = Depends(get_db),
        current_user: DBUser = Depends(manage_roles),
):
    """创建角色"""
    try:
        # 检查角色名是否已存在
        existing_role = await db.execute(
            select(DBRole).where(DBRole.name == role_in.name))
        if existing_role.scalar_one_or_none():

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名已存在"
            )

        # 创建新角色
        db_role = DBRole(
            name=role_in.name,
            description=role_in.description
        )
        db.add(db_role)
        await db.flush()
        await db.refresh(db_role)

        # 添加权限 - 需要确保权限存在并正确关联
        if role_in.permission_ids:
            # 先获取所有权限
            permissions = await db.execute(
                select(DBPermission).where(DBPermission.id.in_(role_in.permission_ids))
            )
            valid_permissions = permissions.scalars().all()

            # 检查是否有无效权限ID
            if len(valid_permissions) != len(role_in.permission_ids):
                invalid_ids = set(role_in.permission_ids) - {p.id for p in valid_permissions}
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"以下权限ID不存在: {invalid_ids}"
                )

            # 关联权限到角色
            for permission in valid_permissions:
                db_role.permissions.append(permission)

            await db.commit()
            await db.refresh(db_role)

        # 重新查询角色以获取完整的关联数据
        query = select(DBRole).options(
            selectinload(DBRole.permissions).selectinload(DBPermission.group)
        ).where(DBRole.id == db_role.id)
        result = await db.execute(query)
        return result.scalar_one()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建角色时发生错误: {str(e)}")
        raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建角色时发生错误"
        )


@router.put("/roles/{role_id}", response_model=Role)
async def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """更新角色"""
    # 获取角色
    query = select(DBRole).where(DBRole.id == role_id)
    result = await db.execute(query)
    db_role = result.scalar_one_or_none()
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查角色名是否已存在
    if role_in.name and role_in.name != db_role.name:
        query = select(DBRole).where(DBRole.name == role_in.name)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名已存在"
            )
    
    # 更新角色
    update_data = role_in.dict(exclude={"permission_ids"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    # 更新权限
    if role_in.permission_ids is not None:
        # 清除现有权限
        db_role.permissions = []
        
        # 添加新权限
        for permission_id in role_in.permission_ids:
            query = select(DBPermission).where(DBPermission.id == permission_id)
            result = await db.execute(query)
            db_permission = result.scalar_one_or_none()
            if db_permission:
                db_role.permissions.append(db_permission)
    
    await db.commit()
    await db.refresh(db_role)

    # 重新查询角色以获取完整的关联数据
    query = select(DBRole).options(
        selectinload(DBRole.permissions).selectinload(DBPermission.group)
    ).where(DBRole.id == db_role.id)
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_roles),
):
    """删除角色"""
    # 获取角色
    query = select(DBRole).where(DBRole.id == role_id)
    result = await db.execute(query)
    db_role = result.scalar_one_or_none()
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 删除角色
    await db.execute(delete(user_role).where(user_role.c.role_id == role_id))
    await db.delete(db_role)
    await db.commit()
    return {"detail": "角色已删除"}

# 用户角色管理接口
@router.get("/users/{user_id}/roles", response_model=UserWithRoles)
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(auth.get_current_active_user),
):
    """获取用户角色"""
    # 检查权限：用户只能查看自己的角色，或者管理员可以查看所有用户角色
    if current_user.id != user_id and not has_permission(current_user, "user:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能查看自己的角色信息"
        )

    # 获取用户
    # 使用selectin加载策略预先加载roles和permissions的group
    query = select(DBUser).options(
        selectinload(DBUser.roles).selectinload(DBRole.permissions).selectinload(DBPermission.group)
    ).where(DBUser.id == user_id)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return db_user

@router.post("/users/assign-roles", response_model=UserWithRoles)
async def assign_user_roles(
    role_request: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(manage_users),
):
    """分配用户角色"""
    # 获取用户
    query = select(DBUser).where(DBUser.id == role_request.user_id)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 清除现有角色
    db_user.roles = []

    # 添加新角色
    for role_id in role_request.role_ids:
        query = select(DBRole).where(DBRole.id == role_id)
        result = await db.execute(query)
        db_role = result.scalar_one_or_none()
        if db_role:
            db_user.roles.append(db_role)

    await db.commit()
    await db.refresh(db_user)

    # 重新查询用户以获取完整的关联数据
    query = select(DBUser).options(
        selectinload(DBUser.roles).selectinload(DBRole.permissions).selectinload(DBPermission.group)
    ).where(DBUser.id == db_user.id)
    result = await db.execute(query)
    return result.scalar_one()

# 头像上传API
@router.post("/upload-avatar")
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: DBUser = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传用户头像

    Args:
        avatar: 头像文件
        current_user: 当前用户
        db: 数据库会话

    Returns:
        包含头像URL的响应
    """
    try:
        # 验证文件类型
        if not avatar.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能上传图片文件"
            )

        # 验证文件大小（5MB限制）
        if avatar.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小不能超过10MB"
            )

        # 创建上传目录
        upload_dir = Path("static/avatars")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        file_extension = Path(avatar.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await avatar.read()
            buffer.write(content)

        # 生成访问URL
        avatar_url = f"/static/avatars/{unique_filename}"

        logger.info(f"用户 {current_user.username} 上传头像成功: {avatar_url}")

        return {
            "message": "头像上传成功",
            "avatar_url": avatar_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"头像上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="头像上传失败"
        )

# 获取用户列表
