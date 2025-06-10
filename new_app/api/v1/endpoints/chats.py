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
from new_app.crud import crud_chat, crud_message
from new_app.models.user import User as UserModel
from new_app.core.websocket_manager import websocket_manager

router = APIRouter()

@router.get("", response_model=List[ChatSchema])
async def read_chats(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取当前用户的聊天列表
    """
    chats = await crud_chat.get_user_chats(db, user_id=current_user.id)
    return chats

@router.post("", response_model=ChatSchema)
async def create_chat(
    *,
    db: AsyncSession = Depends(get_db),
    chat_in: ChatCreate,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    创建新聊天
    """
    chat = await crud_chat.create_with_owner(
        db=db,
        obj_in=chat_in,
        owner_id=current_user.id
    )
    return chat

@router.get("/{chat_id}", response_model=ChatSchema)
async def read_chat(
    *,
    db: AsyncSession = Depends(get_db),
    chat_id: int,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取聊天信息
    """
    chat = await crud_chat.get(db=db, id=chat_id)
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
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    删除聊天
    """
    chat = await crud_chat.get(db=db, id=chat_id)
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
    await crud_chat.remove(db=db, id=chat_id)
    return {"message": "聊天已删除"}

@router.get("/{chat_id}/messages", response_model=List[MessageSchema])
async def read_messages(
    *,
    db: AsyncSession = Depends(get_db),
    chat_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    获取聊天消息列表
    """
    chat = await crud_chat.get(db=db, id=chat_id)
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
    messages = await crud_message.get_chat_messages(
        db=db,
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
    current_user: UserModel = Depends(auth.get_current_active_user),
) -> Any:
    """
    发送消息
    """
    chat = await crud_chat.get(db=db, id=chat_id)
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
    
    message = await crud_message.create(
        db=db,
        obj_in=MessageCreate(
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