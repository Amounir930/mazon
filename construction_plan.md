# Engineering Build Plan: Amazon SP-API Auto-Listing System

**Project Code Name:** `Crazy Lister v2.0`  
**Architect:** Senior Backend Architect & Full-Stack Engineer  
**Date:** April 9, 2026  
**Status:** 🔴 PHASE RED INITIATED

---

## Table of Contents
- [Executive Summary](#executive-summary)
- [Phase RED: Infrastructure](#phase-red-infrastructure)
- [Phase BLUE: Authentication](#phase-blue-authentication)
- [Phase GREEN: Core Engine](#phase-green-core-engine)
- [Phase GOLD: Deployment](#phase-gold-deployment)
- [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

### Current State Analysis
The existing `Crazy Lister.py` is a **monolithic Tkinter desktop application** with the following critical issues:

| Category | Current State | Target State |
|----------|---------------|--------------|
| **Architecture** | Single monolithic class (`AmazonAutoListingBot`) | Client-Server (FastAPI + React/Frontend) |
| **Amazon Integration** | Legacy MWS (deprecated) + simulated uploads | Amazon SP-API (official, production-grade) |
| **Data Storage** | `amazon_inventory.json` (flat file) | PostgreSQL (production) / SQLite (dev) |
| **Task Processing** | Synchronous Tkinter threads | Celery/Redis async queue |
| **Authentication** | Hardcoded credentials, manual OTP | OAuth2 + LWA + secure OTP bridge |
| **Scalability** | Single-user, single-seller | Multi-tenant, multi-marketplace |
| **Validation** | Manual Tkinter form checks | Pydantic v2 models |
| **Logging** | `print()` statements | Structured logging (Loguru) |

### Migration Strategy
**Incremental migration** preserving backward compatibility where possible. The Tkinter UI will be temporarily retained as a legacy client while the new FastAPI backend is built.

---

## Phase RED: Infrastructure

**Objective:** Establish the foundational architecture, database schema, and FastAPI boilerplate with Dockerization.

### Duration: Week 1-2

### Deliverables

#### 1. Project Structure
```
crazy_lister_v2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry
│   │   ├── config.py                  # Settings & environment variables
│   │   ├── database.py                # SQLAlchemy engine & session
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── seller.py              # Seller account model
│   │   │   ├── product.py             # Product catalog model
│   │   │   ├── listing.py             # Listing queue model
│   │   │   └── task.py                # Async task tracking model
│   │   ├── schemas/                   # Pydantic v2 models
│   │   │   ├── __init__.py
│   │   │   ├── seller.py
│   │   │   ├── product.py
│   │   │   ├── listing.py
│   │   │   └── feed.py
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # Master router
│   │   │   ├── sellers.py
│   │   │   ├── products.py
│   │   │   ├── listings.py
│   │   │   └── feeds.py
│   │   ├── services/                  # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── sp_api.py              # SP-API wrapper
│   │   │   ├── auth.py                # LWA/OAuth2 service
│   │   │   ├── product_service.py     # Product CRUD logic
│   │   │   └── feed_service.py        # Feed submission logic
│   │   ├── tasks/                     # Celery tasks
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   └── listing_tasks.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── validators.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_products.py
│   │   ├── test_listings.py
│   │   └── test_auth.py
│   ├── alembic/                       # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/                          # (Future web dashboard)
├── legacy_client/                     # Migrated Tkinter client (temporary)
├── docs/
│   ├── api.md
│   └── setup.md
└── README.md
```

#### 2. Database Schema Design

**Seller Accounts Table (`sellers`)**
```sql
CREATE TABLE sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    seller_id VARCHAR(100) UNIQUE NOT NULL,  -- Amazon Merchant Identifier
    marketplace_id VARCHAR(20) NOT NULL,      -- e.g., ARBP9OOSHTCHU (Egypt)
    region VARCHAR(10) NOT NULL,              -- EU, NA, FE
    lwa_refresh_token TEXT NOT NULL,          -- Login with Amazon refresh token
    mws_auth_token TEXT,                      -- Legacy MWS token (deprecated)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Products Table (`products`)**
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID REFERENCES sellers(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    brand VARCHAR(200),
    upc VARCHAR(50),
    ean VARCHAR(50),
    description TEXT,
    bullet_points JSONB DEFAULT '[]',
    price DECIMAL(10, 2) NOT NULL,
    compare_price DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    quantity INTEGER DEFAULT 0,
    weight DECIMAL(8, 2),
    dimensions JSONB,  -- {"length": float, "width": float, "height": float, "unit": "cm"}
    images JSONB DEFAULT '[]',
    attributes JSONB DEFAULT '{}',  -- color, size, material, etc.
    keywords TEXT[],
    status VARCHAR(20) DEFAULT 'draft',  -- draft, queued, processing, published, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(seller_id, sku)
);
```

**Listing Queue Table (`listings`)**
```sql
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES sellers(id) ON DELETE CASCADE,
    feed_submission_id VARCHAR(100),  -- Amazon Feed ID
    status VARCHAR(30) DEFAULT 'queued',  -- queued, processing, submitted, success, failed
    amazon_asin VARCHAR(20),
    amazon_url VARCHAR(500),
    error_message TEXT,
    queue_position INTEGER,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Tasks Table (`tasks`)**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    celery_task_id VARCHAR(255),
    task_type VARCHAR(50),  -- listing_upload, feed_status_check, inventory_sync
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, success, failed, retry
    payload JSONB,
    result JSONB,
    retries INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. FastAPI Boilerplate

**`app/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.database import engine, Base

app = FastAPI(
    title="Crazy Lister API",
    description="Amazon SP-API Auto-Listing System",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
```

**`app/config.py`**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Crazy Lister API"
    DEBUG: bool = False
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str = "sqlite:///./crazy_lister.db"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Amazon SP-API
    SP_API_CLIENT_ID: str
    SP_API_CLIENT_SECRET: str
    SP_API_REDIRECT_URI: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "eu-west-1"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

#### 4. Docker Configuration

**`docker-compose.yml`**
```yaml
version: '3.9'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/crazy_lister
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/crazy_lister
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=crazy_lister
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  flower:
    build: ./backend
    command: celery -A app.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1

volumes:
  postgres_data:
```

**`backend/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Phase BLUE: Authentication

**Objective:** Implement Amazon SP-API authentication flow, LWA OAuth2, and secure credential management.

### Duration: Week 2-3

### Deliverables

#### 1. Amazon SP-API App Registration

**Steps:**
1. Create Amazon Developer Account at [developer.amazonservices.com](https://developer.amazonservices.com)
2. Register a new SP-API application
3. Configure OAuth redirect URI (`http://localhost:8000/api/v1/auth/callback`)
4. Obtain LWA Client ID & Client Secret
5. Configure IAM roles and policies in AWS Console

#### 2. LWA OAuth2 Service

**`app/services/auth.py`**
```python
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.seller import Seller
from app.config import get_settings
from loguru import logger

class LWAAuthService:
    """Login with Amazon OAuth2 Service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.lwa_auth_url = "https://www.amazon.com/ap/oa"
        self.lwa_token_url = "https://api.amazon.com/auth/o2/token"
    
    def get_auth_url(self, seller_email: str) -> str:
        """Generate Amazon OAuth2 authorization URL"""
        params = {
            "client_id": self.settings.SP_API_CLIENT_ID,
            "scope": "sellingpartnerapi::migration",
            "response_type": "code",
            "redirect_uri": self.settings.SP_API_REDIRECT_URI,
            "state": seller_email
        }
        return f"{self.lwa_auth_url}?{requests.compat.urlencode(params)}"
    
    async def exchange_code_for_token(self, auth_code: str) -> dict:
        """Exchange authorization code for LWA access token"""
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": self.settings.SP_API_CLIENT_ID,
            "client_secret": self.settings.SP_API_CLIENT_SECRET,
            "redirect_uri": self.settings.SP_API_REDIRECT_URI
        }
        
        response = requests.post(self.lwa_token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh expired access token"""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.settings.SP_API_CLIENT_ID,
            "client_secret": self.settings.SP_API_CLIENT_SECRET
        }
        
        response = requests.post(self.lwa_token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    async def register_seller(self, db: Session, seller_email: str, auth_code: str) -> Seller:
        """Complete seller registration with Amazon"""
        # Exchange code for tokens
        token_data = await self.exchange_code_for_token(auth_code)
        
        # Check if seller exists
        seller = db.query(Seller).filter(Seller.email == seller_email).first()
        
        if seller:
            # Update tokens
            seller.lwa_refresh_token = token_data["refresh_token"]
            seller.updated_at = datetime.utcnow()
        else:
            # Create new seller
            seller = Seller(
                email=seller_email,
                lwa_refresh_token=token_data["refresh_token"],
                marketplace_id="A2NODRKZP88ZB9",
                region="EU"
            )
            db.add(seller)
        
        db.commit()
        db.refresh(seller)
        
        logger.info(f"Seller registered: {seller_email}")
        return seller

auth_service = LWAAuthService()
```

#### 3. OTP & Session Bridge

For manual OTP handling (when Seller Central requires 2FA):

**Approach:** Create a secure OTP input endpoint that accepts OTP codes via API during the authentication flow. This is a temporary bridge until full SP-API migration is complete.

```python
# app/api/auth.py
@router.post("/otp/submit")
async def submit_otp(otp_code: str, session_id: str):
    """Submit OTP for pending authentication session"""
    # Store OTP in Redis with TTL for session matching
    await redis.set(f"otp:{session_id}", otp_code, ex=300)
    return {"status": "otp_submitted"}
```

#### 4. AWS IAM Policy Configuration

Create IAM role with minimal required permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "execute-api:Invoke"
            ],
            "Resource": [
                "arn:aws:execute-api:*:*:*"
            ]
        }
    ]
}
```

---

## Phase GREEN: Core Engine

**Objective:** Migrate listing logic to SP-API Feeds & Listings Items API. Implement product management, queue processing, and Amazon integration.

### Duration: Week 3-5

### Deliverables

#### 1. SP-API Wrapper Service

**`app/services/sp_api.py`**
```python
from sp_api.api import ListingsItems, Feeds, CatalogItems, Orders
from sp_api.base import SellingApiException, Marketplaces
from sp_api.base.credentials import Credentials
from loguru import logger

class SPAPIClient:
    """Amazon Selling Partner API Client Wrapper"""
    
    def __init__(self, seller_id: str, access_token: str):
        self.credentials = Credentials(
            lwa_app_id=settings.SP_API_CLIENT_ID,
            lwa_client_secret=settings.SP_API_CLIENT_SECRET,
            aws_access_key=settings.AWS_ACCESS_KEY_ID,
            aws_secret_key=settings.AWS_SECRET_ACCESS_KEY,
            role_arn=settings.AWS_SELLER_ROLE_ARN
        )
        self.seller_id = seller_id
        self.access_token = access_token
    
    def create_or_update_listing(self, sku: str, product_data: dict, marketplace_id: str) -> dict:
        """Create or update a product listing"""
        try:
            listings_api = ListingsItems(credentials=self.credentials)
            
            response = listings_api.put_listings_item(
                sellerId=self.seller_id,
                sku=sku,
                marketplaceId=marketplace_id,
                body={
                    "productType": "PRODUCT",
                    "attributes": product_data,
                    "requirements": "LISTING",
                    "attributes": {
                        "item_name": [{"value": product_data["name"], "language_tag": "en_US"}],
                        "brand": [{"value": product_data["brand"], "language_tag": "en_US"}],
                        "product_description": [{"value": product_data["description"], "language_tag": "en_US"}],
                    }
                }
            )
            
            logger.info(f"Listing created/updated: {sku}")
            return response
            
        except SellingApiException as e:
            logger.error(f"SP-API error for SKU {sku}: {str(e)}")
            raise
    
    def submit_feed(self, feed_type: str, feed_data: bytes, marketplace_ids: list) -> str:
        """Submit a feed to Amazon (for bulk operations)"""
        try:
            feeds_api = Feeds(credentials=self.credentials)
            
            # Create feed document
            doc_response = feeds_api.create_feed_document(
                contentType="text/xml; charset=UTF-8"
            )
            
            # Upload feed content
            feeds_api.upload_feed_document(
                document_id=doc_response.payload['documentId'],
                content=feed_data
            )
            
            # Create feed
            feed_response = feeds_api.create_feed(
                feedType=feed_type,
                marketplaceIds=marketplace_ids,
                inputFeedDocumentId=doc_response.payload['documentId']
            )
            
            feed_id = feed_response.payload['feedId']
            logger.info(f"Feed submitted: {feed_id}")
            return feed_id
            
        except SellingApiException as e:
            logger.error(f"Feed submission error: {str(e)}")
            raise
    
    def get_feed_status(self, feed_id: str) -> dict:
        """Check feed processing status"""
        try:
            feeds_api = Feeds(credentials=self.credentials)
            response = feeds_api.get_feed(feed_id)
            return response.payload
        except SellingApiException as e:
            logger.error(f"Feed status check error: {str(e)}")
            raise
    
    def get_inventory_summary(self, sku: str) -> dict:
        """Get inventory summary for a SKU"""
        try:
            listings_api = ListingsItems(credentials=self.credentials)
            response = listings_api.get_listings_item(
                sellerId=self.seller_id,
                sku=sku,
                marketplaceId="A2NODRKZP88ZB9"
            )
            return response.payload
        except SellingApiException as e:
            logger.error(f"Inventory check error: {str(e)}")
            raise
```

#### 2. Product Service

**`app/services/product_service.py`**
```python
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from loguru import logger

class ProductService:
    """Product CRUD operations"""
    
    @staticmethod
    def create_product(db: Session, seller_id: str, product_data: ProductCreate) -> Product:
        """Create a new product"""
        product = Product(
            seller_id=seller_id,
            **product_data.model_dump()
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        logger.info(f"Product created: {product.sku}")
        return product
    
    @staticmethod
    def get_product(db: Session, product_id: str) -> Product | None:
        """Get product by ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def get_products_by_seller(db: Session, seller_id: str, skip: int = 0, limit: int = 50) -> list[Product]:
        """Get all products for a seller"""
        return db.query(Product).filter(
            Product.seller_id == seller_id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_product(db: Session, product_id: str, update_data: ProductUpdate) -> Product:
        """Update product"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product not found: {product_id}")
        
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(product, key, value)
        
        db.commit()
        db.refresh(product)
        logger.info(f"Product updated: {product.sku}")
        return product
    
    @staticmethod
    def delete_product(db: Session, product_id: str) -> bool:
        """Delete product"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        
        db.delete(product)
        db.commit()
        logger.info(f"Product deleted: {product_id}")
        return True
```

#### 3. Feed Service

**`app/services/feed_service.py`**
```python
from app.services.sp_api import SPAPIClient
from app.models.listing import Listing
from app.models.seller import Seller
from sqlalchemy.orm import Session
from loguru import logger
import xml.etree.ElementTree as ET

class FeedService:
    """Handle Amazon feed generation and submission"""
    
    @staticmethod
    def generate_product_xml(product: dict, seller_id: str) -> bytes:
        """Generate Amazon MWS/SP-API compliant XML"""
        envelope = ET.Element("AmazonEnvelope", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "amzn-envelope.xsd"
        })
        
        # Header
        header = ET.SubElement(envelope, "Header")
        ET.SubElement(header, "DocumentVersion").text = "1.01"
        ET.SubElement(header, "MerchantIdentifier").text = seller_id
        
        ET.SubElement(envelope, "MessageType").text = "Product"
        ET.SubElement(envelope, "PurgeAndReplace").text = "false"
        
        # Message
        message = ET.SubElement(envelope, "Message")
        ET.SubElement(message, "MessageID").text = "1"
        ET.SubElement(message, "OperationType").text = "Update"
        
        product_elem = ET.SubElement(message, "Product")
        ET.SubElement(product_elem, "SKU").text = product["sku"]
        
        standard_id = ET.SubElement(product_elem, "StandardProductID")
        ET.SubElement(standard_id, "Type").text = "UPC"
        ET.SubElement(standard_id, "Value").text = product["upc"]
        
        desc_data = ET.SubElement(product_elem, "DescriptionData")
        ET.SubElement(desc_data, "Title").text = product["name"]
        ET.SubElement(desc_data, "Brand").text = product["brand"]
        ET.SubElement(desc_data, "Description").text = product["description"]
        
        for bullet in product.get("bullet_points", []):
            ET.SubElement(desc_data, "BulletPoint").text = bullet
        
        # Pricing
        pricing_data = ET.SubElement(product_elem, "PricingData")
        standard_price = ET.SubElement(pricing_data, "StandardPrice")
        standard_price.set("currency", "EGP")
        standard_price.text = str(product["price"])
        
        ET.SubElement(product_elem, "Quantity").text = str(product["quantity"])
        
        xml_string = ET.tostring(envelope, encoding="UTF-8", xml_declaration=True)
        return xml_string
    
    @staticmethod
    async def submit_listing_to_amazon(db: Session, listing: Listing, seller: Seller) -> bool:
        """Submit a single listing to Amazon via SP-API"""
        try:
            # Get product data
            product = listing.product
            
            # Generate XML
            xml_data = FeedService.generate_product_xml(product.__dict__, seller.seller_id)
            
            # Initialize SP-API client
            sp_client = SPAPIClient(
                seller_id=seller.seller_id,
                access_token=seller.lwa_refresh_token  # In production, use short-lived token
            )
            
            # Submit feed
            feed_id = sp_client.submit_feed(
                feed_type="_POST_PRODUCT_DATA_",
                feed_data=xml_data,
                marketplace_ids=[seller.marketplace_id]
            )
            
            # Update listing
            listing.feed_submission_id = feed_id
            listing.status = "submitted"
            
            db.commit()
            logger.info(f"Listing submitted to Amazon: {listing.id}, Feed: {feed_id}")
            return True
            
        except Exception as e:
            listing.status = "failed"
            listing.error_message = str(e)
            db.commit()
            logger.error(f"Listing submission failed: {listing.id}: {str(e)}")
            return False
```

#### 4. API Routes

**`app/api/products.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    seller_id: str,  # Extract from auth in production
    db: Session = Depends(get_db)
):
    """Create a new product"""
    return ProductService.create_product(db, seller_id, product_data)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get product by ID"""
    product = ProductService.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/", response_model=list[ProductResponse])
async def list_products(
    seller_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all products for a seller"""
    return ProductService.get_products_by_seller(db, seller_id, skip, limit)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update product"""
    return ProductService.update_product(db, product_id, update_data)

@router.delete("/{product_id}")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Delete product"""
    success = ProductService.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}
```

---

## Phase GOLD: Deployment

**Objective:** Deploy the system with monitoring, CI/CD pipeline, and optional web dashboard.

### Duration: Week 5-6

### Deliverables

#### 1. Legacy Tkinter Client Migration

The existing Tkinter UI will be converted to an API client:

**`legacy_client/amazon_bot_client.py`**
```python
import requests
from datetime import datetime

class AmazonBotAPIClient:
    """Thin wrapper to make Tkinter UI communicate with FastAPI backend"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
    
    def create_product(self, product_data: dict) -> dict:
        """Create product via API"""
        response = requests.post(
            f"{self.api_base_url}/api/v1/products/",
            json=product_data
        )
        response.raise_for_status()
        return response.json()
    
    def submit_listing(self, product_id: str, seller_id: str) -> dict:
        """Submit listing to queue"""
        response = requests.post(
            f"{self.api_base_url}/api/v1/listings/submit/",
            json={"product_id": product_id, "seller_id": seller_id}
        )
        response.raise_for_status()
        return response.json()
    
    def get_listings_queue(self, seller_id: str) -> list:
        """Get current listings queue"""
        response = requests.get(
            f"{self.api_base_url}/api/v1/listings/",
            params={"seller_id": seller_id}
        )
        response.raise_for_status()
        return response.json()
```

#### 2. Monitoring & Logging Setup

**`app/config.py` additions:**
```python
# Add to Settings class
LOG_FILE: str = "logs/crazy_lister.log"
LOG_ROTATION: str = "500 MB"
LOG_RETENTION: str = "30 days"
```

**Logging configuration:**
```python
from loguru import logger
import sys

def setup_logging():
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(
        settings.LOG_FILE,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level="DEBUG"
    )
```

#### 3. CI/CD Pipeline (GitHub Actions)

**`.github/workflows/deploy.yml`**
```yaml
name: Deploy Crazy Lister

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v
      
      - name: Build Docker images
        run: docker-compose build
      
      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: |
          docker-compose up -d
```

#### 4. API Documentation

The FastAPI auto-generated docs will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Risk Mitigation

| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| **Amazon API Rate Limits** | High | Implement retry logic with exponential backoff, queue throttling |
| **LWA Token Expiration** | High | Auto-refresh tokens before expiry, alert on refresh failure |
| **Data Loss During Migration** | Critical | Backup JSON files, validate all migrated products |
| **SP-API Credential Leakage** | Critical | Use AWS Secrets Manager, never hardcode credentials |
| **Amazon Policy Violation** | High | Follow Amazon listing guidelines, validate all submissions |
| **Database Corruption** | Medium | Regular backups, transaction logs, WAL mode |
| **Celery Task Failures** | Medium | Dead letter queue, retry policies, manual intervention alerts |

---

## Next Steps

1. ✅ **Complete Phase RED** (Infrastructure setup)
2. 🔄 **Begin Phase BLUE** (Authentication implementation)
3. ⏳ **Execute Phase GREEN** (Core engine development)
4. ⏳ **Finalize Phase GOLD** (Deployment & monitoring)

---

*Document Version: 1.0*  
*Last Updated: April 9, 2026*  
*Classification: Engineering Internal*
