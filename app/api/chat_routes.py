"""
聊天API路由模块

提供聊天室管理和消息相关的API路由，包括：
- 获取聊天室列表
- 创建新聊天室
- 获取聊天室详情
- 加入/退出聊天室
- 发送聊天消息
- 获取历史消息
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status, Request
from pydantic import BaseModel
import os
import uuid
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.auth import get_current_user
from app.db.models import ChatMessage, ChatRoomMember
from app.models.user import User,  ChatRoomCreate , ChatRoom as ChatRoomObj
from app.db.models import ChatRoom
from app.core.database import Database
from app.db.database import get_db
from app.core.logger import get_logger
from app.core.file_manager import FileManager
from app.schemas.chat import (
    ChatRoomResponse, 
    ChatRoomList, 
    ChatMessageCreate, 
    ChatMessageResponse,
    ImageUploadResponse
)

logger = get_logger("chat_routes")
router = APIRouter(prefix="/api/chat", tags=["chat"])
db_instance = None
file_manager = None

# 允许的图片类型
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

# 创建上传目录
UPLOAD_DIR = os.path.join("static", "uploads", "chat")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_router(db: Database, fm: FileManager):
    """初始化路由，设置数据库实例和文件管理器"""
    global db_instance, file_manager
    db_instance = db
    file_manager = fm
    return router

# ===== 聊天室相关模型 =====

class ChatRoomResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_private: bool
    created_by: int
    creator_username: str
    creator_nickname: Optional[str] = None
    member_count: int
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    username: str
    nickname: Optional[str] = None
    message: str
    has_image: bool
    image_path: Optional[str] = None
    created_at: str


class ChatMessageCreate(BaseModel):
    room_id: int
    message: str


# ===== 聊天室API路由 =====

@router.get("/rooms", response_model=ChatRoomList)
async def get_chat_rooms(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天室列表"""
    # 查询所有聊天室
    query = select(ChatRoom).order_by(ChatRoom.created_at.desc())
    result = await session.execute(query)
    rooms = result.scalars().all()
    
    # 过滤私有聊天室
    filtered_rooms = []
    for room in rooms:
        # 如果是公共聊天室，或者用户是聊天室成员，或者用户是管理员
        if not room.is_private or await is_room_member(session, room.id, current_user.id) or current_user.role == "ADMIN":
            filtered_rooms.append(room)
    
    return {"rooms": filtered_rooms}


@router.post("/rooms", )# response_model=ChatRoomResponse
async def create_chat_room(
    room_data: ChatRoomCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建聊天室"""
    # 创建聊天室
    room = ChatRoom(
        # id=room_data.room_id,
        name=room_data.name,
        description=room_data.description,
        is_private=room_data.is_private,
        created_by=current_user.id,
        updated_at=datetime.now(),
        created_at=datetime.now(),
    )
    session.add(room)
    await session.commit()
    await session.refresh(room)
    
    # 将创建者添加为聊天室成员
    member = ChatRoomMember(
        room_id=room.id,
        user_id=current_user.id,
        is_admin=True,
        # created_at=datetime.now(),
        # updated_at=datetime.now()
    )
    session.add(member)
    await session.commit()
    print(123,room)
    return {"message": "聊天室创建成功", "room": room}


@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天室详情"""
    room = await get_room_or_404(session, room_id)
    print(123123)
    # 检查是否有权限访问该聊天室
    if room.is_private and not await is_room_member(session, room_id, current_user.id) and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="没有权限访问该聊天室")
    
    return {"message": "获取聊天室成功", "room": room}


