"""
定时任务管理路由模块

提供Web界面和API接口，用于管理定时任务的创建、查看、启停等操作。
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Optional, Union
import datetime
import json
import os
import pytz
import importlib
import importlib.util
from app.api.extension_routes import get_extensions
from app.core.auth import get_current_user
from app.core.logger import get_logger
from app.core.app_scheduler import AppScheduler
from pydantic import BaseModel

from app.core.sandbox import load_module_in_sandbox, execute_query_in_sandbox
from app.models.user import User
logger = get_logger("scheduler_routes")
from .extension_routes import get_extension
router = APIRouter(prefix="/scheduler", tags=["scheduler"])
from config import TEMPLATE_DIR,data_dir
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 任务类型定义
TASK_TYPES = {
    "cron": "Cron定时任务",
    "interval": "间隔任务",
    "date": "一次性任务"
}

# 示例任务函数列表，实际应用中可以从插件系统动态获取
example_tasks = {
    "tasks.example.send_notification": "发送通知",
    "tasks.example.sync_data": "同步数据",
    "tasks.example.generate_report": "生成报表",
    "tasks.example.clean_old_data": "清理旧数据",
    "tasks.example.backup_database": "数据库备份"
}

# 页面路由
@router.get("/", response_class=HTMLResponse)
async def scheduler_page(request: Request, user=Depends(get_current_user)):
    """定时任务管理页面"""
    # 获取所有任务
    scheduler = request.app.state.scheduler
    jobs = await scheduler.get_jobs()
    
    # 按任务类型分组
    grouped_jobs = {
        "cron": [],
        "interval": [],
        "date": []
    }
    
    for job in jobs:
        job_type = "cron" if "cron" in job["trigger"].lower() else \
                  "interval" if "interval" in job["trigger"].lower() else "date"
        grouped_jobs[job_type].append(job)
    
    return templates.TemplateResponse(
        "scheduler/index.html",
        {
            "request": request,
            "jobs": jobs,
            "grouped_jobs": grouped_jobs,
            "task_types": TASK_TYPES,
            "example_tasks": example_tasks,
            "user": user
        }
    )

@router.get("/job/{job_id}", response_class=HTMLResponse)
async def job_detail_page(request: Request, job_id: str, user=Depends(get_current_user)):
    """任务详情页面"""
    scheduler = request.app.state.scheduler
    job = await scheduler.get_job(job_id)
    
    if not job:
        return templates.TemplateResponse(
            "scheduler/error.html",
            {
                "request": request,
                "message": f"任务 {job_id} 不存在",
                "user": user
            }
        )
    
    # 确定任务类型
    job_type = "cron" if "cron" in job["trigger"].lower() else \
              "interval" if "interval" in job["trigger"].lower() else "date"
    job['active']=job.get("next_run_time")
    job['func_name']=job.get("func_name")
    job['job_type']=job_type
    print(job,job_type)
    return templates.TemplateResponse(
        "scheduler/job_detail.html",
        {
            "request": request,
            "job": job,
            "job_type": job_type,
            "task_types": TASK_TYPES,
            "user": user
        }
    )

@router.get("/add", response_class=HTMLResponse)
async def add_job_page(request: Request, user=Depends(get_current_user)):
    """添加任务页面"""
    # 获取所有扩展中的扩展名及execute_query方法，以便添加定时任务
    extensions = await get_extensions()
    extension_methods = [
        {
            "extension_name": extension['name'],
            "method_name": "execute_query",
            "extension_id": extension['id']
        }
        for extension in extensions
    ]
    
    return templates.TemplateResponse(
        "scheduler/add_job.html",
        {
            "request": request,
            "task_types": TASK_TYPES,
            "extension_methods": extension_methods,
            "user": user
        }
    )

# API路由
@router.get("/api/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(request: Request, user=Depends(get_current_user)):
    """获取所有任务"""
    try:
        scheduler = request.app.state.scheduler
        jobs = await scheduler.get_jobs()
        return jobs
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.get("/api/job/{job_id}", response_model=Dict[str, Any])
async def get_job(request: Request, job_id: str, user=Depends(get_current_user)):
    """获取任务详情"""
    try:
        scheduler = request.app.state.scheduler
        job = await scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"任务 {job_id} 不存在")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")

@router.post("/api/job/{job_id}/pause")
async def pause_job(request: Request, job_id: str, user=Depends(get_current_user)):
    """暂停任务"""
    try:
        scheduler = request.app.state.scheduler
        result = await scheduler.pause_job(job_id)
        if result:
            logger.info(f"用户 {user.username} 暂停了任务 {job_id}")
            return {"success": True, "message": f"任务 {job_id} 已暂停"}
        else:
            raise HTTPException(status_code=400, detail=f"暂停任务 {job_id} 失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")

@router.post("/api/job/{job_id}/resume")
async def resume_job(request: Request, job_id: str, user=Depends(get_current_user)):
    """恢复任务"""
    try:
        scheduler = request.app.state.scheduler
        result = await scheduler.resume_job(job_id)
        if result:
            logger.info(f"用户 {user.username} 恢复了任务 {job_id}")
            return {"success": True, "message": f"任务 {job_id} 已恢复"}
        else:
            raise HTTPException(status_code=400, detail=f"恢复任务 {job_id} 失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"恢复任务失败: {str(e)}")

@router.post("/api/job/{job_id}/run")
async def run_job(request: Request, job_id: str, user=Depends(get_current_user)):
    """立即执行任务"""
    try:
        scheduler = request.app.state.scheduler
        result = await scheduler.run_job(job_id)
        if result:
            logger.info(f"用户 {user.username} 手动执行了任务 {job_id}")
            return {"success": True, "message": f"任务 {job_id} 已触发执行"}
        else:
            raise HTTPException(status_code=400, detail=f"执行任务 {job_id} 失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行任务失败: {str(e)}")

@router.delete("/api/job/{job_id}")
async def remove_job(request: Request, job_id: str, user=Depends(get_current_user)):
    """删除任务"""
    try:
        scheduler = request.app.state.scheduler
        job = await scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"任务 {job_id} 不存在")
            
        result = await scheduler.remove_job(job_id)
        if result:
            logger.info(f"用户 {user.username} 删除了任务 {job_id}")
            return {"success": True, "message": f"任务 {job_id} 已删除"}
        else:
            raise HTTPException(status_code=400, detail=f"删除任务 {job_id} 失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

# 任务示例函数
async def log_time_task():
    """记录当前时间示例任务"""
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[定时任务] 当前时间: {formatted_time}")
    return {"time": formatted_time}

async def cleanup_temp_task():
    """清理临时文件示例任务"""
    # 模拟清理操作
    logger.info("[定时任务] 清理临时文件")
    return {"cleaned_files": 0}

async def send_report_task():
    """发送报告示例任务"""
    # 模拟发送报告
    logger.info("[定时任务] 发送报告")
    return {"report_sent": True}

# 任务函数映射
TASK_FUNCTIONS = {
    "log_time": log_time_task,
    "cleanup_temp": cleanup_temp_task,
    "send_report": send_report_task
}

@router.post("/api/jobs/cron")
async def add_cron_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    minute: str = Form("*"),
    hour: str = Form("*"),
    day: str = Form("*"),
    month: str = Form("*"),
    day_of_week: str = Form("*"),
    second: str = Form("0"),
    user:User=Depends(get_current_user)
):
    """添加Cron任务"""
    try:
        # if task_func not in TASK_FUNCTIONS:
        #     raise HTTPException(status_code=400, detail=f"无效的任务函数: {task_func}")
        # task_func = task_func+".execute_query"
        # 生成任务ID（如果未提供）
        if not job_id:
            job_id = f"cron_{task_func}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        scheduler = request.app.state.scheduler
        # func = TASK_FUNCTIONS[task_func]

        # 动态导入模块
        # 创建模块

        # module = load_module_in_sandbox(task_func, f"data/extensions/{task_func}.py")

        extension = await get_extension(task_func)
        config = extension.get("config")
        func = execute_query_in_sandbox
        # 添加任务
        job_id = await scheduler.add_cron_job(
            func,
            kwargs={"module":None,"params": {"file_manager":request.app.state.file_manager,"extension_id": task_func},"config":config} ,
            job_id=job_id,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            second=second
        )
        
        logger.info(f"用户 {user.username} 添加了Cron任务: {job_id}")
        return {
            "success": True,
            "job_id": job_id,
            "message": f"已添加Cron任务: {job_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加Cron任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加Cron任务失败: {str(e)}")

@router.post("/api/jobs/interval")
async def add_interval_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    seconds: int = Form(0),
    minutes: int = Form(0),
    hours: int = Form(0),
    days: int = Form(0),
    user=Depends(get_current_user)
):
    """添加间隔任务"""
    try:
        # if task_func not in TASK_FUNCTIONS:
        #     raise HTTPException(status_code=400, detail=f"无效的任务函数: {task_func}")
        
        # 至少要指定一个时间间隔
        if seconds == 0 and minutes == 0 and hours == 0 and days == 0:
            raise HTTPException(status_code=400, detail="必须指定至少一个时间间隔")
        
        # 生成任务ID（如果未提供）
        if not job_id:
            job_id = f"interval_{task_func}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        scheduler = request.app.state.scheduler
        # 动态导入模块
        # py_path = os.path.join(data_dir,f"extensions/{task_func}.py")
        # module = load_module_in_sandbox(task_func, os.path.abspath(py_path))

        # 获取函数
        extension = await get_extension(task_func)
        config = extension.get("config")
        func = execute_query_in_sandbox

        # 添加任务
        job_id = await scheduler.add_interval_job(
            func,
            kwargs={"module":None,"params": {"file_manager":request.app.state.file_manager,"extension_id": task_func},"config":config} ,
            job_id=job_id,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days
        )
        
        logger.info(f"用户 {user.username} 添加了间隔任务: {job_id}")
        return {
            "success": True,
            "job_id": job_id,
            "message": f"已添加间隔任务: {job_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加间隔任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加间隔任务失败: {str(e)}")

@router.post("/api/jobs/date")
async def add_date_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    run_date: str = Form(...),  # 格式: YYYY-MM-DD HH:MM:SS
    user=Depends(get_current_user)
):
    """添加一次性任务"""
    try:
        # if task_func not in TASK_FUNCTIONS:
        #     raise HTTPException(status_code=400, detail=f"无效的任务函数: {task_func}")
        
        # 解析日期时间
        try:
            run_datetime = datetime.datetime.strptime(run_date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的日期时间格式，应为: YYYY-MM-DD HH:MM:SS")
        
        # 检查日期是否在未来
        if run_datetime <= datetime.datetime.now():
            raise HTTPException(status_code=400, detail="执行时间必须在未来")
        
        # 生成任务ID（如果未提供）
        if not job_id:
            job_id = f"date_{task_func}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        scheduler = request.app.state.scheduler

        # 动态导入模块
        # module = load_module_in_sandbox(task_func, f"data/extensions/{task_func}.py")

        # 获取函数
        extension = await get_extension(task_func)
        config = extension.get("config")
        func = execute_query_in_sandbox

        # 添加任务
        job_id = await scheduler.add_date_job(
            func,
            kwargs={"module":None,"params": {"file_manager":request.app.state.file_manager,"extension_id": task_func},"config":config} ,
            job_id=job_id,
            run_date=run_datetime
        )
        
        logger.info(f"用户 {user.username} 添加了一次性任务: {job_id}, 执行时间: {run_date}")
        return {
            "success": True,
            "job_id": job_id,
            "message": f"已添加一次性任务: {job_id}, 执行时间: {run_date}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加一次性任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加一次性任务失败: {str(e)}")

# 初始化路由
def init_router(app):
    """初始化路由"""
    app.include_router(router)
    logger.info("定时任务管理路由已初始化")

class JobResponse(BaseModel):
    """任务响应模型"""
    success: bool
    message: str
    job_id: Optional[str] = None
    detail: Optional[str] = None

@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail_page(request: Request, job_id: str):
    """任务详情页面"""
    scheduler = request.app.state.scheduler
    job = await scheduler.get_job(job_id)
    
    if not job:
        return templates.TemplateResponse(
            "scheduler/job_detail.html", 
            {
                "request": request,
                "job": None
            }
        )
    
    # 添加更多有用的任务信息
    job_info = job.copy()
    
    # 确定任务类型
    if job.trigger.startswith("cron"):
        job_info["type"] = "cron"
        # 从trigger中提取cron表达式
        trigger_parts = job.trigger.split(":", 1)[1]
        job_info["cron_expression"] = trigger_parts
        job_info["cron_description"] = "每" + _describe_cron(trigger_parts)
    elif job.trigger.startswith("interval"):
        job_info["type"] = "interval"
        interval_parts = job.trigger.split(":", 1)[1]
        job_info["interval_description"] = _describe_interval(interval_parts)
    else:
        job_info["type"] = "date"
    
    # 格式化时间
    if job_info.get("next_run_time"):
        job_info["next_run_time"] = _format_datetime(job_info["next_run_time"])
    
    # 添加最近执行记录信息（模拟数据，实际应用中应该从执行记录中获取）
    # 在实际应用中，可以从日志或数据库中获取任务的执行记录
    job_info["last_run_info"] = [
        {
            "run_time": _format_datetime(datetime.now()),
            "result": "执行成功，处理了123条数据",
            "duration": 1.25,
            "success": True
        },
        {
            "run_time": _format_datetime(datetime.now().replace(hour=datetime.now().hour-1)),
            "result": None,
            "duration": 0.85,
            "success": True
        }
    ]
    
    return templates.TemplateResponse(
        "scheduler/job_detail.html", 
        {
            "request": request,
            "job": job_info
        }
    )

@router.get("/api/jobs", response_class=JSONResponse)
async def get_all_jobs(request: Request):
    """获取所有任务"""
    scheduler = request.app.state.scheduler
    jobs = await scheduler.get_jobs()
    return {"success": True, "jobs": jobs}

@router.get("/api/jobs/{job_id}", response_class=JSONResponse)
async def get_job(request: Request, job_id: str):
    """获取指定任务详情"""
    scheduler = request.app.state.scheduler
    job = await scheduler.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {"success": True, "job": job}

@router.post("/api/jobs/cron", response_class=JSONResponse)
async def add_cron_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    second: str = Form("0"),
    minute: str = Form("*"),
    hour: str = Form("*"),
    day: str = Form("*"),
    month: str = Form("*"),
    day_of_week: str = Form("*")
):
    """添加Cron定时任务"""
    try:
        scheduler = request.app.state.scheduler
        
        # 构建cron表达式
        cron_expression = f"{second} {minute} {hour} {day} {month} {day_of_week}"
        
        # 添加任务
        job = await scheduler.add_cron_job(
            func=task_func,
            cron_expression=cron_expression,
            job_id=job_id
        )
        
        return JobResponse(
            success=True,
            message="Cron定时任务添加成功",
            job_id=job.id
        )
    except Exception as e:
        return JobResponse(
            success=False,
            message="添加Cron定时任务失败",
            detail=str(e)
        )

@router.post("/api/jobs/interval", response_class=JSONResponse)
async def add_interval_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    seconds: int = Form(0),
    minutes: int = Form(0),
    hours: int = Form(0),
    days: int = Form(0)
):
    """添加间隔任务"""
    try:
        # 检查至少有一个时间间隔参数大于0
        if seconds <= 0 and minutes <= 0 and hours <= 0 and days <= 0:
            return JobResponse(
                success=False,
                message="添加间隔任务失败",
                detail="时间间隔必须大于0"
            )
        
        scheduler = request.app.state.scheduler
        
        # 构建间隔参数
        interval_kwargs = {}
        if seconds > 0:
            interval_kwargs["seconds"] = seconds
        if minutes > 0:
            interval_kwargs["minutes"] = minutes
        if hours > 0:
            interval_kwargs["hours"] = hours
        if days > 0:
            interval_kwargs["days"] = days
        
        # 添加任务
        job = await scheduler.add_interval_job(
            func=task_func,
            job_id=job_id,
            **interval_kwargs
        )
        
        return JobResponse(
            success=True,
            message="间隔任务添加成功",
            job_id=job.id
        )
    except Exception as e:
        return JobResponse(
            success=False,
            message="添加间隔任务失败",
            detail=str(e)
        )

@router.post("/api/jobs/date", response_class=JSONResponse)
async def add_date_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    run_date: str = Form(...)
):
    """添加一次性任务"""
    try:
        # 解析日期时间
        try:
            run_date_obj = datetime.fromisoformat(run_date)
        except ValueError:
            # 尝试其他常见格式
            run_date_obj = datetime.strptime(run_date, "%Y-%m-%d %H:%M:%S")
        
        # 检查日期是否在未来
        if run_date_obj <= datetime.now():
            return JobResponse(
                success=False,
                message="添加一次性任务失败",
                detail="执行时间必须在未来"
            )
        
        scheduler = request.app.state.scheduler
        
        # 添加任务
        job = await scheduler.add_date_job(
            func=task_func,
            run_date=run_date_obj,
            job_id=job_id
        )
        
        return JobResponse(
            success=True,
            message="一次性任务添加成功",
            job_id=job.id
        )
    except Exception as e:
        return JobResponse(
            success=False,
            message="添加一次性任务失败",
            detail=str(e)
        )

@router.post("/api/jobs/{job_id}/pause", response_class=JSONResponse)
async def pause_job(request: Request, job_id: str):
    """暂停任务"""
    try:
        scheduler = request.app.state.scheduler
        await scheduler.pause_job(job_id)
        return {"success": True, "message": "任务已暂停"}
    except Exception as e:
        return {"success": False, "detail": str(e)}

@router.post("/api/jobs/{job_id}/resume", response_class=JSONResponse)
async def resume_job(request: Request, job_id: str):
    """恢复任务"""
    try:
        scheduler = request.app.state.scheduler
        await scheduler.resume_job(job_id)
        return {"success": True, "message": "任务已恢复"}
    except Exception as e:
        return {"success": False, "detail": str(e)}

@router.post("/api/jobs/{job_id}/run", response_class=JSONResponse)
async def run_job_now(request: Request, job_id: str):
    """立即执行任务"""
    try:
        scheduler = request.app.state.scheduler
        result = await scheduler.run_job(job_id)
        return {"success": True, "message": "任务已执行", "result": str(result)}
    except Exception as e:
        return {"success": False, "detail": str(e)}

@router.delete("/api/jobs/{job_id}", response_class=JSONResponse)
async def delete_job(request: Request, job_id: str):
    """删除任务"""
    try:
        scheduler = request.app.state.scheduler
        await scheduler.remove_job(job_id)
        return {"success": True, "message": "任务已删除"}
    except Exception as e:
        return {"success": False, "detail": str(e)}

def _format_datetime(dt: datetime) -> str:
    """格式化日期时间为友好格式"""
    if not dt:
        return ""
    
    local_tz = pytz.timezone('Asia/Shanghai')
    
    # 如果dt不包含时区信息，假定为UTC时间并转换为本地时间
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt).astimezone(local_tz)
    elif dt.tzinfo != local_tz:
        dt = dt.astimezone(local_tz)
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def _describe_cron(cron_expression: str) -> str:
    """描述cron表达式"""
    parts = cron_expression.split()
    if len(parts) < 6:
        return "自定义时间"
    
    second, minute, hour, day, month, day_of_week = parts
    
    if second == "0" and minute == "0" and hour == "0" and day == "*" and month == "*" and day_of_week == "*":
        return "天 00:00:00"
    elif second == "0" and minute == "0" and hour == "*" and day == "*" and month == "*" and day_of_week == "*":
        return "小时 00:00"
    elif second == "0" and minute == "*" and hour == "*" and day == "*" and month == "*" and day_of_week == "*":
        return "分钟 :00秒"
    elif second == "0" and minute == "0" and hour == "9" and day == "*" and month == "*" and day_of_week == "1-5":
        return "工作日 09:00:00"
    elif second == "0" and minute == "0" and hour == "0" and day == "1" and month == "*" and day_of_week == "*":
        return "月1日 00:00:00"
    
    return "自定义时间"

def _describe_interval(interval_string: str) -> str:
    """描述间隔时间"""
    parts = interval_string.split(",")
    interval_dict = {}
    
    for part in parts:
        key, value = part.strip().split("=")
        interval_dict[key.strip()] = int(value.strip())
    
    if "days" in interval_dict and interval_dict["days"] == 1:
        return "每天"
    elif "hours" in interval_dict and interval_dict["hours"] == 1:
        return "每小时"
    elif "minutes" in interval_dict and interval_dict["minutes"] == 1:
        return "每分钟"
    elif "seconds" in interval_dict and interval_dict["seconds"] == 1:
        return "每秒"
    
    parts = []
    if "days" in interval_dict and interval_dict["days"] > 0:
        parts.append(f"{interval_dict['days']}天")
    if "hours" in interval_dict and interval_dict["hours"] > 0:
        parts.append(f"{interval_dict['hours']}小时")
    if "minutes" in interval_dict and interval_dict["minutes"] > 0:
        parts.append(f"{interval_dict['minutes']}分钟")
    if "seconds" in interval_dict and interval_dict["seconds"] > 0:
        parts.append(f"{interval_dict['seconds']}秒")
    
    return "每" + "".join(parts) 