#!/usr/bin/env python3
"""
现代化聊天室系统的Pydantic模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    """消息类型"""
    text = "text"
    image = "image"
    file = "file"
    system = "system"
    voice = "voice"
    video = "video"
    emoji = "emoji"

class SystemMessageType(str, Enum):
    """系统消息类型"""
    # 加入申请相关
    join_request = "join_request"                    # 申请加入
    join_request_approved = "join_request_approved"  # 申请通过
    join_request_rejected = "join_request_rejected"  # 申请拒绝

    # 成员管理
    member_joined = "member_joined"                  # 成员加入
    member_left = "member_left"                      # 成员离开
    member_kicked = "member_kicked"                  # 成员被踢出
    member_invited = "member_invited"                # 成员被邀请

    # 权限变更
    role_changed = "role_changed"                    # 角色变更
    admin_promoted = "admin_promoted"                # 提升为管理员
    admin_demoted = "admin_demoted"                  # 取消管理员
    owner_transferred = "owner_transferred"          # 转让群主

    # 聊天室设置
    room_name_changed = "room_name_changed"          # 聊天室名称修改
    room_description_changed = "room_description_changed"  # 描述修改
    room_rules_changed = "room_rules_changed"        # 规则修改
    room_settings_changed = "room_settings_changed"  # 其他设置修改

    # 消息管理
    message_pinned = "message_pinned"                # 消息置顶
    message_unpinned = "message_unpinned"            # 取消置顶
    message_deleted_by_admin = "message_deleted_by_admin"  # 管理员删除消息

    # 文件分享
    file_uploaded = "file_uploaded"                  # 文件上传
    file_shared = "file_shared"                      # 文件分享

class RoomType(str, Enum):
    """聊天室类型"""
    public = "public"      # 公开聊天室
    private = "private"    # 私聊
    group = "group"        # 私密聊天室
    channel = "channel"    # 频道

class MessageStatus(str, Enum):
    """消息状态"""
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"

# 基础模型
class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    is_online: bool = False

  # 群内昵称

class MessageReaction(BaseModel):
    """消息反应"""
    emoji: str
    count: int
    users: List[UserInfo]
    user_reacted: bool = False

# 聊天室相关模型
class ChatRoomBase(BaseModel):
    """聊天室基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="聊天室名称")
    description: Optional[str] = Field(None, max_length=500, description="聊天室描述")
    room_type: RoomType = Field(RoomType.group, description="聊天室类型")
    avatar: Optional[str] = Field(None, description="聊天室头像URL")
    is_public: bool = Field(True, description="是否公开")
    max_members: int = Field(500, ge=2, le=10000, description="最大成员数")
    allow_member_invite: bool = Field(True, description="允许成员邀请")
    allow_member_modify_info: bool = Field(False, description="允许成员修改信息")
    message_history_visible: bool = Field(True, description="消息历史可见")
    allow_search: bool = Field(False, description="是否允许被搜索（仅私密聊天室）")
    enable_invite_code: bool = Field(True, description="是否启用邀请码（仅私密聊天室）")

    # 高级设置
    auto_delete_messages: bool = Field(False, description="自动删除消息")
    message_retention_days: int = Field(30, ge=1, le=365, description="消息保留天数")
    allow_file_upload: bool = Field(True, description="允许文件上传")
    max_file_size: int = Field(10, ge=1, le=100, description="最大文件大小(MB)")
    welcome_message: Optional[str] = Field(None, max_length=1000, description="欢迎消息")
    rules: Optional[str] = Field(None, max_length=2000, description="聊天室规则")

class ChatRoomCreate(ChatRoomBase):
    """创建聊天室"""
    pass

