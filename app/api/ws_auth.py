"""
WebSocket认证模块

提供WebSocket连接的认证功能。
"""

import jwt
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, status
from config import JWT_SECRET_KEY
from app.models.user import User
from app.core.logger import get_logger
from app.core.database import Database

logger = get_logger("ws_auth")

class WebSocketException(Exception):
    """WebSocket异常类"""
    def __init__(self, code: int, message: str = None):
        self.code = code
        self.message = message
        super().__init__(message)

async def get_current_user_ws(websocket: WebSocket) -> User:
    """
    从WebSocket连接中获取当前用户
    
    Args:
        websocket: WebSocket连接
        
    Returns:
        User: 当前用户
    
    Raises:
        WebSocketException: 如果认证失败，将导致WebSocket连接关闭
    """
    try:
        # 从cookie中获取token
        token = websocket.cookies.get("access_token")
        if not token:
            logger.warning("WebSocket认证失败: 缺少令牌")
            raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED, message="认证失败: 缺少令牌")
        
        # 移除 "Bearer " 前缀（如果存在）
        if token.startswith("Bearer "):
            token = token[7:]
        
        # 解码并验证令牌
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        
        if not username:
            logger.warning("WebSocket认证失败: 令牌缺少用户名")
            raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED, message="认证失败: 令牌缺少用户名")
        
        # 检查token是否过期
        expiration = payload.get("exp")
        if expiration is None or datetime.fromtimestamp(expiration) < datetime.now():
            logger.warning("WebSocket认证失败: 令牌已过期")
            raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED, message="认证失败: 令牌已过期")
        
        # 获取数据库实例
        from app.main import app
        db: Database = app.state.db
        
        # 验证用户是否存在
        user = db.get_user_by_username(username)
        if not user:
            logger.warning(f"WebSocket认证失败: 用户 {username} 不存在")
            raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED, message="认证失败: 用户不存在")
        
        # 返回用户对象
        return User(
            id=user["id"],
            username=user["username"],
            nickname=user["nickname"],
            role=user["role"],
            email=user["email"],
            avatar=user["avatar"]
        )
        
    except jwt.PyJWTError as e:
        logger.warning(f"WebSocket认证失败: 令牌无效 - {str(e)}")
        raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED, message="认证失败: 令牌无效")
    except Exception as e:
        logger.error(f"WebSocket认证时发生错误: {str(e)}")
        raise WebSocketException(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="服务器内部错误") 