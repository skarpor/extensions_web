"""
APScheduler调度器接口

提供与应用程序集成的调度器功能接口。
这是对scheduler.py中功能的简单包装，提供异步API支持。
"""
from .scheduler import get_scheduler
from .logger import get_logger

logger = get_logger("aps")
from config import settings

# 在应用启动时启动调度器
async def start_scheduler():
    """启动调度器"""
    try:
        # scheduler = get_scheduler(db_url=f"sqlite:///{db_path}")
        scheduler = get_scheduler(db_url=settings.SYNC_SQLALCHEMY_DATABASE_URI,async_mode=True)
        scheduler.start()
        logger.info("调度器已启动")
    except Exception as e:
        logger.error(f"启动调度器失败: {str(e)}")

# 在应用关闭时关闭调度器
async def stop_scheduler():
    """关闭调度器"""
    try:
        scheduler = get_scheduler()
        if scheduler.is_running:
            scheduler.shutdown()
            logger.info("调度器已关闭")
    except Exception as e:
        logger.error(f"关闭调度器失败: {str(e)}")

# 添加任务
async def add_job(func, **kwargs):
    """添加任务"""
    try:
        scheduler = get_scheduler()
        job_id = scheduler.add_job(func, **kwargs)
        return job_id
    except Exception as e:
        logger.error(f"添加任务失败: {str(e)}")
        return None

# 添加cron任务
async def add_cron_job(func, **kwargs):
    """添加Cron定时任务"""
    try:
        scheduler = get_scheduler()
        job_id = scheduler.add_cron_job(func, **kwargs)
        return job_id
    except Exception as e:
        logger.error(f"添加Cron任务失败: {str(e)}")
        raise

# 添加间隔任务
async def add_interval_job(func, **kwargs):
    """添加间隔定时任务"""
    try:
        scheduler = get_scheduler()
        job_id = scheduler.add_interval_job(func, **kwargs)
        return job_id
    except Exception as e:
        logger.error(f"添加间隔任务失败: {str(e)}")
        return None

# 添加一次性任务
async def add_date_job(func, **kwargs):
    """添加一次性定时任务"""
    try:
        scheduler = get_scheduler()
        job_id = scheduler.add_date_job(func, **kwargs)
        return job_id
    except Exception as e:
        logger.error(f"添加一次性任务失败: {str(e)}")
        return None

# 移除任务
async def remove_job(job_id):
    """移除任务"""
    try:
        scheduler = get_scheduler()
        return scheduler.remove_job(job_id)
    except Exception as e:
        logger.error(f"移除任务失败: {str(e)}")
        return False

# 暂停任务
async def pause_job(job_id):
    """暂停任务"""
    try:
        scheduler = get_scheduler()
        return scheduler.pause_job(job_id)
    except Exception as e:
        logger.error(f"暂停任务失败: {str(e)}")
        return False

# 恢复任务
async def resume_job(job_id):
    """恢复任务"""
    try:
        scheduler = get_scheduler()
        return scheduler.resume_job(job_id)
    except Exception as e:
        logger.error(f"恢复任务失败: {str(e)}")
        return False

# 获取任务信息
async def get_job(job_id):
    """获取任务信息"""
    try:
        scheduler = get_scheduler()
        return scheduler.get_job(job_id)
    except Exception as e:
        logger.error(f"获取任务信息失败: {str(e)}")
        return None

# 获取所有任务
async def get_jobs():
    """获取所有任务"""
    try:
        scheduler = get_scheduler()
        return scheduler.get_jobs()
    except Exception as e:
        logger.error(f"获取所有任务失败: {str(e)}")
        return []

# 立即运行任务
async def run_job(job_id):
    """立即运行任务"""
    try:
        scheduler = get_scheduler()
        return scheduler.run_job(job_id)
    except Exception as e:
        logger.error(f"立即运行任务失败: {str(e)}")
        return False



