"""
应用调度器接口模块

为应用提供简化的调度器接口，用户可以通过app.state.scheduler直接访问。
这个模块提供了连接FastAPI应用和调度器的桥梁。
"""
from fastapi import FastAPI
from typing import Callable, Optional, Dict, Any, List, Union
import datetime
import asyncio

from .aps import (
    start_scheduler, stop_scheduler, add_job, add_cron_job,
    add_interval_job, add_date_job, remove_job, pause_job,
    resume_job, get_job, get_jobs, run_job
)

from .logger import get_logger

logger = get_logger("app_scheduler")

def init_scheduler(app: FastAPI):
    """
    初始化应用的调度器，并添加到app.state
    
    Args:
        app: FastAPI应用实例
    """
    # 在应用启动时启动调度器
    @app.on_event("startup")
    async def start_app_scheduler():
        await start_scheduler()
        # 创建一个简化的接口供应用使用
        app.state.scheduler = AppScheduler()
        logger.info("应用调度器已初始化")
    
    # 在应用关闭时停止调度器
    @app.on_event("shutdown")
    async def stop_app_scheduler():
        await stop_scheduler()
        logger.info("应用调度器已关闭")

class AppScheduler:
    """应用调度器接口类"""
    
    async def add_job(self, func: Callable, **kwargs) -> str:
        """添加任务"""
        return await add_job(func, **kwargs)
    
    async def add_cron_job(self, 
                          func: Callable, 
                          job_id: str = None,
                          minute: str = "*", 
                          hour: str = "*", 
                          day: str = "*", 
                          month: str = "*", 
                          day_of_week: str = "*",
                          second: str = "0",
                          **kwargs) -> str:
        """
        添加Cron定时任务
        
        Args:
            func: 要执行的异步函数
            job_id: 任务ID
            minute: 分钟 (0-59)
            hour: 小时 (0-23)
            day: 日期 (1-31)
            month: 月份 (1-12)
            day_of_week: 星期 (0-6 or mon,tue,wed,thu,fri,sat,sun)
            second: 秒 (0-59)
            
        Returns:
            任务ID
        """
        return await add_cron_job(
            func, 
            job_id=job_id,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            second=second,
            **kwargs
        )
    
    async def add_interval_job(self,
                              func: Callable,
                              job_id: str = None,
                              seconds: int = 0,
                              minutes: int = 0,
                              hours: int = 0,
                              days: int = 0,
                              weeks: int = 0,
                              **kwargs) -> str:
        """
        添加间隔定时任务
        
        Args:
            func: 要执行的异步函数
            job_id: 任务ID
            seconds: 秒数
            minutes: 分钟数
            hours: 小时数
            days: 天数
            weeks: 周数
            
        Returns:
            任务ID
        """
        return await add_interval_job(
            func,
            job_id=job_id,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            weeks=weeks,
            **kwargs
        )
    
    async def add_date_job(self,
                          func: Callable,
                          job_id: str = None,
                          run_date: datetime.datetime = None,
                          **kwargs) -> str:
        """
        添加一次性定时任务
        
        Args:
            func: 要执行的异步函数
            job_id: 任务ID
            run_date: 执行时间
            
        Returns:
            任务ID
        """
        return await add_date_job(
            func,
            job_id=job_id,
            run_date=run_date,
            **kwargs
        )
    
    async def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        return await remove_job(job_id)
    
    async def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        return await pause_job(job_id)
    
    async def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        return await resume_job(job_id)
    
    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """获取任务信息"""
        return await get_job(job_id)
    
    async def get_jobs(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return await get_jobs()
    
    async def run_job(self, job_id: str) -> bool:
        """立即执行任务"""
        return await run_job(job_id) 