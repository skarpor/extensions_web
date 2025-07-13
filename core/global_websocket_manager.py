"""
全局WebSocket管理器
用于管理用户的全局WebSocket连接，处理各种类型的实时通知
"""

import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
from enum import Enum

logger = logging.getLogger("global_websocket_manager")

class MessageType(str, Enum):
    """消息类型枚举"""
    # 系统消息
    SYSTEM_NOTIFICATION = "system_notification"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    
    # 聊天室相关
    ROOM_CREATED = "room_created"
    ROOM_DELETED = "room_deleted"
    ROOM_UPDATED = "room_updated"
    PRIVATE_ROOM_CREATED = "private_room_created"
    
    # 消息相关
    NEW_MESSAGE = "new_message"
    MESSAGE_UPDATED = "message_updated"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_REACTION = "message_reaction"
    
    # 认证相关
    AUTH_RESPONSE = "auth_response"
    ERROR = "error"

class GlobalWebSocketManager:
    """全局WebSocket管理器"""
    
    def __init__(self):
        # 用户ID -> WebSocket连接
        self.active_connections: Dict[int, WebSocket] = {}
        # 用户在线状态
        self.user_status: Dict[int, datetime] = {}
        # 用户所在的聊天室
        self.user_rooms: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """建立全局WebSocket连接"""
        try:
            # 如果用户已有连接，先断开旧连接
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].close()
                except:
                    pass
            
            # 建立新连接
            self.active_connections[user_id] = websocket
            self.user_status[user_id] = datetime.now()
            
            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            
            logger.info(f"用户 {user_id} 建立全局WebSocket连接")
            
            # 广播用户上线状态
            await self.broadcast_user_status(user_id, True)
            
        except Exception as e:
            logger.error(f"建立全局WebSocket连接失败: {e}")
    
    async def disconnect(self, user_id: int):
        """断开全局WebSocket连接"""
        try:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            
            if user_id in self.user_status:
                del self.user_status[user_id]
            
            if user_id in self.user_rooms:
                del self.user_rooms[user_id]
            
            logger.info(f"用户 {user_id} 断开全局WebSocket连接")
            
            # 广播用户下线状态
            await self.broadcast_user_status(user_id, False)
            
        except Exception as e:
            logger.error(f"断开全局WebSocket连接失败: {e}")
    
    async def send_to_user(self, user_id: int, message_type: MessageType, data: Any):
        """向指定用户发送消息"""
        if user_id not in self.active_connections:
            return False
        
        try:
            message = {
                "type": message_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.active_connections[user_id].send_text(json.dumps(message))
            return True
            
        except Exception as e:
            logger.error(f"向用户 {user_id} 发送消息失败: {e}")
            # 连接可能已断开，清理连接
            await self.disconnect(user_id)
            return False
    
    async def send_to_users(self, user_ids: list, message_type: MessageType, data: Any, exclude_user: int = None):
        """向多个用户发送消息"""
        success_count = 0
        
        for user_id in user_ids:
            if exclude_user and user_id == exclude_user:
                continue
                
            if await self.send_to_user(user_id, message_type, data):
                success_count += 1
        
        return success_count
    
    async def broadcast_to_all(self, message_type: MessageType, data: Any, exclude_user: int = None):
        """向所有在线用户广播消息"""
        user_ids = list(self.active_connections.keys())
        return await self.send_to_users(user_ids, message_type, data, exclude_user)
    
    async def broadcast_to_room_members(self, room_id: int, message_type: MessageType, data: Any, exclude_user: int = None):
        """向聊天室成员广播消息"""
        room_members = []
        
        for user_id, rooms in self.user_rooms.items():
            if room_id in rooms:
                room_members.append(user_id)
        
        return await self.send_to_users(room_members, message_type, data, exclude_user)
    
    async def join_room(self, user_id: int, room_id: int):
        """用户加入聊天室"""
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        
        self.user_rooms[user_id].add(room_id)
        logger.info(f"用户 {user_id} 加入聊天室 {room_id}")
    
    async def leave_room(self, user_id: int, room_id: int):
        """用户离开聊天室"""
        if user_id in self.user_rooms and room_id in self.user_rooms[user_id]:
            self.user_rooms[user_id].remove(room_id)
            logger.info(f"用户 {user_id} 离开聊天室 {room_id}")
    
    async def broadcast_user_status(self, user_id: int, is_online: bool):
        """广播用户在线状态"""
        try:
            status_data = {
                "user_id": user_id,
                "is_online": is_online,
                "timestamp": datetime.now().isoformat()
            }
            
            message_type = MessageType.USER_ONLINE if is_online else MessageType.USER_OFFLINE
            await self.broadcast_to_all(message_type, status_data, exclude_user=user_id)
            
        except Exception as e:
            logger.error(f"广播用户状态失败: {e}")
    
    def get_online_users(self) -> list:
        """获取在线用户列表"""
        return list(self.active_connections.keys())
    
    def is_user_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections
    
    def get_user_rooms(self, user_id: int) -> Set[int]:
        """获取用户所在的聊天室"""
        return self.user_rooms.get(user_id, set())

# 全局WebSocket管理器实例
global_ws_manager = GlobalWebSocketManager()
