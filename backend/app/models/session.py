"""
Session Model
Stores browser and SP-API authentication sessions
"""
from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Session(Base):
    """Authentication session for Amazon seller account"""

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Auth method
    auth_method = Column(String(20), nullable=False)  # 'browser' or 'sp_api'

    # Browser auth fields
    email = Column(String(255))
    country_code = Column(String(5), default="us")  # us, uk, ae, sa, eg
    cookies_json = Column(Text)  # Encrypted JSON of cookies
    seller_name = Column(String(255))
    csrf_token = Column(String(500))  # Amazon anti-csrf token for ABIS requests

    # SP-API auth fields
    lwa_client_id = Column(String(255))
    lwa_client_secret = Column(String(255))
    refresh_token = Column(Text)
    aws_access_key = Column(String(100))
    aws_secret_key = Column(String(100))
    marketplace_id = Column(String(20))

    # Session state
    is_active = Column(Boolean, default=True)
    is_valid = Column(Boolean, default=True)
    last_verified_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Session {self.id} - {self.auth_method} - {self.email or self.lwa_client_id}>"
