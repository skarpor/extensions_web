#!/usr/bin/env python3
"""
现代化聊天室API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc, func, update, delete
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid


from core.auth import (
    get_current_active_user,
    create_chat_rooms,
    view_chat_rooms,
    update_chat_rooms,
    delete_chat_rooms,
    manage_chat_rooms,
    send_chat_messages,
    join_chat_rooms,
    search_chat_rooms
, create_chats, view_chats, update_chats, delete_chats)
from db.session import get_db
from config import settings
from models.user import User as DBUser
from models.chat import (
    ChatRoom as DBChatRoom, ChatMessage as DBChatMessage, MessageReadReceipt,
    MessageReaction as DBMessageReaction, UserTyping, chat_room_members, RoomType,
    ChatRoomJoinRequest as DBChatRoomJoinRequest, JoinRequestStatus as DBJoinRequestStatus
)
from schemas.modern_chat import (
    ChatRoom, ChatRoomCreate, ChatRoomUpdate, ChatRoomListItem,
    Message, MessageCreate, MessageCreateRequest, MessageUpdate, MessageList,
    WSMessage, WSMessageType, TypingStatus, OnlineStatus,
    ChatRoomInvite, ChatRoomMemberUpdate, MessageSearch,
    FileUpload, EmojiReaction, PinMessage, UserInfo, RoomMember,
    JoinRoomRequest, JoinRoomByInviteCode, ChatRoomJoinRequestInfo,
    ProcessJoinRequest, InviteCodeInfo, JoinRequestStatus,
    InviteUserRequest, MuteMemberRequest, ChangeMemberRoleRequest, TransferOwnershipRequest
)
from core.logger import get_logger
from core.global_websocket_manager import global_ws_manager, MessageType

router = APIRouter()
logger = get_logger("chat")

# ==================== 聊天室管理 ====================

@router.get("/rooms", response_model=List[ChatRoomListItem])
async def get_chat_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    room_type: Optional[str] = Query(None),
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """获取聊天室列表"""
    try:
        # 构建查询
        query = select(DBChatRoom).options(
            selectinload(DBChatRoom.creator),
            selectinload(DBChatRoom.members),
            selectinload(DBChatRoom.messages).selectinload(DBChatMessage.sender)
        ).where(DBChatRoom.is_active == True)
        
        # 过滤类型
        if room_type:
            query = query.where(DBChatRoom.room_type == room_type)
        
        # 只显示用户参与的聊天室或公开聊天室
        query = query.where(
            or_(
                DBChatRoom.is_public == True,
                DBChatRoom.members.any(DBUser.id == current_user.id)
            )
        )
        
        query = query.order_by(desc(DBChatRoom.last_message_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        rooms = result.scalars().all()
        
        # 转换为响应模型
        room_list = []
        for room in rooms:
            # 获取最后一条消息
            last_message = None
            if room.messages:
                last_msg = max(room.messages, key=lambda x: x.created_at)
                last_message = last_msg.content[:50] + "..." if len(last_msg.content) > 50 else last_msg.content
            
            # 计算未读消息数（简化版）
            unread_count = 0  # TODO: 实现真正的未读计数
            
            # 对于私聊，显示对方的用户名
            display_name = room.name
            display_avatar = room.avatar

            if room.room_type == RoomType.private:
                # 获取私聊中的其他用户
                other_user = None
                for member in room.members:
                    if member.id != current_user.id:
                        other_user = member
                        break

                if other_user:
                    display_name = other_user.nickname or other_user.username
                    display_avatar = getattr(other_user, 'avatar', None)

            # 检查用户是否是成员
            is_member = any(member.id == current_user.id for member in room.members)

            room_item = ChatRoomListItem(
                id=room.id,
                name=display_name,
                description=room.description,
                room_type=room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
                is_public=room.is_public,
                avatar=display_avatar,
                member_count=len(room.members),
                is_member=is_member,
                created_at=room.created_at,
                last_message=last_message,
                last_message_at=room.last_message_at,
                unread_count=unread_count,
                is_muted=False,  # TODO: 实现静音状态
                allow_search=room.allow_search,
                enable_invite_code=room.enable_invite_code,
                max_members=room.max_members,
                is_active=room.is_active
            )
            room_list.append(room_item)
        
        return room_list
        
    except Exception as e:
        logger.error(f"获取聊天室列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取聊天室列表失败")

@router.post("/rooms", response_model=ChatRoom)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(create_chat_rooms)
):
    """创建聊天室"""
    try:
        # 创建聊天室
        db_room = DBChatRoom(
            name=room_data.name,
            description=room_data.description,
            room_type=room_data.room_type,
            avatar=room_data.avatar,
            is_public=room_data.is_public,
            max_members=room_data.max_members,
            created_by=current_user.id,
            allow_member_invite=room_data.allow_member_invite,
            allow_member_modify_info=room_data.allow_member_modify_info,
            message_history_visible=room_data.message_history_visible,
            allow_search=room_data.allow_search,  # 直接使用Schema字段
            enable_invite_code=room_data.enable_invite_code,  # 直接使用Schema字段
            auto_delete_messages=room_data.auto_delete_messages,
            message_retention_days=room_data.message_retention_days,
            allow_file_upload=room_data.allow_file_upload,
            max_file_size=room_data.max_file_size,
            welcome_message=room_data.welcome_message,
            rules=room_data.rules
        )
        
        db.add(db_room)
        await db.flush()
        
        # 添加创建者为管理员
        await db.execute(
            chat_room_members.insert().values(
                room_id=db_room.id,
                user_id=current_user.id,
                role="admin"
            )
        )
        
        await db.commit()
        await db.refresh(db_room)
        
        # 加载关联数据
        query = select(DBChatRoom).options(
            selectinload(DBChatRoom.creator),
            selectinload(DBChatRoom.members)
        ).where(DBChatRoom.id == db_room.id)
        
        result = await db.execute(query)
        room = result.scalar_one()
        
        logger.info(f"用户 {current_user.username} 创建聊天室: {room.name}")

        # 如果是公开聊天室，通知所有在线用户
        if room.is_public:
            room_data = {
                "room": {
                    "id": room.id,
                    "name": room.name,
                    "description": room.description,
                    "room_type": room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
                    "is_public": room.is_public,
                    "creator": {
                        "id": current_user.id,
                        "username": current_user.username,
                        "nickname": current_user.nickname
                    }
                }
            }

            # 只有公开聊天室才广播给所有用户
            if room.room_type == RoomType.public:
                await global_ws_manager.broadcast_to_all(MessageType.ROOM_CREATED, room_data, exclude_user=current_user.id)
            else:
                # 私密聊天室只通知创建者
                logger.info(f"私密聊天室 {room.name} 创建完成，不进行全局广播")

        # 转换为响应模型
        return ChatRoom(
            id=room.id,
            name=room.name,
            description=room.description,
            room_type=room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
            avatar=room.avatar,
            is_public=room.is_public,
            max_members=room.max_members,
            allow_member_invite=room.allow_member_invite,
            allow_member_modify_info=room.allow_member_modify_info,
            message_history_visible=room.message_history_visible,
            allow_search=room.allow_search,
            enable_invite_code=room.enable_invite_code,
            auto_delete_messages=room.auto_delete_messages,
            message_retention_days=room.message_retention_days,
            allow_file_upload=room.allow_file_upload,
            max_file_size=room.max_file_size,
            welcome_message=room.welcome_message,
            rules=room.rules,
            creator=UserInfo(
                id=room.creator.id,
                username=room.creator.username,
                nickname=room.creator.nickname,
                avatar=getattr(room.creator, 'avatar', None)
            ),
            members=[],
            member_count=len(room.members),
            is_active=room.is_active,
            created_at=room.created_at,
            updated_at=room.updated_at
        )
        
    except Exception as e:
        logger.error(f"创建聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="创建聊天室失败")

@router.get("/rooms/{room_id}", response_model=ChatRoom)
async def get_chat_room(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """获取聊天室详情"""
    try:
        # 查询聊天室
        query = select(DBChatRoom).options(
            selectinload(DBChatRoom.creator),
            selectinload(DBChatRoom.members)
        ).where(DBChatRoom.id == room_id)
        
        result = await db.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")
        
        # 检查访问权限
        if not room.is_public and current_user not in room.members:
            raise HTTPException(status_code=403, detail="无权访问此聊天室")
        
        # 获取成员信息
        members = []
        for member in room.members:
            # 获取成员在聊天室中的角色信息
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == member.id
                )
            )
            member_result = await db.execute(member_query)
            member_info = member_result.first()
            
            room_member = RoomMember(
                user_id=member.id,
                username=member.username,
                nickname=member.nickname,
                avatar=getattr(member, 'avatar', None),
                email=getattr(member, 'email', None),
                role=member_info.role if member_info else "member",
                joined_at=member_info.joined_at if member_info else datetime.now(),
                is_muted=member_info.is_muted if member_info else False
            )
            members.append(room_member)
        
        return ChatRoom(
            id=room.id,
            name=room.name,
            description=room.description,
            room_type=room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
            avatar=room.avatar,
            is_public=room.is_public,
            max_members=room.max_members,
            allow_member_invite=room.allow_member_invite,
            allow_member_modify_info=room.allow_member_modify_info,
            message_history_visible=room.message_history_visible,
            creator=UserInfo(
                id=room.creator.id,
                username=room.creator.username,
                nickname=room.creator.nickname,
                avatar=getattr(room.creator, 'avatar', None)
            ),
            members=members,
            member_count=len(room.members),
            last_message_at=room.last_message_at,
            is_active=room.is_active,
            created_at=room.created_at,
            updated_at=room.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天室详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取聊天室详情失败")

@router.put("/rooms/{room_id}", response_model=ChatRoom)
async def update_chat_room(
    room_id: int,
    room_data: ChatRoomUpdate,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(update_chat_rooms)
):
    """更新聊天室"""
    try:
        # 查询聊天室
        query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        result = await db.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")
        
        # 检查权限（只有创建者或管理员可以修改）
        if room.created_by != current_user.id:
            # 检查是否是管理员
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == current_user.id,
                    chat_room_members.c.role == "admin"
                )
            )
            member_result = await db.execute(member_query)
            if not member_result.first():
                raise HTTPException(status_code=403, detail="无权修改此聊天室")
        
        # 更新字段
        update_data = room_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room, field, value)
        
        await db.commit()
        await db.refresh(room)
        
        logger.info(f"用户 {current_user.username} 更新聊天室: {room.name}")
        
        # 重新获取完整信息
        return await get_chat_room(room_id, current_user, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="更新聊天室失败")

@router.delete("/rooms/{room_id}")
async def delete_chat_room(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(delete_chat_rooms)
):
    """删除聊天室"""
    try:
        # 查询聊天室
        query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        result = await db.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")
        
        # 检查权限
        if room.room_type == RoomType.private:
            # 私聊聊天室：任何成员都可以删除
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == current_user.id
                )
            )
            member_result = await db.execute(member_query)
            is_member = member_result.first() is not None

            if not is_member:
                raise HTTPException(status_code=403, detail="您不是此私聊的成员")
        else:
            # 群聊和频道：只有创建者可以删除
            if room.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="只有创建者可以删除聊天室")
        
        # 通知聊天室成员聊天室即将被删除
        room_data = {
            "room_id": room.id,
            "room_name": room.name,
            "deleted_by": {
                "id": current_user.id,
                "username": current_user.username,
                "nickname": current_user.nickname
            }
        }

        # 如果是公开聊天室，通知所有在线用户（排除删除者自己）
        if room.is_public:
            await global_ws_manager.broadcast_to_all(MessageType.ROOM_DELETED, room_data, exclude_user=current_user.id)
        else:
            # 如果是私有聊天室，只通知聊天室成员（排除删除者自己）
            await notify_room_members(room.id, MessageType.ROOM_DELETED, room_data)

        # 软删除
        room.is_active = False
        await db.commit()

        logger.info(f"用户 {current_user.username} 删除聊天室: {room.name}")

        return {"message": "聊天室删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="删除聊天室失败")

@router.post("/private-rooms", response_model=ChatRoom)
async def create_or_get_private_room(
    target_user_id: int = Body(..., embed=True),
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(create_chat_rooms)
):
    """创建或获取私聊聊天室"""
    try:
        # 检查目标用户是否存在
        target_user_query = select(DBUser).where(DBUser.id == target_user_id)
        target_user_result = await db.execute(target_user_query)
        target_user = target_user_result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="目标用户不存在")

        if target_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能与自己私聊")

        # 查找是否已存在私聊聊天室
        # 私聊聊天室的特征：room_type='private'，且两个用户都是成员
        existing_room_query = select(DBChatRoom).join(
            chat_room_members, DBChatRoom.id == chat_room_members.c.room_id
        ).where(
            and_(
                DBChatRoom.room_type == RoomType.private,
                chat_room_members.c.user_id.in_([current_user.id, target_user.id])
            )
        ).group_by(DBChatRoom.id).having(
            func.count(chat_room_members.c.user_id) == 2
        )

        existing_room_result = await db.execute(existing_room_query)
        existing_room = existing_room_result.scalar_one_or_none()

        if existing_room:
            # 返回现有的私聊聊天室
            await db.refresh(existing_room, ['creator', 'members'])

            # 私聊显示对方的用户名
            display_name = target_user.nickname or target_user.username

            return ChatRoom(
                id=existing_room.id,
                name=display_name,
                description=f"与 {display_name} 的私聊",
                room_type=existing_room.room_type.value if hasattr(existing_room.room_type, 'value') else existing_room.room_type,
                avatar=getattr(target_user, 'avatar', None),
                is_public=False,
                max_members=2,
                allow_member_invite=False,
                allow_member_modify_info=False,
                message_history_visible=True,
                creator=UserInfo(
                    id=existing_room.creator.id,
                    username=existing_room.creator.username,
                    nickname=existing_room.creator.nickname,
                    avatar=getattr(existing_room.creator, 'avatar', None)
                ),
                members=[],
                member_count=2,
                is_active=existing_room.is_active,
                created_at=existing_room.created_at,
                updated_at=existing_room.updated_at
            )

        # 创建新的私聊聊天室
        display_name = target_user.nickname or target_user.username

        db_room = DBChatRoom(
            name=display_name,  # 存储对方的显示名称
            description=f"与 {display_name} 的私聊",
            room_type=RoomType.private,
            is_public=False,
            max_members=2,
            created_by=current_user.id,
            allow_member_invite=False,
            allow_member_modify_info=False,
            message_history_visible=True
        )

        db.add(db_room)
        await db.commit()
        await db.refresh(db_room)

        # 添加两个用户为成员
        members_to_add = [
            {
                'room_id': db_room.id,
                'user_id': current_user.id,
                'role': 'admin',
                'joined_at': datetime.now(),
                'last_read_at': datetime.now()
            },
            {
                'room_id': db_room.id,
                'user_id': target_user.id,
                'role': 'member',
                'joined_at': datetime.now(),
                'last_read_at': datetime.now()
            }
        ]

        for member_data in members_to_add:
            member_insert = chat_room_members.insert().values(**member_data)
            await db.execute(member_insert)

        await db.commit()

        # 重新加载聊天室信息
        await db.refresh(db_room, ['creator'])

        logger.info(f"用户 {current_user.username} 创建了与 {target_user.username} 的私聊")

        # 通知目标用户有新的私聊聊天室
        await notify_private_room_created(db_room.id, current_user, target_user)

        return ChatRoom(
            id=db_room.id,
            name=display_name,
            description=f"与 {display_name} 的私聊",
            room_type=db_room.room_type.value if hasattr(db_room.room_type, 'value') else db_room.room_type,
            avatar=getattr(target_user, 'avatar', None),
            is_public=False,
            max_members=2,
            allow_member_invite=False,
            allow_member_modify_info=False,
            message_history_visible=True,
            creator=UserInfo(
                id=db_room.creator.id,
                username=db_room.creator.username,
                nickname=db_room.creator.nickname,
                avatar=getattr(db_room.creator, 'avatar', None)
            ),
            members=[],
            member_count=2,
            is_active=db_room.is_active,
            created_at=db_room.created_at,
            updated_at=db_room.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建私聊聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="创建私聊聊天室失败")


# 这个函数已经移动到文件末尾的WebSocket通知函数部分

# ==================== 消息管理 ====================

@router.get("/rooms/{room_id}/messages", response_model=MessageList)
async def get_room_messages(
    room_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """获取聊天室消息"""
    try:
        # 检查聊天室访问权限
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否是聊天室成员
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        is_member = member_result.first() is not None

        if not is_member:
            if room.room_type.value == "public":
                # 公共聊天室：自动加入
                insert_member = chat_room_members.insert().values(
                    room_id=room_id,
                    user_id=current_user.id,
                    role="member",
                    joined_at=datetime.utcnow(),
                    is_muted=False
                )
                await db.execute(insert_member)
                await db.commit()

                print(f"用户 {current_user.username} 自动加入公共聊天室 {room.name}")
            else:
                # 私密聊天室：拒绝访问
                raise HTTPException(status_code=403, detail="无权访问此聊天室")

        # 查询消息，使用joinedload避免懒加载问题
        from sqlalchemy.orm import joinedload

        query = select(DBChatMessage).options(
            joinedload(DBChatMessage.sender),
            joinedload(DBChatMessage.reply_to).joinedload(DBChatMessage.sender),
        ).where(
            and_(
                DBChatMessage.room_id == room_id,
                DBChatMessage.is_deleted == False
            )
        ).order_by(desc(DBChatMessage.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        messages = result.scalars().all()

        # 转换为响应模型
        message_list = []
        for msg in messages:
            # 构建回复消息
            reply_to = None
            if msg.reply_to:
                reply_to = Message(
                    id=msg.reply_to.id,
                    room_id=msg.reply_to.room_id,
                    content=msg.reply_to.content,
                    message_type=msg.reply_to.message_type.value if hasattr(msg.reply_to.message_type, 'value') else msg.reply_to.message_type,
                    sender=UserInfo(
                        id=msg.reply_to.sender.id,
                        username=msg.reply_to.sender.username,
                        nickname=msg.reply_to.sender.nickname,
                        avatar=getattr(msg.reply_to.sender, 'avatar', None)
                    ),
                    created_at=msg.reply_to.created_at,
                    updated_at=msg.reply_to.updated_at,
                    is_edited=msg.reply_to.is_edited,
                    is_deleted=msg.reply_to.is_deleted,
                    is_pinned=msg.reply_to.is_pinned,
                    edit_count=msg.reply_to.edit_count,
                    read_count=0,  # 暂时设为0，避免懒加载问题
                    reactions=[]
                )

            # 解析system_data
            system_data = None
            if msg.system_data:
                try:
                    import json
                    system_data = json.loads(msg.system_data) if isinstance(msg.system_data, str) else msg.system_data
                except (json.JSONDecodeError, TypeError):
                    system_data = None

            message = Message(
                id=msg.id,
                room_id=msg.room_id,
                content=msg.content,
                message_type=msg.message_type.value if hasattr(msg.message_type, 'value') else msg.message_type,
                reply_to_id=msg.reply_to_id,
                sender=UserInfo(
                    id=msg.sender.id,
                    username=msg.sender.username,
                    nickname=msg.sender.nickname,
                    avatar=getattr(msg.sender, 'avatar', None)
                ),
                reply_to=reply_to,
                file_url=msg.file_url,
                file_name=msg.file_name,
                file_size=msg.file_size,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
                is_edited=msg.is_edited,
                is_deleted=msg.is_deleted,
                is_pinned=msg.is_pinned,
                edit_count=msg.edit_count,
                pinned_by=msg.pinned_by,
                pinned_at=msg.pinned_at,
                read_count=0,  # 暂时设为0，避免懒加载问题
                reactions=[],  # TODO: 实现表情反应
                system_data=system_data
            )
            message_list.append(message)

        # 获取总数
        count_query = select(func.count(DBChatMessage.id)).where(
            and_(
                DBChatMessage.room_id == room_id,
                DBChatMessage.is_deleted == False
            )
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        return MessageList(
            messages=list(reversed(message_list)),  # 按时间正序返回
            total=total,
            has_more=skip + limit < total
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天室消息失败: {e}")
        raise HTTPException(status_code=500, detail="获取聊天室消息失败")


@router.post("/rooms/{room_id}/mark-read")
async def mark_messages_as_read(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """标记聊天室消息为已读"""
    try:
        # 检查聊天室访问权限
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否是聊天室成员
        if not room.is_public:
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == current_user.id
                )
            )
            member_result = await db.execute(member_query)
            is_member = member_result.first() is not None

            if not is_member:
                raise HTTPException(status_code=403, detail="无权访问此聊天室")

        # 这里可以添加具体的已读标记逻辑
        # 目前只是返回成功，前端已经清除了未读计数

        return {"message": "消息已标记为已读"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记消息已读失败: {e}")
        raise HTTPException(status_code=500, detail="标记消息已读失败")


# ==================== 图片上传功能 ====================

def ensure_upload_dir():
    """确保上传目录存在"""
    upload_dir = settings.CHAT_UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def validate_image(file: UploadFile) -> bool:
    """验证图片文件"""
    # 检查文件类型
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        return False

    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        return False

    return True

def generate_filename(original_filename: str) -> str:
    """生成唯一的文件名"""
    file_ext = os.path.splitext(original_filename)[1].lower()
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{unique_id}{file_ext}"

@router.post("/upload-image")
async def upload_chat_image(
    file: UploadFile = File(...),
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(send_chat_messages)
):
    """上传聊天图片"""
    try:
        # 验证文件
        if not validate_image(file):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片格式。支持的格式: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
            )

        # 检查文件大小
        file_content = await file.read()
        if len(file_content) > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"图片文件过大。最大支持 {settings.MAX_IMAGE_SIZE // (1024*1024)}MB"
            )

        # 确保上传目录存在
        upload_dir = ensure_upload_dir()

        # 生成唯一文件名
        filename = generate_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 生成访问URL
        file_url = f"{settings.CHAT_IMAGE_URL_PREFIX}/{filename}"

        logger.info(f"用户 {current_user.username} 上传聊天图片: {filename}")

        return {
            "success": True,
            "filename": filename,
            "url": file_url,
            "size": len(file_content),
            "content_type": file.content_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传聊天图片失败: {e}")
        raise HTTPException(status_code=500, detail="上传图片失败")


# ==================== WebSocket通知函数 ====================

async def send_new_message_notification(message: DBChatMessage, room: DBChatRoom, sender: DBUser):
    """发送新消息通知"""
    try:
        message_data = {
            "id": message.id,
            "room_id": message.room_id,
            "content": message.content,
            "message_type": message.message_type.value if hasattr(message.message_type, 'value') else message.message_type,
            "sender": {
                "id": sender.id,
                "username": sender.username,
                "nickname": sender.nickname,
                "avatar": getattr(sender, 'avatar', None)
            },
            "file_url": message.file_url,
            "file_name": message.file_name,
            "file_size": message.file_size,
            "created_at": message.created_at.isoformat(),
            "reply_to_id": message.reply_to_id
        }

        # 根据聊天室类型选择通知范围
        if room.room_type == RoomType.private:
            # 私聊：通知聊天室成员
            await notify_room_members(room.id, MessageType.NEW_MESSAGE, message_data)
        else:
            # 公开聊天室：通知所有在线用户
            await global_ws_manager.broadcast_to_all(MessageType.NEW_MESSAGE, message_data, exclude_user=sender.id)

    except Exception as e:
        logger.error(f"发送新消息通知失败: {e}")

async def send_room_update_notification(room: DBChatRoom, last_message: DBChatMessage, sender: DBUser):
    """发送聊天室更新通知"""
    try:
        room_data = {
            "room_id": room.id,
            "last_message": {
                "content": last_message.content,
                "sender": {
                    "username": sender.username,
                    "nickname": sender.nickname
                },
                "created_at": last_message.created_at.isoformat()
            },
            "last_message_at": room.last_message_at.isoformat()
        }

        # 根据聊天室类型选择通知范围
        if room.room_type == RoomType.private:
            # 私聊：通知聊天室成员
            await notify_room_members(room.id, MessageType.ROOM_UPDATED, room_data)
        else:
            # 公开聊天室：通知所有在线用户
            await global_ws_manager.broadcast_to_all(MessageType.ROOM_UPDATED, room_data)

    except Exception as e:
        logger.error(f"发送聊天室更新通知失败: {e}")

async def notify_room_members(room_id: int, message_type: MessageType, data: dict):
    """通知聊天室成员"""
    try:
        from db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # 获取聊天室成员
            member_query = select(chat_room_members).where(chat_room_members.c.room_id == room_id)
            member_result = await db.execute(member_query)
            members = member_result.fetchall()

            # 通知每个成员
            member_ids = [member.user_id for member in members]
            await global_ws_manager.send_to_users(member_ids, message_type, data)

    except Exception as e:
        logger.error(f"通知聊天室成员失败: {e}")

async def notify_private_room_created(room_id: int, creator_user: DBUser, target_user: DBUser):
    """通知目标用户有新的私聊聊天室"""
    try:
        private_room_data = {
            "room": {
                "id": room_id,
                "name": creator_user.nickname or creator_user.username,
                "description": f"与 {creator_user.nickname or creator_user.username} 的私聊",
                "room_type": "private",
                "avatar": getattr(creator_user, 'avatar', None),
                "creator": {
                    "id": creator_user.id,
                    "username": creator_user.username,
                    "nickname": creator_user.nickname
                }
            }
        }

        # 只通知目标用户
        await global_ws_manager.send_to_user(target_user.id, MessageType.PRIVATE_ROOM_CREATED, private_room_data)
        logger.info(f"已通知用户 {target_user.username} 新的私聊聊天室")

    except Exception as e:
        logger.error(f"通知私聊创建失败: {e}")

@router.post("/rooms/{room_id}/messages", response_model=Message)
async def send_message(
    room_id: int,
    message_data: MessageCreateRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(send_chat_messages)
):
    """发送消息"""
    try:
        # 检查聊天室权限
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 根据聊天室类型检查权限
        if room.room_type.value == "public":
            # 公共聊天室：检查是否是成员，如果不是则自动加入
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == current_user.id
                )
            )
            member_result = await db.execute(member_query)
            is_member = member_result.first() is not None

            if not is_member:
                # 自动加入公共聊天室
                insert_member = chat_room_members.insert().values(
                    room_id=room_id,
                    user_id=current_user.id,
                    role="member",
                    joined_at=datetime.utcnow(),
                    is_muted=False
                )
                await db.execute(insert_member)
                await db.commit()

                logger.info(f"用户 {current_user.username} 自动加入公共聊天室 {room.name}")
                is_member = True
        else:
            # 私密聊天室和私聊：需要检查成员资格
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == current_user.id
                )
            )
            member_result = await db.execute(member_query)
            is_member = member_result.first() is not None

            if not is_member:
                if room.room_type.value == "private":
                    raise HTTPException(status_code=403, detail="您不是此私聊的参与者")
                else:
                    raise HTTPException(status_code=403, detail="您不是此私密聊天室的成员")

        # 检查是否被静音（只对非公开聊天室检查）
        if room.room_type.value != "public":
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == current_user.id
                )
            )
            member_result = await db.execute(member_query)
            member_info = member_result.first()

            if member_info and member_info.is_muted:
                raise HTTPException(status_code=403, detail="您在此聊天室中被静音")

        # 创建消息
        db_message = DBChatMessage(
            room_id=room_id,
            sender_id=current_user.id,
            content=message_data.content,
            message_type=message_data.message_type,
            reply_to_id=message_data.reply_to_id,
            file_url=message_data.file_url,
            file_name=message_data.file_name,
            file_size=message_data.file_size
        )

        db.add(db_message)

        # 更新聊天室最后消息时间
        room.last_message_at = datetime.now()

        await db.commit()
        await db.refresh(db_message)

        # 加载发送者信息
        query = select(DBChatMessage).options(
            selectinload(DBChatMessage.sender)
        ).where(DBChatMessage.id == db_message.id)

        result = await db.execute(query)
        message = result.scalar_one()

        logger.info(f"用户 {current_user.username} 在聊天室 {room.name} 发送消息")

        # 通过全局WebSocket发送新消息通知
        await send_new_message_notification(message, room, current_user)

        # 发送聊天室更新通知
        await send_room_update_notification(room, message, current_user)

        return Message(
            id=message.id,
            room_id=message.room_id,
            content=message.content,
            message_type=message.message_type.value if hasattr(message.message_type, 'value') else message.message_type,
            reply_to_id=message.reply_to_id,
            sender=UserInfo(
                id=message.sender.id,
                username=message.sender.username,
                nickname=message.sender.nickname,
                avatar=getattr(message.sender, 'avatar', None)
            ),
            file_url=message.file_url,
            file_name=message.file_name,
            file_size=message.file_size,
            created_at=message.created_at,
            updated_at=message.updated_at,
            is_edited=message.is_edited,
            is_deleted=message.is_deleted,
            is_pinned=message.is_pinned,
            edit_count=message.edit_count,
            read_count=0,
            reactions=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail="发送消息失败")


# ==================== 私密聊天室加入功能 ====================

@router.post("/rooms/{room_id}/join-request", response_model=dict)
async def request_join_room(
    room_id: int,
    request_data: JoinRoomRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(join_chat_rooms)
):
    """申请加入私密聊天室"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查是否是私密聊天室
        if room.room_type.value == "public":
            raise HTTPException(status_code=400, detail="公开聊天室无需申请")

        # 检查是否已经是成员
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        is_member = member_result.first() is not None

        if is_member:
            raise HTTPException(status_code=400, detail="您已经是聊天室成员")

        # 检查是否已有待处理的申请
        existing_request_query = select(DBChatRoomJoinRequest).where(
            and_(
                DBChatRoomJoinRequest.room_id == room_id,
                DBChatRoomJoinRequest.user_id == current_user.id,
                DBChatRoomJoinRequest.status == DBJoinRequestStatus.pending
            )
        )
        existing_request_result = await db.execute(existing_request_query)
        existing_request = existing_request_result.scalar_one_or_none()

        if existing_request:
            # 检查是否在1分钟内
            time_diff = datetime.utcnow() - existing_request.created_at
            if time_diff.total_seconds() < 60:
                remaining_seconds = 60 - int(time_diff.total_seconds())
                raise HTTPException(
                    status_code=429,
                    detail=f"请等待 {remaining_seconds} 秒后再次申请"
                )
            else:
                # 更新现有申请
                existing_request.message = request_data.message
                existing_request.expires_at = datetime.utcnow() + timedelta(days=7)
                existing_request.created_at = datetime.utcnow()
        else:
            # 创建新申请
            new_request = DBChatRoomJoinRequest(
                room_id=room_id,
                user_id=current_user.id,
                message=request_data.message,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.add(new_request)

        await db.commit()

        # 创建系统消息记录
        from utils.system_messages import create_system_message
        from schemas.modern_chat import SystemMessageType

        system_data = {
            "user_id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname,
            "request_id": new_request.id if 'new_request' in locals() else existing_request.id,
            "message": request_data.message
        }

        await create_system_message(
            db=db,
            room_id=room_id,
            sender_id=current_user.id,
            message_type=SystemMessageType.join_request,
            content=f"用户 {current_user.nickname or current_user.username} 申请加入聊天室",
            system_data=system_data
        )

        return {"message": "申请已发送，等待管理员审核"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"申请加入聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="申请失败")


@router.post("/rooms/join-by-invite", response_model=dict)
async def join_room_by_invite_code(
    request_data: JoinRoomByInviteCode,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(join_chat_rooms)
):
    """通过邀请码加入聊天室"""
    try:
        # 查找邀请码对应的聊天室
        room_query = select(DBChatRoom).where(
            DBChatRoom.invite_code == request_data.invite_code
        )
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="邀请码无效")

        # 检查邀请码是否过期
        if room.invite_code_expires_at and room.invite_code_expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="邀请码已过期")

        # 检查是否已经是成员
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room.id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        is_member = member_result.first() is not None

        if is_member:
            raise HTTPException(status_code=400, detail="您已经是聊天室成员")

        # 添加用户到聊天室
        insert_member = chat_room_members.insert().values(
            room_id=room.id,
            user_id=current_user.id,
            role="member",
            joined_at=datetime.utcnow(),
            is_muted=False
        )
        await db.execute(insert_member)
        await db.commit()

        # 通知聊天室成员
        await notify_room_members(
            room.id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"用户 {current_user.username} 通过邀请码加入了聊天室",
                "type": "member_joined",
                "user_id": current_user.id,
                "username": current_user.username,
                "room_id": room.id,
                "room_name": room.name
            }
        )

        return {
            "message": f"成功加入聊天室 {room.name}",
            "room_id": room.id,
            "room_name": room.name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"通过邀请码加入聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="加入失败")


@router.get("/rooms/{room_id}/invite-code", response_model=InviteCodeInfo)
async def get_room_invite_code(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """获取聊天室邀请码"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否是聊天室成员
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        # 如果没有邀请码，生成一个
        if not room.invite_code:
            import secrets
            room.invite_code = secrets.token_urlsafe(16)
            room.invite_code_expires_at = datetime.utcnow() + timedelta(days=30)
            await db.commit()

        is_expired = (
            room.invite_code_expires_at and
            room.invite_code_expires_at < datetime.utcnow()
        )

        return InviteCodeInfo(
            invite_code=room.invite_code,
            expires_at=room.invite_code_expires_at,
            is_expired=is_expired
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取邀请码失败: {e}")
        raise HTTPException(status_code=500, detail="获取邀请码失败")


@router.post("/rooms/{room_id}/refresh-invite-code", response_model=InviteCodeInfo)
async def refresh_room_invite_code(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """刷新聊天室邀请码"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否是管理员
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        if member_info.role not in ["admin", "creator"] and room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有管理员可以刷新邀请码")

        # 生成新的邀请码
        import secrets
        room.invite_code = secrets.token_urlsafe(16)
        room.invite_code_expires_at = datetime.utcnow() + timedelta(days=30)
        await db.commit()

        return InviteCodeInfo(
            invite_code=room.invite_code,
            expires_at=room.invite_code_expires_at,
            is_expired=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新邀请码失败: {e}")
        raise HTTPException(status_code=500, detail="刷新邀请码失败")


@router.post("/join-requests/{user_id}/process", response_model=dict)
async def process_join_request(
    user_id: int,
    request_data: ProcessJoinRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """处理加入申请"""
    try:
        room_id = request_data.room_id

        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查当前用户是否有权限处理申请（管理员或创建者）
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        if member_info.role not in ["admin", "creator"] and room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有管理员可以处理加入申请")

        # 查找待处理的申请
        join_request_query = select(DBChatRoomJoinRequest).where(
            and_(
                DBChatRoomJoinRequest.room_id == room_id,
                DBChatRoomJoinRequest.user_id == user_id,
                DBChatRoomJoinRequest.status == DBJoinRequestStatus.pending
            )
        )
        join_request_result = await db.execute(join_request_query)
        join_request = join_request_result.scalar_one_or_none()

        if not join_request:
            raise HTTPException(status_code=404, detail="未找到待处理的申请")

        # 获取申请用户信息
        user_query = select(DBUser).where(DBUser.id == user_id)
        user_result = await db.execute(user_query)
        applicant = user_result.scalar_one_or_none()

        if not applicant:
            raise HTTPException(status_code=404, detail="申请用户不存在")

        # 处理申请
        if request_data.action == 'approve':
            # 同意申请
            join_request.status = DBJoinRequestStatus.approved
            join_request.processed_by = current_user.id
            join_request.processed_at = datetime.utcnow()

            # 添加用户到聊天室
            insert_member = chat_room_members.insert().values(
                room_id=room_id,
                user_id=user_id,
                role="member",
                joined_at=datetime.utcnow(),
                is_muted=False
            )
            await db.execute(insert_member)

            # 通知聊天室成员
            await notify_room_members(
                room_id,
                MessageType.SYSTEM_NOTIFICATION,
                {
                    "message": f"用户 {applicant.username} 已加入聊天室",
                    "type": "member_joined",
                    "user_id": user_id,
                    "username": applicant.username,
                    "room_id": room_id,
                    "room_name": room.name
                }
            )

            message = f"已同意 {applicant.username} 的加入申请"

        elif request_data.action == 'reject':
            # 拒绝申请
            join_request.status = DBJoinRequestStatus.rejected
            join_request.processed_by = current_user.id
            join_request.processed_at = datetime.utcnow()

            message = f"已拒绝 {applicant.username} 的加入申请"

        else:
            raise HTTPException(status_code=400, detail="无效的操作")

        await db.commit()

        # 创建系统消息记录
        system_message = DBChatMessage(
            room_id=room_id,
            sender_id=current_user.id,
            content=message,
            message_type="system",
            system_data={
                "type": "join_request_result",
                "user_id": user_id,
                "room_id": room_id,
                "action": request_data.action,
                "processed_by": current_user.id
            }
        )
        db.add(system_message)
        await db.commit()
        await db.refresh(system_message)

        # 通知聊天室成员
        await notify_room_members(
            room_id,
            MessageType.NEW_MESSAGE,
            {
                "id": system_message.id,
                "content": system_message.content,
                "message_type": "system",
                "system_data": system_message.system_data,
                "sender": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "nickname": current_user.nickname
                },
                "created_at": system_message.created_at.isoformat(),
                "room_id": room_id
            }
        )

        # 通知申请人结果
        await global_ws_manager.send_to_user(
            user_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"您的加入申请已被{('同意' if request_data.action == 'approve' else '拒绝')}",
                "type": "join_request_result",
                "room_id": room_id,
                "room_name": room.name,
                "action": request_data.action
            }
        )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理加入申请失败: {e}")
        raise HTTPException(status_code=500, detail="处理申请失败")


@router.get("/search-rooms", response_model=List[ChatRoomListItem])
async def search_rooms(
    q: str = Query(..., description="搜索关键词"),
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(search_chat_rooms)
):
    """搜索聊天室"""
    try:
        if not q.strip():
            return []

        # 搜索聊天室名称 - 搜索公开聊天室和允许被搜索的私密聊天室
        search_query = select(DBChatRoom).where(
            and_(
                DBChatRoom.name.contains(q.strip()),
                or_(
                    DBChatRoom.room_type == RoomType.public,  # 所有公开聊天室
                    and_(
                        DBChatRoom.room_type == RoomType.group,  # 私密聊天室
                        DBChatRoom.allow_search == True  # 且允许被搜索
                    )
                )
            )
        ).limit(20)

        result = await db.execute(search_query)
        rooms = result.scalars().all()

        room_list = []
        for room in rooms:
            # 获取成员数量
            member_count_query = select(func.count(chat_room_members.c.user_id)).where(
                chat_room_members.c.room_id == room.id
            )
            member_count_result = await db.execute(member_count_query)
            member_count = member_count_result.scalar() or 0

            # 检查用户是否已经是成员
            is_member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room.id,
                    chat_room_members.c.user_id == current_user.id
                )
            )
            is_member_result = await db.execute(is_member_query)
            is_member = is_member_result.first() is not None

            room_data = ChatRoomListItem(
                id=room.id,
                name=room.name,
                description=room.description,
                room_type=room.room_type.value,
                is_public=room.is_public,
                avatar=room.avatar,
                member_count=member_count,
                is_member=is_member,
                created_at=room.created_at,
                last_message=None,
                last_message_at=None,
                unread_count=0,
                allow_search=room.allow_search,
                enable_invite_code=room.enable_invite_code,
                max_members=room.max_members,
                is_active=room.is_active
            )
            room_list.append(room_data)

        return room_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="搜索失败")


