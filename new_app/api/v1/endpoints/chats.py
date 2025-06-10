"""
聊天相关的API端点
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core import auth
from new_app.db.session import get_db
from new_app.schemas.chat import Chat as ChatSchema
from new_app.schemas.chat import ChatCreate, Message as MessageSchema
from new_app.schemas.chat import MessageCreate
from new_app.models.user import User
from new_app.core.websocket_manager import manager as websocket_manager
from new_app.core.logger import get_logger
from new_app.core.chat import chat_manager
router = APIRouter()
logger = get_logger("chats")
@router.get("", response_model=List[ChatSchema])
async def read_chats(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取当前用户的聊天列表
    """
    chats = await chat_manager.get_chats(current_user.id)
    return chats

@router.post("", response_model=ChatSchema)
async def create_chat(
    *,
    db: AsyncSession = Depends(get_db),
    chat_in: ChatCreate,
    current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    创建新聊天
    """
    chat = await chat_manager.create_chat(
        user_id=current_user.id,
        chat_type=chat_in.chat_type,
        title=chat_in.title
    )
    return chat

@router.get("/{chat_id}", response_model=ChatSchema)
async def read_chat(
    *,
    db: AsyncSession = Depends(get_db),
    chat_id: int,
    current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取聊天信息
    """
    chat = await chat_manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在"
        )
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return chat

@router.delete("/{chat_id}")
async def delete_chat(
    *,
    db: AsyncSession = Depends(get_db),
    chat_id: int,
    current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    删除聊天
    """
    chat = await chat_manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在"
        )
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    await chat_manager.delete_chat(chat_id)
    return {"message": "聊天已删除"}

@router.get("/{chat_id}/messages", response_model=List[MessageSchema])
async def read_messages(
    *,
    db: AsyncSession = Depends(get_db),
    chat_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取聊天消息列表
    """
    chat = await chat_manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在"
        )
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    messages = await chat_manager.get_chat_messages(
        chat_id=chat_id,
        skip=skip,
        limit=limit
    )
    return messages

@router.post("/{chat_id}/messages", response_model=MessageSchema)
async def create_message(
    *,
    db: AsyncSession = Depends(get_db),
    chat_id: int,
    message_in: MessageCreate,
    current_user: User = Depends(auth.get_current_active_user),
) -> Any:
    """
    发送消息
    """
    chat = await chat_manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在"
        )
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    message = await chat_manager.create_message(
        MessageCreate(
            **message_in.dict(),
            chat_id=chat_id,
            user_id=current_user.id
        )
    )
    
    # 通过WebSocket发送消息
    await websocket_manager.send_personal_message(
        {
            "type": "new_message",
            "data": {
                "chat_id": chat_id,
                "message": message
            }
        },
        current_user.id
    )
    
    return message 