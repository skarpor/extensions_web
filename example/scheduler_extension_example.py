"""
定时任务扩展示例

本示例展示了如何使用定时任务功能创建自动执行的任务。
通过app.state.scheduler访问调度器功能，无需了解内部实现细节。
"""
import os
import time
import datetime
import json
from typing import Dict, Any, List
from app.core.logger import get_logger

# 设置日志
logger = get_logger("scheduler_extension")

# 定义扩展信息
EXTENSION_ID = "scheduler_example"
EXTENSION_NAME = "定时任务示例"
EXTENSION_DESCRIPTION = "展示如何使用定时任务功能创建自动执行的任务"
EXTENSION_VERSION = "1.0.0"
EXTENSION_AUTHOR = "系统"

# 扩展配置默认值
DEFAULT_CONFIG = {
    "enabled": True,
    "log_dir": "logs/scheduler_example",
    "cron_schedule": "*/5 * * * *",  # 每5分钟执行一次
    "interval_seconds": 30,  # 每30秒执行一次
}

# 全局变量，用于跟踪已注册的任务
registered_jobs = {}

# 任务执行计数
execution_count = 0

# 应用实例
app_instance = None

# 设置应用实例
def set_app(app):
    """设置应用实例"""
    global app_instance
    app_instance = app
    logger.info("已设置应用实例")

# 示例Cron任务函数
async def example_cron_task():
    """示例Cron定时任务"""
    global execution_count
    execution_count += 1
    
    # 获取当前时间
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 记录日志
    logger.info(f"Cron任务执行 #{execution_count} 时间: {now}")
    
    # 创建日志目录
    os.makedirs(DEFAULT_CONFIG["log_dir"], exist_ok=True)
    
    # 写入执行记录
    log_file = os.path.join(DEFAULT_CONFIG["log_dir"], "cron_task.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{now} - Cron任务执行 #{execution_count}\n")
    
    return f"Cron任务执行完成 #{execution_count}"

# 示例间隔任务函数
async def example_interval_task():
    """示例间隔定时任务"""
    # 获取当前时间
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 记录日志
    logger.info(f"间隔任务执行 时间: {now}")
    
    # 创建日志目录
    os.makedirs(DEFAULT_CONFIG["log_dir"], exist_ok=True)
    
    # 写入执行记录
    log_file = os.path.join(DEFAULT_CONFIG["log_dir"], "interval_task.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{now} - 间隔任务执行\n")
    
    return "间隔任务执行完成"

# 示例一次性任务函数
async def example_date_task():
    """示例一次性定时任务"""
    # 获取当前时间
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 记录日志
    logger.info(f"一次性任务执行 时间: {now}")
    
    # 创建日志目录
    os.makedirs(DEFAULT_CONFIG["log_dir"], exist_ok=True)
    
    # 写入执行记录
    log_file = os.path.join(DEFAULT_CONFIG["log_dir"], "date_task.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{now} - 一次性任务执行\n")
    
    return "一次性任务执行完成"

# 初始化扩展并注册任务
async def init_tasks(config: Dict[str, Any] = None):
    """初始化任务"""
    global registered_jobs, app_instance
    
    # 检查应用实例是否已设置
    if app_instance is None:
        logger.error("应用实例未设置，无法初始化任务")
        return False
    
    # 检查调度器是否已初始化
    if not hasattr(app_instance.state, 'scheduler'):
        logger.error("调度器未初始化，无法注册任务")
        return False
    
    # 获取调度器实例
    scheduler = app_instance.state.scheduler
    
    # 合并配置
    cfg = DEFAULT_CONFIG.copy()
    if config:
        cfg.update(config)
    
    # 确保日志目录存在
    os.makedirs(cfg["log_dir"], exist_ok=True)
    
    # 如果扩展被禁用，不注册任务
    if not cfg["enabled"]:
        logger.info("定时任务扩展已禁用")
        return False
    
    try:
        # 清理之前注册的任务
        for job_id in registered_jobs.values():
            await scheduler.remove_job(job_id)
        registered_jobs = {}
        
        # 注册Cron任务
        cron_parts = cfg["cron_schedule"].split()
        if len(cron_parts) != 5:
            logger.error(f"无效的cron表达式: {cfg['cron_schedule']}")
            return False
            
        cron_job_id = await scheduler.add_cron_job(
            example_cron_task,
            job_id=f"{EXTENSION_ID}_cron",
            # 解析cron表达式
            # 格式: 分 时 日 月 星期
            # */5 * * * * 表示每5分钟执行一次
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4]
        )
        registered_jobs["cron"] = cron_job_id
        logger.info(f"已注册Cron任务: {cron_job_id}")
        
        # 注册间隔任务
        interval_job_id = await scheduler.add_interval_job(
            example_interval_task,
            job_id=f"{EXTENSION_ID}_interval",
            seconds=cfg["interval_seconds"]
        )
        registered_jobs["interval"] = interval_job_id
        logger.info(f"已注册间隔任务: {interval_job_id}")
        
        # 注册一次性任务（1分钟后执行）
        run_date = datetime.datetime.now() + datetime.timedelta(minutes=1)
        date_job_id = await scheduler.add_date_job(
            example_date_task,
            job_id=f"{EXTENSION_ID}_date",
            run_date=run_date
        )
        registered_jobs["date"] = date_job_id
        logger.info(f"已注册一次性任务: {date_job_id}, 执行时间: {run_date}")
        
        return True
    except Exception as e:
        logger.error(f"注册任务失败: {str(e)}")
        return False

