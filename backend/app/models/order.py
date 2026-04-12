"""
Order Model
Represents an Amazon order
"""
from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Order(Base):
    """Amazon order model"""

    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String(36), ForeignKey("sellers.id"), nullable=True, index=True)

    # Order Information
    amazon_order_id = Column(String(50), nullable=False, index=True, unique=True)  # 123-4567890-1234567
    merchant_order_id = Column(String(50))  # Seller's order ID
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # DB timestamp
    purchase_date = Column(DateTime(timezone=True))  # Order date from Amazon
    last_update_date = Column(DateTime(timezone=True))

    # Order Status
    order_status = Column(String(30), default="Pending")  # Pending, Unshipped, Shipped, Delivered, Canceled
    fulfillment_channel = Column(String(20), default="MFN")  # MFN (Merchant), AFN (Amazon)
    sales_channel = Column(String(50))  # Amazon.com, Amazon.co.uk, etc.

    # Buyer Information
    buyer_name = Column(String(200))
    buyer_email = Column(String(200))
    buyer_phone = Column(String(50))

    # Shipping Address (JSON)
    ship_address = Column(JSON)  # {name, line1, line2, city, state, postal_code, country}
    ship_city = Column(String(100))
    ship_state = Column(String(100))
    ship_postal_code = Column(String(20))
    ship_country = Column(String(10))

    # Pricing
    total = Column(Numeric(10, 2), default=0)
    item_total = Column(Numeric(10, 2), default=0)
    shipping_total = Column(Numeric(10, 2), default=0)
    tax_total = Column(Numeric(10, 2), default=0)
    currency = Column(String(10), default="EGP")

    # Items (JSON)
    items = Column(JSON)  # [{sku, name, quantity, price, ...}]

    # Additional Data
    raw_data = Column(JSON)  # Full order data from Amazon (for reference)

    # Sync Metadata
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(20), default="cookie")  # cookie, sp_api, manual

    # Relationships
    seller = relationship("Seller", back_populates="orders")

    def __repr__(self):
        return f"<Order {self.amazon_order_id} - {self.order_status}>"
