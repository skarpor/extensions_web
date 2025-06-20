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

from config import settings
from core.logger import get_logger
from db.session import get_db
from models.user import User, Permission
from schemas.user import UserCreate


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
    return pwd_context.hash(password.strip())

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
    # 检查用户是否具有指定权限,权限在角色中
    for role in user.roles:
        if permission in role.permissions:
            return True
    return False

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"用户{username}不存在！")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=f"用户名或密码错误！")
    user.last_login=datetime.now()
    db.add(user)
    await db.commit()
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

async def create_user(db: AsyncSession, user_in: Dict[str, Any]) -> User:
    """创建用户"""
    if isinstance(user_in, dict):
        # 如果是字典，直接使用
        user_data = user_in
    else:
        # 如果是 UserCreate 对象，转换为字典
        user_data = user_in.model_dump()
    
    # 确保密码字段被正确处理
    if "password" in user_data:
        hashed_password = get_password_hash(user_data.pop("password"))
        user_data["hashed_password"] = hashed_password
    
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user(db: AsyncSession, db_obj: User, obj_in: UserCreate) -> User:
    """更新用户"""
    user = db_obj
    user.username = obj_in.username
    user.nickname = obj_in.nickname
    user.email = obj_in.email
    # user.password = get_password_hash(obj_in.password)
    db.add(user)
    await db.commit()
    return user
async def update_password(db: AsyncSession, db_obj: User, obj_in: UserCreate) -> User:
    """更新用户密码"""
    user = db_obj
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

    # 系统预定义权限,并非全部会用到
    permissions = [
        Permission(code="system:manage", name="系统管理",url="/api/v1/system/manage", description="可以管理系统配置"),
        Permission(code="extension:manage", name="扩展管理",url="/api/v1/extension/manage", description="可以管理扩展"),
        Permission(code="extension:upload", name="上传扩展",url="/api/v1/extension/upload", description="可以上传扩展"),
        Permission(code="extension:delete", name="删除扩展",url="/api/v1/extension/delete", description="可以删除扩展"),
        Permission(code="extension:update", name="更新扩展",url="/api/v1/extension/update", description="可以更新扩展"),
        Permission(code="extension:view", name="查看扩展",url="/api/v1/extension/view", description="可以查看扩展"),
# 文件管理
        Permission(code="file:manage", name="文件管理",url="/api/v1/file/manage", description="可以管理文件"),
        Permission(code="file:upload", name="上传文件",url="/api/v1/file/upload", description="可以上传文件"),
        Permission(code="file:delete", name="删除文件",url="/api/v1/file/delete", description="可以删除文件"),
        Permission(code="file:view", name="查看文件",url="/api/v1/file/view", description="可以查看文件"),
        Permission(code="file:download", name="下载文件",url="/api/v1/file/download", description="可以下载文件"),
        
        # 用户管理
        Permission(code="user:create", name="创建用户",url="/api/v1/user/create", description="可以创建新用户"),
        Permission(code="user:read", name="查看用户",url="/api/v1/user/read", description="可以查看用户信息"),
        Permission(code="user:update", name="更新用户",url="/api/v1/user/update", description="可以更新用户信息"),
        Permission(code="user:delete", name="删除用户",url="/api/v1/user/delete", description="可以删除用户"),
        Permission(code="role:manage", name="角色管理",url="/api/v1/role/manage", description="可以管理角色和权限分配"),
    # 角色管理
        Permission(code="role:create", name="创建角色",url="/api/v1/role/create", description="可以创建新角色"),
        Permission(code="role:read", name="查看角色",url="/api/v1/role/read", description="可以查看角色信息"),
        Permission(code="role:update", name="更新角色",url="/api/v1/role/update", description="可以更新角色信息"),
        Permission(code="role:delete", name="删除角色",url="/api/v1/role/delete", description="可以删除角色"),
    # 聊天 
        Permission(code="chat:create", name="创建聊天",url="/api/v1/chat/create", description="可以创建新聊天"),
        Permission(code="chat:read", name="查看聊天",url="/api/v1/chat/read", description="可以查看聊天信息"),
        Permission(code="chat:update", name="更新聊天",url="/api/v1/chat/update", description="可以更新聊天信息"),
        Permission(code="chat:delete", name="删除聊天",url="/api/v1/chat/delete", description="可以删除聊天"),
    # 消息
        Permission(code="message:create", name="创建消息",url="/api/v1/message/create", description="可以创建新消息"),
        Permission(code="message:read", name="查看消息",url="/api/v1/message/read", description="可以查看消息信息"),
        Permission(code="message:update", name="更新消息",url="/api/v1/message/update", description="可以更新消息信息"),
        Permission(code="message:delete", name="删除消息",url="/api/v1/message/delete", description="可以删除消息"),
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
        User(
            username="tyy",
            nickname="唐洋洋",
            email="tyy@666.com",
            hashed_password=get_password_hash("123"),
            is_active=True,
            is_superuser=True,
        ),
        User(
            username="admin",
            nickname="管理员",
            email="admin@666.com",
            hashed_password=get_password_hash("123"),
            is_active=True,
            is_superuser=True,
        ),
    ]

    db.add_all(users)
    logger.info("用户初始化完成")
    await db.commit()
