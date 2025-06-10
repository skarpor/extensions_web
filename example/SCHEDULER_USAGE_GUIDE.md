# 定时任务使用指南

本文档介绍了如何在系统中使用定时任务功能，实现自动化任务调度。

## 目录

- [概述](#概述)
- [定时任务类型](#定时任务类型)
- [在FastAPI应用中使用定时任务](#在fastapi应用中使用定时任务)
- [在扩展中使用定时任务](#在扩展中使用定时任务)
- [API接口参考](#api接口参考)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 概述

定时任务系统基于APScheduler（Advanced Python Scheduler）实现，提供了三种类型的任务调度机制：

1. **Cron任务**：基于cron表达式的任务调度，可以精确指定任务在特定时间点执行
2. **间隔任务**：按固定时间间隔重复执行的任务
3. **一次性任务**：在指定的时间点执行一次的任务

系统提供了两种方式访问调度器功能：
1. 通过`app.state.scheduler`（推荐）
2. 通过`app.core.aps`模块（仅内部使用）

## 定时任务类型

### Cron任务

Cron任务基于cron表达式进行调度，格式为：`分 时 日 月 星期`

例如：
- `*/5 * * * *` - 每5分钟执行一次
- `0 * * * *` - 每小时整点执行
- `0 9 * * 1-5` - 工作日上午9点执行
- `0 0 1 * *` - 每月1日零点执行

### 间隔任务

间隔任务按固定时间间隔重复执行，可以指定秒、分钟、小时等间隔单位。

例如：
- 每30秒执行一次
- 每2小时执行一次

### 一次性任务

一次性任务在指定的日期和时间执行一次，执行完成后自动从调度器中移除。

## 在FastAPI应用中使用定时任务

在FastAPI应用中，定时任务调度器已经在应用启动时自动初始化，并挂载到`app.state.scheduler`上。您可以直接使用它来添加和管理任务。

### 创建任务函数

任务函数必须是异步函数（使用`async def`定义）：

```python
async def my_task(param1, param2="default"):
    # 任务逻辑
    print(f"执行定时任务，参数: {param1}, {param2}")
    return "任务执行完成"
```

### 在路由处理函数中添加任务

```python
@app.post("/schedule")
async def schedule_task(request: Request, task_data: dict):
    # 从请求中获取参数
    interval = task_data.get("interval", 60)  # 默认60秒
    
    # 添加间隔任务
    job_id = await request.app.state.scheduler.add_interval_job(
        my_task,  # 任务函数
        args=["参数1"],  # 位置参数
        kwargs={"param2": "自定义值"},  # 关键字参数
        job_id="my_custom_job",  # 任务ID
        seconds=interval  # 间隔时间
    )
    
    return {"success": True, "job_id": job_id}
```

### 管理任务

```python
@app.post("/jobs/{job_id}/pause")
async def pause_job(request: Request, job_id: str):
    # 暂停任务
    result = await request.app.state.scheduler.pause_job(job_id)
    return {"success": result}

@app.post("/jobs/{job_id}/resume")
async def resume_job(request: Request, job_id: str):
    # 恢复任务
    result = await request.app.state.scheduler.resume_job(job_id)
    return {"success": result}

@app.delete("/jobs/{job_id}")
async def delete_job(request: Request, job_id: str):
    # 删除任务
    result = await request.app.state.scheduler.remove_job(job_id)
    return {"success": result}
```

## 在扩展中使用定时任务

对于扩展开发者，您可以通过两种方式使用定时任务功能：

### 方式1：使用app.state.scheduler（推荐）

使用此方法，扩展需要实现`set_app`方法接收应用实例，然后通过`app.state.scheduler`访问调度器。

```python
# 应用实例
app_instance = None

def set_app(app):
    """设置应用实例"""
    global app_instance
    app_instance = app

async def init_tasks(config):
    """初始化任务"""
    global app_instance
    
    # 确保应用实例存在
    if app_instance is None or not hasattr(app_instance.state, 'scheduler'):
        return False
    
    # 通过app.state.scheduler访问调度器
    scheduler = app_instance.state.scheduler
    
    # 添加任务
    job_id = await scheduler.add_interval_job(
        my_task_function,
        job_id="extension_task",
        seconds=30
    )
    
    return job_id
```

### 方式2：使用app.core.aps模块（不推荐）

这种方式会绕过应用状态，直接访问内部模块，不推荐使用。仅在不得已情况下使用。

```python
from app.core import aps

async def init_tasks(config):
    # 添加任务
    job_id = await aps.add_interval_job(
        my_task_function,
        job_id="extension_task",
        seconds=30
    )
    
    return job_id
```

## API接口参考

### 启动和停止调度器

这些函数通常不需要手动调用，应用会自动管理调度器的生命周期。

### 添加任务

```python
# 添加通用任务
job_id = await app.state.scheduler.add_job(
    func,  # 异步函数
    job_id=None,  # 可选，任务ID
    **kwargs  # 其他APScheduler参数
)

# 添加Cron任务
job_id = await app.state.scheduler.add_cron_job(
    func,  # 异步函数
    job_id=None,  # 可选，任务ID
    minute="0",  # cron参数
    hour="*",
    day="*",
    month="*",
    day_of_week="*",
    second="0"  # 秒参数，默认为0
)

# 添加间隔任务
job_id = await app.state.scheduler.add_interval_job(
    func,  # 异步函数
    job_id=None,  # 可选，任务ID
    seconds=0,  # 间隔参数，至少指定一个
    minutes=0,
    hours=0,
    days=0,
    weeks=0
)

# 添加一次性任务
job_id = await app.state.scheduler.add_date_job(
    func,  # 异步函数
    job_id=None,  # 可选，任务ID
    run_date=None  # 执行日期时间，datetime对象
)
```

### 管理任务

```python
# 移除任务
success = await app.state.scheduler.remove_job(job_id)

# 暂停任务
success = await app.state.scheduler.pause_job(job_id)

# 恢复任务
success = await app.state.scheduler.resume_job(job_id)

# 获取单个任务信息
job_info = await app.state.scheduler.get_job(job_id)

# 获取所有任务
all_jobs = await app.state.scheduler.get_jobs()

# 立即执行任务
success = await app.state.scheduler.run_job(job_id)
```

## 最佳实践

1. **使用有意义的任务ID**：为任务指定有意义的ID，便于管理和调试

2. **异常处理**：在任务函数中添加异常处理，避免任务失败导致调度器异常

   ```python
   async def safe_task():
       try:
           # 任务逻辑
           return "任务执行成功"
       except Exception as e:
           logger.error(f"任务执行失败: {str(e)}")
           return f"任务执行失败: {str(e)}"
   ```

3. **任务超时处理**：对于可能长时间运行的任务，考虑添加超时机制

4. **状态管理**：对于关键任务，保存任务执行状态和结果，便于监控和排查问题

5. **资源使用**：避免在同一时间点调度过多任务，以免造成系统资源竞争

6. **任务独立性**：保持任务的独立性，避免任务之间的强耦合

7. **优先使用app.state.scheduler**：在扩展和路由中，优先使用`app.state.scheduler`而不是直接导入内部模块

## 常见问题

### 任务不执行

检查以下可能的原因：
- 调度器是否已启动
- 任务是否被暂停
- cron表达式是否正确
- 任务函数是否有未捕获的异常

### 任务执行时间不准确

APScheduler的任务执行可能存在轻微的延迟，特别是在系统负载较高时。如果需要精确的定时执行，可以考虑使用更专业的任务调度系统。

### 内存泄漏

长时间运行的定时任务可能导致内存泄漏。确保任务函数不会持有大量资源，并在完成后正确释放资源。

### 应用重启后任务丢失

默认情况下，APScheduler任务存储在内存中，应用重启后会丢失。如果需要持久化任务，可以考虑使用APScheduler的JobStore功能将任务保存到数据库中。

---

更多信息，请参考[APScheduler官方文档](https://apscheduler.readthedocs.io/)和[系统开发文档](./index.md)。 