"""
Activity Log Model
Tracks all operations on products and listings
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class ActivityLog(Base):
    """Activity log model for tracking product/listing operations"""

    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    listing_id = Column(String(36), ForeignKey("listings.id"), nullable=True, index=True)

    # Action details
    action = Column(String(50), nullable=False)  # created, updated, submitted, published, failed, synced
    status = Column(String(20), nullable=False)  # success, failed
    details = Column(Text)  # JSON string with additional details

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", backref="activity_logs")
    listing = relationship("Listing", backref="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.action} - {self.status}>"
