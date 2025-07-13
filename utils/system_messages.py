#!/usr/bin/env python3
"""
系统消息工具函数
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.chat import ChatMessage as DBChatMessage
from schemas.modern_chat import SystemMessageType
from core.global_websocket_manager import global_ws_manager, MessageType


async def create_system_message(
    db: AsyncSession,
    room_id: int,
    sender_id: int,
    message_type: SystemMessageType,
    content: str,
    system_data: Dict[str, Any],
    notify: bool = True
) -> DBChatMessage:
    """
    创建系统消息
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        sender_id: 发送者ID（通常是触发操作的用户）
        message_type: 系统消息类型
        content: 消息内容
        system_data: 系统数据
        notify: 是否发送WebSocket通知
    
    Returns:
        创建的系统消息对象
    """
    # 添加通用系统数据
    system_data.update({
        "type": message_type.value,
        "room_id": room_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # 创建系统消息记录
    system_message = DBChatMessage(
        room_id=room_id,
        sender_id=sender_id,
        content=content,
        message_type="system",
        system_data=json.dumps(system_data)
    )
    
    db.add(system_message)
    await db.commit()
    await db.refresh(system_message)
    
    # 发送WebSocket通知
    if notify:
        await notify_system_message(system_message, system_data)
    
    return system_message


async def notify_system_message(message: DBChatMessage, system_data: Dict[str, Any]):
    """发送系统消息的WebSocket通知"""
    from api.v1.endpoints.modern_chat import notify_room_members
    
    await notify_room_members(
        message.room_id,
        MessageType.NEW_MESSAGE,
        {
            "id": message.id,
            "content": message.content,
            "message_type": "system",
            "system_data": system_data,
            "sender": {
                "id": message.sender_id,
                "username": "系统",
                "nickname": "系统"
            },
            "created_at": message.created_at.isoformat(),
            "room_id": message.room_id
        }
    )


# ==================== 成员管理系统消息 ====================

async def create_member_joined_message(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    username: str,
    nickname: Optional[str] = None,
    invited_by: Optional[int] = None
):
    """创建成员加入消息"""
    if invited_by:
        content = f"{nickname or username} 被邀请加入了聊天室"
        system_data = {
            "user_id": user_id,
            "username": username,
            "nickname": nickname,
            "invited_by": invited_by,
            "action": "invited"
        }
    else:
        content = f"{nickname or username} 加入了聊天室"
        system_data = {
            "user_id": user_id,
            "username": username,
            "nickname": nickname,
            "action": "joined"
        }
    
    return await create_system_message(
        db, room_id, user_id, SystemMessageType.member_joined,
        content, system_data
    )


async def create_member_left_message(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    username: str,
    nickname: Optional[str] = None,
    kicked_by: Optional[int] = None
):
    """创建成员离开消息"""
    if kicked_by:
        content = f"{nickname or username} 被移出了聊天室"
        system_data = {
            "user_id": user_id,
            "username": username,
            "nickname": nickname,
            "kicked_by": kicked_by,
            "action": "kicked"
        }
        message_type = SystemMessageType.member_kicked
    else:
        content = f"{nickname or username} 离开了聊天室"
        system_data = {
            "user_id": user_id,
            "username": username,
            "nickname": nickname,
            "action": "left"
        }
        message_type = SystemMessageType.member_left
    
    return await create_system_message(
        db, room_id, user_id, message_type,
        content, system_data
    )


# ==================== 权限变更系统消息 ====================

async def create_role_changed_message(
    db: AsyncSession,
    room_id: int,
    target_user_id: int,
    target_username: str,
    target_nickname: Optional[str],
    old_role: str,
    new_role: str,
    changed_by: int
):
    """创建角色变更消息"""
    role_names = {
        "creator": "群主",
        "admin": "管理员",
        "member": "普通成员"
    }
    
    old_role_name = role_names.get(old_role, old_role)
    new_role_name = role_names.get(new_role, new_role)
    
    if new_role == "admin":
        content = f"{target_nickname or target_username} 被设为管理员"
        message_type = SystemMessageType.admin_promoted
    elif old_role == "admin" and new_role == "member":
        content = f"{target_nickname or target_username} 被取消管理员"
        message_type = SystemMessageType.admin_demoted
    elif new_role == "creator":
        content = f"群主已转让给 {target_nickname or target_username}"
        message_type = SystemMessageType.owner_transferred
    else:
        content = f"{target_nickname or target_username} 的角色从 {old_role_name} 变更为 {new_role_name}"
        message_type = SystemMessageType.role_changed
    
    system_data = {
        "target_user_id": target_user_id,
        "target_username": target_username,
        "target_nickname": target_nickname,
        "old_role": old_role,
        "new_role": new_role,
        "changed_by": changed_by
    }
    
    return await create_system_message(
        db, room_id, changed_by, message_type,
        content, system_data
    )


# ==================== 聊天室设置系统消息 ====================

async def create_room_settings_changed_message(
    db: AsyncSession,
    room_id: int,
    changed_by: int,
    change_type: str,
    old_value: Any,
    new_value: Any,
    field_name: str
):
    """创建聊天室设置变更消息"""
    field_names = {
        "name": "聊天室名称",
        "description": "聊天室描述",
        "rules": "聊天室规则",
        "max_members": "最大成员数",
        "allow_search": "搜索权限",
        "enable_invite_code": "邀请码功能"
    }
    
    field_display = field_names.get(field_name, field_name)
    
    if field_name == "name":
        content = f"聊天室名称已修改为「{new_value}」"
        message_type = SystemMessageType.room_name_changed
    elif field_name == "description":
        content = f"聊天室描述已更新"
        message_type = SystemMessageType.room_description_changed
    elif field_name == "rules":
        content = f"聊天室规则已更新"
        message_type = SystemMessageType.room_rules_changed
    else:
        content = f"{field_display} 已从 {old_value} 修改为 {new_value}"
        message_type = SystemMessageType.room_settings_changed
    
    system_data = {
        "field_name": field_name,
        "field_display": field_display,
        "old_value": old_value,
        "new_value": new_value,
        "changed_by": changed_by
    }
    
    return await create_system_message(
        db, room_id, changed_by, message_type,
        content, system_data
    )


# ==================== 消息管理系统消息 ====================

async def create_message_pinned_message(
    db: AsyncSession,
    room_id: int,
    message_id: int,
    message_content: str,
    pinned_by: int,
    pinned_by_username: str
):
    """创建消息置顶系统消息"""
    content = f"📌 {pinned_by_username} 置顶了一条消息"
    
    system_data = {
        "pinned_message_id": message_id,
        "pinned_message_content": message_content[:50] + ("..." if len(message_content) > 50 else ""),
        "pinned_by": pinned_by,
        "pinned_by_username": pinned_by_username,
        "action": "pinned"
    }
    
    return await create_system_message(
        db, room_id, pinned_by, SystemMessageType.message_pinned,
        content, system_data
    )


async def create_message_unpinned_message(
    db: AsyncSession,
    room_id: int,
    message_id: int,
    unpinned_by: int,
    unpinned_by_username: str
):
    """创建取消置顶系统消息"""
    content = f"📌 {unpinned_by_username} 取消了一条消息的置顶"
    
    system_data = {
        "unpinned_message_id": message_id,
        "unpinned_by": unpinned_by,
        "unpinned_by_username": unpinned_by_username,
        "action": "unpinned"
    }
    
    return await create_system_message(
        db, room_id, unpinned_by, SystemMessageType.message_unpinned,
        content, system_data
    )
