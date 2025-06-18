"""
WebSocket管理器模块
"""
from datetime import datetime
import json
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.logger import get_logger
from models.user import User
from core.auth import ALGORITHM, get_user_by_id, get_user_by_username
from db.session import get_db
logger = get_logger("websocket_manager")

class WebSocketManager:
    """WebSocket管理器"""
    
    def __init__(self):
        """初始化WebSocket管理器"""
        self.active_connections: Dict[int, List[WebSocket]] = {}  # 用户ID -> WebSocket连接列表
        self.session_data: Dict[int, Dict[str, Any]] = {}  # 用户ID -> 会话数据
        self.user_rooms: Dict[int, Set[str]] = {}  # 用户ID -> 房间集合
        self.room_users: Dict[str, Set[int]] = {}  # 房间ID -> 用户ID集合
    
    async def authenticate_connection(self, websocket: WebSocket, token: str,db: AsyncSession = Depends(get_db)) -> Optional[User]:
        """验证WebSocket连接"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_name: str = payload.get("sub")
            if user_name is None:
                return None
            
            # 这里可以添加从数据库获取用户信息的逻辑
            user = await get_user_by_username(db, username=user_name)
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
    
    async def disconnect(self, websocket: WebSocket, user_id: int,db: AsyncSession = Depends(get_db)) -> None:
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
    
    async def send_personal_message(self, message: dict, user_id: int,db: AsyncSession = Depends(get_db)) -> None:
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
    
    async def broadcast(self, message: dict,db: AsyncSession = Depends(get_db)) -> None:
        """广播消息给所有用户"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id,db)
    
    async def broadcast_to_users(self, message: dict, user_ids: List[int],db: AsyncSession = Depends(get_db)) -> None:
        """广播消息给指定用户列表"""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id,db)
    
    async def broadcast_to_room(self, room: str, message: dict, exclude_user: Optional[int] = None,db: AsyncSession = Depends(get_db)) -> None:
        """广播消息给房间内的所有用户"""
        if room in self.room_users:
            for user_id in self.room_users[room]:
                if user_id != exclude_user:
                    await self.send_personal_message(message, user_id,db)
    
    async def join_room(self, user_id: int, room: str,db: AsyncSession = Depends(get_db)) -> None:
        """加入房间"""
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room)
        
        if room not in self.room_users:
            self.room_users[room] = set()
        self.room_users[room].add(user_id)
        
        logger.info(f"用户 {user_id} 加入房间 {room}")
    
    async def leave_room(self, user_id: int, room: str,db: AsyncSession = Depends(get_db)) -> None:
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
    
    def set_session_data(self, user_id: int, key: str, value: Any,db: AsyncSession = Depends(get_db)) -> None:
        """设置会话数据"""
        if user_id not in self.session_data:
            self.session_data[user_id] = {}
        self.session_data[user_id][key] = value
    
    def get_session_data(self, user_id: int, key: str, default: Any = None,db: AsyncSession = Depends(get_db)) -> Any:
        """获取会话数据"""
        return self.session_data.get(user_id, {}).get(key, default)
    
    def remove_session_data(self, user_id: int, key: str,db: AsyncSession = Depends(get_db)) -> None:
        """移除会话数据，是否是撤回信息"""

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
    
    def get_online_users(self) -> List[int]:
        """获取在线用户列表"""
        return list(self.active_connections.keys())
    
    def get_room_members(self, room_id: int) -> List[str]:
        """获取房间成员列表"""
        return list(self.room_users.get(room_id, set()))

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
# manager = WebSocketManager() 


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃的连接: {username: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 用户ID映射: {username: user_id}
        self.user_ids: Dict[str, int] = {}
        
        # 用户昵称映射: {username: nickname}
        self.user_nicknames: Dict[str, str] = {}
        
        # 聊天室成员: {room_id: set(username)}
        self.room_members: Dict[int, Set[str]] = {}
        
        # 在线用户的详细信息: {user_id: {username, nickname, ...}}
        self.online_users: Dict[int, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, username: str):
        """建立WebSocket连接"""
        # 接受连接
        await websocket.accept()
        
        # 如果用户已经有一个连接，关闭旧连接
        if username in self.active_connections:
            try:
                await self.active_connections[username].close(code=1000)
                logger.info(f"关闭用户 {username} 的旧连接")
            except Exception as e:
                logger.error(f"关闭旧连接时出错: {str(e)}")
        
        # 添加到活跃连接
        self.active_connections[username] = websocket
        logger.info(f"用户 {username} 已连接")
    
    async def disconnect(self, username: str):
        """关闭WebSocket连接"""
        # 从活跃连接中移除
        if username in self.active_connections:
            del self.active_connections[username]
            logger.info(f"用户 {username} 已断开连接")
        
        # 从用户ID映射中移除
        user_id = self.user_ids.pop(username, None)
        if user_id:
            self.online_users.pop(user_id, None)
        
        # 从用户昵称映射中移除
        self.user_nicknames.pop(username, None)
        
        # 从所有聊天室中移除
        for room_id in list(self.room_members.keys()):
            if username in self.room_members[room_id]:
                await self.leave_room(username, room_id)
    
    async def send_personal_message(self, message: Dict, username: str):
        """发送个人消息"""
        if username in self.active_connections:
            await self.active_connections[username].send_text(json.dumps(message))
    
    async def broadcast(self, message: Dict):
        """广播消息给所有连接的用户"""
        disconnected_users = []
        
        for username, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"向用户 {username} 发送消息时出错: {str(e)}")
                disconnected_users.append(username)
        
        # 移除断开的连接
        for username in disconnected_users:
            await self.disconnect(username)
    
    async def broadcast_to_room(self, message: Dict, room_id: int):
        """广播消息给聊天室的所有成员"""
        if room_id not in self.room_members:
            return
        
        disconnected_users = []
        
        for username in self.room_members[room_id]:
            try:
                if username in self.active_connections:
                    await self.active_connections[username].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"向聊天室 {room_id} 的成员 {username} 发送消息时出错: {str(e)}")
                disconnected_users.append(username)
        
        # 移除断开的连接
        for username in disconnected_users:
            await self.disconnect(username)
    
    async def join_room(self, username: str, room_id: int):
        """用户加入聊天室"""
        # 确保聊天室存在
        if room_id not in self.room_members:
            self.room_members[room_id] = set()
        
        # 将用户添加到聊天室
        self.room_members[room_id].add(username)
        
        # 通知聊天室其他成员
        nickname = self.user_nicknames.get(username, username)
        await self.broadcast_to_room({
            "type": "user_join",
            "username": username,
            "nickname": nickname,
            "room_id": room_id,
            "timestamp": datetime.now().isoformat()
        }, room_id)
        
        logger.info(f"用户 {username} 加入聊天室 {room_id}")
    
    async def leave_room(self, username: str, room_id: int):
        """用户离开聊天室"""
        if room_id in self.room_members and username in self.room_members[room_id]:
            # 从聊天室移除用户
            self.room_members[room_id].remove(username)
            
            # 如果聊天室为空，移除聊天室
            if not self.room_members[room_id]:
                del self.room_members[room_id]
            else:
                # 通知聊天室其他成员
                nickname = self.user_nicknames.get(username, username)
                await self.broadcast_to_room({
                    "type": "user_leave",
                    "username": username,
                    "nickname": nickname,
                    "room_id": room_id,
                    "timestamp": datetime.now().isoformat()
                }, room_id)
            
            logger.info(f"用户 {username} 离开聊天室 {room_id}")
    
    def set_user_info(self, username: str, user_id: int, nickname: Optional[str] = None):
        """设置用户信息"""
        self.user_ids[username] = user_id
        if nickname:
            self.user_nicknames[username] = nickname
        
        # 更新在线用户信息
        self.online_users[user_id] = {
            "id": user_id,
            "username": username,
            "nickname": nickname or username,
            "online": True
        }
    
    def get_online_users(self) -> List[Dict]:
        """获取所有在线用户"""
        return list(self.online_users.values())
    
    def get_room_members(self, room_id: int) -> List[str]:
        """获取聊天室成员的用户名列表"""
        if room_id not in self.room_members:
            return []
        return list(self.room_members[room_id])


