"""
WebSocket模块

提供WebSocket连接支持，主要用于实时聊天功能。
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from app.core.auth import get_current_active_user
from app.models.user import User

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接: {用户ID: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # 用户信息: {用户ID: 用户信息}
        self.users: Dict[int, dict] = {}
        # 正在输入的用户: {用户ID}
        self.typing_users: Set[int] = set()
    
    async def connect(self, websocket: WebSocket, user: User):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections[user.id] = websocket
        self.users[user.id] = {
            "id": user.id,
            "username": user.username,
            "nickname": getattr(user, "nickname", None) or user.username,
            "role": user.role,
            "online": True,
            "last_seen": datetime.now().isoformat()
        }
    
    def disconnect(self, user_id: int):
        """关闭WebSocket连接"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # 将用户标记为离线但保留用户信息
        if user_id in self.users:
            self.users[user_id]["online"] = False
            self.users[user_id]["last_seen"] = datetime.now().isoformat()
        
        # 移除正在输入状态
        if user_id in self.typing_users:
            self.typing_users.remove(user_id)
    
    async def send_personal_message(self, message: dict, user_id: int):
        """发送个人消息"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))
    
    async def broadcast(self, message: dict, exclude: Optional[int] = None):
        """广播消息给所有连接的客户端"""
        for user_id, connection in self.active_connections.items():
            if exclude is None or user_id != exclude:
                await connection.send_text(json.dumps(message))
    
    async def update_typing_status(self, user_id: int, is_typing: bool):
        """更新用户输入状态"""
        if is_typing:
            self.typing_users.add(user_id)
        elif user_id in self.typing_users:
            self.typing_users.remove(user_id)
        
        # 广播输入状态变化
        user_info = self.users.get(user_id, {})
        await self.broadcast({
            "type": "typing",
            "username": user_info.get("username", ""),
            "nickname": user_info.get("nickname", ""),
            "isTyping": is_typing
        }, exclude=user_id)
    
    def update_nickname(self, user_id: int, nickname: str):
        """更新用户昵称"""
        if user_id in self.users:
            self.users[user_id]["nickname"] = nickname
    
    def get_users_list(self):
        """获取用户列表"""
        return list(self.users.values())


# 创建连接管理器实例
manager = ConnectionManager()


async def handle_chat_message(websocket: WebSocket, data: dict, user: User):
    """处理聊天消息"""
    message_type = data.get("type", "")
    
    if message_type == "message":
        # 处理普通聊天消息
        message_content = data.get("message", "").strip()
        if message_content:
            # 准备消息数据
            message_data = {
                "type": "message",
                "username": user.username,
                "nickname": manager.users[user.id]["nickname"],
                "message": message_content,
                "time": datetime.now().isoformat()
            }
            # 广播给所有用户
            await manager.broadcast(message_data)
    
    elif message_type == "typing":
        # 处理正在输入状态
        is_typing = data.get("isTyping", False)
        await manager.update_typing_status(user.id, is_typing)
    
    elif message_type == "nickname":
        # 处理昵称更新
        nickname = data.get("nickname", "").strip() or user.username
        manager.update_nickname(user.id, nickname)
        
        # 通知所有用户列表更新
        await manager.broadcast({
            "type": "users",
            "users": manager.get_users_list()
        })


async def chat_endpoint(websocket: WebSocket, user: User = Depends(get_current_user_ws)):
    """聊天WebSocket端点"""
    await manager.connect(websocket, user)
    
    # 广播用户加入消息
    await manager.broadcast({
        "type": "join",
        "username": user.username,
        "nickname": manager.users[user.id]["nickname"],
        "users": manager.get_users_list()
    })
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            try:
                # 解析JSON数据
                message_data = json.loads(data)
                # 处理消息
                await handle_chat_message(websocket, message_data, user)
            except json.JSONDecodeError:
                # JSON解析错误，忽略消息
                pass
    except WebSocketDisconnect:
        # 处理连接断开
        manager.disconnect(user.id)
        # 广播用户离开消息
        await manager.broadcast({
            "type": "leave",
            "username": user.username,
            "nickname": manager.users[user.id]["nickname"],
            "users": manager.get_users_list()
        })