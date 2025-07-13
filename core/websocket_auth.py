#!/usr/bin/env python3
"""
WebSocket认证工具函数
"""

import json
import asyncio
from typing import Optional, Tuple
from fastapi import WebSocket
from models.user import User as DBUser
from core.auth import get_current_user_from_token
from core.logger import get_logger

logger = get_logger(__name__)

async def authenticate_websocket(websocket: WebSocket, timeout: float = 10.0) -> Tuple[bool, Optional[DBUser], Optional[str]]:
    """
    WebSocket认证函数
    
    Args:
        websocket: WebSocket连接对象
        timeout: 认证超时时间（秒）
    
    Returns:
        Tuple[bool, Optional[DBUser], Optional[str]]: (是否认证成功, 用户对象, 错误信息)
    """
    try:
        # 等待认证消息
        auth_data = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
        auth_message = json.loads(auth_data)
        
        # 检查消息类型
        if auth_message.get("type") != "auth":
            return False, None, "需要认证消息"
        
        # 获取token
        token = auth_message.get("token")
        if not token:
            return False, None, "缺少认证令牌"
        
        # 验证用户身份
        user = await get_current_user_from_token(token)
        if not user:
            return False, None, "认证失败"
        
        logger.info(f"WebSocket认证成功: 用户 {user.username} (ID: {user.id})")
        return True, user, None
        
    except asyncio.TimeoutError:
        return False, None, "认证超时"
    except json.JSONDecodeError:
        return False, None, "认证消息格式错误"
    except Exception as e:
        logger.error(f"WebSocket认证过程出错: {e}")
        return False, None, f"认证过程出错: {str(e)}"

async def send_auth_response(websocket: WebSocket, success: bool, user: Optional[DBUser] = None, error: Optional[str] = None, extra_data: dict = None):
    """
    发送认证响应消息
    
    Args:
        websocket: WebSocket连接对象
        success: 认证是否成功
        user: 用户对象（认证成功时）
        error: 错误信息（认证失败时）
        extra_data: 额外数据
    """
    try:
        response_data = {
            "type": "auth_response",
            "success": success,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        if success and user:
            response_data["user"] = {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname
            }
            response_data["message"] = "认证成功"
        else:
            response_data["error"] = error or "认证失败"
        
        if extra_data:
            response_data.update(extra_data)
        
        await websocket.send_text(json.dumps(response_data))
        
    except Exception as e:
        logger.error(f"发送认证响应失败: {e}")

class WebSocketAuthenticator:
    """WebSocket认证器类"""
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.authenticated_users = {}  # {websocket: user}
    
    async def authenticate(self, websocket: WebSocket) -> Tuple[bool, Optional[DBUser]]:
        """
        认证WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
        
        Returns:
            Tuple[bool, Optional[DBUser]]: (是否认证成功, 用户对象)
        """
        success, user, error = await authenticate_websocket(websocket, self.timeout)
        
        if success and user:
            self.authenticated_users[websocket] = user
            await send_auth_response(websocket, True, user)
            return True, user
        else:
            await send_auth_response(websocket, False, error=error)
            return False, None
    
    def get_user(self, websocket: WebSocket) -> Optional[DBUser]:
        """获取WebSocket连接对应的用户"""
        return self.authenticated_users.get(websocket)
    
    def is_authenticated(self, websocket: WebSocket) -> bool:
        """检查WebSocket连接是否已认证"""
        return websocket in self.authenticated_users
    
    def remove_connection(self, websocket: WebSocket):
        """移除WebSocket连接"""
        if websocket in self.authenticated_users:
            user = self.authenticated_users[websocket]
            del self.authenticated_users[websocket]
            logger.info(f"移除WebSocket连接: 用户 {user.username} (ID: {user.id})")

# 全局认证器实例
websocket_authenticator = WebSocketAuthenticator()

async def require_websocket_auth(websocket: WebSocket) -> Optional[DBUser]:
    """
    装饰器风格的WebSocket认证要求
    
    Args:
        websocket: WebSocket连接对象
    
    Returns:
        Optional[DBUser]: 认证成功返回用户对象，失败返回None
    """
    if websocket_authenticator.is_authenticated(websocket):
        return websocket_authenticator.get_user(websocket)
    
    success, user = await websocket_authenticator.authenticate(websocket)
    return user if success else None

class WebSocketMessage:
    """WebSocket消息包装类"""
    
    def __init__(self, message_type: str, data: dict = None, user_id: int = None, room_id: int = None):
        self.type = message_type
        self.data = data or {}
        self.user_id = user_id
        self.room_id = room_id
        self.timestamp = asyncio.get_event_loop().time()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "type": self.type,
            "data": self.data,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict())
    
    async def send(self, websocket: WebSocket):
        """发送消息到WebSocket"""
        try:
            await websocket.send_text(self.to_json())
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")

def create_system_message(message: str, **kwargs) -> WebSocketMessage:
    """创建系统消息"""
    return WebSocketMessage(
        message_type="system_message",
        data={"message": message, **kwargs}
    )

def create_error_message(error: str, **kwargs) -> WebSocketMessage:
    """创建错误消息"""
    return WebSocketMessage(
        message_type="error",
        data={"error": error, **kwargs}
    )

def create_user_message(message_type: str, user: DBUser, data: dict = None, **kwargs) -> WebSocketMessage:
    """创建用户消息"""
    message_data = {
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname
        }
    }
    if data:
        message_data.update(data)
    
    return WebSocketMessage(
        message_type=message_type,
        data=message_data,
        user_id=user.id,
        **kwargs
    )