@router.delete("/rooms/{room_id}")
async def delete_chat_room(
    room_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除聊天室"""
    room = await get_room_or_404(session, room_id)
    
    # 检查是否为创建者或管理员
    if room.created_by != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="只有聊天室创建者或系统管理员可以删除聊天室")
    
    # 删除聊天室
    await session.delete(room)
    await session.commit()
    
    return {"message": "聊天室删除成功"}


@router.post("/rooms/{room_id}/members")
async def add_room_member(
    room_id: int,
    user_id: int,
    is_admin: bool = False,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加聊天室成员"""
    room = await get_room_or_404(session, room_id)
    
    # 检查操作者是否为聊天室管理员或系统管理员
    if not await is_room_admin(session, room_id, current_user.id) and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="只有聊天室管理员或系统管理员可以添加成员")
    
    # 检查用户是否存在
    user_query = select(User_DB).where(User_DB.id == user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已经是成员
    if await is_room_member(session, room_id, user_id):
        raise HTTPException(status_code=400, detail="该用户已经是聊天室成员")
    
    # 添加成员
    member = ChatRoomMember(
        room_id=room_id,
        user_id=user_id,
        is_admin=is_admin
    )
    session.add(member)
    await session.commit()
    
    return {"message": "成员添加成功"}


@router.delete("/rooms/{room_id}/members/{user_id}")
async def remove_room_member(
    room_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除聊天室成员"""
    room = await get_room_or_404(session, room_id)
    
    # 检查操作者是否为聊天室管理员或系统管理员，或者是自己
    if not await is_room_admin(session, room_id, current_user.id) and current_user.role != "ADMIN" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="只有聊天室管理员、系统管理员或用户自己可以移除成员")
    
    # 如果是创建者，不能移除
    if room.created_by == user_id and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="不能移除聊天室创建者")
    
    # 检查是否为成员
    member_query = select(ChatRoomMember).where(
        and_(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == user_id
        )
    )
    member_result = await session.execute(member_query)
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="该用户不是聊天室成员")
    
    # 移除成员
    await session.delete(member)
    await session.commit()
    
    return {"message": "成员移除成功"}


@router.get("/rooms/{room_id}/members")
async def get_room_members(
    room_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天室成员列表"""
    room = await get_room_or_404(session, room_id)
    
    # 检查是否有权限访问该聊天室
    if room.is_private and not await is_room_member(session, room_id, current_user.id) and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="没有权限访问该聊天室")
    
    # 查询成员
    query = select(User_DB, ChatRoomMember) \
        .join(ChatRoomMember, User_DB.id == ChatRoomMember.user_id) \
        .where(ChatRoomMember.room_id == room_id) \
        .order_by(ChatRoomMember.is_admin.desc(), User.nickname)
        
    result = await session.execute(query)
    members = []
    
    for user, member in result.fetchall():
        members.append({
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "is_admin": member.is_admin,
            "joined_at": member.created_at,
            "online": False  # 在线状态由WebSocket管理
        })
    
    return {"members": members}

from app.db.models import User as User_DB
@router.get("/rooms/{room_id}/messages")
async def get_room_messages(
    room_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天室消息历史"""
    room = await get_room_or_404(session, room_id)
    
    # 检查是否有权限访问该聊天室
    if room.is_private and not await is_room_member(session, room_id, current_user.id) and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="没有权限访问该聊天室")
    
    # 构建查询
    query = select(ChatMessage) \
        .where(ChatMessage.room_id == room_id) \
        .order_by(ChatMessage.created_at.desc()) \
        .limit(limit)
    
    if before_id:
        before_msg_query = select(ChatMessage).where(ChatMessage.id == before_id)
        before_msg_result = await session.execute(before_msg_query)
        before_msg = before_msg_result.scalar_one_or_none()
        
        if before_msg:
            query = query.where(ChatMessage.created_at < before_msg.created_at)
    
    result = await session.execute(query)
    messages = result.scalars().all()
    
    # 获取用户信息
    user_ids = set(msg.sender_id for msg in messages)
    users_query = select(User_DB).where(User_DB.id.in_(user_ids))
    users_result = await session.execute(users_query)
    users = {user.id: user for user in users_result.scalars().all()}
    
    # 构造响应
    messages_data = []
    for msg in messages:
        user = users.get(msg.sender_id)
        messages_data.append({
            "id": msg.id,
            "room_id": msg.room_id,
            "sender_id": msg.sender_id,
            "username": user.username if user else "未知用户",
            "nickname": user.nickname if user else "未知用户",
            "message_type": msg.message_type,
            "message": msg.content,
            "timestamp": msg.created_at
        })
    
    # 反转顺序，使最新的消息在最后
    messages_data.reverse()
    
    return {"messages": messages_data}


@router.get("/messages")
async def get_private_messages(
    with_user_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取私聊消息历史"""
    # 检查用户是否存在
    user_query = select(User_DB).where(User_DB.id == with_user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 构建查询（获取两个用户之间的消息）
    query = select(ChatMessage) \
        .where(
            and_(
                ChatMessage.room_id.is_(None),
                or_(
                    and_(
                        ChatMessage.sender_id == current_user.id,
                        ChatMessage.receiver_id == with_user_id
                    ),
                    and_(
                        ChatMessage.sender_id == with_user_id,
                        ChatMessage.receiver_id == current_user.id
                    )
                )
            )
        ) \
        .order_by(ChatMessage.created_at.desc()) \
        .limit(limit)
    
    if before_id:
        before_msg_query = select(ChatMessage).where(ChatMessage.id == before_id)
        before_msg_result = await session.execute(before_msg_query)
        before_msg = before_msg_result.scalar_one_or_none()
        
        if before_msg:
            query = query.where(ChatMessage.created_at < before_msg.created_at)
    
    result = await session.execute(query)
    messages = result.scalars().all()
    
    # 获取用户信息
    user_ids = set(msg.sender_id for msg in messages) | {with_user_id}
    users_query = select(User_DB).where(User_DB.id.in_(user_ids))
    users_result = await session.execute(users_query)
    users = {user.id: user for user in users_result.scalars().all()}
    
    # 构造响应
    messages_data = []
    for msg in messages:
        user = users.get(msg.sender_id)
        messages_data.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "username": user.username if user else "未知用户",
            "nickname": user.nickname if user else "未知用户",
            "message_type": msg.message_type,
            "message": msg.content,
            "timestamp": msg.created_at
        })
    
    # 反转顺序，使最新的消息在最后
    messages_data.reverse()
    
    return {"messages": messages_data}


@router.post("/upload_image", response_model=ImageUploadResponse)
async def upload_chat_image(
    request: Request,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传聊天图片"""
    # 检查文件类型
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="只支持JPEG、PNG、GIF和WebP格式的图片")
    
    # 检查文件大小（最大5MB）
    contents = await image.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")
    
    # 重置文件指针
    await image.seek(0)
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{current_user.id}_{timestamp}_{uuid.uuid4().hex}.{image.filename.split('.')[-1]}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)
    
    # 生成URL
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/{file_path.replace(os.sep, '/')}"
    
    return {"image_url": image_url}


# ===== 辅助函数 =====

async def get_room_or_404(session: AsyncSession, room_id: int) -> ChatRoom:
    """获取聊天室或返回404错误"""
    query = select(ChatRoom).where(ChatRoom.id == room_id)
    result = await session.execute(query)
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="聊天室不存在")
    
    return room


async def is_room_member(session: AsyncSession, room_id: int, user_id: int) -> bool:
    """检查用户是否为聊天室成员"""
    query = select(ChatRoomMember).where(
        and_(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == user_id
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def is_room_admin(session: AsyncSession, room_id: int, user_id: int) -> bool:
    """检查用户是否为聊天室管理员"""
    query = select(ChatRoomMember).where(
        and_(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == user_id,
            ChatRoomMember.is_admin == True
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None 