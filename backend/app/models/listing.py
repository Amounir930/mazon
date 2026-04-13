"""
Listing Model
Represents a product listing submission to Amazon
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Listing(Base):
    """Listing submission model for tracking Amazon listing uploads"""

    __tablename__ = "listings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(String(36), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Amazon Integration
    feed_submission_id = Column(String(100))
    status = Column(String(30), default="queued")  # queued, processing, submitted, success, failed
    stage = Column(String(20), default="queued")  # queued, validating, processing, submitted, success, failed

    # Results
    amazon_asin = Column(String(20))  # Amazon Standard Identification Number
    amazon_url = Column(String(500))  # Product URL on Amazon
    error_message = Column(Text)  # Error details if failed

    # Queue Management
    queue_position = Column(Integer)

    # SP-API Integration Fields
    sp_api_submission_id = Column(String(100), nullable=True)  # Amazon submission ID
    sp_api_status = Column(String(30), nullable=True)  # ACCEPTED / INVALID / ACTIVE
    sp_api_last_polled_at = Column(DateTime(timezone=True), nullable=True)  # Last polling timestamp
    amazon_asin = Column(String(20))  # Amazon Standard Identification Number

    # Timestamps
    submitted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Retry tracking
    retry_count = Column(Integer, default=0)

    # Relationships
    product = relationship("Product", back_populates="listings")
    seller = relationship("Seller", back_populates="listings")

    def __repr__(self):
        return f"<Listing {self.id} - {self.status}>"
