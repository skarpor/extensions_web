from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel
class Scheduler(BaseModel):
    __tablename__ = "scheduler_status"
    id = Column(String, primary_key=True)
    is_running = Column(Boolean, default=False)
    last_run_time = Column(String(200), nullable=True)
    next_run_time = Column(String(200), nullable=True)
    duration = Column(String(200), nullable=True)
    result = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    job_id = Column(String(200), nullable=True)
    job_name = Column(String(200), nullable=True)
    job_type = Column(String(200), nullable=True)
    job_trigger = Column(String(200), nullable=True)