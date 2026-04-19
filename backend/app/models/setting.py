from sqlalchemy import Column, String, Integer
from app.database import Base

class Setting(Base):
    """Global application settings and counters"""
    __tablename__ = "settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(200))
    description = Column(String(200))