class ChatRoomUpdate(BaseModel):
    """更新聊天室"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar: Optional[str] = None
    is_public: Optional[bool] = None
    max_members: Optional[int] = Field(None, ge=2, le=10000)
    allow_member_invite: Optional[bool] = None
    allow_member_modify_info: Optional[bool] = None
    message_history_visible: Optional[bool] = None

    # 私密房间设置
    allow_search: Optional[bool] = None
    enable_invite_code: Optional[bool] = None

    # 高级设置
    auto_delete_messages: Optional[bool] = None
    message_retention_days: Optional[int] = Field(None, ge=1, le=365)
    allow_file_upload: Optional[bool] = None
    max_file_size: Optional[int] = Field(None, ge=1, le=100)
    welcome_message: Optional[str] = Field(None, max_length=1000)
    rules: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None

# 消息相关模型
class MessageBase(BaseModel):
    """消息基础模型"""
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")
    message_type: MessageType = Field(MessageType.text, description="消息类型")
    reply_to_id: Optional[int] = Field(None, description="回复的消息ID")

class MessageCreateRequest(MessageBase):
    """创建消息请求（不包含room_id，从URL获取）"""
    file_url: Optional[str] = Field(None, description="文件URL")
    file_name: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小")

class MessageCreate(MessageBase):
    """创建消息（包含room_id，用于内部处理）"""
    room_id: int = Field(..., description="聊天室ID")
    file_url: Optional[str] = Field(None, description="文件URL")
    file_name: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小")

class MessageUpdate(BaseModel):
    """更新消息"""
    content: str = Field(..., min_length=1, max_length=5000)

class Message(MessageBase):
    """消息详情"""
    id: int
    room_id: int
    sender: UserInfo
    reply_to: Optional['Message'] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    is_edited: bool = False
    is_deleted: bool = False
    is_pinned: bool = False
    edit_count: int = 0
    created_at: datetime
    updated_at: datetime

    # 置顶相关
    pinned_by: Optional[int] = None
    pinned_at: Optional[datetime] = None

    # 消息状态
    read_count: int = 0
    reactions: List[MessageReaction] = []

    # 系统消息数据
    system_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# 聊天室成员相关模型
class RoomMember(BaseModel):
    """聊天室成员信息"""
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    role: str = "member"  # creator, admin, member
    joined_at: datetime
    is_muted: bool = False

class ChatRoom(ChatRoomBase):
    """聊天室详情"""
    id: int
    creator: UserInfo
    members: List[RoomMember] = []
    member_count: int = 0
    last_message: Optional[Message] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatRoomListItem(BaseModel):
    """聊天室列表项"""
    id: int
    name: str
    description: Optional[str] = None
    room_type: RoomType
    is_public: bool = True
    avatar: Optional[str] = None
    member_count: int = 0
    is_member: bool = False
    created_at: datetime
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    is_muted: bool = False

    # 添加缺失的字段
    allow_search: bool = False
    enable_invite_code: bool = True
    max_members: int = 500
    is_active: bool = True

class MessageList(BaseModel):
    """消息列表"""
    messages: List[Message]
    total: int
    has_more: bool = False

class TypingStatus(BaseModel):
    """正在输入状态"""
    room_id: int
    user: UserInfo
    started_at: datetime

class OnlineStatus(BaseModel):
    """在线状态"""
    user_id: int
    is_online: bool
    last_seen: Optional[datetime] = None

# WebSocket消息类型
class WSMessageType(str, Enum):
    """WebSocket消息类型"""
    # 消息相关
    NEW_MESSAGE = "new_message"
    MESSAGE_UPDATED = "message_updated"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_REACTION = "message_reaction"
    
    # 用户状态
    USER_TYPING = "user_typing"
    USER_STOP_TYPING = "user_stop_typing"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    
    # 聊天室相关
    ROOM_UPDATED = "room_updated"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_UPDATED = "member_updated"
    
    # 系统消息
    SYSTEM_MESSAGE = "system_message"
    ERROR = "error"

class WSMessage(BaseModel):
    """WebSocket消息"""
    type: WSMessageType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    room_id: Optional[int] = None

class ChatRoomInvite(BaseModel):
    """聊天室邀请"""
    room_id: int
    user_ids: List[int]
    message: Optional[str] = None

class ChatRoomMemberUpdate(BaseModel):
    """更新聊天室成员"""
    user_id: int
    role: Optional[str] = None
    is_muted: Optional[bool] = None
    nickname: Optional[str] = None

class MessageSearch(BaseModel):
    """消息搜索"""
    query: str = Field(..., min_length=1, max_length=100)
    room_id: Optional[int] = None
    message_type: Optional[MessageType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ChatStatistics(BaseModel):
    """聊天统计"""
    total_rooms: int
    total_messages: int
    active_users: int
    popular_rooms: List[ChatRoomListItem]

class FileUpload(BaseModel):
    """文件上传"""
    file_url: str
    file_name: str
    file_size: int
    file_type: str

class EmojiReaction(BaseModel):
    """表情反应"""
    emoji: str

class PinMessage(BaseModel):
    """置顶消息"""
    message_id: int
    is_pinned: bool

# 加入申请相关Schema
class JoinRequestStatus(str, Enum):
    """加入申请状态"""
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class JoinRoomRequest(BaseModel):
    """加入聊天室申请"""
    room_id: int = Field(..., description="聊天室ID")
    message: Optional[str] = Field(None, description="申请消息")


class JoinRoomByInviteCode(BaseModel):
    """通过邀请码加入聊天室"""
    invite_code: str = Field(..., description="邀请码")


class ChatRoomJoinRequestInfo(BaseModel):
    """聊天室加入申请信息"""
    id: int
    room_id: int
    user_id: int
    status: JoinRequestStatus
    message: Optional[str] = None
    processed_by: Optional[int] = None
    processed_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime

    # 关联信息
    user: UserInfo
    room_name: str
    processor: Optional[UserInfo] = None


class ProcessJoinRequest(BaseModel):
    """处理加入申请"""
    room_id: int = Field(..., description="聊天室ID")
    action: str = Field(..., description="操作：approve 或 reject")
    message: Optional[str] = Field(None, description="处理消息")


class InviteCodeInfo(BaseModel):
    """邀请码信息"""
    invite_code: str
    expires_at: Optional[datetime] = None
    is_expired: bool = False


# 更新前向引用
Message.model_rebuild()

class RoomMemberUpdate(BaseModel):
    """更新聊天室成员"""
    user_id: int
    role: Optional[str] = None
    is_muted: Optional[bool] = None
    nickname: Optional[str] = None

class InviteUserRequest(BaseModel):
    """邀请用户加入聊天室"""
    user_id: int = Field(..., description="被邀请用户ID")

class MuteMemberRequest(BaseModel):
    """禁言/取消禁言成员"""
    is_muted: bool = Field(..., description="是否禁言")
    reason: Optional[str] = Field(None, description="禁言原因")

class ChangeMemberRoleRequest(BaseModel):
    """更改成员角色"""
    role: str = Field(..., description="新角色：member 或 admin")

class TransferOwnershipRequest(BaseModel):
    """转让群主"""
    new_owner_id: int = Field(..., description="新群主用户ID")
