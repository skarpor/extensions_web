# APS 调度器任务模型
from pydantic import BaseModel
from typing import Optional

class Job(BaseModel):
    job_id: str
    job_name: str
    job_description: str
    job_status: str
    job_schedule: str
    job_trigger: str
    job_params: dict
    job_result: dict
    job_history: dict
    job_logs: dict


