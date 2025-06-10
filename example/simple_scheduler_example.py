"""
简单定时任务示例

这是一个简单的定时任务示例，演示如何使用定时任务API
"""
import asyncio
import datetime
from app.core import aps
from app.core.logger import get_logger

# 设置日志记录器
logger = get_logger("simple_scheduler")

# 示例任务函数
async def simple_hello_task():
    """简单的问候任务"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{now}] 你好，世界！这是一个简单的定时任务。"
    logger.info(message)
    return message

# 示例时间戳任务
async def timestamp_task():
    """时间戳任务"""
    now = datetime.datetime.now()
    timestamp = int(now.timestamp())
    message = f"当前时间戳: {timestamp}"
    logger.info(message)
    return message

# 示例日期和时间任务
async def date_time_task():
    """日期和时间任务"""
    now = datetime.datetime.now()
    formatted_date = now.strftime("%Y年%m月%d日")
    formatted_time = now.strftime("%H时%M分%S秒")
    message = f"今天是 {formatted_date}，现在是 {formatted_time}"
    logger.info(message)
    return message

# 主函数
async def main():
    """主函数"""
    print("定时任务示例启动...")
    
    # 启动调度器
    await aps.start_scheduler()
    print("调度器已启动")
    
    try:
        # 添加一个每5秒执行一次的任务
        interval_job_id = await aps.add_interval_job(
            simple_hello_task,
            job_id="simple_interval_job",
            seconds=5
        )
        print(f"已添加间隔任务: {interval_job_id}")
        
        # 添加一个cron任务（每分钟的第15秒执行）
        cron_job_id = await aps.add_cron_job(
            timestamp_task,
            job_id="simple_cron_job",
            second="15",
            minute="*",
            hour="*"
        )
        print(f"已添加Cron任务: {cron_job_id}")
        
        # 添加一个一次性任务（30秒后执行）
        run_date = datetime.datetime.now() + datetime.timedelta(seconds=30)
        date_job_id = await aps.add_date_job(
            date_time_task,
            job_id="simple_date_job",
            run_date=run_date
        )
        print(f"已添加一次性任务: {date_job_id}，将在 {run_date.strftime('%H:%M:%S')} 执行")
        
        # 获取所有任务信息
        jobs = await aps.get_jobs()
        print(f"当前共有 {len(jobs)} 个任务:")
        for job in jobs:
            print(f"  - {job['id']}: {job['next_run_time']}")
        
        # 等待60秒观察任务执行
        print("\n等待60秒观察任务执行...\n")
        for i in range(60):
            await asyncio.sleep(1)
            # 每10秒打印一次计数
            if i > 0 and i % 10 == 0:
                print(f"已等待 {i} 秒...")
        
        # 暂停interval任务
        print(f"\n暂停任务: {interval_job_id}")
        await aps.pause_job(interval_job_id)
        
        # 等待10秒
        print("等待10秒（interval任务应该不会执行）...")
        await asyncio.sleep(10)
        
        # 恢复interval任务
        print(f"恢复任务: {interval_job_id}")
        await aps.resume_job(interval_job_id)
        
        # 等待10秒
        print("等待10秒（interval任务应该会恢复执行）...")
        await asyncio.sleep(10)
        
        # 立即执行一次cron任务
        print(f"立即执行任务: {cron_job_id}")
        await aps.run_job(cron_job_id)
        
        # 等待5秒
        await asyncio.sleep(5)
        
        # 移除所有任务
        print("移除所有任务...")
        for job_id in [interval_job_id, cron_job_id, date_job_id]:
            await aps.remove_job(job_id)
        
        # 确认任务已移除
        jobs = await aps.get_jobs()
        print(f"移除后剩余任务数: {len(jobs)}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        # 停止调度器
        print("停止调度器...")
        await aps.stop_scheduler()
        print("定时任务示例结束")

# 如果直接运行此文件
if __name__ == "__main__":
    asyncio.run(main())