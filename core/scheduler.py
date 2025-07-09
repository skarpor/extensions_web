"""
定时任务调度模块

提供定时任务的创建、管理和执行功能。
基于APScheduler库实现，支持多种调度器类型和任务触发方式。
"""
import datetime
import pickle
from typing import Dict, Any, List, Union, Callable

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job, ref_to_obj
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from .sandbox import load_module_in_sandbox
from .logger import get_logger

logger = get_logger("scheduler")


class CustomJob(Job):
    def __setstate__(self, state):
        if isinstance(state, bytes):
            try:
                state = pickle.loads(state)
            except pickle.UnpicklingError as e:
                raise LookupError(f"任务数据反序列化失败: {e}")

        if not isinstance(state, dict):
            raise LookupError(f"无效的任务状态类型: {type(state)}")

        # 先让父类处理基础字段
        self.id = state["id"]
        self.func_ref = state["func"]
        self.trigger = state["trigger"]
        self.executor = state["executor"]
        self.args = state["args"]
        self.kwargs = state["kwargs"]
        self.name = state["name"]
        self.misfire_grace_time = state["misfire_grace_time"]
        self.coalesce = state["coalesce"]
        self.max_instances = state["max_instances"]
        self.next_run_time = state["next_run_time"]
        # 2. 恢复内部属性（关键修复）
        self._jobstore_alias = getattr(self, '_jobstore_alias', 'default')
        self._scheduler = getattr(self, '_scheduler', None)
        self._jobstore = getattr(self, '_jobstore', None)

        # 自定义函数解析逻辑
        if "extension_" in self.func_ref:
            module_name, func_name = self.func_ref.split(":")
            module_path = f"{settings.EXTENSIONS_DIR}/{module_name}.py"

            try:
                module = load_module_in_sandbox(module_path)
                self.func = getattr(module, func_name)
            except Exception as e:
                raise LookupError(f"无法加载动态函数: {e}")
        else:
            # 默认处理
            self.func = ref_to_obj(self.func_ref)


class CustomSQLAlchemyJobStore(SQLAlchemyJobStore):
    def _reconstitute_job(self, job_state):
        try:
            job = CustomJob.__new__(CustomJob)

            # 注入当前scheduler引用
            job._scheduler = self._scheduler
            job._jobstore_alias = self._alias

            job.__setstate__(job_state)
            return job
        except Exception as e:
            raise LookupError("任务无效")  # 让 APScheduler 清理该任务


