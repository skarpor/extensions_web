# 聊天功能

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from models.chat import ChatRoomMember, ChatRoom
from schemas.chat import Chat, Message
from db.session import get_db


class ChatManager:
    def __init__(self, db: AsyncSession=Depends(get_db)):
        self.db = db

    async def create_chat(self, user_id: int, chat_type: str, title: Optional[str] = None) -> Chat:
        """创建聊天"""
        chat = Chat(
            user_id=user_id,
            chat_type=chat_type,
            title=title
        )
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)
        return chat

    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        """获取聊天"""
        return await self.db.get(Chat, chat_id)

    async def get_chats(self, user_id: int) -> List[Chat]:
        """获取用户聊天列表"""
        return await self.db.execute(
            select(Chat).where(Chat.user_id == user_id)
        )

    async def get_chat_messages(self, chat_id: int) -> List[Message]:
        """获取聊天消息"""
        return await self.db.execute(
            select(Message).where(Message.chat_id == chat_id)
        )

    async def create_message(self, message: Message) -> Message:
        """创建消息"""
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete_message(self, message_id: int) -> None:
        """删除消息"""
        message = await self.db.get(Message, message_id)
        if message:
            await self.db.delete(message)
            await self.db.commit()

    async def get_message(self, message_id: int) -> Optional[Message]:
        """获取消息"""
        return await self.db.get(Message, message_id)

    async def get_message_history(self, chat_id: int) -> List[Message]:
        """获取消息历史"""
        return await self.db.execute(
            select(Message).where(Message.chat_id == chat_id)
        )

    async def revoke_message(self, message_id: int) -> None:
        """撤回消息"""
        message = await self.db.get(Message, message_id)
        if message:
            message.is_deleted = True
            await self.db.commit()


# ===== 辅助函数 =====

async def get_room_or_404(session: AsyncSession, room_id: int) -> ChatRoom:
    """获取聊天室或返回404错误"""
    query = select(ChatRoom).where(ChatRoom.id == room_id)
    result = await session.execute(query)
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    return room


async def is_room_member(session: AsyncSession, room_id: int, user_id: int) -> bool:
    """检查用户是否为聊天室成员"""
    query = select(ChatRoomMember).where(
        and_(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == user_id
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def is_room_admin(session: AsyncSession, room_id: int, user_id: int) -> bool:
    """检查用户是否为聊天室管理员"""
    query = select(ChatRoomMember).where(
        and_(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == user_id,
            ChatRoomMember.is_admin == True
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None
chat_manager = ChatManager()