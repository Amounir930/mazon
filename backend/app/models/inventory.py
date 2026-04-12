"""
Inventory Model
Represents Amazon inventory/stock levels
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Inventory(Base):
    """Amazon inventory/stock levels model"""

    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String(36), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)

    # Product Identifiers
    sku = Column(String(100), nullable=False, index=True)
    asin = Column(String(20), index=True)
    product_name = Column(String(500))

    # Stock Levels
    available = Column(Integer, default=0)  # Available quantity
    reserved = Column(Integer, default=0)  # Reserved (pending orders)
    inbound = Column(Integer, default=0)  # Inbound shipments
    unfulfillable = Column(Integer, default=0)  # Damaged/defective

    # Fulfillment Type
    fulfillment_channel = Column(String(20), default="MFN")  # MFN, AFN
    fba = Column(Boolean, default=False)  # Fulfilled by Amazon
    fbm = Column(Boolean, default=True)  # Fulfilled by Merchant

    # Pricing (from inventory)
    price = Column(Numeric(10, 2), default=0)
    currency = Column(String(10), default="EGP")

    # Status
    status = Column(String(30), default="Active")  # Active, Inactive, Closed

    # Additional Data
    raw_data = Column(JSON)  # Full inventory data from Amazon (for reference)

    # Sync Metadata
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(20), default="cookie")  # cookie, sp_api, manual

    # Relationships
    seller = relationship("Seller", back_populates="inventories")
    product = relationship("Product", back_populates="inventory_records")

    def __repr__(self):
        return f"<Inventory {self.sku}: {self.available} available>"