# 创建连接管理器实例
manager = ConnectionManager()


from models.chat import ChatMessage,ChatRoom,ChatRoomMember
async def handle_chat_message(session: AsyncSession, username: str, user_id: int, message_data: Dict):
    """处理聊天消息"""
    try:
        message_type = message_data.get("message_type", "text")
        content = message_data.get("message", "")
        room_id = message_data.get("room_id")
        receiver_id = message_data.get("receiver_id")
        
        # 空消息不处理
        if not content:
            return
        
        # 获取用户昵称
        nickname = manager.user_nicknames.get(username, username)
        
        # 创建消息记录
        chat_message = ChatMessage(
            sender_id=user_id,
            room_id=room_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content
        )
        session.add(chat_message)
        await session.commit()
        await session.refresh(chat_message)
        
        # 构建响应消息
        response_message = {
            "type": "chat",
            "id": chat_message.id,
            "sender_id": user_id,
            "username": username,
            "nickname": nickname,
            "message_type": message_type,
            "message": content,
            "timestamp": chat_message.created_at.isoformat()
        }
        
        if room_id:
            # 聊天室消息
            response_message["room_id"] = room_id
            await manager.broadcast_to_room(response_message, room_id)
        elif receiver_id:
            # 私聊消息
            response_message["receiver_id"] = receiver_id
            
            # 发送给接收者
            receiver_username = None
            for uname, uid in manager.user_ids.items():
                if uid == receiver_id:
                    receiver_username = uname
                    break
            
            if receiver_username:
                await manager.send_personal_message(response_message, receiver_username)
            
            # 发送给发送者
            await manager.send_personal_message(response_message, username)
    
    except Exception as e:
        logger.error(f"处理聊天消息时出错: {str(e)}")


