"""
Listing Model
Represents a product listing submission to Amazon
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Listing(Base):
    """Listing submission model for tracking Amazon listing uploads"""
    
    __tablename__ = "listings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Amazon Integration
    feed_submission_id = Column(String(100))  # Amazon Feed ID
    status = Column(String(30), default="queued")  # queued, processing, submitted, success, failed
    
    # Results
    amazon_asin = Column(String(20))  # Amazon Standard Identification Number
    amazon_url = Column(String(500))  # Product URL on Amazon
    error_message = Column(Text)  # Error details if failed
    
    # Queue Management
    queue_position = Column(Integer)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="listings")
    seller = relationship("Seller", backref="listings")
    
    def __repr__(self):
        return f"<Listing {self.id} - {self.status}>"