# 查询任务信息
async def get_task_info() -> Dict[str, Any]:
    """获取任务信息"""
    global registered_jobs, app_instance
    
    if app_instance is None or not hasattr(app_instance.state, 'scheduler'):
        logger.error("调度器未初始化，无法获取任务信息")
        return {
            "error": "调度器未初始化",
            "registered_jobs": {},
            "execution_count": execution_count,
            "log_files": []
        }
    
    # 获取调度器实例
    scheduler = app_instance.state.scheduler
    
    result = {
        "registered_jobs": {},
        "execution_count": execution_count,
        "log_files": []
    }
    
    # 获取任务详情
    for task_type, job_id in registered_jobs.items():
        job_info = await scheduler.get_job(job_id)
        if job_info:
            result["registered_jobs"][task_type] = job_info
    
    # 获取日志文件
    if os.path.exists(DEFAULT_CONFIG["log_dir"]):
        for file in os.listdir(DEFAULT_CONFIG["log_dir"]):
            if file.endswith(".log"):
                log_path = os.path.join(DEFAULT_CONFIG["log_dir"], file)
                log_size = os.path.getsize(log_path)
                log_mtime = os.path.getmtime(log_path)
                
                # 读取最后10行
                last_lines = []
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        last_lines = lines[-10:] if len(lines) > 10 else lines
                except Exception as e:
                    last_lines = [f"读取日志出错: {str(e)}"]
                
                result["log_files"].append({
                    "name": file,
                    "size": log_size,
                    "last_modified": datetime.datetime.fromtimestamp(log_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "last_lines": last_lines
                })
    
    return result

# 主查询接口 - 由应用调用
def execute_query(params: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    扩展查询接口
    
    Args:
        params: 查询参数
        config: 扩展配置
        
    Returns:
        查询结果
    """
    global app_instance, registered_jobs
    
    action = params.get("action", "info")
    
    # 导入asyncio以运行异步函数
    import asyncio
    
    if action == "init":
        # 初始化任务
        result = asyncio.run(init_tasks(config))
        return {
            "success": result,
            "message": "任务初始化成功" if result else "任务初始化失败"
        }
    
    elif action == "info":
        # 获取任务信息
        task_info = asyncio.run(get_task_info())
        return {
            "success": True,
            "task_info": task_info
        }
    
    elif action == "run":
        # 立即运行指定任务
        task_type = params.get("task_type")
        if not task_type or task_type not in registered_jobs:
            return {
                "success": False,
                "message": f"无效的任务类型: {task_type}"
            }
        
        # 检查调度器
        if app_instance is None or not hasattr(app_instance.state, 'scheduler'):
            return {
                "success": False,
                "message": "调度器未初始化"
            }
            
        job_id = registered_jobs[task_type]
        result = asyncio.run(app_instance.state.scheduler.run_job(job_id))
        
        return {
            "success": result,
            "message": f"任务 {job_id} 已触发执行" if result else f"触发任务 {job_id} 失败"
        }
    
    elif action == "pause":
        # 暂停指定任务
        task_type = params.get("task_type")
        if not task_type or task_type not in registered_jobs:
            return {
                "success": False,
                "message": f"无效的任务类型: {task_type}"
            }
        
        # 检查调度器
        if app_instance is None or not hasattr(app_instance.state, 'scheduler'):
            return {
                "success": False,
                "message": "调度器未初始化"
            }
            
        job_id = registered_jobs[task_type]
        result = asyncio.run(app_instance.state.scheduler.pause_job(job_id))
        
        return {
            "success": result,
            "message": f"任务 {job_id} 已暂停" if result else f"暂停任务 {job_id} 失败"
        }
    
    elif action == "resume":
        # 恢复指定任务
        task_type = params.get("task_type")
        if not task_type or task_type not in registered_jobs:
            return {
                "success": False,
                "message": f"无效的任务类型: {task_type}"
            }
        
        # 检查调度器
        if app_instance is None or not hasattr(app_instance.state, 'scheduler'):
            return {
                "success": False,
                "message": "调度器未初始化"
            }
            
        job_id = registered_jobs[task_type]
        result = asyncio.run(app_instance.state.scheduler.resume_job(job_id))
        
        return {
            "success": result,
            "message": f"任务 {job_id} 已恢复" if result else f"恢复任务 {job_id} 失败"
        }
    
    else:
        return {
            "success": False,
            "message": f"未知操作: {action}"
        } 