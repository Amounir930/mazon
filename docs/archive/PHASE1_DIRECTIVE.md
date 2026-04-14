# 🎯 ENGINEERING DIRECTIVE — Phase 1: SP-API Backend Integration

> **من: القائد التقني**
> **إلى: مهندس الـ Backend**
> **الموضوع: تنفيذ المرحلة الأولى — دمج SP-API في النظام**
> **الأولوية: 🔴 عالية جداً**

---

## 📋 Executive Summary

لدينا `sp_api_client.py` أثبت نجاحه في إرسال منتج لـ Amazon عبر SP-API (Status: ACCEPTED, 0 errors).
**المطلوب الآن**: تحويل الـ test script إلى **API endpoints حقيقية** مربوطة بـ Database و Frontend.

---

## 🗺️ الخريطة الكاملة (A → Z)

```
┌─────────────────────────────────────────────────────────────┐
│              Phase 1: SP-API Backend Integration            │
│                                                              │
│  Step 1: إنشاء sp_api_router.py (endpoints جديدة)          │
│  Step 2: تحديث sp_api_client.py (دالة إنشاء من Product)    │
│  Step 3: ربط Product → SP-API في products.py               │
│  Step 4: تحديث Listing model (حقول جديدة)                  │
│  Step 5: Error handling بالعربي                             │
│  Step 6: router.py (تسجيل الـ router الجديد)                │
│                                                              │
│  Testing: curl + Postman → قبول من Amazon                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Step 1: إنشاء `backend/app/api/sp_api_router.py`

### الملف الجديد:

```python
"""
SP-API Router
Handles all Amazon SP-API operations through our backend
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger

from app.database import SessionLocal
from app.models.product import Product
from app.models.listing import Listing
from app.models.seller import Seller
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data
from app.services.sp_api_client import SPAPIClient
from datetime import datetime
import json

router = APIRouter()


class SubmitToListingsRequest(BaseModel):
    product_id: str


@router.post("/submit/{product_id}")
async def submit_product_to_amazon(product_id: str):
    """
    Submit a product from our database to Amazon via SP-API.
    
    Flow:
    1. Get product from DB
    2. Get active session (cookies + credentials)
    3. Build SP-API payload
    4. PUT /listings/2021-08-01/items/{sellerId}/{sku}
    5. Create listing record in DB
    6. Return result
    """
    db = SessionLocal()
    try:
        # 1. Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        logger.info(f"Submitting product to Amazon: {product.sku} — {product.name}")
        
        # 2. Validate product has required fields
        if not product.ean and not product.upc:
            raise HTTPException(
                status_code=400,
                detail="المنتج محتاج باركود (EAN أو UPC) عشان يترفع على أمازون"
            )
        
        if not product.price or product.price <= 0:
            raise HTTPException(
                status_code=400,
                detail="المنتج محتاج سعر أكبر من صفر"
            )
        
        if not product.quantity or product.quantity < 0:
            raise HTTPException(
                status_code=400,
                detail="المنتج محتاج كمية صحيحة"
            )
        
        # 3. Get active session
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
            AuthSession.is_valid == True,
        ).order_by(AuthSession.created_at.desc()).first()
        
        if not auth_session or not auth_session.credentials_json:
            raise HTTPException(
                status_code=400,
                detail="مفيش حساب Amazon متصل. روح لـ /settings وسجل دخول الأول"
            )
        
        # 4. Get Seller credentials
        seller = db.query(Seller).first()
        if not seller:
            raise HTTPException(
                status_code=400,
                detail="مفيش Seller ID محفوظ. أضف Seller ID من Settings"
            )
        
        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        seller_id = seller.seller_id  # A1DSHARRBRWYZW
        marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code or "eg"
        
        # 5. Create listing record (status: processing)
        listing = Listing(
            product_id=product.id,
            seller_id=product.seller_id,
            status="processing",
            stage="submitting",
            submitted_at=datetime.utcnow(),
            sp_api_submission_id=None,
        )
        db.add(listing)
        db.commit()
        
        # 6. Build product data for SP-API
        product_data = {
            "sku": product.sku,
            "name": product.name or product.name_en or "Unnamed Product",
            "description": product.description or product.name or "No description",
            "brand": product.brand or "Generic",
            "manufacturer": product.manufacturer or (product.brand or "Generic"),
            "model_number": product.model_number or product.sku,
            "ean": product.ean or "",
            "upc": product.upc or "",
            "price": float(product.price),
            "quantity": int(product.quantity),
            "condition": product.condition or "New",
            "fulfillment_channel": product.fulfillment_channel or "MFN",
            "country_of_origin": product.country_of_origin or "CN",
            "product_type": product.product_type or "HOME_ORGANIZERS_AND_STORAGE",
            "bullet_points": product.bullet_points if isinstance(product.bullet_points, list) else [],
            "browse_node_id": product.browse_node_id or "21863799031",
        }
        
        # 7. Initialize SP-API client
        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        
        # 8. Create listing on Amazon
        result = client.create_listing_from_product(
            seller_id=seller_id,
            sku=product.sku,
            product_data=product_data,
        )
        
        # 9. Update listing record
        listing.sp_api_submission_id = result.get("submissionId", "")
        listing.sp_api_status = result.get("status", "UNKNOWN")
        
        if result.get("success"):
            listing.status = "success"
            listing.stage = "accepted"
            listing.amazon_asin = result.get("asin", "")
            listing.completed_at = datetime.utcnow()
            logger.info(f"✅ Listing success: {product.sku} → {listing.amazon_asin}")
        else:
            errors = result.get("errors", [])
            error_messages = [e.get("message", "Unknown error") for e in errors]
            listing.status = "failed"
            listing.stage = "rejected"
            listing.error_message = "\n".join(error_messages)[:500]
            listing.completed_at = datetime.utcnow()
            logger.error(f"❌ Listing failed: {product.sku} — {error_messages}")
        
        db.commit()
        
        # 10. Return result
        return {
            "success": result.get("success", False),
            "listing_id": listing.id,
            "submission_id": listing.sp_api_submission_id,
            "status": listing.sp_api_status,
            "asin": listing.amazon_asin,
            "errors": result.get("errors", []),
            "message": "تم إرسال المنتج لأمزون بنجاح" if result.get("success") else "فشل إرسال المنتج — راجع الأخطاء",
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"SP-API submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"خطأ في الإرسال: {str(e)}")
    finally:
        db.close()


@router.get("/listing/{sku}")
async def get_listing_status(sku: str):
    """Get listing status from Amazon SP-API"""
    db = SessionLocal()
    try:
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
        ).order_by(AuthSession.created_at.desc()).first()
        
        if not auth_session:
            raise HTTPException(status_code=400, detail="No active session")
        
        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        seller_id = credentials.get("seller_id", "A1DSHARRBRWYZW")
        marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code or "eg"
        
        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        result = client.get_listing_item(seller_id, sku)
        
        return {
            "sku": sku,
            "status": result.get("status", "UNKNOWN"),
            "asin": result.get("asin", ""),
            "data": result,
        }
    except Exception as e:
        logger.error(f"Get listing status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/schema/{product_type}")
async def get_product_type_schema(product_type: str):
    """Get required attributes for a product type from Amazon"""
    db = SessionLocal()
    try:
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
        ).order_by(AuthSession.created_at.desc()).first()
        
        if not auth_session:
            raise HTTPException(status_code=400, detail="No active session")
        
        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code or "eg"
        
        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        schema = client.get_product_type_definitions(product_type)
        
        # Extract required attributes
        required_attrs = []
        if isinstance(schema, dict):
            requirements = schema.get("requirements", {})
            if isinstance(requirements, dict):
                listing_reqs = requirements.get("LISTING", {})
                for attr_name, attr_info in listing_reqs.items():
                    if isinstance(attr_info, dict) and attr_info.get("required", False):
                        required_attrs.append(attr_name)
        
        return {
            "product_type": product_type,
            "required_attributes": required_attrs,
            "full_schema": schema,
        }
    except Exception as e:
        logger.error(f"Get schema error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
```

---

## 🔧 Step 2: تحديث `backend/app/services/sp_api_client.py`

### أضف هذه الدالة في نهاية الكلاس:

```python
    def create_listing_from_product(
        self,
        seller_id: str,
        sku: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a listing on Amazon from our internal Product data.
        
        This is the main integration method that:
        1. Builds the correct SP-API payload
        2. Handles all required attributes
        3. Returns structured result with success/failure
        
        Args:
            seller_id: Amazon Seller ID (A1DSHARRBRWYZW)
            sku: Product SKU
            product_data: Dict with product fields
            
        Returns:
            {
                "success": bool,
                "status": "ACCEPTED" | "INVALID",
                "submissionId": str,
                "asin": str,
                "errors": [...],
            }
        """
        # Build the full SP-API payload
        payload = self._build_listing_payload(product_data)
        
        # Send to Amazon
        result = self.put_listing_item(seller_id, sku, payload)
        
        # Parse response
        issues = result.get("issues", [])
        errors = [i for i in issues if i.get("severity") == "ERROR"]
        warnings = [i for i in issues if i.get("severity") == "WARNING"]
        
        return {
            "success": len(errors) == 0,
            "status": result.get("status", "UNKNOWN"),
            "submissionId": result.get("submissionId", ""),
            "asin": result.get("asin", ""),
            "errors": errors,
            "warnings": warnings,
            "raw_response": result,
        }

    def _build_listing_payload(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the complete SP-API listing payload with ALL required attributes.
        
        This uses the EXACT formats that Amazon accepts (tested and verified).
        """
        name = product_data.get("name", "Unnamed Product")
        description = product_data.get("description", name)
        brand = (product_data.get("brand") or "Generic").strip() or "Generic"
        ean = product_data.get("ean", "")
        upc = product_data.get("upc", "")
        price = float(product_data.get("price", 0))
        quantity = int(product_data.get("quantity", 0))
        condition = product_data.get("condition", "New")
        fulfillment = product_data.get("fulfillment_channel", "MFN")
        country_origin = product_data.get("country_of_origin", "CN")
        model_number = product_data.get("model_number", product_data.get("sku", "N/A"))
        manufacturer = (product_data.get("manufacturer") or brand).strip() or brand
        bullet_points = product_data.get("bullet_points", [])
        browse_node = product_data.get("browse_node_id", "21863799031")
        
        # Map condition
        condition_map = {"New": "new_new"}
        condition_value = condition_map.get(condition, "new_new")
        
        # Build attributes
        attributes = {
            # Identity
            "item_name": [{"value": name, "language_tag": "en_US"}],
            "brand": [{"value": brand, "language_tag": "en_US"}],
            "product_description": [{"value": description, "language_tag": "en_US"}],
            
            # Bullet points
            "bullet_point": [
                {"value": bp, "language_tag": "en_US"} 
                for bp in (bullet_points if bullet_points else [name])
            ],
            
            # Manufacturer & Model
            "manufacturer": [{"value": manufacturer, "language_tag": "en_US"}],
            "model_name": [{"value": model_number, "language_tag": "en_US"}],
            "model_number": [{"value": model_number, "language_tag": "en_US"}],
            
            # Condition & Origin
            "condition_type": [{"value": condition_value}],
            "country_of_origin": [{"value": country_origin.upper() if len(country_origin) == 2 else "CN"}],
            "recommended_browse_nodes": [{"value": browse_node}],
            
            # Included components
            "included_components": [{"value": name, "language_tag": "en_US"}],
            "number_of_boxes": [{"value": 1}],
            "merchant_suggested_asin": [{"value": product_data.get("merchant_suggested_asin", "")}],
            
            # Compliance
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "batteries_required": [{"value": False}],
            
            # EAN/UPC
            "externally_assigned_product_identifier": [{
                "value": {
                    "type": "ean" if ean else "upc",
                    "value": ean or upc or "000000000000"
                }
            }],
            
            # Weight (FLAT format)
            "item_weight": [{"value": 0.5, "unit": "kilograms"}],
            "item_package_weight": [{"value": 0.7, "unit": "kilograms"}],
            
            # Unit count
            "unit_count": [{"value": 1, "unit": "count"}],
            
            # Package dimensions (CORRECT format!)
            "item_package_dimensions": [{
                "length": {"value": 25.0, "unit": "centimeters"},
                "width": {"value": 10.0, "unit": "centimeters"},
                "height": {"value": 15.0, "unit": "centimeters"},
            }],
            
            # Price
            "purchasable_offer": [{
                "our_price": [{"schedule": [{"value_with_tax": price}]}],
                "currency": "EGP",
            }],
        }
        
        return {
            "productType": product_data.get("product_type", "HOME_ORGANIZERS_AND_STORAGE"),
            "requirements": "LISTING",
            "attributes": attributes,
        }
```

---

## 🔧 Step 3: تحديث `backend/app/api/products.py`

### أضف هذا endpoint في نهاية الملف:

```python
from fastapi import APIRouter, Depends, HTTPException
# ... existing imports ...

# Add this import
from app.api import sp_api_router

@router.post("/{product_id}/submit-to-amazon")
async def submit_product_to_amazon(product_id: str):
    """
    Submit a product to Amazon via SP-API.
    
    This endpoint calls the SP-API router internally.
    """
    from app.api.sp_api_router import submit_product_to_amazon as sp_submit
    return await sp_submit(product_id)
```

---

## 🔧 Step 4: تحديث Listing Model

### في `backend/app/models/listing.py`, أضف هذه الحقول:

```python
from sqlalchemy import Column, String, DateTime

class Listing(Base):
    __tablename__ = "listings"
    
    # ... existing fields ...
    
    # NEW: SP-API fields
    sp_api_submission_id = Column(String, nullable=True)  # Amazon submission ID
    sp_api_status = Column(String, nullable=True)  # ACCEPTED / INVALID
    amazon_asin = Column(String, nullable=True)  # Assigned ASIN from Amazon
```

### أنشئ migration جديدة:

```bash
cd backend
alembic revision --autogenerate -m "add sp_api fields to listings"
alembic upgrade head
```

---

## 🔧 Step 5: تحديث `backend/app/api/router.py`

### أضف هذا السطر:

```python
from app.api import sp_api_router

# ... existing routers ...
api_router.include_router(sp_api_router.router, prefix="/sp-api", tags=["sp-api"])
```

---

## 🧪 Step 6: Testing

### Test 1: Submit product to Amazon

```bash
curl -X POST http://127.0.0.1:8765/api/v1/sp-api/submit/0e3f283e-52af-4e22-959a-b9c071cf9712
```

**Expected response:**
```json
{
  "success": true,
  "listing_id": "...",
  "submission_id": "abc123...",
  "status": "ACCEPTED",
  "asin": "",
  "errors": [],
  "message": "تم إرسال المنتج لأمزون بنجاح"
}
```

### Test 2: Get listing status

```bash
curl http://127.0.0.1:8765/api/v1/sp-api/listing/TEST-ABIS-001
```

### Test 3: Get product type schema

```bash
curl http://127.0.0.1:8765/api/v1/sp-api/schema/HOME_ORGANIZERS_AND_STORAGE
```

---

## 📋 Checklist للمهندس

بعد التنفيذ، تأكد من:

- [ ] `sp_api_router.py` موجود وفيه 3 endpoints
- [ ] `sp_api_client.py` فيه `create_listing_from_product()` و `_build_listing_payload()`
- [ ] Listing model فيه حقول: `sp_api_submission_id`, `sp_api_status`, `amazon_asin`
- [ ] Migration اتعملت واتطبقت
- [ ] `router.py` فيه `sp_api_router`
- [ ] Test 1 بيرد بـ `{"success": true, "status": "ACCEPTED"}`
- [ ] المنتج بيظهر في Amazon.eg

---

## ⚠️ ملاحظات مهمة

1. **الأبعاد**: الفورمات الصحيح:
```python
"item_package_dimensions": [{
    "length": {"value": 25.0, "unit": "centimeters"},
    "width": {"value": 10.0, "unit": "centimeters"},
    "height": {"value": 15.0, "unit": "centimeters"},
}]
```

2. **البطاريات**: مطلوب دائمًا:
```python
"batteries_required": [{"value": False}]
```

3. **الباركود**: لازم يكون داخل object:
```python
"externally_assigned_product_identifier": [{
    "value": {"type": "ean", "value": "1245768907654"}
}]
```

4. **Seller ID**: `A1DSHARRBRWYZW` (موجود في DB)

---

## 🔴 ملحق إلزامي من القائد التقني (لازم يتطبق قبل التنفيذ)

### 1. الـ Payload لازم يستخدم الـ 29 حقل المعتمد

**ممنوع** بناء الـ Payload من الصفر. لازم `_build_listing_payload()` تستخدم القاموس الكامل (The Ultimate Dictionary) اللي فيه:
- `ar_AE` كلغة أساسية
- `EGP` للعملة
- الهيكل المتداخل الصحيح `attributeProperties`
- كل الـ 29 حقل REQUIRED

### 2. Background Polling Task — تحديث الحالة بعد الإرسال

أمازون SP-API في مسار `Listings Items` بيرد بـ `ACCEPTED` فوراً (كاستلام مبدئي)، بس بيخد من **2 لـ 15 دقيقة** ليعالج المنتج ويصدر الـ `ASIN` أو يرفضه.

**المطلوب**: إضافة Background Task يحدث حالة الـ listing تلقائياً:

```python
# في backend/app/tasks/polling_tasks.py
import asyncio
from datetime import datetime, timedelta
from loguru import logger

async def poll_listing_status(sku: str, seller_id: str, listing_id: str, max_polls: int = 12, interval_seconds: int = 300):
    """
    Poll Amazon SP-API for listing status updates.
    Runs every 5 minutes for up to 1 hour (12 polls).
    Updates listing record when status changes to ACTIVE or INVALID.
    """
    from app.database import SessionLocal
    from app.models.listing import Listing
    from app.services.sp_api_client import SPAPIClient
    
    client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
    
    for poll_num in range(max_polls):
        await asyncio.sleep(interval_seconds)
        
        try:
            result = client.get_listing_item(seller_id, sku)
            status = result.get('status', 'UNKNOWN')
            asin = result.get('asin', '')
            issues = result.get('issues', [])
            
            db = SessionLocal()
            try:
                listing = db.query(Listing).filter(Listing.id == listing_id).first()
                if not listing:
                    break
                
                listing.sp_api_status = status
                listing.sp_api_last_polled_at = datetime.utcnow()
                
                if status == 'ACTIVE' or asin:
                    listing.status = 'success'
                    listing.stage = 'active'
                    listing.amazon_asin = asin
                    listing.completed_at = datetime.utcnow()
                    logger.info(f"✅ Listing ACTIVE: {sku} → ASIN {asin}")
                    db.commit()
                    break
                elif status == 'INVALID' and issues:
                    errors = [i for i in issues if i.get('severity') == 'ERROR']
                    if errors:
                        listing.status = 'failed'
                        listing.stage = 'rejected'
                        listing.error_message = '\n'.join([e.get('message', '')[:200] for e in errors])[:500]
                        listing.completed_at = datetime.utcnow()
                        logger.error(f"❌ Listing INVALID: {sku} — {errors[0].get('message', '')}")
                        db.commit()
                        break
            finally:
                db.close()
                
        except Exception as e:
            logger.warning(f"Poll #{poll_num+1} failed for {sku}: {e}")
    
    logger.info(f"Polling complete for {sku} after {poll_num+1} attempts")
```

### 3. تشغيل الـ Polling Task بعد كل إرسال

في `sp_api_router.py`, بعد ما الـ listing يتبعت بنجاح:

```python
from fastapi import BackgroundTasks

@router.post("/submit/{product_id}")
async def submit_product_to_amazon(product_id: str, background_tasks: BackgroundTasks):
    # ... existing code ...
    
    if result.get("success"):
        # Queue background polling to check for ASIN assignment
        background_tasks.add_task(
            poll_listing_status,
            sku=product.sku,
            seller_id=seller_id,
            listing_id=listing.id,
        )
```

---

**انطلق! 🚀**
