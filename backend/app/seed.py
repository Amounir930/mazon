"""
Database Seed Script
Creates a demo user for testing
Run with: python -m app.seed
"""
from sqlalchemy.orm import Session
from loguru import logger

from app.database import SessionLocal, init_db
from app.models.seller import Seller
from app.api.auth.service import get_password_hash


def seed_demo_user(db: Session):
    """Create a demo user if it doesn't exist"""
    email = "demo@example.com"
    
    existing = db.query(Seller).filter(Seller.email == email).first()
    if existing:
        logger.info(f"Demo user already exists: {email}")
        return existing

    user = Seller(
        email=email,
        hashed_password=get_password_hash("demo123"),
        name="Demo Seller",
        seller_id="DEMO-SELLER-001",
        marketplace_id="ARBP9OOSHTCHU",
        region="EU",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Demo user created: {email}")
    return user


def main():
    """Main seed function"""
    logger.info("Starting database seed...")
    init_db()
    
    db = SessionLocal()
    try:
        seed_demo_user(db)
        logger.info("Database seeded successfully")
    finally:
        db.close()


if __name__ == "__main__":
    main()
