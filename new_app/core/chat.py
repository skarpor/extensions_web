# 聊天功能

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from new_app.schemas.chat import Chat, Message
from new_app.db.session import get_db


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



chat_manager = ChatManager()