# ==================== 聊天室成员管理 ====================

@router.get("/rooms/{room_id}/members", response_model=List[RoomMember])
async def get_room_members(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """获取聊天室成员列表"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否有权限查看成员列表
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        user_member = member_result.first()

        if not user_member and room.room_type != RoomType.public:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        # 获取成员列表
        members_query = select(
            chat_room_members.c.user_id,
            chat_room_members.c.role,
            chat_room_members.c.joined_at,
            chat_room_members.c.is_muted,
            DBUser.username,
            DBUser.nickname,
            DBUser.avatar,
            DBUser.email
        ).select_from(
            chat_room_members.join(DBUser, chat_room_members.c.user_id == DBUser.id)
        ).where(chat_room_members.c.room_id == room_id)

        members_result = await db.execute(members_query)
        members = members_result.fetchall()

        member_list = []
        for member in members:
            member_info = RoomMember(
                user_id=member.user_id,
                username=member.username,
                nickname=member.nickname,
                avatar=member.avatar,
                email=member.email,
                role=member.role,
                joined_at=member.joined_at,
                is_muted=member.is_muted
            )
            member_list.append(member_info)

        return member_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天室成员失败: {e}")
        raise HTTPException(status_code=500, detail="获取成员列表失败")


@router.post("/rooms/{room_id}/members/{user_id}/kick")
async def kick_member(
    room_id: int,
    user_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """踢出聊天室成员"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查当前用户权限
        current_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        current_member_result = await db.execute(current_member_query)
        current_member = current_member_result.first()

        if not current_member:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        if current_member.role not in ["admin", "creator"] and room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有管理员可以踢出成员")

        # 检查被踢用户是否存在
        target_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == user_id
            )
        )
        target_member_result = await db.execute(target_member_query)
        target_member = target_member_result.first()

        if not target_member:
            raise HTTPException(status_code=404, detail="用户不是聊天室成员")

        # 不能踢出创建者
        if room.created_by == user_id:
            raise HTTPException(status_code=400, detail="不能踢出聊天室创建者")

        # 不能踢出自己
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能踢出自己")

        # 获取被踢用户信息
        user_query = select(DBUser).where(DBUser.id == user_id)
        user_result = await db.execute(user_query)
        target_user = user_result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 删除成员关系
        delete_member = delete(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == user_id
            )
        )
        await db.execute(delete_member)
        await db.commit()

        # 通知聊天室成员
        await notify_room_members(
            room_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"用户 {target_user.username} 被踢出聊天室",
                "type": "member_kicked",
                "user_id": user_id,
                "username": target_user.username,
                "room_id": room_id,
                "room_name": room.name,
                "kicked_by": current_user.username
            }
        )

        # 通知被踢用户
        await global_ws_manager.send_to_user(
            user_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"您已被踢出聊天室 {room.name}",
                "type": "kicked_from_room",
                "room_id": room_id,
                "room_name": room.name,
                "kicked_by": current_user.username
            }
        )

        logger.info(f"用户 {current_user.username} 踢出了用户 {target_user.username} 从聊天室 {room.name}")
        return {"message": f"已踢出用户 {target_user.username}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"踢出成员失败: {e}")
        raise HTTPException(status_code=500, detail="踢出成员失败")


@router.post("/rooms/{room_id}/members/invite")
async def invite_user_to_room(
    room_id: int,
    invite_data: InviteUserRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """邀请用户加入聊天室"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查当前用户权限
        current_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        current_member_result = await db.execute(current_member_query)
        current_member = current_member_result.first()

        if not current_member:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        # 检查是否有邀请权限
        if current_member.role not in ["admin", "creator"] and room.created_by != current_user.id:
            if not room.allow_member_invite:
                raise HTTPException(status_code=403, detail="该聊天室不允许普通成员邀请")

        # 检查被邀请用户是否存在
        target_user_query = select(DBUser).where(DBUser.id == invite_data.user_id)
        target_user_result = await db.execute(target_user_query)
        target_user = target_user_result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="被邀请用户不存在")

        # 检查用户是否已经是成员
        existing_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == invite_data.user_id
            )
        )
        existing_member_result = await db.execute(existing_member_query)
        existing_member = existing_member_result.first()

        if existing_member:
            raise HTTPException(status_code=400, detail="用户已经是聊天室成员")

        # 检查聊天室成员数量限制
        member_count_query = select(func.count(chat_room_members.c.user_id)).where(
            chat_room_members.c.room_id == room_id
        )
        member_count_result = await db.execute(member_count_query)
        member_count = member_count_result.scalar()

        if member_count >= room.max_members:
            raise HTTPException(status_code=400, detail="聊天室已达到最大成员数限制")

        # 添加用户到聊天室
        insert_member = chat_room_members.insert().values(
            room_id=room_id,
            user_id=invite_data.user_id,
            role="member",
            joined_at=datetime.utcnow(),
            is_muted=False
        )
        await db.execute(insert_member)
        await db.commit()

        # 通知聊天室成员
        await notify_room_members(
            room_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"用户 {target_user.username} 被 {current_user.username} 邀请加入聊天室",
                "type": "member_invited",
                "user_id": invite_data.user_id,
                "username": target_user.username,
                "invited_by": current_user.username,
                "room_id": room_id,
                "room_name": room.name
            }
        )

        # 通知被邀请用户
        await global_ws_manager.send_to_user(
            invite_data.user_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"您被邀请加入聊天室 {room.name}",
                "type": "invited_to_room",
                "room_id": room_id,
                "room_name": room.name,
                "invited_by": current_user.username
            }
        )

        logger.info(f"用户 {current_user.username} 邀请用户 {target_user.username} 加入聊天室 {room.name}")
        return {"message": f"已邀请用户 {target_user.username} 加入聊天室"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"邀请用户失败: {e}")
        raise HTTPException(status_code=500, detail="邀请用户失败")


@router.post("/rooms/{room_id}/members/{user_id}/mute")
async def mute_member(
    room_id: int,
    user_id: int,
    mute_data: MuteMemberRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """禁言聊天室成员"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查当前用户权限
        current_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        current_member_result = await db.execute(current_member_query)
        current_member = current_member_result.first()

        if not current_member:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        if current_member.role not in ["admin", "creator"] and room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有管理员可以禁言成员")

        # 检查被禁言用户是否存在
        target_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == user_id
            )
        )
        target_member_result = await db.execute(target_member_query)
        target_member = target_member_result.first()

        if not target_member:
            raise HTTPException(status_code=404, detail="用户不是聊天室成员")

        # 不能禁言创建者
        if room.created_by == user_id:
            raise HTTPException(status_code=400, detail="不能禁言聊天室创建者")

        # 不能禁言自己
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能禁言自己")

        # 获取被禁言用户信息
        user_query = select(DBUser).where(DBUser.id == user_id)
        user_result = await db.execute(user_query)
        target_user = user_result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 更新禁言状态
        is_muting = mute_data.is_muted
        update_member = update(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == user_id
            )
        ).values(is_muted=is_muting)

        await db.execute(update_member)
        await db.commit()

        # 通知聊天室成员
        action = "禁言" if is_muting else "取消禁言"
        await notify_room_members(
            room_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"用户 {target_user.username} 被管理员 {current_user.username} {action}",
                "type": "member_muted" if is_muting else "member_unmuted",
                "user_id": user_id,
                "username": target_user.username,
                "room_id": room_id,
                "room_name": room.name,
                "operated_by": current_user.username,
                "is_muted": is_muting
            }
        )

        # 通知被操作用户
        await global_ws_manager.send_to_user(
            user_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"您在聊天室 {room.name} 中被{action}",
                "type": "mute_status_changed",
                "room_id": room_id,
                "room_name": room.name,
                "operated_by": current_user.username,
                "is_muted": is_muting
            }
        )

        logger.info(f"用户 {current_user.username} {action}了用户 {target_user.username} 在聊天室 {room.name}")
        return {"message": f"已{action}用户 {target_user.username}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁言操作失败: {e}")
        raise HTTPException(status_code=500, detail="禁言操作失败")


