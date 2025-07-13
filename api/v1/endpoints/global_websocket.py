"""
全局WebSocket端点
处理用户的全局WebSocket连接
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.global_websocket_manager import global_ws_manager, MessageType
from core.websocket_auth import authenticate_websocket
from db.session import get_db
from models.user import User as DBUser

logger = logging.getLogger("global_websocket")
router = APIRouter()

@router.websocket("/global-ws")
async def global_websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """全局WebSocket连接端点"""
    await websocket.accept()
    user = None
    user_id = None
    
    try:
        # WebSocket认证
        success, user, error = await authenticate_websocket(websocket)
        if not success or not user:
            await websocket.close(code=4001, reason=error or "认证失败")
            return
        
        user_id = user.id
        logger.info(f"全局WebSocket认证成功: 用户 {user.username} (ID: {user_id})")
        
        # 建立全局连接
        await global_ws_manager.connect(websocket, user_id)
        
        # 发送认证成功响应
        await global_ws_manager.send_to_user(
            user_id,
            MessageType.AUTH_RESPONSE,
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname
                },
                "message": "全局WebSocket连接成功"
            }
        )
        
        # 处理消息循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理不同类型的消息
                await handle_global_message(user_id, message, db)
                
            except WebSocketDisconnect:
                logger.info(f"用户 {user.username} 主动断开全局WebSocket连接")
                break
            except json.JSONDecodeError:
                logger.error(f"用户 {user_id} 发送的消息格式错误")
                await global_ws_manager.send_to_user(
                    user_id,
                    MessageType.ERROR,
                    {"message": "消息格式错误"}
                )
            except Exception as e:
                logger.error(f"处理全局WebSocket消息时出错: {e}")
                await global_ws_manager.send_to_user(
                    user_id,
                    MessageType.ERROR,
                    {"message": "处理消息时出错"}
                )
    
    except WebSocketDisconnect:
        logger.info(f"用户断开全局WebSocket连接")
    except Exception as e:
        logger.error(f"全局WebSocket连接出错: {e}")
    finally:
        # 清理连接
        if user_id:
            await global_ws_manager.disconnect(user_id)

async def handle_global_message(user_id: int, message: dict, db: AsyncSession):
    """处理全局WebSocket消息"""
    try:
        message_type = message.get("type")
        data = message.get("data", {})
        
        if message_type == "ping":
            # 心跳检测
            await global_ws_manager.send_to_user(
                user_id,
                MessageType.SYSTEM_NOTIFICATION,
                {"message": "pong"}
            )
        
        elif message_type == "join_room":
            # 加入聊天室
            room_id = data.get("room_id")
            if room_id:
                await global_ws_manager.join_room(user_id, room_id)
                await global_ws_manager.send_to_user(
                    user_id,
                    MessageType.SYSTEM_NOTIFICATION,
                    {"message": f"已加入聊天室 {room_id}"}
                )
        
        elif message_type == "leave_room":
            # 离开聊天室
            room_id = data.get("room_id")
            if room_id:
                await global_ws_manager.leave_room(user_id, room_id)
                await global_ws_manager.send_to_user(
                    user_id,
                    MessageType.SYSTEM_NOTIFICATION,
                    {"message": f"已离开聊天室 {room_id}"}
                )
        
        elif message_type == "get_online_users":
            # 获取在线用户列表
            online_users = global_ws_manager.get_online_users()
            await global_ws_manager.send_to_user(
                user_id,
                MessageType.SYSTEM_NOTIFICATION,
                {"online_users": online_users}
            )
        
        else:
            logger.warning(f"未知的全局消息类型: {message_type}")
            await global_ws_manager.send_to_user(
                user_id,
                MessageType.ERROR,
                {"message": f"未知的消息类型: {message_type}"}
            )
    
    except Exception as e:
        logger.error(f"处理全局消息失败: {e}")
        await global_ws_manager.send_to_user(
            user_id,
            MessageType.ERROR,
            {"message": "处理消息失败"}
        )
