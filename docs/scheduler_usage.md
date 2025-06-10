# 定时任务管理模块使用说明

本文档提供了定时任务管理模块的使用说明，帮助用户了解如何使用定时任务功能来自动执行重复性任务。

## 功能概述

定时任务管理模块基于APScheduler实现，提供了以下功能：

- 支持三种类型的定时任务：Cron定时任务、间隔任务和一次性任务
- 通过Web界面管理任务（添加、暂停、恢复、删除）
- 查看任务详情和执行记录
- 立即执行指定任务
- 通过API接口进行编程控制

## 使用方法

### 通过Web界面管理

1. 在导航栏点击"定时任务"进入定时任务管理页面
2. 任务列表页面展示了所有已添加的任务，可以按类型进行筛选
3. 点击"添加任务"按钮可以创建新的定时任务
4. 点击任务ID可以查看任务详情
5. 在任务列表和详情页面可以执行以下操作：
   - 查看：查看任务详情
   - 运行：立即执行任务
   - 暂停/恢复：暂停或恢复任务的执行
   - 删除：永久删除任务

### 添加新任务

添加任务时，需要根据不同类型的任务填写相应信息：

#### Cron定时任务

Cron定时任务基于cron表达式指定执行时间，适合需要在特定时间点执行的任务。

必填信息：
- 任务函数：选择要执行的函数
- Cron表达式：指定执行时间（分、时、日、月、周）

示例：
- `* * * * *`：每分钟执行
- `0 * * * *`：每小时整点执行
- `0 9 * * 1-5`：工作日早上9点执行
- `0 0 1 * *`：每月1日零点执行

#### 间隔任务

间隔任务按指定的时间间隔重复执行，适合需要定期执行的任务。

必填信息：
- 任务函数：选择要执行的函数
- 时间间隔：指定执行间隔（秒、分钟、小时、天）

示例：
- 5分钟：每5分钟执行一次
- 1小时：每小时执行一次
- 1天：每天执行一次

#### 一次性任务

一次性任务只在指定的时间执行一次，执行完成后自动移除。

必填信息：
- 任务函数：选择要执行的函数
- 执行时间：指定任务执行的具体日期和时间

### 通过代码管理

除了使用Web界面，您还可以通过代码直接操作定时任务。系统提供了`app.state.scheduler`对象，可以在应用代码中直接调用。

```python
# 添加Cron定时任务
job = await app.state.scheduler.add_cron_job(
    func="tasks.example.send_notification",
    cron_expression="0 9 * * 1-5",  # 工作日上午9点
    job_id="daily_notification"
)

# 添加间隔任务
job = await app.state.scheduler.add_interval_job(
    func="tasks.example.sync_data",
    minutes=30,  # 每30分钟
    job_id="sync_data_job"
)

# 添加一次性任务
from datetime import datetime, timedelta
tomorrow = datetime.now() + timedelta(days=1)
job = await app.state.scheduler.add_date_job(
    func="tasks.example.generate_report",
    run_date=tomorrow,
    job_id="monthly_report"
)

# 暂停任务
await app.state.scheduler.pause_job("job_id")

# 恢复任务
await app.state.scheduler.resume_job("job_id")

# 立即执行任务
result = await app.state.scheduler.run_job("job_id")

# 删除任务
await app.state.scheduler.remove_job("job_id")

# 获取所有任务
jobs = await app.state.scheduler.get_jobs()

# 获取特定任务
job = await app.state.scheduler.get_job("job_id")
```

## 示例任务

系统提供了一些示例任务，可用于测试定时任务功能：

- `tasks.example.send_notification`：模拟发送通知
- `tasks.example.sync_data`：模拟数据同步
- `tasks.example.generate_report`：模拟生成报表
- `tasks.example.clean_old_data`：模拟清理旧数据
- `tasks.example.backup_database`：模拟数据库备份

您也可以根据实际需求创建自己的任务函数。

## 注意事项

1. 任务函数应该是可导入的模块路径，例如`tasks.example.send_notification`
2. Cron表达式使用标准格式：`秒 分 时 日 月 星期`
3. 一次性任务的执行时间必须在未来
4. 间隔任务必须至少指定一个时间单位（秒、分钟、小时或天）
5. 任务ID可以自动生成，也可以手动指定，但必须保证唯一性
6. 暂停的任务不会执行，但保留在系统中，可以随时恢复
7. 删除的任务将永久移除，无法恢复

## 故障排除

如果遇到定时任务相关问题，请检查：

1. 任务函数是否存在并且可以正常导入
2. Cron表达式或时间间隔是否设置正确
3. 任务是否处于暂停状态
4. 查看系统日志获取详细错误信息

## 高级用法

### 在插件中使用定时任务

插件可以通过以下方式添加定时任务：

```python
async def on_plugin_init(app):
    # 在插件初始化时添加定时任务
    scheduler = app.state.scheduler
    await scheduler.add_cron_job(
        func="your_plugin.tasks.your_task",
        cron_expression="0 * * * *",
        job_id="your_plugin_task"
    )
```

### 在任务函数中访问应用上下文

如果任务函数需要访问应用上下文，可以使用以下模式：

```python
async def your_task(app=None):
    """任务函数可以接收app参数"""
    if app:
        # 使用app访问应用上下文
        db = app.state.db
        # 其他操作...
```

定时任务管理模块会自动将应用实例传递给任务函数。 