class SchedulerManager:
    """定时任务调度管理器"""
    
    def __init__(self, db_url: str = None, async_mode: bool = True):
        """
        初始化调度管理器
        
        Args:
            db_url: 数据库连接URL，用于持久化任务。默认使用SQLite。
            async_mode: 是否使用异步模式，默认为False。
        """
        self.scheduler = None
        self.db_url = db_url or "sqlite:///scheduler.sqlite"
        self.async_mode = async_mode
        self.is_running = False
        self.initialize()
        
    def initialize(self):
        """初始化调度器"""
        # 确保data目录存在
        # os.makedirs("data", exist_ok=True)
        # async_engine = create_async_engine(self.db_url)
        # job_store = SQLAlchemyJobStore()

        # 配置作业存储
        jobstores = {
            'default': CustomSQLAlchemyJobStore(url=self.db_url)
        }
        
        # 配置执行器
        executors = {
            'default': AsyncIOExecutor()  # 最佳选择
            # 'default': ThreadPoolExecutor(20),  # 默认线程池
            # 'processpool': ProcessPoolExecutor(5)  # 进程池
        }
        
        # 任务默认配置
        job_defaults = {
            'coalesce': False,  # 是否合并执行
            'max_instances': 3,  # 同一个任务的最大实例数
            'misfire_grace_time': 60  # 任务错过执行时间的容忍度（秒）
        }

        # 创建调度器
        if self.async_mode:
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone="Asia/Shanghai"
            )
        else:
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone="Asia/Shanghai"
            )
        
        # 添加任务执行监听器
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        logger.info("调度器初始化完成")
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("调度器已启动")
        else:
            logger.warning("调度器已经在运行中")
    
    def shutdown(self, wait: bool = True):
        """
        关闭调度器
        
        Args:
            wait: 是否等待所有正在执行的任务完成
        """
        if self.is_running:
            self.scheduler.shutdown(wait=wait)
            self.is_running = False
            logger.info("调度器已关闭")
        else:
            logger.warning("调度器尚未启动")
    
    def _job_listener(self, event):
        """
        任务执行监听器
        
        Args:
            event: 任务事件
        """
        if event.exception:
            logger.error(f"任务 {event.job_id} 执行失败: {str(event.exception)}")
            logger.error(f"异常跟踪: {event.traceback}")
        else:
            logger.info(f"任务 {event.job_id} 执行成功，返回值: {event.retval}")
    
    def add_job(self, 
                func: Callable, 
                trigger: str = None, 
                job_id: str = None, 
                **trigger_args) -> str:
        """
        添加定时任务
        
        Args:
            func: 要执行的函数
            trigger: 触发器类型，支持 'date', 'interval', 'cron'
            job_id: 任务ID，如果不提供则自动生成
            **trigger_args: 触发器参数
            
        Returns:
            任务ID
        """
        if not self.is_running:
            logger.warning("调度器尚未启动，自动启动中...")
            self.start()
        
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            **trigger_args
        )
        
        logger.info(f"已添加任务: {job.id}, 触发器: {trigger}, 下次运行时间: {job.next_run_time}")
        return job.id
    
    def add_cron_job(self, 
                     func: Callable, 
                     job_id: str = None, 
                     year: Union[int, str] = None,
                     month: Union[int, str] = None, 
                     day: Union[int, str] = None,
                     week: Union[int, str] = None,
                     day_of_week: Union[int, str] = None,
                     hour: Union[int, str] = None, 
                     minute: Union[int, str] = None,
                     second: Union[int, str] = None,
                     **kwargs) -> str:
        """
        添加Cron定时任务
        
        Args:
            func: 要执行的函数
            job_id: 任务ID，如果不提供则自动生成
            year: 年，例如 2023
            month: 月，1-12
            day: 日，1-31
            week: 周，1-53
            day_of_week: 星期几，0-6 或 mon,tue,wed,thu,fri,sat,sun
            hour: 小时，0-23
            minute: 分钟，0-59
            second: 秒，0-59
            **kwargs: 其他参数
            
        Returns:
            任务ID
        """
        trigger_args = {
            'year': year,
            'month': month,
            'day': day,
            'week': week,
            'day_of_week': day_of_week,
            'hour': hour,
            'minute': minute,
            'second': second
        }
        
        # 过滤掉None值
        trigger_args = {k: v for k, v in trigger_args.items() if v is not None}
        
        return self.add_job(
            func=func,
            trigger='cron',
            job_id=job_id,
            **trigger_args,
            **kwargs
        )
    
    def add_interval_job(self, 
                         func: Callable, 
                         job_id: str = None,
                         weeks: int = 0, 
                         days: int = 0, 
                         hours: int = 0,
                         minutes: int = 0, 
                         seconds: int = 0, 
                         start_date: datetime.datetime = None,
                         end_date: datetime.datetime = None,
                         **kwargs) -> str:
        """
        添加间隔定时任务
        
        Args:
            func: 要执行的函数
            job_id: 任务ID，如果不提供则自动生成
            weeks: 周数
            days: 天数
            hours: 小时数
            minutes: 分钟数
            seconds: 秒数
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
            
        Returns:
            任务ID
        """
        trigger_args = {
            'weeks': weeks,
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'start_date': start_date,
            'end_date': end_date
        }
        
        # 过滤掉None值和0值
        trigger_args = {k: v for k, v in trigger_args.items() 
                       if v is not None and (not isinstance(v, int) or v > 0)}
        
        if not any(k in trigger_args for k in ['weeks', 'days', 'hours', 'minutes', 'seconds']):
            raise ValueError("必须至少指定一个时间间隔参数")
        
        return self.add_job(
            func=func,
            trigger='interval',
            job_id=job_id,
            **trigger_args,
            **kwargs
        )
    
    def add_date_job(self, 
                     func: Callable, 
                     job_id: str = None,
                     run_date: Union[datetime.datetime, str] = None,
                     **kwargs) -> str:
        """
        添加一次性定时任务
        
        Args:
            func: 要执行的函数
            job_id: 任务ID，如果不提供则自动生成
            run_date: 运行日期时间
            **kwargs: 其他参数
            
        Returns:
            任务ID
        """
        if run_date is None:
            run_date = datetime.datetime.now() + datetime.timedelta(seconds=1)
        
        return self.add_job(
            func=func,
            trigger='date',
            job_id=job_id,
            run_date=run_date,
            **kwargs
        )
    
    def remove_job(self, job_id: str) -> bool:
        """
        移除定时任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功移除
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"已移除任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"移除任务 {job_id} 失败: {str(e)}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """
        暂停定时任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功暂停
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"已暂停任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"暂停任务 {job_id} 失败: {str(e)}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        恢复定时任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功恢复
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"已恢复任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"恢复任务 {job_id} 失败: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        获取任务信息
        
        Args:
            job_id: 任务ID
            
        Returns:
            任务信息字典，如果任务不存在则返回None
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None
            
            job_info = {
                'id': job.id,
                'name': job.name,
                'func': str(job.func),
                'trigger': str(job.trigger),
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'misfire_grace_time': job.misfire_grace_time,
                'max_instances': job.max_instances,
                'coalesce': job.coalesce
            }
            return job_info
        except Exception as e:
            logger.error(f"获取任务 {job_id} 信息失败: {str(e)}")
            return None
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        获取所有任务信息
        
        Returns:
            任务信息列表
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'func': str(job.func),
                'trigger': str(job.trigger),
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'misfire_grace_time': job.misfire_grace_time,
                'max_instances': job.max_instances,
                'coalesce': job.coalesce
            }
            jobs.append(job_info)
        return jobs
    
    def run_job(self, job_id: str) -> bool:
        """
        立即运行指定任务一次
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功触发
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.error(f"任务 {job_id} 不存在")
                return False
            
            self.scheduler.modify_job(job_id, next_run_time=datetime.datetime.now())
            logger.info(f"已触发任务立即运行: {job_id}")
            return True
        except Exception as e:
            logger.error(f"立即运行任务 {job_id} 失败: {str(e)}")
            return False

# 创建一个全局的调度器实例
scheduler_instance = None
def get_scheduler(db_url: str=None, async_mode: bool = True) -> SchedulerManager:
    """
    获取调度器实例（单例模式）
    
    Args:
        db_url: 数据库连接URL
        async_mode: 是否使用异步模式
        
    Returns:
        调度器管理器实例
    """
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = SchedulerManager(db_url, async_mode)
    return scheduler_instance

