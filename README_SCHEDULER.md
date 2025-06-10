# 定时任务模块

## 概述

本模块提供了基于APScheduler的定时任务调度功能，支持以下类型的任务：

- **Cron任务**：基于cron表达式的定时任务
- **间隔任务**：按固定时间间隔执行的任务
- **一次性任务**：在指定时间点执行一次的任务

## 模块结构

```
app/
  ├── core/
  │   ├── app_scheduler.py     # 应用调度器接口（推荐使用）
  │   ├── aps.py               # 底层调度器API接口
  │   └── scheduler.py         # 调度器核心实现
  │
example/
  ├── scheduler_extension_example.py  # 完整扩展示例
  ├── simple_scheduler_example.py     # 简单使用示例
  └── app_scheduler_example.py        # FastAPI应用集成示例
  
docs/
  └── SCHEDULER_USAGE_GUIDE.md        # 详细使用指南
```

## 快速开始

### 在FastAPI应用中使用（推荐）

```python
from fastapi import FastAPI, Request

app = FastAPI()

# 1. 创建任务函数
async def my_task():
    print("执行定时任务")
    return "任务执行完成"

# 2. 在路由处理函数中添加任务
@app.post("/add-task")
async def add_task(request: Request):
    # 使用app.state.scheduler访问调度器
    job_id = await request.app.state.scheduler.add_interval_job(
        my_task,
        job_id="my_job",
        seconds=30  # 每30秒执行一次
    )
    return {"job_id": job_id}

# 3. 管理任务
@app.delete("/jobs/{job_id}")
async def remove_task(request: Request, job_id: str):
    result = await request.app.state.scheduler.remove_job(job_id)
    return {"success": result}
```

### 在扩展中使用

```python
# 1. 添加接收应用实例的方法
app_instance = None

def set_app(app):
    global app_instance
    app_instance = app

# 2. 创建任务函数
async def my_task():
    print("执行定时任务")
    return "任务执行完成"

# 3. 添加任务
async def init_tasks(config):
    if not app_instance or not hasattr(app_instance.state, 'scheduler'):
        return False
        
    # 使用app.state.scheduler访问调度器
    scheduler = app_instance.state.scheduler
    
    job_id = await scheduler.add_cron_job(
        my_task,
        job_id="my_cron_job",
        minute="*/5",  # 每5分钟执行一次
        hour="*",
        day="*",
        month="*",
        day_of_week="*"
    )
    
    return job_id
```

## 任务类型

### Cron任务

使用cron表达式定义的任务，格式为：`分 时 日 月 星期`。

```python
job_id = await scheduler.add_cron_job(
    my_task,
    minute="*/5",  # 每5分钟执行一次
    hour="*",
    day="*",
    month="*",
    day_of_week="*"
)
```

### 间隔任务

按固定时间间隔执行的任务。

```python
job_id = await scheduler.add_interval_job(
    my_task,
    seconds=30,  # 每30秒执行一次
    minutes=0,
    hours=0
)
```

### 一次性任务

在指定时间点执行一次的任务。

```python
import datetime
run_date = datetime.datetime.now() + datetime.timedelta(hours=1)
job_id = await scheduler.add_date_job(
    my_task,
    run_date=run_date  # 1小时后执行
)
```

## 示例运行

### FastAPI应用集成示例

运行应用后，可以通过以下API测试定时任务功能：

- GET `/scheduler` - 获取所有任务信息
- POST `/scheduler/jobs/cron` - 添加Cron任务
- POST `/scheduler/jobs/interval` - 添加间隔任务
- POST `/scheduler/jobs/date` - 添加一次性任务
- POST `/scheduler/jobs/{job_id}/pause` - 暂停任务
- POST `/scheduler/jobs/{job_id}/resume` - 恢复任务
- POST `/scheduler/jobs/{job_id}/run` - 立即执行任务
- DELETE `/scheduler/jobs/{job_id}` - 删除任务
- GET `/scheduler/jobs/{job_id}` - 获取任务信息

### 扩展示例

扩展示例展示了如何在扩展中集成定时任务功能，包括：

- 任务初始化
- 配置管理
- 日志记录
- 任务状态查询

## 更多资源

- [详细使用指南](docs/SCHEDULER_USAGE_GUIDE.md)
- [APScheduler官方文档](https://apscheduler.readthedocs.io/)

## 注意事项

1. 所有任务函数必须是异步函数（使用`async def`定义）
2. 默认情况下，任务存储在内存中，应用重启后会丢失
3. 任务函数应包含适当的异常处理，避免任务失败导致调度器异常
4. 任务ID应保持唯一，重复的任务ID会覆盖现有任务
5. 优先使用`app.state.scheduler`，而不是直接导入内部模块 