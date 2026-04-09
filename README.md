# Crazy Lister v2.0 - Amazon SP-API Auto-Listing System

> **Modern, scalable Amazon listing automation platform**  
> Migrated from legacy Tkinter monolith to FastAPI + Celery + PostgreSQL architecture

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Amazon SP-API](https://img.shields.io/badge/Amazon%20SP--API-FF9900?style=for-the-badge&logo=amazon)](https://developer.amazonservices.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-378141?style=for-the-badge&logo=celery)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [API Documentation](#api-documentation)
- [Migration from v1.0](#migration-from-v10)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Engineering Plans](#engineering-plans)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🎯 Overview

**Crazy Lister** is an automated Amazon product listing management system that helps sellers:

✅ **Create and manage** product catalogs efficiently  
✅ **Automate listing submissions** to Amazon via SP-API  
✅ **Queue and process** bulk uploads asynchronously  
✅ **Track submission statuses** in real-time  
✅ **Scale to thousands** of products and sellers  

### What Changed from v1.0?

| Aspect | v1.0 (Legacy) | v2.0 (Current) |
|--------|---------------|----------------|
| **Architecture** | Monolithic Tkinter app | FastAPI + Celery microservices |
| **Amazon Integration** | Legacy MWS (deprecated) | Official SP-API |
| **Data Storage** | JSON files | PostgreSQL database |
| **Task Processing** | Synchronous threads | Async Celery task queue |
| **Authentication** | Hardcoded credentials | OAuth2 + LWA secure flow |
| **Scalability** | Single-user | Multi-tenant, multi-marketplace |
| **Validation** | Manual Tkinter checks | Pydantic v2 models |
| **API** | None | RESTful API with OpenAPI docs |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Tkinter UI  │  │  Web Dashboard│  │  Third-party Apps│  │
│  │  (Legacy)    │  │  (Future)    │  │                  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼────────────────────┼────────────┘
          │                 │                    │
          └─────────────────┼────────────────────┘
                            │
                   HTTP/REST API
                            │
┌───────────────────────────┼────────────────────────────────┐
│                    API Layer                                │
│                   FastAPI Server                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /api/v1/sellers  /api/v1/products  /api/v1/listings │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────┘
                            │
                   Business Logic
                            │
┌───────────────────────────┼────────────────────────────────┐
│                  Service Layer                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │  Auth    │ │ Product  │ │ Listing  │ │ SP-API Client│  │
│  │ Service  │ │ Service  │ │ Service  │ │   Wrapper    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└───────────────────────────┬────────────────────────────────┘
                            │
                   Task Queue (Redis)
                            │
┌───────────────────────────┼────────────────────────────────┐
│                 Async Worker Layer                         │
│                    Celery Workers                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Listings   │  │    Feeds     │  │   Inventory     │  │
│  │   Queue      │  │   Queue      │  │    Queue        │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└───────────────────────────┬────────────────────────────────┘
                            │
                   Data Persistence
                            │
┌───────────────────────────┼────────────────────────────────┐
│                  Storage Layer                              │
│        ┌──────────────┐         ┌──────────────────┐       │
│        │  PostgreSQL  │         │  Redis Cache     │       │
│        │  (Primary)   │         │  (Broker/Cache)  │       │
│        └──────────────┘         └──────────────────┘       │
└────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Core Features
- **Product Catalog Management** - CRUD operations with validation
- **Automated Listing Submission** - Queue-based async processing
- **Amazon SP-API Integration** - Official API, fully compliant
- **Feed Processing** - Bulk operations via Amazon Feeds API
- **Real-time Status Tracking** - Monitor submission progress
- **Multi-Seller Support** - Isolated data per seller account

### Advanced Features
- **Pydantic Validation** - Type-safe data validation
- **Celery Task Queue** - Scalable async processing
- **Redis Caching** - Rate limiting and distributed locks
- **Structured Logging** - Loguru with rotation
- **API Documentation** - Auto-generated OpenAPI/Swagger
- **Docker Support** - One-command deployment

### Future Features (See expansion_plan.md)
- AI-powered listing optimization
- Multi-marketplace expansion (NA, EU, FE)
- Pricing intelligence
- Demand forecasting
- Web dashboard (React)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** installed
- **Docker & Docker Compose** (recommended) OR
- **PostgreSQL 15+** and **Redis 7+** (for manual setup)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
cd C:\Users\Dell\Desktop\learn\amazon

# Copy environment template
copy backend\.env.example backend\.env

# Edit .env file with your Amazon SP-API credentials
# SP_API_CLIENT_ID=your_client_id
# SP_API_CLIENT_SECRET=your_secret
# AWS_ACCESS_KEY_ID=your_aws_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret

# Start all services
cd backend
docker-compose up -d

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f api
```

**Access Points:**
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Flower (Celery Monitor):** http://localhost:5555

### Option 2: Manual Setup

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Start PostgreSQL and Redis
# (Ensure they're running on default ports)

# 3. Configure environment
copy .env.example .env
# Edit .env with your settings

# 4. Run database migrations (if using alembic)
alembic upgrade head

# 5. Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start Celery worker (in separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# 7. Start Flower monitoring (optional)
celery -A app.tasks.celery_app flower --port=5555
```

---

## 💻 Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Install dev tools
pip install pytest pytest-asyncio pytest-cov black isort mypy
```

### 2. Database Setup

```bash
# Using SQLite (easiest for development)
# Already configured in .env.example:
DATABASE_URL=sqlite:///./crazy_lister.db

# Using PostgreSQL (recommended for production)
# Create database
createdb -U postgres crazy_lister

# Update .env:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/crazy_lister
```

### 3. Run Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=app --cov-report=html

# View coverage report
# Open backend/htmlcov/index.html in browser
```

### 4. Code Formatting

```bash
# Format code
black backend/

# Sort imports
isort backend/

# Type checking
mypy backend/app/
```

---

## 📚 API Documentation

Once the server is running, access:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Quick API Examples

#### 1. Register a Seller

```bash
curl -X POST "http://localhost:8000/api/v1/sellers/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seller@example.com",
    "seller_id": "YOUR_AMAZON_SELLER_ID",
    "marketplace_id": "ARBP9OOSHTCHU",
    "region": "EU",
    "lwa_refresh_token": "YOUR_LWA_REFRESH_TOKEN"
  }'
```

#### 2. Create a Product

```bash
curl -X POST "http://localhost:8000/api/v1/products/?seller_id=YOUR_SELLER_UUID" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST-001",
    "name": "Test Product",
    "brand": "Test Brand",
    "category": "Electronics",
    "price": 99.99,
    "quantity": 100,
    "upc": "123456789012",
    "parent_sku": null,
    "variation_theme": "Color"
  }'
```

#### 3. Submit a Listing

```bash
curl -X POST "http://localhost:8000/api/v1/listings/submit/" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_UUID",
    "seller_id": "SELLER_UUID"
  }'
```

#### 4. Check Health

```bash
curl "http://localhost:8000/health"
```

---

## 🔄 Migration from v1.0

### Automated Migration

The legacy Tkinter client includes a migration helper:

```python
from legacy_client.amazon_bot_client import AmazonBotAPIClient

# Initialize API client
client = AmazonBotAPIClient("http://localhost:8000")

# Migrate from old JSON file
migrated = client.migrate_from_json("amazon_inventory.json")
print(f"Migrated {migrated} products")
```

### Manual Migration Steps

1. **Backup your data**
   ```bash
   copy amazon_inventory.json amazon_inventory.json.backup
   copy amazon_bot_settings.json amazon_bot_settings.json.backup
   ```

2. **Start the new backend**
   ```bash
   cd backend
   docker-compose up -d
   ```

3. **Register your seller account** via API or Swagger UI

4. **Migrate products** using the migration helper script

5. **Verify migration**
   ```bash
   curl "http://localhost:8000/api/v1/products/?seller_id=YOUR_ID"
   ```

6. **Keep legacy client** as fallback during transition

---

## 📁 Project Structure

```
amazon/
├── Crazy Lister.py              # Legacy Tkinter application (v1.0)
├── construction_plan.md         # Engineering build plan (Phase RED-GOLD)
├── expansion_plan.md            # Scalability roadmap
├── README.md                    # This file
│
├── backend/                     # FastAPI backend (v2.0)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Settings & environment vars
│   │   ├── database.py          # SQLAlchemy setup & sessions
│   │   │
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── seller.py        # Seller account model
│   │   │   ├── product.py       # Product catalog model
│   │   │   ├── listing.py       # Listing submission model
│   │   │   └── task.py          # Async task tracking model
│   │   │
│   │   ├── schemas/             # Pydantic v2 validation models
│   │   │   └── product.py       # All request/response schemas
│   │   │
│   │   ├── api/                 # REST API routes
│   │   │   ├── router.py        # Master router
│   │   │   ├── sellers.py       # Seller endpoints
│   │   │   ├── products.py      # Product endpoints
│   │   │   ├── listings.py      # Listing endpoints
│   │   │   └── feeds.py         # Feed endpoints
│   │   │
│   │   ├── services/            # Business logic layer
│   │   │   ├── auth.py          # LWA OAuth2 service
│   │   │   ├── product_service.py
│   │   │   ├── listing_service.py
│   │   │   ├── feed_service.py
│   │   │   └── sp_api.py        # Amazon SP-API wrapper
│   │   │
│   │   ├── tasks/               # Celery async tasks
│   │   │   ├── celery_app.py    # Celery configuration
│   │   │   └── listing_tasks.py # Listing submission tasks
│   │   │
│   │   └── utils/               # Utilities & helpers
│   │
│   ├── tests/                   # Pytest test suite
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Docker image definition
│   ├── docker-compose.yml       # Multi-service orchestration
│   └── .env.example             # Environment template
│
└── legacy_client/               # Migrated Tkinter client (temporary)
    └── amazon_bot_client.py     # API wrapper for legacy UI
```

---

## ⚙️ Configuration

All configuration is managed via environment variables. See `.env.example` for all options.

### Key Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | SQLite file |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 |
| `CELERY_BROKER_URL` | Celery message broker | redis://localhost:6379/1 |
| `SP_API_CLIENT_ID` | Amazon LWA Client ID | Required |
| `SP_API_CLIENT_SECRET` | Amazon LWA Client Secret | Required |
| `AWS_ACCESS_KEY_ID` | AWS IAM Access Key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM Secret Key | Required |
| `DEFAULT_MARKETPLACE_ID` | Amazon Marketplace ID | ARBP9OOSHTCHU |
| `DEBUG` | Enable debug mode | true |
| `SECRET_KEY` | App secret key | Change in production! |

---

## 🧪 Testing

### Run Test Suite

```bash
# All tests
pytest backend/tests/ -v

# Specific test file
pytest backend/tests/test_products.py -v

# With coverage
pytest backend/tests/ --cov=app --cov-report=term-missing

# Parallel execution
pytest backend/tests/ -n auto
```

### Write Tests

```python
# backend/tests/test_products.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_product():
    response = client.post(
        "/api/v1/products/",
        json={
            "sku": "TEST-001",
            "name": "Test Product",
            "price": 99.99,
            "quantity": 10,
        },
        params={"seller_id": "test-seller-uuid"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "TEST-001"
    assert data["name"] == "Test Product"
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=false`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Use AWS Secrets Manager for credentials
- [ ] Configure log rotation and retention
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategies
- [ ] Test disaster recovery

### Deploy to Production

```bash
# 1. Update .env with production values
# 2. Build and deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Verify deployment
docker-compose ps
curl https://your-domain.com/health

# 4. Check logs
docker-compose logs -f api
docker-compose logs -f celery_worker
```

### Kubernetes Deployment

For Kubernetes deployment, see the HPA configuration in `expansion_plan.md`.

---

## 📊 Monitoring

### Flower - Celery Dashboard

Access at http://localhost:5555

- View active tasks
- Monitor queue depths
- Inspect task results
- Retry failed tasks

### Logging

Logs are stored in `backend/logs/crazy_lister.log`

```bash
# View recent logs
tail -f backend/logs/crazy_lister.log

# Search for errors
grep "ERROR" backend/logs/crazy_lister.log
```

### Metrics to Monitor

- API response time (p95 < 200ms)
- Task success rate (> 98%)
- Queue depth (< 1000 pending tasks)
- Database connection pool usage
- Memory and CPU usage

---

## 📋 Engineering Plans

Detailed engineering documentation:

- **[Construction Plan](construction_plan.md)** - Phase-by-phase build plan (RED → BLUE → GREEN → GOLD)
- **[Expansion Plan](expansion_plan.md)** - Scalability roadmap, AI integration, marketplace expansion

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Error

```
Error: could not connect to server: Connection refused
```

**Solution:** Ensure PostgreSQL is running:
```bash
# Check status
pg_isready

# Start service (Linux)
sudo systemctl start postgresql

# Or use Docker
docker-compose up -d db
```

#### 2. Celery Worker Not Connecting

```
Error: Unable to connect to broker
```

**Solution:** Check Redis is running:
```bash
redis-cli ping
# Should return: PONG

# If not running:
docker-compose up -d redis
```

#### 3. SP-API Authentication Error

```
SellingApiException: Access token expired
```

**Solution:** Refresh your LWA token:
```python
from app.services.auth import auth_service

# Refresh token
new_token = await auth_service.refresh_access_token(old_refresh_token)
```

#### 4. Port Already in Use

```
Error: [Errno 10048] error while attempting to bind on address
```

**Solution:** Change port in docker-compose.yml or stop conflicting service:
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

### Get Help

1. Check the [GitHub Issues](https://github.com/your-repo/crazy-lister/issues)
2. Review API docs at http://localhost:8000/docs
3. Check logs: `docker-compose logs -f`
4. Verify environment variables are set correctly

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 style guide
- Use type hints everywhere
- Write tests for new features
- Update documentation
- Use meaningful commit messages

---

## 📄 License

This project is for educational purposes.

---

## 📞 Support

- **Documentation:** See `/docs` folder
- **Issues:** Open a GitHub issue
- **Email:** your-email@example.com

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [python-amazon-sp-api](https://github.com/saleweaver/python-amazon-sp-api) - SP-API wrapper
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Amazon Selling Partner API](https://developer.amazonservices.com/) - Official Amazon API

---

**Built with ❤️ for Amazon sellers worldwide**

*Version: 2.0.0*  
*Last Updated: April 9, 2026*
