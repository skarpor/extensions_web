"""
FastAPI应用调度器示例

本示例展示了如何在FastAPI应用中使用调度器。
使用app.state.scheduler访问调度器，无需了解内部实现细节。
"""
import asyncio
import datetime
from fastapi import FastAPI, Depends, APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from app.core.logger import get_logger

# 设置日志记录器
logger = get_logger("app_scheduler_example")

# 创建路由器
router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# 示例任务函数
async def demo_task():
    """演示任务"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"演示任务执行于 {now}"
    logger.info(message)
    return message

# 获取当前时间任务
async def get_time_task():
    """获取当前时间的任务"""
    now = datetime.datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": int(now.timestamp())
    }

# 创建路由端点
@router.get("/")
async def scheduler_info(request: Request):
    """获取调度器信息"""
    # 通过request.app.state.scheduler访问调度器
    jobs = await request.app.state.scheduler.get_jobs()
    
    return {
        "status": "running",
        "job_count": len(jobs),
        "jobs": jobs
    }

@router.post("/jobs/cron")
async def add_cron_job(request: Request, job_data: Dict[str, Any]):
    """添加Cron任务"""
    try:
        job_id = await request.app.state.scheduler.add_cron_job(
            demo_task,
            job_id=job_data.get("job_id"),
            minute=job_data.get("minute", "*/1"),
            hour=job_data.get("hour", "*"),
            day=job_data.get("day", "*"),
            month=job_data.get("month", "*"),
            day_of_week=job_data.get("day_of_week", "*")
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"已添加Cron任务: {job_id}"
        }
    except Exception as e:
        logger.error(f"添加Cron任务失败: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"添加任务失败: {str(e)}"
            }
        )

@router.post("/jobs/interval")
async def add_interval_job(request: Request, job_data: Dict[str, Any]):
    """添加间隔任务"""
    try:
        job_id = await request.app.state.scheduler.add_interval_job(
            demo_task,
            job_id=job_data.get("job_id"),
            seconds=job_data.get("seconds", 30),
            minutes=job_data.get("minutes", 0),
            hours=job_data.get("hours", 0)
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"已添加间隔任务: {job_id}"
        }
    except Exception as e:
        logger.error(f"添加间隔任务失败: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"添加任务失败: {str(e)}"
            }
        )

@router.post("/jobs/date")
async def add_date_job(request: Request, job_data: Dict[str, Any]):
    """添加一次性任务"""
    try:
        # 计算执行时间
        seconds = job_data.get("seconds", 60)
        run_date = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        
        job_id = await request.app.state.scheduler.add_date_job(
            demo_task,
            job_id=job_data.get("job_id"),
            run_date=run_date
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "run_date": run_date.strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"已添加一次性任务: {job_id}"
        }
    except Exception as e:
        logger.error(f"添加一次性任务失败: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"添加任务失败: {str(e)}"
            }
        )

@router.post("/jobs/{job_id}/pause")
async def pause_job(request: Request, job_id: str):
    """暂停任务"""
    result = await request.app.state.scheduler.pause_job(job_id)
    return {
        "success": result,
        "message": f"任务 {job_id} {'已暂停' if result else '暂停失败'}"
    }

@router.post("/jobs/{job_id}/resume")
async def resume_job(request: Request, job_id: str):
    """恢复任务"""
    result = await request.app.state.scheduler.resume_job(job_id)
    return {
        "success": result,
        "message": f"任务 {job_id} {'已恢复' if result else '恢复失败'}"
    }

@router.post("/jobs/{job_id}/run")
async def run_job(request: Request, job_id: str):
    """立即执行任务"""
    result = await request.app.state.scheduler.run_job(job_id)
    return {
        "success": result,
        "message": f"任务 {job_id} {'已触发执行' if result else '触发执行失败'}"
    }

@router.delete("/jobs/{job_id}")
async def remove_job(request: Request, job_id: str):
    """移除任务"""
    result = await request.app.state.scheduler.remove_job(job_id)
    return {
        "success": result,
        "message": f"任务 {job_id} {'已移除' if result else '移除失败'}"
    }

@router.get("/jobs/{job_id}")
async def get_job(request: Request, job_id: str):
    """获取任务信息"""
    job_info = await request.app.state.scheduler.get_job(job_id)
    if job_info:
        return {
            "success": True,
            "job": job_info
        }
    else:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": f"任务 {job_id} 不存在"
            }
        )

# 初始化示例路由
def init_router(app: FastAPI):
    """将路由器添加到应用"""
    app.include_router(router)
    
    # 添加示例任务
    @app.on_event("startup")
    async def add_example_jobs():
        # 等待调度器初始化完成
        await asyncio.sleep(1)
        
        # 添加一个获取时间的任务，每分钟执行一次
        await app.state.scheduler.add_cron_job(
            get_time_task,
            job_id="time_job",
            minute="*"
        )
        
        logger.info("已添加示例任务") 