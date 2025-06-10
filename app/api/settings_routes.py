"""
系统设置路由模块

提供全局设置相关的路由和功能，包括定时任务设置
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Optional, Any
import importlib
import inspect
import json
import os
import time
import asyncio
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.logger import get_logger

logger = get_logger("settings_routes")

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="templates")

# 用户注册的任务函数存储
REGISTERED_TASKS_FILE = "data/user_tasks.json"
os.makedirs(os.path.dirname(REGISTERED_TASKS_FILE), exist_ok=True)

# 加载用户注册的任务函数
def load_registered_tasks() -> Dict[str, Dict]:
    if os.path.exists(REGISTERED_TASKS_FILE):
        try:
            with open(REGISTERED_TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载用户任务函数失败: {str(e)}")
    return {}

# 保存用户注册的任务函数
def save_registered_tasks(tasks: Dict[str, Dict]) -> bool:
    try:
        with open(REGISTERED_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存用户任务函数失败: {str(e)}")
        return False

# 验证函数路径是否可导入
def validate_function_path(func_path: str) -> bool:
    try:
        module_path, func_name = func_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        return callable(func)
    except Exception as e:
        logger.error(f"验证函数路径失败: {str(e)}")
        return False

# 页面路由
@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request
                        # , user=Depends(get_current_user)
                        ):
    """系统设置页面"""
    return templates.TemplateResponse(
        "settings/index.html",
        {
            "request": request,
            # "user": user
        }
    )

@router.get("/scheduler", response_class=HTMLResponse)
async def scheduler_settings_page(request: Request, user=Depends(get_current_user)):
    """定时任务设置页面"""
    registered_tasks = load_registered_tasks()
    
    return templates.TemplateResponse(
        "settings/scheduler.html",
        {
            "request": request,
            "user": user,
            "registered_tasks": registered_tasks
        }
    )

# API路由
class TaskFunction(BaseModel):
    """任务函数模型"""
    func_path: str
    func_name: str
    func_desc: str
    enabled: bool = True

class TestFunctionRequest(BaseModel):
    """测试函数请求模型"""
    func_path: str

@router.get("/api/scheduler/tasks", response_model=Dict[str, TaskFunction])
async def get_registered_tasks(request: Request, user=Depends(get_current_user)):
    """获取注册的任务函数"""
    registered_tasks = load_registered_tasks()
    return registered_tasks

@router.post("/api/scheduler/tasks")
async def register_task_function(
    request: Request,
    func_path: str = Form(...),
    func_name: str = Form(...),
    func_desc: str = Form(...),
    user=Depends(get_current_user)
):
    """注册任务函数"""
    # 验证函数路径
    if not validate_function_path(func_path):
        raise HTTPException(status_code=400, detail=f"无法导入函数: {func_path}")
    
    # 加载现有任务
    registered_tasks = load_registered_tasks()
    
    # 添加新任务
    registered_tasks[func_path] = {
        "func_path": func_path,
        "func_name": func_name,
        "func_desc": func_desc,
        "enabled": True
    }
    
    # 保存任务
    if not save_registered_tasks(registered_tasks):
        raise HTTPException(status_code=500, detail="保存任务函数失败")
    
    logger.info(f"用户 {user['username']} 注册了任务函数: {func_path}")
    return {"success": True, "message": f"成功注册任务函数: {func_name}"}

@router.post("/api/scheduler/tasks/test")
async def test_task_function(
    request: Request,
    test_request: TestFunctionRequest,
    user=Depends(get_current_user)
):
    """测试任务函数"""
    func_path = test_request.func_path
    
    try:
        # 尝试导入函数
        module_path, func_name = func_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        
        if not callable(func):
            return {
                "success": False,
                "error": f"{func_path} 不是一个可调用的函数",
                "duration": 0
            }
        
        # 检查函数是否是异步函数
        is_async = inspect.iscoroutinefunction(func)
        
        # 执行函数
        start_time = time.time()
        
        try:
            if is_async:
                result = await func()
            else:
                # 如果是同步函数，在事件循环中执行以避免阻塞
                result = await asyncio.to_thread(func)
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": True,
                "result": result,
                "duration": duration
            }
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(f"测试任务函数 {func_path} 失败: {str(e)}")
            return {
                "success": False,
                "error": f"函数执行失败: {str(e)}",
                "duration": duration
            }
    except Exception as e:
        logger.error(f"导入任务函数 {func_path} 失败: {str(e)}")
        return {
            "success": False,
            "error": f"导入函数失败: {str(e)}",
            "duration": 0
        }

@router.delete("/api/scheduler/tasks/{func_path}")
async def delete_task_function(
    request: Request,
    func_path: str,
    user=Depends(get_current_user)
):
    """删除任务函数"""
    # 加载现有任务
    registered_tasks = load_registered_tasks()
    
    # 检查任务是否存在
    if func_path not in registered_tasks:
        raise HTTPException(status_code=404, detail=f"任务函数不存在: {func_path}")
    
    # 删除任务
    del registered_tasks[func_path]
    
    # 保存任务
    if not save_registered_tasks(registered_tasks):
        raise HTTPException(status_code=500, detail="保存任务函数失败")
    
    logger.info(f"用户 {user['username']} 删除了任务函数: {func_path}")
    return {"success": True, "message": f"成功删除任务函数: {func_path}"}

@router.put("/api/scheduler/tasks/{func_path}")
async def update_task_function(
    request: Request,
    func_path: str,
    task: TaskFunction,
    user=Depends(get_current_user)
):
    """更新任务函数"""
    # 加载现有任务
    registered_tasks = load_registered_tasks()
    
    # 检查任务是否存在
    if func_path not in registered_tasks:
        raise HTTPException(status_code=404, detail=f"任务函数不存在: {func_path}")
    
    # 如果函数路径变更，需要验证新路径
    if task.func_path != func_path and not validate_function_path(task.func_path):
        raise HTTPException(status_code=400, detail=f"无法导入函数: {task.func_path}")
    
    # 如果函数路径变更，需要删除旧路径
    if task.func_path != func_path:
        del registered_tasks[func_path]
    
    # 更新任务
    registered_tasks[task.func_path] = task.dict()
    
    # 保存任务
    if not save_registered_tasks(registered_tasks):
        raise HTTPException(status_code=500, detail="保存任务函数失败")
    
    logger.info(f"用户 {user['username']} 更新了任务函数: {func_path} -> {task.func_path}")
    return {"success": True, "message": f"成功更新任务函数: {task.func_name}"}

class SchedulerGeneralSettings(BaseModel):
    """调度器通用设置模型"""
    max_jobs: int
    default_timezone: str
    enable_scheduler: bool
    persist_jobs: bool
    log_job_execution: bool

@router.post("/api/scheduler/general")
async def update_scheduler_general_settings(
    request: Request,
    settings: SchedulerGeneralSettings,
    user=Depends(get_current_user)
):
    """更新调度器通用设置"""
    # 这里实现保存设置的逻辑
    # 在实际应用中，您需要将设置保存到数据库或配置文件中
    
    # 模拟保存成功
    logger.info(f"用户 {user['username']} 更新了调度器通用设置")
    return {"success": True, "message": "成功更新调度器通用设置"}

class ExecutionSettings(BaseModel):
    """执行设置模型"""
    max_instances: int
    job_timeout: int
    retry_attempts: int
    retry_delay: int
    notification_email: Optional[str] = None
    notify_on_success: bool
    notify_on_failure: bool

@router.post("/api/scheduler/execution")
async def update_execution_settings(
    request: Request,
    settings: ExecutionSettings,
    user=Depends(get_current_user)
):
    """更新执行设置"""
    # 这里实现保存设置的逻辑
    # 在实际应用中，您需要将设置保存到数据库或配置文件中
    
    # 模拟保存成功
    logger.info(f"用户 {user['username']} 更新了执行设置")
    return {"success": True, "message": "成功更新执行设置"}

# 初始化路由
def init_router(app):
    """初始化路由"""
    global database
    database = app
    logger.info("系统设置路由已初始化")

def get_all_users():
    return

@router.get("/user", response_class=HTMLResponse)
async def user_settings_page(request: Request, user=Depends(get_current_user)):
    """用户管理页面"""
    return templates.TemplateResponse(
        "settings/user.html",
        {
            "request": request,
            "user": user,
            "all_users": get_all_users()  # 需要实现获取用户列表的方法
        }
    )
def load_system_config():
    pass
@router.get("/system", response_class=HTMLResponse)
async def system_settings_page(request: Request, user=Depends(get_current_user)):
    """系统配置页面"""
    return templates.TemplateResponse(
        "settings/system.html",
        {
            "request": request,
            "user": user,
            "system_config": load_system_config()  # 需要实现系统配置加载方法
        }
    )

def get_all_plugins():
    return []
# 插件管理界面
@router.get("/plugins", response_class=HTMLResponse)
async def plugins_settings_page(request: Request, user=Depends(get_current_user)):
    """插件管理页面"""
    return templates.TemplateResponse(
        "settings/plugins.html",
        {
            "request": request,
            "user": user,
            "plugins": get_all_plugins()  # 需要实现获取插件列表的方法
        }
    )

