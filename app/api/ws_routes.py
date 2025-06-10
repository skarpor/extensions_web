"""
WebSocket路由，处理实时聊天
"""
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.db.database import get_db
from app.db.models import User, ChatRoom, ChatRoomMember, ChatMessage

# 创建路由器
router = APIRouter()

# 设置日志记录器
logger = get_logger("ws_chat")


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
            "timestamp": datetime.utcnow().isoformat()
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
                    "timestamp": datetime.utcnow().isoformat()
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


@router.websocket("/ws/chat/{username}")
async def websocket_endpoint(
    websocket: WebSocket, 
    username: str,
    session: AsyncSession = Depends(get_db)
):
    """WebSocket端点"""
    # 连接WebSocket
    await manager.connect(websocket, username)
    
    try:
        # 查询用户信息
        from sqlalchemy import select
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # 用户不存在，关闭连接
            await websocket.close(code=1008, reason="用户不存在")
            return
        
        # 设置用户信息
        manager.set_user_info(username, user.id, user.nickname)
        
        # 发送在线用户列表
        await manager.send_personal_message({
            "type": "users_list",
            "users": manager.get_online_users()
        }, username)
        
        # 广播用户上线通知
        await manager.broadcast({
            "type": "users_list",
            "users": manager.get_online_users()
        })
        
        # 处理消息
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                # 解析消息
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "chat":
                    # 处理聊天消息
                    await handle_chat_message(session, username, user.id, message_data)
                
                elif message_type == "join_room":
                    # 加入聊天室
                    room_id = message_data.get("room_id")
                    if room_id:
                        await handle_join_room(session, username, user.id, room_id)
                
                elif message_type == "leave_room":
                    # 离开聊天室
                    room_id = message_data.get("room_id")
                    if room_id:
                        await manager.leave_room(username, room_id)
                
                elif message_type == "typing":
                    # 处理正在输入状态
                    await handle_typing_status(username, user.id, message_data)
                
                elif message_type == "get_members":
                    # 获取聊天室成员
                    room_id = message_data.get("room_id")
                    if room_id:
                        await handle_get_members(session, username, room_id)
                
                elif message_type == "user_info":
                    # 更新用户信息
                    nickname = message_data.get("nickname")
                    if nickname:
                        manager.set_user_info(username, user.id, nickname)
                        
                        # 更新在线用户列表
                        await manager.broadcast({
                            "type": "users_list",
                            "users": manager.get_online_users()
                        })
                
                elif message_type == "nickname":
                    # 更新昵称
                    nickname = message_data.get("nickname")
                    if nickname:
                        manager.set_user_info(username, user.id, nickname)
                        
                        # 更新在线用户列表
                        await manager.broadcast({
                            "type": "users_list",
                            "users": manager.get_online_users()
                        })
                
                else:
                    logger.warning(f"未知消息类型: {message_type}")
            
            except json.JSONDecodeError:
                logger.error(f"无效的JSON消息: {data}")
            except Exception as e:
                logger.error(f"处理消息时出错: {str(e)}")
    
    except WebSocketDisconnect:
        # 连接断开时清理资源
        await manager.disconnect(username)
        
        # 广播用户下线通知
        await manager.broadcast({
            "type": "users_list",
            "users": manager.get_online_users()
        })
    
    except Exception as e:
        logger.error(f"WebSocket连接出错: {str(e)}")
        await manager.disconnect(username)


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



# async def handle_get_rooms(session: AsyncSession,username:str):
#     pass