@router.post("/rooms/{room_id}/members/{user_id}/role")
async def change_member_role(
    room_id: int,
    user_id: int,
    role_data: ChangeMemberRoleRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """更改聊天室成员角色"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查当前用户权限（只有创建者可以设置管理员）
        if room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有聊天室创建者可以设置管理员")

        # 检查目标用户是否存在
        target_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == user_id
            )
        )
        target_member_result = await db.execute(target_member_query)
        target_member = target_member_result.first()

        if not target_member:
            raise HTTPException(status_code=404, detail="用户不是聊天室成员")

        # 不能更改创建者角色
        if room.created_by == user_id:
            raise HTTPException(status_code=400, detail="不能更改创建者角色")

        # 验证角色
        valid_roles = ["member", "admin"]
        if role_data.role not in valid_roles:
            raise HTTPException(status_code=400, detail="无效的角色")

        # 获取目标用户信息
        user_query = select(DBUser).where(DBUser.id == user_id)
        user_result = await db.execute(user_query)
        target_user = user_result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 更新角色
        old_role = target_member.role
        update_member = update(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == user_id
            )
        ).values(role=role_data.role)

        await db.execute(update_member)
        await db.commit()

        # 通知聊天室成员
        role_names = {"member": "普通成员", "admin": "管理员"}
        await notify_room_members(
            room_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"用户 {target_user.username} 被设置为{role_names[role_data.role]}",
                "type": "member_role_changed",
                "user_id": user_id,
                "username": target_user.username,
                "room_id": room_id,
                "room_name": room.name,
                "old_role": old_role,
                "new_role": role_data.role,
                "operated_by": current_user.username
            }
        )

        # 通知被操作用户
        await global_ws_manager.send_to_user(
            user_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"您在聊天室 {room.name} 中的角色已更改为{role_names[role_data.role]}",
                "type": "role_changed",
                "room_id": room_id,
                "room_name": room.name,
                "old_role": old_role,
                "new_role": role_data.role,
                "operated_by": current_user.username
            }
        )

        logger.info(f"用户 {current_user.username} 将用户 {target_user.username} 在聊天室 {room.name} 的角色从 {old_role} 更改为 {role_data.role}")
        return {"message": f"已将用户 {target_user.username} 设置为{role_names[role_data.role]}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更改成员角色失败: {e}")
        raise HTTPException(status_code=500, detail="更改成员角色失败")


@router.post("/rooms/{room_id}/leave")
async def leave_room(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """退出聊天室"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否是成员
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=404, detail="您不是聊天室成员")

        # 创建者不能直接退出，需要先转让群主或解散群聊
        if room.created_by == current_user.id:
            # 检查是否还有其他成员
            other_members_query = select(func.count(chat_room_members.c.user_id)).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id != current_user.id
                )
            )
            other_members_result = await db.execute(other_members_query)
            other_members_count = other_members_result.scalar()

            if other_members_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail="作为群主，您需要先转让群主身份或解散群聊才能退出"
                )

        # 删除成员关系
        delete_member = delete(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        await db.execute(delete_member)

        # 如果是创建者且没有其他成员，删除聊天室
        if room.created_by == current_user.id:
            # 删除聊天室相关数据
            await db.execute(delete(DBChatMessage).where(DBChatMessage.room_id == room_id))
            await db.execute(delete(DBChatRoomJoinRequest).where(DBChatRoomJoinRequest.room_id == room_id))
            await db.execute(delete(DBChatRoom).where(DBChatRoom.id == room_id))

            await db.commit()

            logger.info(f"用户 {current_user.username} 解散了聊天室 {room.name}")
            return {"message": f"聊天室 {room.name} 已解散"}

        await db.commit()

        # 通知其他聊天室成员
        await notify_room_members(
            room_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"用户 {current_user.username} 退出了聊天室",
                "type": "member_left",
                "user_id": current_user.id,
                "username": current_user.username,
                "room_id": room_id,
                "room_name": room.name
            }
        )

        logger.info(f"用户 {current_user.username} 退出了聊天室 {room.name}")
        return {"message": f"已退出聊天室 {room.name}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"退出聊天室失败: {e}")
        raise HTTPException(status_code=500, detail="退出聊天室失败")


@router.post("/rooms/{room_id}/transfer-ownership")
async def transfer_room_ownership(
    room_id: int,
    transfer_data: TransferOwnershipRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """转让聊天室群主"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查当前用户是否是创建者
        if room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有群主可以转让群主身份")

        # 检查目标用户是否是成员
        target_member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == transfer_data.new_owner_id
            )
        )
        target_member_result = await db.execute(target_member_query)
        target_member = target_member_result.first()

        if not target_member:
            raise HTTPException(status_code=404, detail="目标用户不是聊天室成员")

        # 不能转让给自己
        if transfer_data.new_owner_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能转让给自己")

        # 获取目标用户信息
        user_query = select(DBUser).where(DBUser.id == transfer_data.new_owner_id)
        user_result = await db.execute(user_query)
        new_owner = user_result.scalar_one_or_none()

        if not new_owner:
            raise HTTPException(status_code=404, detail="目标用户不存在")

        # 更新聊天室创建者
        update_room = update(DBChatRoom).where(DBChatRoom.id == room_id).values(
            created_by=transfer_data.new_owner_id
        )
        await db.execute(update_room)

        # 更新原群主角色为管理员
        update_old_owner = update(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        ).values(role="admin")
        await db.execute(update_old_owner)

        # 更新新群主角色为创建者
        update_new_owner = update(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == transfer_data.new_owner_id
            )
        ).values(role="creator")
        await db.execute(update_new_owner)

        await db.commit()

        # 通知聊天室成员
        await notify_room_members(
            room_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"群主 {current_user.username} 将群主身份转让给了 {new_owner.username}",
                "type": "ownership_transferred",
                "old_owner_id": current_user.id,
                "old_owner_username": current_user.username,
                "new_owner_id": transfer_data.new_owner_id,
                "new_owner_username": new_owner.username,
                "room_id": room_id,
                "room_name": room.name
            }
        )

        # 通知新群主
        await global_ws_manager.send_to_user(
            transfer_data.new_owner_id,
            MessageType.SYSTEM_NOTIFICATION,
            {
                "message": f"您已成为聊天室 {room.name} 的新群主",
                "type": "became_owner",
                "room_id": room_id,
                "room_name": room.name,
                "transferred_by": current_user.username
            }
        )

        logger.info(f"用户 {current_user.username} 将聊天室 {room.name} 的群主身份转让给了 {new_owner.username}")
        return {"message": f"已将群主身份转让给 {new_owner.username}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转让群主失败: {e}")
        raise HTTPException(status_code=500, detail="转让群主失败")


# ==================== 表情反应功能 ====================

@router.post("/messages/{message_id}/reactions")
async def add_message_reaction(
    message_id: int,
    reaction_data: EmojiReaction,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(send_chat_messages)
):
    """添加消息表情反应"""
    try:
        # 检查消息是否存在
        message_query = select(DBChatMessage).where(DBChatMessage.id == message_id)
        message_result = await db.execute(message_query)
        message = message_result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")

        # 检查用户是否有权限访问该聊天室
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == message.room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        # 检查是否已经有相同的表情反应
        existing_reaction_query = select(DBMessageReaction).where(
            and_(
                DBMessageReaction.message_id == message_id,
                DBMessageReaction.user_id == current_user.id,
                DBMessageReaction.emoji == reaction_data.emoji
            )
        )
        existing_reaction_result = await db.execute(existing_reaction_query)
        existing_reaction = existing_reaction_result.scalar_one_or_none()

        if existing_reaction:
            # 如果已存在，删除反应
            await db.delete(existing_reaction)
            action = "removed"
        else:
            # 添加新的表情反应
            new_reaction = DBMessageReaction(
                message_id=message_id,
                user_id=current_user.id,
                emoji=reaction_data.emoji,
                created_at=datetime.utcnow()
            )
            db.add(new_reaction)
            action = "added"

        await db.commit()

        # 通知聊天室成员
        await notify_room_members(
            message.room_id,
            MessageType.MESSAGE_REACTION,
            {
                "message_id": message_id,
                "user_id": current_user.id,
                "username": current_user.username,
                "emoji": reaction_data.emoji,
                "action": action
            }
        )

        logger.info(f"用户 {current_user.username} {action} 表情反应 {reaction_data.emoji} 到消息 {message_id}")
        return {"message": f"表情反应已{('添加' if action == 'added' else '移除')}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"表情反应操作失败: {e}")
        raise HTTPException(status_code=500, detail="表情反应操作失败")


@router.get("/messages/{message_id}/reactions")
async def get_message_reactions(
    message_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """获取消息的表情反应"""
    try:
        # 检查消息是否存在
        message_query = select(DBChatMessage).where(DBChatMessage.id == message_id)
        message_result = await db.execute(message_query)
        message = message_result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")

        # 检查用户是否有权限访问该聊天室
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == message.room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        # 获取表情反应统计
        reactions_query = select(
            DBMessageReaction.emoji,
            func.count(DBMessageReaction.id).label('count'),
            func.group_concat(DBUser.username).label('users')
        ).join(
            DBUser, DBMessageReaction.user_id == DBUser.id
        ).where(
            DBMessageReaction.message_id == message_id
        ).group_by(DBMessageReaction.emoji)

        reactions_result = await db.execute(reactions_query)
        reactions = reactions_result.fetchall()

        reaction_list = []
        for reaction in reactions:
            # 检查当前用户是否反应了这个表情
            user_reacted_query = select(DBMessageReaction).where(
                and_(
                    DBMessageReaction.message_id == message_id,
                    DBMessageReaction.user_id == current_user.id,
                    DBMessageReaction.emoji == reaction.emoji
                )
            )
            user_reacted_result = await db.execute(user_reacted_query)
            user_reacted = user_reacted_result.scalar_one_or_none() is not None

            reaction_list.append({
                "emoji": reaction.emoji,
                "count": reaction.count,
                "user_reacted": user_reacted,
                "users": reaction.users.split(',') if reaction.users else []
            })

        return reaction_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取表情反应失败: {e}")
        raise HTTPException(status_code=500, detail="获取表情反应失败")


# ==================== 消息删除和修改功能 ====================

@router.put("/rooms/{room_id}/messages/{message_id}")
async def update_message(
    room_id: int,
    message_id: int,
    message_data: dict,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(update_chats)  # 使用更新聊天权限
):
    """修改消息"""
    try:
        # 检查消息是否存在
        message_query = select(DBChatMessage).where(
            and_(
                DBChatMessage.id == message_id,
                DBChatMessage.room_id == room_id
            )
        )
        message_result = await db.execute(message_query)
        message = message_result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")

        # 检查权限（只有消息发送者可以修改）
        if message.sender_id != current_user.id:
            raise HTTPException(status_code=403, detail="只能修改自己的消息")

        # 检查消息是否已被删除
        if message.is_deleted:
            raise HTTPException(status_code=400, detail="已删除的消息无法修改")

        # 更新消息内容
        new_content = message_data.get('content', '').strip()
        if not new_content:
            raise HTTPException(status_code=400, detail="消息内容不能为空")

        message.content = new_content
        message.is_edited = True
        message.edit_count = (message.edit_count or 0) + 1
        message.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(message)

        # 通知聊天室成员
        await notify_room_members(
            room_id,
            MessageType.MESSAGE_UPDATED,
            {
                "message_id": message_id,
                "content": new_content,
                "is_edited": True,
                "edit_count": message.edit_count,
                "updated_at": message.updated_at.isoformat()
            }
        )

        logger.info(f"用户 {current_user.username} 修改了消息 {message_id}")
        return {"message": "消息修改成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改消息失败: {e}")
        raise HTTPException(status_code=500, detail="修改消息失败")


@router.delete("/rooms/{room_id}/messages/{message_id}")
async def delete_message(
    room_id: int,
    message_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(delete_chats)  # 使用删除聊天权限
):
    """删除消息"""
    try:
        # 检查消息是否存在
        message_query = select(DBChatMessage).where(
            and_(
                DBChatMessage.id == message_id,
                DBChatMessage.room_id == room_id
            )
        )
        message_result = await db.execute(message_query)
        message = message_result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")

        # 检查权限（消息发送者或聊天室管理员可以删除）
        can_delete = False

        # 1. 消息发送者可以删除自己的消息
        if message.sender_id == current_user.id:
            can_delete = True
        else:
            # 2. 聊天室管理员可以删除任何消息
            member_query = select(chat_room_members).where(
                and_(
                    chat_room_members.c.room_id == room_id,
                    chat_room_members.c.user_id == current_user.id,
                    or_(
                        chat_room_members.c.role == "admin",
                        chat_room_members.c.role == "creator"
                    )
                )
            )
            member_result = await db.execute(member_query)
            if member_result.first():
                can_delete = True

        if not can_delete:
            raise HTTPException(status_code=403, detail="无权删除此消息")

        # 软删除消息
        message.is_deleted = True
        message.content = "[此消息已被删除]"
        message.updated_at = datetime.utcnow()

        await db.commit()

        # 通知聊天室成员
        await notify_room_members(
            room_id,
            MessageType.MESSAGE_DELETED,
            {
                "message_id": message_id,
                "deleted_by": current_user.id,
                "deleted_by_username": current_user.username
            }
        )

        logger.info(f"用户 {current_user.username} 删除了消息 {message_id}")
        return {"message": "消息删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除消息失败: {e}")
        raise HTTPException(status_code=500, detail="删除消息失败")


# ==================== 聊天室统计信息 ====================

@router.get("/rooms/{room_id}/statistics")
async def get_room_statistics(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """获取聊天室统计信息"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否有权限查看
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        user_member = member_result.first()

        if not user_member and room.room_type != RoomType.public:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        # 获取统计信息
        # 总消息数
        total_messages_query = select(func.count(DBChatMessage.id)).where(
            DBChatMessage.room_id == room_id
        )
        total_messages_result = await db.execute(total_messages_query)
        total_messages = total_messages_result.scalar()

        # 今日消息数
        today = datetime.utcnow().date()
        today_messages_query = select(func.count(DBChatMessage.id)).where(
            and_(
                DBChatMessage.room_id == room_id,
                func.date(DBChatMessage.created_at) == today
            )
        )
        today_messages_result = await db.execute(today_messages_query)
        today_messages = today_messages_result.scalar()

        # 总成员数
        total_members_query = select(func.count(chat_room_members.c.user_id)).where(
            chat_room_members.c.room_id == room_id
        )
        total_members_result = await db.execute(total_members_query)
        total_members = total_members_result.scalar()

        # 活跃成员数（最近7天发过消息）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_members_query = select(func.count(func.distinct(DBChatMessage.sender_id))).where(
            and_(
                DBChatMessage.room_id == room_id,
                DBChatMessage.created_at >= seven_days_ago
            )
        )
        active_members_result = await db.execute(active_members_query)
        active_members = active_members_result.scalar()

        # 置顶消息数
        pinned_messages_query = select(func.count(DBChatMessage.id)).where(
            and_(
                DBChatMessage.room_id == room_id,
                DBChatMessage.is_pinned == True
            )
        )
        pinned_messages_result = await db.execute(pinned_messages_query)
        pinned_messages = pinned_messages_result.scalar()

        # 最活跃用户（发消息最多的前5名）
        top_users_query = select(
            DBChatMessage.sender_id,
            func.count(DBChatMessage.id).label('message_count'),
            DBUser.username,
            DBUser.nickname
        ).join(
            DBUser, DBChatMessage.sender_id == DBUser.id
        ).where(
            DBChatMessage.room_id == room_id
        ).group_by(
            DBChatMessage.sender_id, DBUser.username, DBUser.nickname
        ).order_by(
            func.count(DBChatMessage.id).desc()
        ).limit(5)

        top_users_result = await db.execute(top_users_query)
        top_users = top_users_result.fetchall()

        top_users_list = []
        for user in top_users:
            top_users_list.append({
                "user_id": user.sender_id,
                "username": user.username,
                "nickname": user.nickname,
                "message_count": user.message_count
            })

        statistics = {
            "room_id": room_id,
            "room_name": room.name,
            "total_messages": total_messages,
            "today_messages": today_messages,
            "total_members": total_members,
            "active_members": active_members,
            "pinned_messages": pinned_messages,
            "top_users": top_users_list,
            "created_at": room.created_at,
            "last_message_at": room.last_message_at
        }

        return statistics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天室统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


# ==================== 消息置顶功能 ====================

@router.post("/rooms/{room_id}/messages/{message_id}/pin")
async def pin_message(
    room_id: int,
    message_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """置顶消息"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户权限
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        if member_info.role not in ["admin", "creator"] and room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有管理员可以置顶消息")

        # 检查消息是否存在
        message_query = select(DBChatMessage).where(
            and_(
                DBChatMessage.id == message_id,
                DBChatMessage.room_id == room_id
            )
        )
        message_result = await db.execute(message_query)
        message = message_result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")

        # 检查消息是否已经置顶
        if message.is_pinned:
            raise HTTPException(status_code=400, detail="消息已经置顶")

        # 置顶消息
        message.is_pinned = True
        message.pinned_by = current_user.id
        message.pinned_at = datetime.utcnow()

        await db.commit()

        # 创建置顶系统消息
        from utils.system_messages import create_message_pinned_message
        await create_message_pinned_message(
            db=db,
            room_id=room_id,
            message_id=message_id,
            message_content=message.content,
            pinned_by=current_user.id,
            pinned_by_username=current_user.nickname or current_user.username
        )

        logger.info(f"用户 {current_user.username} 置顶了消息 {message_id}")
        return {"message": "消息已置顶"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"置顶消息失败: {e}")
        raise HTTPException(status_code=500, detail="置顶消息失败")


@router.delete("/rooms/{room_id}/messages/{message_id}/pin")
async def unpin_message(
    room_id: int,
    message_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(manage_chat_rooms)
):
    """取消置顶消息"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户权限
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member_info = member_result.first()

        if not member_info:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        if member_info.role not in ["admin", "creator"] and room.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只有管理员可以取消置顶消息")

        # 检查消息是否存在
        message_query = select(DBChatMessage).where(
            and_(
                DBChatMessage.id == message_id,
                DBChatMessage.room_id == room_id
            )
        )
        message_result = await db.execute(message_query)
        message = message_result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")

        # 检查消息是否已经置顶
        if not message.is_pinned:
            raise HTTPException(status_code=400, detail="消息未置顶")

        # 取消置顶
        message.is_pinned = False
        message.pinned_by = None
        message.pinned_at = None

        await db.commit()

        # 创建取消置顶系统消息
        from utils.system_messages import create_message_unpinned_message
        await create_message_unpinned_message(
            db=db,
            room_id=room_id,
            message_id=message_id,
            unpinned_by=current_user.id,
            unpinned_by_username=current_user.nickname or current_user.username
        )

        logger.info(f"用户 {current_user.username} 取消置顶了消息 {message_id}")
        return {"message": "已取消置顶"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消置顶消息失败: {e}")
        raise HTTPException(status_code=500, detail="取消置顶消息失败")


@router.get("/rooms/{room_id}/pinned-messages", response_model=List[Message])
async def get_pinned_messages(
    room_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(view_chat_rooms)
):
    """获取聊天室置顶消息列表"""
    try:
        # 检查聊天室是否存在
        room_query = select(DBChatRoom).where(DBChatRoom.id == room_id)
        room_result = await db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="聊天室不存在")

        # 检查用户是否有权限查看
        member_query = select(chat_room_members).where(
            and_(
                chat_room_members.c.room_id == room_id,
                chat_room_members.c.user_id == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        user_member = member_result.first()

        if not user_member and room.room_type != RoomType.public:
            raise HTTPException(status_code=403, detail="您不是聊天室成员")

        # 获取置顶消息
        pinned_messages_query = select(DBChatMessage).options(
            selectinload(DBChatMessage.sender)
        ).where(
            and_(
                DBChatMessage.room_id == room_id,
                DBChatMessage.is_pinned == True
            )
        ).order_by(DBChatMessage.pinned_at.desc())

        pinned_messages_result = await db.execute(pinned_messages_query)
        pinned_messages = pinned_messages_result.scalars().all()

        message_list = []
        for message in pinned_messages:
            message_data = Message(
                id=message.id,
                content=message.content,
                message_type=message.message_type.value if hasattr(message.message_type, 'value') else message.message_type,
                sender=UserInfo(
                    id=message.sender.id,
                    username=message.sender.username,
                    nickname=message.sender.nickname,
                    avatar=message.sender.avatar
                ),
                room_id=message.room_id,
                created_at=message.created_at,
                updated_at=message.updated_at,
                is_pinned=message.is_pinned,
                pinned_at=message.pinned_at
            )
            message_list.append(message_data)

        return message_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取置顶消息失败: {e}")
        raise HTTPException(status_code=500, detail="获取置顶消息失败")
