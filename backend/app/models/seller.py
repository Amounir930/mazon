"""
Seller Account Model - Single Client
Stores Amazon SP-API credentials
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Seller(Base):
    """Single seller account with Amazon credentials"""

    __tablename__ = "sellers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Amazon SP-API Credentials (المفاتيح الأربعة)
    lwa_client_id = Column(String(255), nullable=False)        # Client ID
    lwa_client_secret = Column(String(255), nullable=False)    # Client Secret
    lwa_refresh_token = Column(Text, nullable=False)           # Refresh Token
    amazon_seller_id = Column(String(100), nullable=False)     # Seller ID

    # Optional Info
    display_name = Column(String(200), default="My Amazon Store")
    marketplace_id = Column(String(20), default="ARBP9OOSHTCHU")
    region = Column(String(10), default="EU")

    # Connection Status
    is_connected = Column(Boolean, default=False)
    last_sync_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="seller")
    listings = relationship("Listing", back_populates="seller")
    orders = relationship("Order", back_populates="seller")
    inventories = relationship("Inventory", back_populates="seller")

    def __repr__(self):
        return f"<Seller {self.display_name} ({self.amazon_seller_id})>"
