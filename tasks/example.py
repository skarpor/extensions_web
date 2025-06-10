"""
示例任务模块
提供可用于测试定时任务功能的示例函数
"""

import time
import random
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tasks.example")


async def send_notification():
    """
    模拟发送通知
    
    此函数模拟向用户发送通知的过程
    """
    logger.info(f"[{datetime.now()}] 开始发送通知...")
    
    # 模拟随机处理时间
    process_time = random.uniform(0.5, 2.0)
    time.sleep(process_time)
    
    recipients = random.randint(5, 20)
    logger.info(f"[{datetime.now()}] 成功发送通知给 {recipients} 位用户，耗时：{process_time:.2f}秒")
    
    return {
        "recipients": recipients,
        "duration": process_time,
        "status": "success"
    }


async def sync_data():
    """
    模拟数据同步
    
    此函数模拟在不同系统之间同步数据的过程
    """
    logger.info(f"[{datetime.now()}] 开始同步数据...")
    
    # 模拟随机处理时间
    process_time = random.uniform(1.0, 5.0)
    time.sleep(process_time)
    
    # 模拟同步结果
    records = random.randint(10, 100)
    success = random.randint(0, records)
    failed = records - success
    
    logger.info(f"[{datetime.now()}] 数据同步完成，成功：{success}，失败：{failed}，总计：{records}，耗时：{process_time:.2f}秒")
    
    return {
        "total": records,
        "success": success,
        "failed": failed,
        "duration": process_time,
        "status": "completed"
    }


async def generate_report():
    """
    模拟生成报表
    
    此函数模拟生成统计报表的过程
    """
    logger.info(f"[{datetime.now()}] 开始生成报表...")
    
    # 模拟随机处理时间
    process_time = random.uniform(2.0, 8.0)
    time.sleep(process_time)
    
    # 模拟报表内容
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_data = {
        "date": report_date,
        "statistics": {
            "users": random.randint(100, 1000),
            "transactions": random.randint(50, 500),
            "revenue": random.uniform(1000.0, 10000.0),
        }
    }
    
    logger.info(f"[{datetime.now()}] 报表生成完成，日期：{report_date}，耗时：{process_time:.2f}秒")
    
    return {
        "report": report_data,
        "duration": process_time,
        "status": "generated"
    }


async def clean_old_data():
    """
    模拟清理旧数据
    
    此函数模拟清理系统中过期的临时数据
    """
    logger.info(f"[{datetime.now()}] 开始清理旧数据...")
    
    # 模拟随机处理时间
    process_time = random.uniform(0.5, 3.0)
    time.sleep(process_time)
    
    # 模拟清理结果
    files_removed = random.randint(5, 50)
    space_freed = random.uniform(10.0, 500.0)
    
    logger.info(f"[{datetime.now()}] 旧数据清理完成，删除文件：{files_removed}个，释放空间：{space_freed:.2f}MB，耗时：{process_time:.2f}秒")
    
    return {
        "files_removed": files_removed,
        "space_freed": f"{space_freed:.2f}MB",
        "duration": process_time,
        "status": "cleaned"
    }


async def backup_database():
    """
    模拟数据库备份
    
    此函数模拟对数据库进行备份的过程
    """
    logger.info(f"[{datetime.now()}] 开始数据库备份...")
    
    # 模拟随机处理时间
    process_time = random.uniform(3.0, 10.0)
    time.sleep(process_time)
    
    # 模拟备份结果
    backup_size = random.uniform(50.0, 500.0)
    backup_path = f"/backups/db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    logger.info(f"[{datetime.now()}] 数据库备份完成，备份大小：{backup_size:.2f}MB，备份路径：{backup_path}，耗时：{process_time:.2f}秒")
    
    return {
        "backup_size": f"{backup_size:.2f}MB",
        "backup_path": backup_path,
        "timestamp": datetime.now().isoformat(),
        "duration": process_time,
        "status": "success"
    }


# 测试函数，用于直接执行时进行测试
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("测试发送通知:")
        result = await send_notification()
        print(f"结果: {result}\n")
        
        print("测试数据同步:")
        result = await sync_data()
        print(f"结果: {result}\n")
        
        print("测试生成报表:")
        result = await generate_report()
        print(f"结果: {result}\n")
        
        print("测试清理旧数据:")
        result = await clean_old_data()
        print(f"结果: {result}\n")
        
        print("测试数据库备份:")
        result = await backup_database()
        print(f"结果: {result}\n")
    
    # 运行测试
    asyncio.run(test()) 