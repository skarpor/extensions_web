"""
WebSocket相关的API端点
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Header
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core import auth
from new_app.core.websocket_manager import manager
from new_app.db.session import get_db
from new_app.models.user import User as UserModel


router = APIRouter()

@router.websocket("/ws/chat/{username}")
async def chat_websocket_endpoint(
    websocket: WebSocket,
    username: str,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None)
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
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        
        # 如果没有授权头，尝试从WebSocket参数中获取token
        if not token:
            try:
                # 尝试从查询参数获取token
                params = dict(websocket.query_params)
                token = params.get("token")
            except:
                pass
        
        if not token:
            await websocket.close(code=4001)
            return
            
        # 根据用户名查找用户
        user = await auth.get_by_username(db, username=username)
        if not user:
            await websocket.close(code=4004)
            return
            
        # 验证token
        try:
            auth_user = await auth.get_current_user(token, db)
            if not auth_user or auth_user.id != user.id:
                await websocket.close(code=4003)
                return
        except:
            await websocket.close(code=4002)
            return
        
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