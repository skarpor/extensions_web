"""
认证模块，提供用户认证和权限管理功能
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from new_app.core.config import settings
from new_app.core.logger import get_logger
from new_app.db.session import get_db
from new_app.models.user import User, Permission
from new_app.schemas.user import UserCreate


logger = get_logger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

ALGORITHM = "HS256"

class AuthError(Exception):
    """认证错误基类"""
    pass

class InvalidCredentialsError(AuthError):
    """无效的凭证"""
    pass

class InactiveUserError(AuthError):
    """用户未激活"""
    pass

class PermissionDeniedError(AuthError):
    """权限不足"""
    pass

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_access_token(
    data: Optional[dict] = None, 
    expires_delta: Optional[timedelta] = None,
    subject: Optional[Union[str, int]] = None
) -> str:
    """
    创建访问令牌
    
    参数:
        data: 要编码的数据字典
        expires_delta: 过期时间增量
        subject: 令牌主题(通常是用户ID或用户名)
    
    返回:
        JWT令牌字符串
    """
    to_encode = data.copy() if data else {}
    
    # 处理subject参数
    if subject is not None:
        to_encode["sub"] = str(subject)
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        
        # 尝试将subject解析为用户ID
        user = await get_user_by_username(db, username=subject)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

class RoleChecker:
    """角色检查器"""
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        # 超级用户拥有所有角色
        if user.is_superuser:
            return user
            
        for role in self.required_roles:
            if role not in user.roles:
                logger.warning(f"用户 {user.username} 缺少所需角色: {role}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {role} is required"
                )
        return user

class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        # 超级用户拥有所有权限
        if user.is_superuser:
            return user
            
        for permission in self.required_permissions:
            if permission not in user.permissions:
                logger.warning(f"用户 {user.username} 缺少所需权限: {permission}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission {permission} is required"
                )
        return user

def has_permission(user: User, permission: str) -> bool:
    """检查用户是否具有指定权限"""
    if user.is_superuser:
        return True
    return permission in user.permissions

def has_role(user: User, role: str) -> bool:
    """检查用户是否具有指定角色"""
    if user.is_superuser:
        return True
    return role in user.roles

def get_user_info(user: User) -> Dict[str, Any]:

    """获取用户信息"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "roles": user.roles,
        "permissions": user.permissions,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    } 
async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """验证用户凭证,不是邮箱，是账号密码"""
    user = await db.execute(select(User).where(User.username == username))
    user = user.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    user = await db.execute(select(User).where(User.email == email))
    return user.scalars().one_or_none()
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    user = await db.execute(select(User).where(User.username == username))
    return user.scalars().one_or_none()

async def get_user_by_id(db: AsyncSession, id: int) -> Optional[User]:
    """根据ID获取用户"""
    user = await db.execute(select(User).where(User.id == id))
    return user.scalars().one_or_none()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """创建用户"""
    user = User(**user_in.model_dump())
    db.add(user)
    await db.commit()
    return user

async def update_user(db: AsyncSession, db_obj: User, obj_in: UserCreate) -> User:
    """更新用户"""
    user = db_obj
    user.username = obj_in.username
    user.email = obj_in.email
    user.password = get_password_hash(obj_in.password)
    db.add(user)
    await db.commit()
    return user

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """获取用户列表"""
    users = await db.execute(select(User).offset(skip).limit(limit))
    return users.scalars().all()

async def delete_user(db: AsyncSession, user: User) -> None:
    """删除用户"""
    await db.delete(user)
    await db.commit()


# 通常在数据库迁移脚本或应用启动时执行
async def init_permissions(db: AsyncSession):
    """初始化系统权限数据"""
    # 检查是否已初始化
    result = await db.execute(select(Permission))
    if result.scalars().first() is not None:
        return

    # 系统预定义权限
    permissions = [
        Permission(code="user:create", name="创建用户", description="可以创建新用户"),
        Permission(code="user:read", name="查看用户", description="可以查看用户信息"),
        Permission(code="user:update", name="更新用户", description="可以更新用户信息"),
        Permission(code="user:delete", name="删除用户", description="可以删除用户"),
        Permission(code="role:manage", name="角色管理", description="可以管理角色和权限分配"),
    ]

    db.add_all(permissions)
    logger.info("权限初始化完成")
    await db.commit()
async def init_users(db: AsyncSession):
    """初始化系统权限数据"""
    # 检查是否已初始化
    result = await db.execute(select(User))
    if result.scalars().first() is not None:
        return

    # 系统预定义权限
    users = [
        User(
            username="zxc",
            nickname="张新宇",
            email="123@666.com",
            hashed_password=get_password_hash("123"),
            is_active=True,
            is_superuser=True,
        ),
    ]

    db.add_all(users)
    logger.info("用户初始化完成")
    await db.commit()
