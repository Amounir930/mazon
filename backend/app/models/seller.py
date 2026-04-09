"""
Seller Account Model
Represents an Amazon seller account with authentication credentials
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Seller(Base):
    """Seller account model for Amazon sellers"""
    
    __tablename__ = "sellers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    seller_id = Column(String(100), unique=True, nullable=False, index=True)  # Amazon Merchant ID
    marketplace_id = Column(String(20), nullable=False)  # e.g., A2NODRKZP88ZB9
    region = Column(String(10), nullable=False)  # EU, NA, FE
    
    # Authentication
    lwa_refresh_token = Column(String, nullable=False)  # Login with Amazon refresh token
    mws_auth_token = Column(String)  # Legacy MWS token (deprecated)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Seller {self.email} ({self.seller_id})>"
