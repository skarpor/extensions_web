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
from core.logger import auth_logger
from db.session import get_db
from models.user import User, Permission, PermissionGroup
from schemas.user import UserCreate


logger = auth_logger

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

        # 获取用户的所有权限
        user_permissions = get_user_permissions(user)

        # 如果是超级用户，直接通过
        if "*" in user_permissions:
            return user

        for permission in self.required_permissions:
            if permission not in user_permissions:
                logger.warning(f"用户 {user.username} 缺少所需权限: {permission}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission {permission} is required"
                )
        return user
def require_permissions(*permissions: str):
    """权限验证装饰器 - 要求用户具有指定权限"""
    return PermissionChecker(list(permissions))

def require_any_permission(*permissions: str):
    """权限验证装饰器 - 要求用户具有任意一个权限"""
    class AnyPermissionChecker:
        def __init__(self, required_permissions: List[str]):
            self.required_permissions = required_permissions

        def __call__(self, user: User = Depends(get_current_active_user)) -> User:
            # 超级用户拥有所有权限
            if user.is_superuser:
                return user

            # 获取用户的所有权限
            user_permissions = get_user_permissions(user)

            # 如果是超级用户，直接通过
            if "*" in user_permissions:
                return user

            # 检查是否具有任意一个权限
            for permission in self.required_permissions:
                if permission in user_permissions:
                    return user

            logger.warning(f"用户 {user.username} 缺少所需权限: {self.required_permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下任意一个权限: {', '.join(self.required_permissions)}"
            )

    return AnyPermissionChecker(list(permissions))

def get_user_permissions(user: User) -> List[str]:
    """获取用户的所有权限代码列表"""
    if user.is_superuser:
        # 超级用户拥有所有权限，这里返回一个特殊标识
        return ["*"]  # 特殊标识，表示拥有所有权限

    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.code)

    return list(permissions)

def has_permission(user: User, permission: str) -> bool:
    """检查用户是否具有指定权限"""
    if user.is_superuser:
        return True

    user_permissions = get_user_permissions(user)
    return permission in user_permissions

def has_role(user: User, role: str) -> bool:
    """检查用户是否具有指定角色"""
    if user.is_superuser:
        return True
    return role in user.roles

# ==================== 权限验证装饰器 ====================



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

async def create_user(db: AsyncSession, user_in: Dict[str, Any], assign_default_role: bool = True) -> User:
    """创建用户"""
    from models.user import Role as DBRole

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
    await db.flush()  # 获取用户ID

    # 为新用户分配默认角色
    if assign_default_role:
        # 查找"普通用户"角色
        default_role_query = select(DBRole).where(DBRole.name == settings.DEFAULT_ROLE)
        result = await db.execute(default_role_query)
        default_role = result.scalar_one_or_none()

        if default_role:
            # 使用关联表直接插入用户-角色关系
            from models.user import user_role
            await db.execute(
                user_role.insert().values(
                    user_id=user.id,
                    role_id=default_role.id
                )
            )
            logger.info(f"为新用户 {user.username} 分配默认角色: 普通用户")
        else:
            logger.warning("未找到默认角色'普通用户'，请检查角色初始化")

    await db.commit()
    await db.refresh(user)
    return user

async def update_user(db: AsyncSession, db_obj: User, obj_in: UserCreate) -> User:
    """更新用户"""
    user = db_obj

    # 调试信息
    logger.info(f"更新用户信息: {user.username}")
    logger.info(f"输入数据: username={obj_in.username}, nickname={obj_in.nickname}, email={obj_in.email}")
    logger.info(f"头像字段: hasattr={hasattr(obj_in, 'avatar')}, avatar={getattr(obj_in, 'avatar', 'NOT_FOUND')}")

    user.username = obj_in.username
    user.nickname = obj_in.nickname
    user.email = obj_in.email

    # 更新头像字段
    if hasattr(obj_in, 'avatar') and obj_in.avatar is not None:
        logger.info(f"更新头像: {obj_in.avatar}")
        user.avatar = obj_in.avatar
    else:
        logger.info("头像字段为空或不存在，不更新头像")

    # user.password = get_password_hash(obj_in.password)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"用户更新完成，最终头像: {user.avatar}")
    return user
