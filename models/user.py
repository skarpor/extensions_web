"""
用户模型模块
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
# 用户-角色关联表(多对多)
user_role = Table(
    'user_role',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
)

# 角色-权限关联表(多对多)
role_permission = Table(
    'role_permission',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
)

class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)  # 允许测试时为空
    nickname = Column(String(50), unique=False)  # 允许测试时为空
    email = Column(String(100), unique=True, index=True)  # 允许测试时为空
    hashed_password = Column(String(100))  # 允许测试时为空
    avatar = Column(String(255), nullable=True)  # 头像
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, default=datetime.now,nullable=True)

    # 角色和权限
    # roles = Column(JSON, default=list)  # 用户角色列表
    # permissions = Column(JSON, default=list)  # 用户权限列表
    roles = relationship("Role", secondary=user_role, back_populates="users")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 用户设置
    # settings = Column(JSON, default=dict)  # 用户个性化设置
    
    # 用户配置
    # config = Column(JSON, default=dict)  # 用户配置信息
    
    # 关联关系
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    qr_files = relationship("QRFile", back_populates="user", cascade="all, delete-orphan")
    extensions = relationship("Extension", back_populates="creator", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    chat_rooms = relationship("ChatRoom", foreign_keys="ChatRoom.created_by", back_populates="creator")
    chat_room_memberships = relationship("ChatRoomMember", back_populates="user")
    sent_messages = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender")
    received_messages = relationship("ChatMessage", foreign_keys="ChatMessage.receiver_id", back_populates="receiver")

    # def __init__(self, **kwargs):
    #     """初始化用户实例"""
    #     super().__init__(**kwargs)
    #     self.username = kwargs.get("username", f"user_{kwargs.get('id', 0)}")
    #     self.email = kwargs.get("email", f"user_{kwargs.get('id', 0)}@example.com")
    #     self.hashed_password = kwargs.get("hashed_password", "password_hash")
    #     # self.full_name = kwargs.get("full_name", f"User {kwargs.get('id', 0)}")
    #     self.is_active = kwargs.get("is_active", True)
    #     # self.is_superuser = kwargs.get("is_superuser", False)
    #     # self.roles = kwargs.get("roles", [])
    #     # self.permissions = kwargs.get("permissions", [])
    #     # self.settings = kwargs.get("settings", {})
    #     # self.config = kwargs.get("config", {})

    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        if self.is_superuser:
            return True

        for role in self.roles:
            for permission in role.permissions:
                if permission.code == permission_code:
                    return True
        return False

    # def add_role(self, role: str) -> None:
    #     """添加角色"""
    #     if role not in self.roles:
    #         self.roles.append(role)
    
    # def remove_role(self, role: str) -> None:
    #     """移除角色"""
    #     if role in self.roles:
    #         self.roles.remove(role)
    #
    # def add_permission(self, permission: str) -> None:
    #     """添加权限"""
    #     if permission not in self.permissions:
    #         self.permissions.append(permission)
    #
    # def remove_permission(self, permission: str) -> None:
    #     """移除权限"""
    #     if permission in self.permissions:
    #         self.permissions.remove(permission)
    
    # def has_role(self, role: str) -> bool:
    #     """检查是否具有指定角色"""
    #     return role in self.roles
    #
    # def has_permission(self, permission: str) -> bool:
    #     """检查是否具有指定权限"""
    #     # 超级用户拥有所有权限
    #     if self.is_superuser:
    #         return True
    #     return permission in self.permissions
    #
    # def update_settings(self, settings: dict) -> None:
    #     """更新用户设置"""
    #     self.settings.update(settings)
    #
    # def get_setting(self, key: str, default: Optional[any] = None) -> any:
    #     """获取用户设置"""
    #     return self.settings.get(key, default)
    #
    # def update_config(self, config: dict) -> None:
    #     """更新用户配置"""
    #     self.config.update(config)
    #
    # def get_config(self, key: str, default: Optional[any] = None) -> any:
    #     """获取用户配置"""
    #     return self.config.get(key, default)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            # "full_name": self.full_name,
            "is_active": self.is_active,
            # "is_superuser": self.is_superuser,
            # "roles": self.roles,
            # "permissions": self.permissions,
            # "settings": self.settings,
            # "config": self.config,
            # "created_at": self.created_at.isoformat() if self.created_at else None,
            # "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Role(BaseModel):
    """角色表"""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

    # 与用户的多对多关系
    users = relationship("User", secondary=user_role, back_populates="roles")
    # 与权限的多对多关系
    permissions = relationship("Permission", secondary=role_permission, back_populates="roles")


class Permission(BaseModel):
    """权限表"""
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)  # 权限代码，如"user:create"
    name = Column(String(100), nullable=False)  # 权限名称，如"创建用户"
    url = Column(String(255),nullable=True)  # 权限URL，如"/user/create"
    description = Column(String(255))

    # 与角色的多对多关系
    roles = relationship("Role", secondary=role_permission, back_populates="permissions")
