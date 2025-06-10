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

from new_app.core.config import settings
from new_app.core.logger import get_logger
from new_app.db.session import get_db
from new_app.models.user import User


logger = get_logger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
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
        try:
            user_id = int(subject)
            user = await crud_user.get(db, id=user_id)
        except (ValueError, TypeError):
            # 如果不是ID，则尝试作为用户名查询
            user = await crud_user.get_by_username(db, username=subject)
        
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