"""
定时任务管理路由模块

提供Web界面和API接口，用于管理定时任务的创建、查看、启停等操作。
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, List, Optional, Union
import datetime
import json
import os
import pytz
import importlib
import importlib.util
from api.v1.endpoints.extensions import get_extensions,get_extension
from core.auth import get_current_user,manage_scheduler,create_scheduler,view_scheduler,update_scheduler,delete_scheduler,execute_scheduler,view_extension,resume_scheduler,pause_scheduler
from core.logger import get_logger
# from core.app_scheduler import AppScheduler
from pydantic import BaseModel

from core.sandbox import load_module_in_sandbox,execute_query_in_sandbox
from db.session import get_db
from models.user import User
logger = get_logger("scheduler")
router = APIRouter()
from config import settings

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



# API路由

@router.get("/extensions",)
async def add_job_page(request: Request, user=Depends(view_extension),db=Depends(get_db)):
    """添加任务页面"""
    # 获取所有扩展中的扩展名及execute_query方法，以便添加定时任务
    extensions = await get_extensions(db)
    extension_methods = [
        {
            "extension_name": extension.name,
            "method_name": "execute_query",
            "extension_id": extension.id
        }
        for extension in extensions
    ]

    return {
            "task_types": TASK_TYPES,
            "extension_methods": extension_methods,
            "user": user
        }



@router.get("/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(request: Request, user=Depends(view_scheduler)):
    """获取所有任务"""
    try:
        scheduler = request.app.state.scheduler
        jobs = await scheduler.get_jobs()
        return jobs
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.get("/job/{job_id}", response_model=Dict[str, Any])
async def get_job(request: Request, job_id: str, user=Depends(view_scheduler)):
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

@router.post("/job/{job_id}/pause")
async def pause_job(request: Request, job_id: str, user=Depends(update_scheduler)):
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

@router.post("/job/{job_id}/resume")
async def resume_job(request: Request, job_id: str, user=Depends(resume_scheduler)):
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

@router.post("/job/{job_id}/run")
async def run_job(request: Request, job_id: str, user=Depends(execute_scheduler)):
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

@router.delete("/job/{job_id}")
async def remove_job(request: Request, job_id: str, user=Depends(delete_scheduler)):
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
async def async_task_wrapper(func, **kwargs):
    """包装异步任务函数"""
    try:
        result = await func(**kwargs)
        logger.info(f"任务执行完成，结果: {result}")
        return result
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        raise

@router.post("/jobs/cron")
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
    user:User=Depends(create_scheduler),db=Depends(get_db)
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

        # module = load_module_in_sandbox(f"data/extensions/{task_func}.py")

        extension = await get_extension(task_func,db=db)
        config = extension.config
        # func = execute_query_in_sandbox
        # 添加任务
        job_id = await scheduler.add_cron_job(
            async_task_wrapper,
            kwargs={"func": execute_query_in_sandbox,"params": {"extension_id": task_func},"config":config,"module":None} ,
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
        raise
        logger.error(f"添加Cron任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加Cron任务失败: {str(e)}")

@router.post("/jobs/interval")
async def add_interval_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    seconds: int = Form(0),
    minutes: int = Form(0),
    hours: int = Form(0),
    days: int = Form(0),
    user=Depends(create_scheduler),db=Depends(get_db)
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
        # py_path = os.path.join(settings.EXTENSIONS_DIR,f"{task_func}.py")
        # module = load_module_in_sandbox(os.path.abspath(py_path))

        # 获取函数
        extension = await get_extension(task_func,db=db)
        config = extension.config
        # func = execute_query_in_sandbox

        # 添加任务
        job_id = await scheduler.add_interval_job(
            async_task_wrapper,
            kwargs={"func": execute_query_in_sandbox,"params": {"extension_id": task_func},"config":config,"module":None} ,
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

@router.post("/jobs/date")
async def add_date_job(
    request: Request,
    task_func: str = Form(...),
    job_id: Optional[str] = Form(None),
    run_date: str = Form(...),  # 格式: YYYY-MM-DD HH:MM:SS
    user=Depends(create_scheduler),db=Depends(get_db)
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
        # module = load_module_in_sandbox(f"data/extensions/{task_func}.py")

        # 获取函数
        extension = await get_extension(task_func,db)
        config = extension.config
        # func = execute_query_in_sandbox

        # 添加任务
        job_id = await scheduler.add_date_job(
            async_task_wrapper,
            kwargs={"func": execute_query_in_sandbox,"params": {"extension_id": task_func},"config":config,"module":None} ,
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


@router.get("/api/jobs", response_class=JSONResponse)
async def get_all_jobs(request: Request,user=Depends(view_scheduler)):
    """获取所有任务"""
    scheduler = request.app.state.scheduler
    jobs = await scheduler.get_jobs()
    return {"success": True, "jobs": jobs}

@router.get("/api/jobs/{job_id}", response_class=JSONResponse)
async def get_job(request: Request, job_id: str,user=Depends(view_scheduler)):
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