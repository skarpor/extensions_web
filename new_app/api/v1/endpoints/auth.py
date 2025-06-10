"""
认证相关的API端点
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core.config import settings
from new_app.db.session import get_db
from new_app.schemas.token import Token
from new_app.schemas.user import UserCreate, User
from new_app.core import auth
from new_app.core.logger import get_logger
router = APIRouter()
logger = get_logger("auth")
@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录
    """
    user = await auth.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/test-token", response_model=User)
async def test_token(
    current_user: User = Depends(auth.get_current_user)
) -> Any:
    """
    测试token
    """
    return current_user 


@router.post("/token", response_model=Token)
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    response: Response = None,
    db: AsyncSession = Depends(get_db)
    ):
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
        user =await auth.authenticate(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"用户登录失败: {form_data.username} - 无效凭证")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建访问令牌
        access_token =await auth.create_access_token(
            data={"sub": user["username"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        # 设置cookie
        # response.set_cookie(
        #     key=settings.TOKEN_NAME,
        #     value=f"Bearer {access_token}",
        #     httponly=True,
        #     max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        #     secure=False,  # 生产环境应设为True，需要HTTPS
        #     samesite="lax"
        # )

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


@router.post("/logout")
async def logout(response: Response):
    """
    用户登出
    
    Args:
        response: HTTP响应对象
        
    Returns:
        成功消息
    """
    response.delete_cookie(key=settings.TOKEN_NAME)
    return {"status_code": status.HTTP_200_OK, "detail": "登出成功"}


@router.post("/register")
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
        existing_user = auth.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        # 检查邮箱是否已存在
        existing_user = auth.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        # 哈希密码
        hashed_password = auth.get_password_hash(user_data.password)
        
        # 创建用户
        user_id = auth.create_user({
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


@router.get("/me")
async def get_me(current_user: User = Depends(auth.get_current_user)):
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
