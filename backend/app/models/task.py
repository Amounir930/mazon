"""
Task Model
Tracks async Celery tasks
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Task(Base):
    """Task tracking model for async operations"""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    celery_task_id = Column(String(255), index=True)  # Celery task ID
    
    # Task Information
    task_type = Column(String(50), nullable=False)  # listing_upload, feed_status_check, inventory_sync
    status = Column(String(20), default="pending")  # pending, running, success, failed, retry
    
    # Data
    payload = Column(JSON)  # Task input data
    result = Column(JSON)  # Task output data
    
    # Retry Logic
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Task {self.task_type} - {self.status}>"