async def update_password(db: AsyncSession, db_obj: User, new_password: str) -> User:
    """更新用户密码"""
    user = db_obj
    user.hashed_password = get_password_hash(new_password)
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
    result = await db.execute(select(PermissionGroup))
    if result.scalars().first() is not None:
        return

    # 创建权限分组
    permission_groups_data = [
        {
            "code": "system_management",
            "name": "系统管理",
            "description": "系统配置和管理相关权限",
            "sort_order": 1,
            "icon": "Setting",
            "permissions": [
                {"code": "system:manage", "name": "系统管理", "url": "/api/v1/settings", "description": "可以管理系统配置"},
                {"code": "system:stats", "name": "系统统计", "url": "/api/v1/dashboard/stats", "description": "可以查看系统统计信息"},
                {"code": "system:monitor", "name": "系统监控", "url": "/api/v1/dashboard/system", "description": "可以查看系统监控信息"},
                {"code": "system:logs", "name": "日志管理", "url": "/api/v1/log", "description": "可以查看和管理系统日志"},
                {"code": "system:database", "name": "数据库管理", "url": "/api/v1/db", "description": "可以管理数据库"},
            ]
        },
        {
            "code": "user_management",
            "name": "用户管理",
            "description": "用户账户管理相关权限",
            "sort_order": 2,
            "icon": "User",
            "permissions": [
                {"code": "user:create", "name": "创建用户", "url": "/api/v1/users", "description": "可以创建新用户"},
                {"code": "user:read", "name": "查看用户", "url": "/api/v1/users", "description": "可以查看用户信息"},
                {"code": "user:update", "name": "更新用户", "url": "/api/v1/users/{id}", "description": "可以更新用户信息"},
                {"code": "user:delete", "name": "删除用户", "url": "/api/v1/users/{id}", "description": "可以删除用户"},
                {"code": "user:profile", "name": "个人资料", "url": "/api/v1/users/me", "description": "可以查看和修改个人资料"},
            ]
        },
        {
            "code": "role_management",
            "name": "角色权限管理",
            "description": "角色和权限管理相关权限",
            "sort_order": 3,
            "icon": "UserFilled",
            "permissions": [
                {"code": "role:manage", "name": "角色管理", "url": "/api/v1/auth/roles", "description": "可以管理角色和权限分配"},
                {"code": "role:create", "name": "创建角色", "url": "/api/v1/auth/roles", "description": "可以创建新角色"},
                {"code": "role:read", "name": "查看角色", "url": "/api/v1/auth/roles", "description": "可以查看角色信息"},
                {"code": "role:update", "name": "更新角色", "url": "/api/v1/auth/roles/{id}", "description": "可以更新角色信息"},
                {"code": "role:delete", "name": "删除角色", "url": "/api/v1/auth/roles/{id}", "description": "可以删除角色"},
                {"code": "role:assign", "name": "分配角色", "url": "/api/v1/auth/users/assign-roles", "description": "可以为用户分配角色"},
            ]
        },
        {
            "code": "extension_management",
            "name": "扩展管理",
            "description": "扩展插件管理相关权限",
            "sort_order": 4,
            "icon": "Grid",
            "permissions": [
                {"code": "extension:manage", "name": "扩展管理", "url": "/api/v1/extensions", "description": "可以管理扩展"},
                {"code": "extension:upload", "name": "上传扩展", "url": "/api/v1/extensions/upload", "description": "可以上传扩展"},
                {"code": "extension:delete", "name": "删除扩展", "url": "/api/v1/extensions/{id}", "description": "可以删除扩展"},
                {"code": "extension:update", "name": "更新扩展", "url": "/api/v1/extensions/{id}", "description": "可以更新扩展"},
                {"code": "extension:view", "name": "查看扩展", "url": "/api/v1/extensions", "description": "可以查看扩展"},
                {"code": "extension:config", "name": "配置扩展", "url": "/api/v1/extensions/{id}/config", "description": "可以配置扩展"},
                {"code": "extension:execute", "name": "执行扩展", "url": "/api/v1/extensions/{id}/execute", "description": "可以执行扩展"},
            ]
        },
        {
            "code": "file_management",
            "name": "文件管理",
            "description": "文件上传下载管理相关权限",
            "sort_order": 5,
            "icon": "Folder",
            "permissions": [
                {"code": "file:manage", "name": "文件管理", "url": "/api/v1/files", "description": "可以管理文件"},
                {"code": "file:upload", "name": "上传文件", "url": "/api/v1/files/upload", "description": "可以上传文件"},
                {"code": "file:download", "name": "下载文件", "url": "/api/v1/files/download", "description": "可以下载文件"},
                {"code": "file:delete", "name": "删除文件", "url": "/api/v1/files/{id}", "description": "可以删除文件"},
                {"code": "file:view", "name": "查看文件", "url": "/api/v1/files", "description": "可以查看文件列表"},
            ]
        },
        {
            "code": "chat_management",
            "name": "聊天管理",
            "description": "聊天功能管理相关权限",
            "sort_order": 6,
            "icon": "ChatDotRound",
            "permissions": [
                {"code": "chat:create", "name": "创建聊天", "url": "/api/v1/chat", "description": "可以创建新聊天"},
                {"code": "chat:read", "name": "查看聊天", "url": "/api/v1/chat", "description": "可以查看聊天信息"},
                {"code": "chat:update", "name": "更新聊天", "url": "/api/v1/chat/{id}", "description": "可以更新聊天信息"},
                {"code": "chat:delete", "name": "删除聊天", "url": "/api/v1/chat/{id}", "description": "可以删除聊天"},
                {"code": "chat:message", "name": "发送消息", "url": "/api/v1/chat/{id}/messages", "description": "可以发送聊天消息"},
                {"code": "chat:room", "name": "聊天室管理", "url": "/api/v1/ws/rooms", "description": "可以管理聊天室"},
            ]
        },
        {
            "code": "scheduler_management",
            "name": "调度器管理",
            "description": "定时任务调度管理相关权限",
            "sort_order": 7,
            "icon": "Timer",
            "permissions": [
                {"code": "scheduler:create", "name": "创建任务", "url": "/api/v1/scheduler/add-cron-job", "description": "可以创建定时任务"},
                {"code": "scheduler:read", "name": "查看任务", "url": "/api/v1/scheduler/api/jobs", "description": "可以查看定时任务"},
                {"code": "scheduler:update", "name": "更新任务", "url": "/api/v1/scheduler/update-job", "description": "可以更新定时任务"},
                {"code": "scheduler:delete", "name": "删除任务", "url": "/api/v1/scheduler/remove-job", "description": "可以删除定时任务"},
                {"code": "scheduler:execute", "name": "执行任务", "url": "/api/v1/scheduler/run-job", "description": "可以手动执行任务"},
            ]
        },
        {
            "code": "qrfile_management",
            "name": "二维码文件管理",
            "description": "二维码文件处理相关权限",
            "sort_order": 8,
            "icon": "QrCode",
            "permissions": [
                {"code": "qrfile:create", "name": "生成二维码", "url": "/api/v1/qrfile/generate-qrcodes", "description": "可以生成二维码"},
                {"code": "qrfile:serialize", "name": "序列化文件", "url": "/api/v1/qrfile/serialize-file", "description": "可以序列化文件为二维码"},
                {"code": "qrfile:restore", "name": "恢复文件", "url": "/api/v1/qrfile/scan-restore", "description": "可以从二维码恢复文件"},
                {"code": "qrfile:download", "name": "下载文件", "url": "/api/v1/qrfile/download", "description": "可以下载恢复的文件"},
                {"code": "qrfile:manage", "name": "管理二维码文件", "url": "/api/v1/qrfile/files", "description": "可以管理二维码文件"},
            ]
        },
        {
            "code": "help_management",
            "name": "帮助文档管理",
            "description": "帮助文档和示例管理相关权限",
            "sort_order": 9,
            "icon": "QuestionFilled",
            "permissions": [
                {"code": "help:view", "name": "查看帮助", "url": "/api/v1/help/view", "description": "可以查看帮助文档"},
                {"code": "help:upload", "name": "上传文档", "url": "/api/v1/help/upload", "description": "可以上传帮助文档"},
                {"code": "help:delete", "name": "删除文档", "url": "/api/v1/help/delete", "description": "可以删除帮助文档"},
                {"code": "help:download", "name": "下载文档", "url": "/api/v1/help/download", "description": "可以下载帮助文档"},
                {"code": "help:list", "name": "文档列表", "url": "/api/v1/help/list", "description": "可以查看文档列表"},
            ]
        },
        {
            "code": "danmu_management",
            "name": "弹幕管理",
            "description": "弹幕功能管理相关权限",
            "sort_order": 10,
            "icon": "VideoPlay",
            "permissions": [
                {"code": "danmu:send", "name": "发送弹幕", "url": "/api/v1/danmu/send_danmu", "description": "可以发送弹幕"},
                {"code": "danmu:view", "name": "查看弹幕", "url": "/api/v1/danmu", "description": "可以查看弹幕页面"},
                {"code": "danmu:websocket", "name": "弹幕WebSocket", "url": "/api/v1/danmu/ws", "description": "可以连接弹幕WebSocket"},
            ]
        },
        {
            "code": "extension_management",
            "name": "扩展管理",
            "description": "扩展插件管理相关权限",
            "sort_order": 4,
            "icon": "Grid",
            "permissions": [
                {"code": "extension:manage", "name": "扩展管理", "url": "/api/v1/extension/manage", "description": "可以管理扩展"},
                {"code": "extension:upload", "name": "上传扩展", "url": "/api/v1/extension/upload", "description": "可以上传扩展"},
                {"code": "extension:delete", "name": "删除扩展", "url": "/api/v1/extension/delete", "description": "可以删除扩展"},
                {"code": "extension:update", "name": "更新扩展", "url": "/api/v1/extension/update", "description": "可以更新扩展"},
                {"code": "extension:view", "name": "查看扩展", "url": "/api/v1/extension/view", "description": "可以查看扩展"},
            ]
        },
        {
            "code": "file_management",
            "name": "文件管理",
            "description": "文件上传下载管理相关权限",
            "sort_order": 5,
            "icon": "Folder",
            "permissions": [
                {"code": "file:manage", "name": "文件管理", "url": "/api/v1/file/manage", "description": "可以管理文件"},
                {"code": "file:upload", "name": "上传文件", "url": "/api/v1/file/upload", "description": "可以上传文件"},
                {"code": "file:delete", "name": "删除文件", "url": "/api/v1/file/delete", "description": "可以删除文件"},
                {"code": "file:view", "name": "查看文件", "url": "/api/v1/file/view", "description": "可以查看文件"},
                {"code": "file:download", "name": "下载文件", "url": "/api/v1/file/download", "description": "可以下载文件"},
            ]
        },
        {
            "code": "chat_management",
            "name": "聊天管理",
            "description": "聊天功能管理相关权限",
            "sort_order": 6,
            "icon": "ChatDotRound",
            "permissions": [
                {"code": "chat:create", "name": "创建聊天", "url": "/api/v1/chat/create", "description": "可以创建新聊天"},
                {"code": "chat:read", "name": "查看聊天", "url": "/api/v1/chat/read", "description": "可以查看聊天信息"},
                {"code": "chat:update", "name": "更新聊天", "url": "/api/v1/chat/update", "description": "可以更新聊天信息"},
                {"code": "chat:delete", "name": "删除聊天", "url": "/api/v1/chat/delete", "description": "可以删除聊天"},
            ]
        },
        {
            "code": "message_management",
            "name": "消息管理",
            "description": "消息通知管理相关权限",
            "sort_order": 7,
            "icon": "Message",
            "permissions": [
                {"code": "message:create", "name": "创建消息", "url": "/api/v1/message/create", "description": "可以创建新消息"},
                {"code": "message:read", "name": "查看消息", "url": "/api/v1/message/read", "description": "可以查看消息信息"},
                {"code": "message:update", "name": "更新消息", "url": "/api/v1/message/update", "description": "可以更新消息信息"},
                {"code": "message:delete", "name": "删除消息", "url": "/api/v1/message/delete", "description": "可以删除消息"},
            ]
        },
        {
            "code": "markdown_management",
            "name": "markdown文档管理",
            "description": "markdown文档管理相关权限",
            "sort_order": 8,
            "icon": "Markdown",
            "permissions": [
                {"code": "message:create", "name": "创建消息", "url": "/api/v1/message/create", "description": "可以markdown文档"},
                {"code": "message:read", "name": "查看消息", "url": "/api/v1/message/read", "description": "可以查看markdown文档"},
                {"code": "message:update", "name": "更新消息", "url": "/api/v1/message/update", "description": "可以更新markdown文档"},
                {"code": "markdown:delete", "name": "删除文档", "url": "/api/v1/message/delete", "description": "可以删除markdown文档"},
            ]
        },
    ]

    # 创建分组和权限
    for group_data in permission_groups_data:
        # 检查权限分组是否已存在
        existing_group_query = select(PermissionGroup).where(PermissionGroup.code == group_data["code"])
        existing_group_result = await db.execute(existing_group_query)
        permission_group = existing_group_result.scalar_one_or_none()

        if not permission_group:
            # 创建权限分组
            permission_group = PermissionGroup(
                code=group_data["code"],
                name=group_data["name"],
                description=group_data["description"],
                sort_order=group_data["sort_order"],
                icon=group_data["icon"]
            )
            db.add(permission_group)
            await db.flush()  # 获取分组ID

        # 创建该分组下的权限
        for perm_data in group_data["permissions"]:
            # 检查权限是否已存在
            existing_perm_query = select(Permission).where(Permission.code == perm_data["code"])
            existing_perm_result = await db.execute(existing_perm_query)
            existing_permission = existing_perm_result.scalar_one_or_none()

            if not existing_permission:
                permission = Permission(
                    code=perm_data["code"],
                    name=perm_data["name"],
                    url=perm_data["url"],
                    description=perm_data["description"],
                    group_id=permission_group.id
                )
                db.add(permission)

    logger.info("权限分组和权限初始化完成")
    await db.commit()

