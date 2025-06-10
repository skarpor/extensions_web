"""
认证路由模块

提供用户认证和授权相关的API路由。
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, Response, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from config import token_name
from app.models.user import Token, UserCreate, User, UserLogin
from app.core.logger import get_logger
from app.core.auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from app.core.database import Database
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import status

logger = get_logger("auth_routes")
router = APIRouter()
db:Database = None

def init_router(database: Database):
    """初始化路由，传递数据库实例"""
    global db
    db = database


@router.post("/api/auth/token", response_model=Token)
async def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None):
    """
    用户登录并获取令牌
    
    Args:
        form_data: 包含用户名和密码的表单数据
        
    Returns:
        带有访问令牌的响应
        
    Raises:
        HTTPException: 如果凭证无效
    """
    logger.info(f"用户尝试登录: {form_data.username}")
    
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"用户登录失败: {form_data.username} - 无效凭证")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建访问令牌
        access_token = create_access_token(
            data={"sub": user["username"]},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        # 设置cookie
        response.set_cookie(
            key=token_name,
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,  # 生产环境应设为True，需要HTTPS
            samesite="lax"
        )

        logger.info(f"用户登录成功: {form_data.username}")
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "username": user["username"], 
            "role": user["role"],
            "id": user["id"],
            "nickname": user.get("nickname") or user["username"]
        }
    except HTTPException as e:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户登录过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="登录处理过程中发生错误"
        )


@router.post("/api/auth/logout")
async def logout(response: Response):
    """
    用户登出
    
    Args:
        response: HTTP响应对象
        
    Returns:
        成功消息
    """
    response.delete_cookie(key=token_name)
    return {"status_code": status.HTTP_200_OK, "detail": "登出成功"}


@router.post("/api/auth/register")
async def register(user_data: UserCreate):
    """
    注册新用户
    
    Args:
        user_data: 用户注册数据
        
    Returns:
        成功消息
        
    Raises:
        HTTPException: 如果用户名已存在或发生其他错误
    """
    try:
        # 检查用户名是否已存在
        existing_user = db.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 哈希密码
        hashed_password = get_password_hash(user_data.password)
        
        # 创建用户
        user_id = db.create_user({
            "username": user_data.username,
            "password": hashed_password,
            "nickname": user_data.nickname or user_data.username,
            "role": "user",  # 默认角色为普通用户
            "email": user_data.email,
            "avatar": user_data.avatar
        })
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建用户失败"
            )
        
        return {"status_code": status.HTTP_201_CREATED, "detail": "注册成功", "user_id": user_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册用户时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册处理过程中发生错误"
        )


@router.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户，由依赖项提供
        
    Returns:
        当前用户信息
    """
    # print(current_user)
    # # 转字典或json
    # current_user_dict = current_user.model_dump()
    return current_user


