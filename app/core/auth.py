"""
认证模块

提供用户认证和授权功能。
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from config import JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, token_name
from app.models.user import User, UserInDB
from app.core.database import Database

# 密码上下文
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token",auto_error=False)
# oauth2_scheme从config中获取
from config import pwd_context,oauth2_scheme
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    获取密码哈希值
    
    Args:
        password: 明文密码
        
    Returns:
        密码哈希值
    """
    return pwd_context.hash(password)

def authenticate_user(db: Database, username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    认证用户
    
    Args:
        db: 数据库实例
        username: 用户名
        password: 密码
        
    Returns:
        用户信息，如果认证失败则返回None
    """
    user = db.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    
    # 更新最后登录时间
    db.update_user_last_login(user["id"])
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 令牌数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme),session: AsyncSession = Depends(get_db),) -> User:
    """
    获取当前用户
    
    Args:
        token: JWT令牌
        
    Returns:
        当前用户
        
    Raises:
        HTTPException: 如果认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # 从应用状态获取数据库实例
    from fastapi import Request
    import inspect
    
    # 获取当前请求的上下文
    frame = inspect.currentframe()
    while frame:
        if 'request' in frame.f_locals:
            request = frame.f_locals['request']
            if hasattr(request, 'app') and hasattr(request.app, 'state') and hasattr(request.app.state, 'db'):
                # session是AsyncSession，需要使用session.execute()
                db=request.app.state.db
                user = db.get_user_by_username(username)
                # user = session.execute(select(User).filter(User.username == username)).scalar_one_or_none()
                if user is None:
                    raise credentials_exception

                return User(
                    id=user["id"],
                    username=user["username"],
                    nickname=user["nickname"],
                    role=user["role"],
                    email=user["email"],
                    # avatar=user["avatar"]
                )
        frame = frame.f_back
    
    # 如果无法获取数据库实例，抛出异常
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="无法获取数据库连接"
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前活跃用户
        
    Raises:
        HTTPException: 如果用户被禁用
    """
    # 这里可以添加检查用户是否被禁用的逻辑
    return current_user

def check_permission(session: AsyncSession, user: User, resource: str, action: str) -> bool:
    """
    检查用户权限
    
    Args:
        db: 数据库实例
        user: 用户
        resource: 资源
        action: 操作
        
    Returns:
        是否有权限
    """
    # 查询用户角色
    user_role = session.execute(select(User.role).filter(User.id == user.id)).scalar_one_or_none()
    # 查询资源
    return None

def require_permission(resource: str, action: str,):
    """
    要求权限装饰器
    
    Args:
        resource: 资源
        action: 操作
        
    Returns:
        依赖函数
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_db)
    ) -> User:
        # 从应用状态获取数据库实例
        import inspect
        from fastapi import Request
        
        # 获取当前请求的上下文
        frame = inspect.currentframe()
        while frame:
            if 'request' in frame.f_locals:
                request = frame.f_locals['request']
                if not check_permission(session, current_user, resource, action):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Permission denied"
                    )
                return current_user
            frame = frame.f_back
        
        # 如果无法获取数据库实例，抛出异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法获取数据库连接"
        )
    
    return permission_dependency


