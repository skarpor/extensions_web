"""
页面路由模块

处理所有页面的路由，包括首页、登录页、仪表盘等。
"""
import datetime

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Database
from config import TEMPLATE_DIR
from app.core.auth import get_current_user
from app.models.user import UserInDB, UserRole
from app.db.database import get_db
# 全局变量
router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=TEMPLATE_DIR)
db_instance:Database = None

def init_router(db):
    """初始化路由，设置数据库实例"""
    global db_instance
    db_instance = db
    return router


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse(
        "index2.html", 
        {
            "request": request,
            "title": "数据查询系统",
            "nav_active": "home"
        }
    )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "url": "login", "title": "登录"}
    )
# 将注册与登录合并

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "url": "register", "title": "注册"}
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """仪表盘页面"""
    # 检查用户是否已登录

    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request}
    )

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: UserInDB = Depends(get_current_user)):
    """聊天页面"""
    # 检查用户是否已登录
    if user.id == 0:  # 访客用户
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "请先登录"}
        )
    
    # 获取系统设置
    settings = db_instance.get_system_settings()
    if settings.get("enable_chat") != "true":
        raise HTTPException(status_code=403, detail="聊天功能已禁用")
    
    return templates.TemplateResponse(
        "chat.html", 
        {"request": request, "user": user}
    )

@router.get("/extensions", response_class=HTMLResponse)
async def extensions_page(request: Request, user: UserInDB = Depends(get_current_user)):
    """扩展管理页面"""
    # 检查用户是否已登录且有权限
    if user.id == 0 or user.role not in [UserRole.ADMIN.value, UserRole.MANAGER.value]:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "没有权限访问此页面"}
        )
    
    # 获取系统设置
    settings = db_instance.get_system_settings()
    if settings.get("enable_extensions") != "true":
        raise HTTPException(status_code=403, detail="扩展管理功能已禁用")
    
    return templates.TemplateResponse(
        "extensions.html", 
        {"request": request, "user": user}
    )

@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request, user: UserInDB = Depends(get_current_user)):
    """文件管理页面"""
    # 检查用户是否已登录
    if user.id == 0:  # 访客用户
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "请先登录"}
        )
    
    # 获取系统设置
    settings = db_instance.get_system_settings()
    if settings.get("enable_files") != "true":
        raise HTTPException(status_code=403, detail="文件管理功能已禁用")
    
    return templates.TemplateResponse(
        "files.html", 
        {"request": request, "user": user}
    )

@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, user: UserInDB = Depends(get_current_user)):
    """日志管理页面"""
    # 检查用户是否已登录且有权限
    if user.id == 0 or user.role not in [UserRole.ADMIN.value]:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "没有权限访问此页面"}
        )
    
    # 获取系统设置
    settings = db_instance.get_system_settings()
    if settings.get("enable_logs") != "true":
        raise HTTPException(status_code=403, detail="日志管理功能已禁用")
    
    return templates.TemplateResponse(
        "logs.html", 
        {"request": request, "user": user}
    )

# 设置页面路由
@router.get("/settings/general", response_class=HTMLResponse)
async def settings_general_page(request: Request
                                # , user: UserInDB = Depends(get_current_user)
                                ):
    """系统设置页面"""
    # 检查用户是否已登录且有权限
    # if user.id == 0 or user.role not in [UserRole.ADMIN.value]:
    #     return templates.TemplateResponse(
    #         "login.html",
    #         {"request": request, "error": "没有权限访问此页面"}
    #     )
    
    # 获取系统设置
    settings = db_instance.get_system_settings()
    if settings.get("enable_settings") != "true":
        raise HTTPException(status_code=403, detail="系统设置功能已禁用")
    
    return templates.TemplateResponse(
        "settings/general.html", 
        {"request": request, "settings": settings}
    )

@router.get("/settings/users", response_class=HTMLResponse)
async def settings_users_page(
        request: Request,
        # user: UserInDB = Depends(get_current_user)
        session: AsyncSession = Depends(get_db),

):
    """用户管理页面"""
    # 检查用户是否已登录且有权限
    # if user.id == 0 or user.role not in [UserRole.ADMIN.value, UserRole.MANAGER.value]:
    #     return templates.TemplateResponse(
    #         "login.html",
    #         {"request": request, "error": "没有权限访问此页面"}
    #     )
    
    # 获取系统设置
    settings = db_instance.get_system_settings()
    if settings.get("enable_settings") != "true":
        raise HTTPException(status_code=403, detail="系统设置功能已禁用")

    # 获取用户列表
    users = await db_instance.get_users(session)
    
    return templates.TemplateResponse(
        "settings/users.html", 
        {"request": request, "user": "user", "users": users}
    )

@router.get("/settings/permissions", response_class=HTMLResponse)
async def settings_permissions_page(
        request: Request,
        session: AsyncSession = Depends(get_db),
        # user: UserInDB = Depends(get_current_user)
):
    """权限管理页面"""
    # 检查用户是否已登录且有权限
    # if user.id == 0 or user.role not in [UserRole.ADMIN.value]:
    #     return templates.TemplateResponse(
    #         "login.html",
    #         {"request": request, "error": "没有权限访问此页面"}
    #     )
    
    # 获取系统设置
    settings = db_instance.get_system_settings()
    if settings.get("enable_settings") != "true":
        raise HTTPException(status_code=403, detail="系统设置功能已禁用")
    
    # 获取所有角色的权限
    admin_permissions = await db_instance.get_permissions_by_role(request.app.state.db, UserRole.ADMIN.value)
    manager_permissions = await db_instance.get_permissions_by_role(request.app.state.db, UserRole.MANAGER.value)
    user_permissions = await db_instance.get_permissions_by_role(request.app.state.db, UserRole.USER.value)
    
    return templates.TemplateResponse(
        "settings/permissions.html", 
        {
            "request": request, 
            "user": "user",
            "admin_permissions": admin_permissions,
            "manager_permissions": manager_permissions,
            "user_permissions": user_permissions
        }
    )
