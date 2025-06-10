"""
WebSocket管理器模块
"""
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from jose import jwt, JWTError

from new_app.core.config import settings
from new_app.core.logger import get_logger
from new_app.models.user import User
from new_app.core.auth import ALGORITHM

logger = get_logger("websocket_manager")

class WebSocketManager:
    """WebSocket管理器"""
    
    def __init__(self):
        """初始化WebSocket管理器"""
        self.active_connections: Dict[int, List[WebSocket]] = {}  # 用户ID -> WebSocket连接列表
        self.session_data: Dict[int, Dict[str, Any]] = {}  # 用户ID -> 会话数据
        self.user_rooms: Dict[int, Set[str]] = {}  # 用户ID -> 房间集合
        self.room_users: Dict[str, Set[int]] = {}  # 房间ID -> 用户ID集合
    
    async def authenticate_connection(self, websocket: WebSocket, token: str) -> Optional[User]:
        """验证WebSocket连接"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            if user_id is None:
                return None
            
            # 这里可以添加从数据库获取用户信息的逻辑
            # 为了示例，我们创建一个简单的用户对象
            user = User(id=user_id)
            return user
            
        except JWTError:
            return None
    
    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """建立WebSocket连接
        
        参数:
            websocket: WebSocket连接
            user_id: 用户ID
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        logger.info(f"用户 {user_id} 建立WebSocket连接")
    
    async def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """断开WebSocket连接
        
        参数:
            websocket: WebSocket连接
            user_id: 用户ID
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    
                    # 清理用户相关数据
                    self.session_data.pop(user_id, None)
                    if user_id in self.user_rooms:
                        rooms = self.user_rooms[user_id].copy()
                        for room in rooms:
                            await self.leave_room(user_id, room)
        
        logger.info(f"用户 {user_id} 断开WebSocket连接")
    
    async def send_personal_message(self, message: dict, user_id: int) -> None:
        """发送个人消息"""
        if user_id in self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    disconnected_connections.append(connection)
                except Exception as e:
                    logger.error(f"发送消息给用户 {user_id} 失败: {str(e)}")
                    disconnected_connections.append(connection)
            
            # 处理断开的连接
            for connection in disconnected_connections:
                if user_id in self.active_connections and connection in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(connection)
                    
            # 如果用户没有连接了，清理数据
            if user_id in self.active_connections and not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.session_data.pop(user_id, None)
                if user_id in self.user_rooms:
                    rooms = self.user_rooms[user_id].copy()
                    for room in rooms:
                        await self.leave_room(user_id, room)
    
    async def broadcast(self, message: dict) -> None:
        """广播消息给所有用户"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    async def broadcast_to_users(self, message: dict, user_ids: List[int]) -> None:
        """广播消息给指定用户列表"""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    async def broadcast_to_room(self, room: str, message: dict, exclude_user: Optional[int] = None) -> None:
        """广播消息给房间内的所有用户"""
        if room in self.room_users:
            for user_id in self.room_users[room]:
                if user_id != exclude_user:
                    await self.send_personal_message(message, user_id)
    
    async def join_room(self, user_id: int, room: str) -> None:
        """加入房间"""
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room)
        
        if room not in self.room_users:
            self.room_users[room] = set()
        self.room_users[room].add(user_id)
        
        logger.info(f"用户 {user_id} 加入房间 {room}")
    
    async def leave_room(self, user_id: int, room: str) -> None:
        """离开房间"""
        if user_id in self.user_rooms and room in self.user_rooms[user_id]:
            self.user_rooms[user_id].remove(room)
            if not self.user_rooms[user_id]:
                del self.user_rooms[user_id]
        
        if room in self.room_users and user_id in self.room_users[room]:
            self.room_users[room].remove(user_id)
            if not self.room_users[room]:
                del self.room_users[room]
        
        logger.info(f"用户 {user_id} 离开房间 {room}")
    
    def set_session_data(self, user_id: int, key: str, value: Any) -> None:
        """设置会话数据"""
        if user_id not in self.session_data:
            self.session_data[user_id] = {}
        self.session_data[user_id][key] = value
    
    def get_session_data(self, user_id: int, key: str, default: Any = None) -> Any:
        """获取会话数据"""
        return self.session_data.get(user_id, {}).get(key, default)
    
    def remove_session_data(self, user_id: int, key: str) -> None:
        """移除会话数据"""
        if user_id in self.session_data and key in self.session_data[user_id]:
            del self.session_data[user_id][key]
            if not self.session_data[user_id]:
                del self.session_data[user_id]
    
    def get_active_users(self) -> List[int]:
        """获取活跃用户列表"""
        return list(self.active_connections.keys())
    
    def get_room_users(self, room: str) -> List[int]:
        """获取房间内的用户列表"""
        return list(self.room_users.get(room, set()))
    
    def get_user_rooms(self, user_id: int) -> List[str]:
        """获取用户加入的房间列表"""
        return list(self.user_rooms.get(user_id, set()))
    
    def is_user_connected(self, user_id: int) -> bool:
        """检查用户是否已连接"""
        return user_id in self.active_connections
    
    def is_user_in_room(self, user_id: int, room: str) -> bool:
        """检查用户是否在指定房间中"""
        return room in self.user_rooms.get(user_id, set())
    
    async def handle_disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """处理连接断开"""
        try:
            await websocket.close()
        except Exception:
            pass
        
        if user_id in self.active_connections and websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.session_data.pop(user_id, None)
                if user_id in self.user_rooms:
                    rooms = self.user_rooms[user_id].copy()
                    for room in rooms:
                        await self.leave_room(user_id, room)
        
        logger.info(f"处理用户 {user_id} 的连接断开")

# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager() 