"""
WebSocket相关的API端点
"""
import os
import uuid
from datetime import datetime
from typing import Any, Optional

import aiofiles
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi import Request, UploadFile, File
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core import auth
from new_app.core.auth import get_current_user
from new_app.core.chat import is_room_member, get_room_or_404, is_room_admin
from new_app.core.config import settings
from new_app.core.websocket_manager import manager
from new_app.db.session import get_db
from new_app.models.chat import ChatMessage, ChatRoom, ChatRoomMember
from new_app.models.user import User as UserModel, User
from new_app.schemas.chat import ImageUploadResponse, ChatRoomList, ChatRoomCreate, ChatRoomResponse

router = APIRouter()

@router.websocket("/chat/{username}")
async def chat_websocket_endpoint(
    websocket: WebSocket,
    username: str,
    db: AsyncSession = Depends(get_db),
    # authorization: Optional[str] = Header(None)
    # user: User = Depends(get_current_user)
):
    """
    聊天WebSocket连接端点
    
    参数:
        websocket: WebSocket连接
        username: 用户名
        db: 数据库会话
        authorization: 授权头，格式为"Bearer {token}"
    """
    try:
        # 从授权头中提取token
        token = None
        # if authorization and authorization.startswith("Bearer "):
        #     token = authorization.replace("Bearer ", "")
        # print(authorization,token)
        user = await auth.get_user_by_username(db,username)
        # if not user:
        #     return
        # 如果没有授权头，尝试从WebSocket参数中获取token
        # if not token:
        #     try:
        #         # 尝试从查询参数获取token
        #         params = dict(websocket.query_params)
        #         token = params.get("token")
        #     except:
        #         pass
        #
        # if not token:
        #     await websocket.close(code=4001)
        #     return

        # 根据用户名查找用户
        # user = await auth.get_by_username(db, username=username)
        if not user:
            await websocket.close(code=4004)
            return
            
        # 验证token
        # try:
        #     auth_user = await auth.get_current_user(token, db)
        #     if not auth_user or auth_user.id != user.id:
        #         await websocket.close(code=4003)
        #         return
        # except:
        #     await websocket.close(code=4002)
        #     return
        
        # 建立连接
        await manager.connect(websocket, user.id)
        
        # 发送初始消息
        await websocket.send_json({
            "type": "system",
            "message": "已连接到聊天服务器"
        })
        
        # 发送在线用户列表
        await websocket.send_json({
            "type": "users_list",
            "users": [
                {
                    "id": user_id,
                    "username": f"user_{user_id}",  # 简化处理，实际应从数据库获取
                    "status": "online"
                }
                for user_id in manager.get_active_users()
                if user_id != user.id  # 不包括当前用户
            ]
        })
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_json()
                
                # 处理不同类型的消息
                message_type = data.get("type")
                
                if message_type == "chat":
                    # 处理聊天消息
                    if "room_id" in data:
                        # 群聊消息
                        room_id = data["room_id"]
                        await manager.broadcast_to_room(
                            room=f"room_{room_id}",
                            message={
                                "type": "chat",
                                "room_id": room_id,
                                "sender_id": user.id,
                                "username": user.username,
                                "nickname": getattr(user, "nickname", user.username),
                                "message_type": data.get("message_type", "text"),
                                "message": data.get("message", ""),
                                "timestamp": data.get("timestamp", None)
                            },
                            exclude_user=None  # 包括发送者
                        )
                    elif "receiver_id" in data:
                        # 私聊消息
                        receiver_id = data["receiver_id"]
                        message = {
                            "type": "chat",
                            "sender_id": user.id,
                            "receiver_id": receiver_id,
                            "username": user.username,
                            "nickname": getattr(user, "nickname", user.username),
                            "message_type": data.get("message_type", "text"),
                            "message": data.get("message", ""),
                            "timestamp": data.get("timestamp", None)
                        }
                        
                        # 发送给接收者
                        await manager.send_personal_message(message, receiver_id)
                        
                        # 也发送给发送者（回显）
                        await websocket.send_json(message)
                
                elif message_type == "join_room":
                    # 加入聊天室
                    room_id = data.get("room_id")
                    if room_id:
                        room_name = f"room_{room_id}"
                        await manager.join_room(user.id, room_name)
                        
                        # 通知房间其他成员
                        await manager.broadcast_to_room(
                            room=room_name,
                            message={
                                "type": "user_join",
                                "room_id": room_id,
                                "user": {
                                    "id": user.id,
                                    "username": user.username,
                                    "nickname": getattr(user, "nickname", user.username)
                                }
                            },
                            exclude_user=user.id
                        )
                
                elif message_type == "leave_room":
                    # 离开聊天室
                    room_id = data.get("room_id")
                    if room_id:
                        room_name = f"room_{room_id}"
                        
                        # 通知房间其他成员
                        await manager.broadcast_to_room(
                            room=room_name,
                            message={
                                "type": "user_leave",
                                "room_id": room_id,
                                "user_id": user.id
                            },
                            exclude_user=user.id
                        )
                        
                        await manager.leave_room(user.id, room_name)
                
                elif message_type == "typing":
                    # 正在输入状态
                    if "room_id" in data:
                        # 群聊中的输入状态
                        room_id = data["room_id"]
                        await manager.broadcast_to_room(
                            room=f"room_{room_id}",
                            message={
                                "type": "typing",
                                "room_id": room_id,
                                "user_id": user.id,
                                "username": user.username,
                                "nickname": getattr(user, "nickname", user.username),
                                "is_typing": data.get("is_typing", True)
                            },
                            exclude_user=user.id
                        )
                    elif "receiver_id" in data:
                        # 私聊中的输入状态
                        receiver_id = data["receiver_id"]
                        await manager.send_personal_message(
                            {
                                "type": "typing",
                                "sender_id": user.id,
                                "username": user.username,
                                "nickname": getattr(user, "nickname", user.username),
                                "is_typing": data.get("is_typing", True)
                            },
                            receiver_id
                        )
                
                elif message_type == "get_members":
                    # 获取聊天室成员
                    room_id = data.get("room_id")
                    if room_id:
                        room_name = f"room_{room_id}"
                        members = manager.get_room_users(room_name)
                        
                        # 简化处理，实际应从数据库获取用户详情
                        await websocket.send_json({
                            "type": "members_list",
                            "room_id": room_id,
                            "members": [
                                {
                                    "id": member_id,
                                    "username": f"user_{member_id}",
                                    "status": "online"
                                }
                                for member_id in members
                            ]
                        })
                
                elif message_type == "ping":
                    # 心跳检测
                    await websocket.send_json({"type": "pong"})
                
                elif message_type == "get_online_users":
                    # 获取在线用户列表
                    await websocket.send_json({
                        "type": "users_list",
                        "users": manager.get_online_users()
                    })
                else:
                    # 未知消息类型，回显
                    await websocket.send_json({
                        "type": "echo",
                        "data": data
                    })
        
        except WebSocketDisconnect:
            # 处理WebSocket断开连接
            for room in manager.get_user_rooms(user.id):
                # 通知房间其他成员
                await manager.broadcast_to_room(
                    room=room,
                    message={
                        "type": "user_leave",
                        "room_id": room.replace("room_", ""),
                        "user_id": user.id
                    },
                    exclude_user=user.id
                )
            
            # 断开连接
            await manager.disconnect(websocket, user.id)
    
    except Exception as e:
        # 记录错误并关闭连接
        print(f"Chat WebSocket错误: {str(e)}")
        try:
            await websocket.close(code=4000)
        except:
            pass

@router.get("/active-users")
async def get_active_users(
    current_user: UserModel = Depends(auth.get_current_superuser),
) -> Any:
    """
    获取当前活跃用户列表（仅超级管理员）
    
    返回:
        含活跃用户ID列表的字典
    """
    return {
        "active_users": manager.get_active_users()
    }


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
        if not room.is_private or await is_room_member(session, room.id,
                                                       current_user.id) or current_user.role == "ADMIN":
            filtered_rooms.append(room)

    return {"rooms": filtered_rooms}


@router.post("/rooms", )  # response_model=ChatRoomResponse
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
    if not await is_room_admin(session, room_id,
                               current_user.id) and current_user.role != "ADMIN" and current_user.id != user_id:
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
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
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
    file_path = os.path.join(settings.CHAT_UPLOAD_DIR, filename)

    # 保存文件
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    # 生成URL
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/{file_path.replace(os.sep, '/')}"

    return {"image_url": image_url}