async def handle_join_room(session: AsyncSession, username: str, user_id: int, room_id: int):
    """处理加入聊天室请求"""
    try:
        # 查询聊天室是否存在
        from sqlalchemy import select, and_
        room_query = select(ChatRoom).where(ChatRoom.id == room_id)
        room_result = await session.execute(room_query)
        room = room_result.scalar_one_or_none()
        
        if not room:
            await manager.send_personal_message({
                "type": "system",
                "message": f"聊天室 {room_id} 不存在"
            }, username)
            return
        
        # 检查是否为私有聊天室，如果是则检查用户是否为成员
        if room.is_private:
            member_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == room_id,
                    ChatRoomMember.user_id == user_id
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member:
                await manager.send_personal_message({
                    "type": "system",
                    "message": "您不是该私有聊天室的成员"
                }, username)
                return
        
        # 加入聊天室
        await manager.join_room(username, room_id)
    
    except Exception as e:
        logger.error(f"处理加入聊天室请求时出错: {str(e)}")


async def handle_typing_status(username: str, user_id: int, message_data: Dict):
    """处理正在输入状态"""
    try:
        is_typing = message_data.get("isTyping", False)
        room_id = message_data.get("room_id")
        receiver_id = message_data.get("receiver_id")
        
        # 获取用户昵称
        nickname = manager.user_nicknames.get(username, username)
        
        typing_message = {
            "type": "typing",
            "sender_id": user_id,
            "username": username,
            "nickname": nickname,
            "isTyping": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if room_id:
            # 聊天室消息
            typing_message["room_id"] = room_id
            await manager.broadcast_to_room(typing_message, room_id)
        elif receiver_id:
            # 私聊消息
            typing_message["receiver_id"] = receiver_id
            
            # 发送给接收者
            receiver_username = None
            for uname, uid in manager.user_ids.items():
                if uid == receiver_id:
                    receiver_username = uname
                    break
            
            if receiver_username:
                await manager.send_personal_message(typing_message, receiver_username)
    
    except Exception as e:
        logger.error(f"处理正在输入状态时出错: {str(e)}")


async def handle_get_members(session: AsyncSession, username: str, room_id: int):
    """处理获取聊天室成员请求"""
    try:
        # 查询聊天室是否存在
        from sqlalchemy import select, and_
        room_query = select(ChatRoom).where(ChatRoom.id == room_id)
        room_result = await session.execute(room_query)
        room = room_result.scalar_one_or_none()
        
        if not room:
            await manager.send_personal_message({
                "type": "system",
                "message": f"聊天室 {room_id} 不存在"
            }, username)
            return
        
        # 查询聊天室成员
        query = select(User, ChatRoomMember) \
            .join(ChatRoomMember, User.id == ChatRoomMember.user_id) \
            .where(ChatRoomMember.room_id == room_id) \
            .order_by(ChatRoomMember.is_admin.desc(), User.nickname)
        
        result = await session.execute(query)
        members = []
        
        for user, member in result.fetchall():
            # 检查用户是否在线
            is_online = user.id in manager.online_users
            
            members.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname or user.username,
                "is_admin": member.is_admin,
                "joined_at": member.created_at.isoformat(),
                "online": is_online
            })
        
        # 发送成员列表
        await manager.send_personal_message({
            "type": "members_list",
            "room_id": room_id,
            "members": members
        }, username)
    
    except Exception as e:
        logger.error(f"处理获取聊天室成员请求时出错: {str(e)}")