async def init_default_roles(db: AsyncSession):
    """初始化默认角色"""
    from models.user import Role as DBRole

    # 检查是否已初始化
    result = await db.execute(select(DBRole))
    if result.scalars().first() is not None:
        return

    # 获取所有权限
    permissions_result = await db.execute(select(Permission))
    all_permissions = permissions_result.scalars().all()

    # 创建权限映射
    permission_map = {p.code: p for p in all_permissions}

    # 定义默认角色
    default_roles_data = [
        {
            "name": "超级管理员",
            "description": "系统超级管理员，拥有所有权限",
            "permissions": [p.code for p in all_permissions]  # 所有权限
        },
        {
            "name": "管理员",
            "description": "系统管理员，拥有大部分管理权限",
            "permissions": [
                # 用户管理
                "user:read", "user:update", "user:create",
                # 角色管理
                "role:read", "role:create", "role:update", "role:assign",
                # 扩展管理
                "extension:view", "extension:manage", "extension:config",
                # 文件管理
                "file:view", "file:upload", "file:download", "file:manage",
                # 聊天管理
                "chat:create", "chat:read", "chat:message", "chat:room",
                # 系统监控
                "system:stats", "system:monitor", "system:logs",
                # 调度器
                "scheduler:read", "scheduler:create", "scheduler:update",
                # 帮助文档
                "help:view", "help:upload", "help:list",
            ]
        },
        {
            "name": "普通用户",
            "description": "普通用户，拥有基础功能权限",
            "permissions": [
                # 个人资料
                "user:profile",
                # 基础扩展功能
                "extension:view", "extension:execute",
                # 基础文件功能
                "file:view", "file:upload", "file:download",
                # 基础聊天功能
                "chat:create", "chat:read", "chat:message",
                # 基础二维码功能
                "qrfile:create", "qrfile:serialize", "qrfile:restore", "qrfile:download",
                # 帮助文档查看
                "help:view", "help:list",
                # 弹幕功能
                "danmu:send", "danmu:view", "danmu:websocket",
            ]
        },
        {
            "name": "访客",
            "description": "访客用户，仅拥有查看权限",
            "permissions": [
                # 基础查看权限
                "extension:view",
                "file:view",
                "help:view", "help:list",
                "danmu:view",
            ]
        }
    ]

    # 创建角色
    for role_data in default_roles_data:
        # 检查角色是否已存在
        existing_role_query = select(DBRole).where(DBRole.name == role_data["name"])
        existing_role_result = await db.execute(existing_role_query)
        db_role = existing_role_result.scalar_one_or_none()

        if not db_role:
            # 创建角色
            db_role = DBRole(
                name=role_data["name"],
                description=role_data["description"]
            )
            db.add(db_role)
            await db.commit()  # 先提交角色
            await db.refresh(db_role)

            # 分配权限 - 使用关联表直接插入
            from models.user import role_permission
            for permission_code in role_data["permissions"]:
                if permission_code in permission_map:
                    permission = permission_map[permission_code]
                    # 检查关联是否已存在
                    existing_relation = await db.execute(
                        select(role_permission).where(
                            role_permission.c.role_id == db_role.id,
                            role_permission.c.permission_id == permission.id
                        )
                    )
                    if not existing_relation.scalar_one_or_none():
                        # 插入角色-权限关联
                        await db.execute(
                            role_permission.insert().values(
                                role_id=db_role.id,
                                permission_id=permission.id
                            )
                        )

            # 提交权限分配
            await db.commit()

    logger.info("默认角色初始化完成")

async def get_current_user_from_token(token: str) -> Optional[User]:
    """从token获取当前用户（用于WebSocket认证）"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    from db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        return user
async def init_users(db: AsyncSession):
    """初始化系统权限数据"""
    # 检查是否已初始化
    result = await db.execute(select(User))
    if result.scalars().first() is not None:
        return

    # 系统预定义权限
    users = [
        User(
            username="zxy",
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
