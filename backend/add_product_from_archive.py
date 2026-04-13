"""
Add a product from the archive report to the database
"""
import sys
import json
from decimal import Decimal

# Add backend to path
sys.path.insert(0, '.')

from app.database import SessionLocal, engine, Base
from app.models import Product, Seller

# Create tables if not exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # 1. Check if seller exists, if not create one
    seller = db.query(Seller).first()
    if not seller:
        print("⚠️ No seller found. Creating a default seller...")
        seller = Seller(
            display_name="Eagle Shop",
            lwa_client_id="amzn1.application-oa2-client.placeholder",
            lwa_client_secret="placeholder_secret",
            lwa_refresh_token="placeholder_token",
            amazon_seller_id="A3PLACEHOLDER",
            marketplace_id="ARBP9OOSHTCHU",
            region="EU"
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)
        print(f"✅ Created seller: {seller.display_name} (ID: {seller.id})")
    else:
        print(f"✅ Using existing seller: {seller.display_name} (ID: {seller.id})")

    # 2. The product from archive report
    product_data = {
        "id": "prod-0923F1ECDX0",
        "seller_id": seller.id,
        "sku": "00-3A5S-1EYF",
        "name": "Professional Electric Hand Mixer - Multi-Speed Egg Cream Dough Maker",
        "name_ar": "مضرب يدوي كهربائي احترافي متعدد السرعات",
        "name_en": "Professional Electric Hand Mixer, Multi-Speed Egg Cream Dough Maker with Powerful Whisk Heads",
        "description": "اكتشف الراحة والقوة مع المضرب اليدوي الكهربائي الاحترافي المصمم خصيصاً ليمنحك نتائج مثالية في خفق البيض، تحضير الكريمة، وخلط العجائن الخفيفة بسرعة وكفاءة عالية.",
        "description_en": "Professional Electric Hand Mixer with powerful whisk heads, ergonomic design, easy to clean for modern kitchens. Multiple speed settings for eggs, cream, and dough.",
        "price": Decimal("350.00"),
        "currency": "EGP",
        "quantity": 19,
        "category": "Kitchen Appliances",
        "brand": "Eagle Shop",
        "condition": "New",
        "fulfillment_channel": "MFN",
        "handling_time": 0,
        "status": "draft",
        "bullet_points": json.dumps([
            "Multiple speed settings for eggs, cream, and dough",
            "Ergonomic anti-slip design for comfortable use",
            "Powerful stainless steel whisk heads",
            "Easy to clean and store",
            "Perfect for modern kitchens"
        ]),
        "bullet_points_ar": json.dumps([
            "إعدادات سرعة متعددة للبيض والكريمة والعجين",
            "تصميم مريح مانع للانزلاق لراحة الاستخدام",
            "رؤوس خفق قوية من الستانلس ستيل",
            "سهل التنظيف والتخزين",
            "مثالي للمطابخ العصرية"
        ]),
        "keywords": json.dumps(["hand mixer", "electric mixer", "kitchen", "eggs", "cream", "dough", "مضرب", "مطبخ"]),
        "attributes": json.dumps({
            "listing_id": "0923F1ECDX0",
            "asin": "B0FSBH1WGZ",
            "source": "archive_report",
            "import_date": "2026-04-13"
        }),
        "upc": "B0FSBH1WGZ"
    }

    # 3. Check if product already exists
    existing = db.query(Product).filter(Product.sku == product_data["sku"]).first()
    if existing:
        print(f"⚠️ Product already exists: {existing.name} (SKU: {existing.sku})")
        print("   Skipping import...")
    else:
        product = Product(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        print(f"\n✅ Product added successfully!")
        print(f"   Name: {product.name}")
        print(f"   SKU: {product.sku}")
        print(f"   Price: {product.price} {product.currency}")
        print(f"   Quantity: {product.quantity}")
        print(f"   Status: {product.status}")
        print(f"   ASIN: B0FSBH1WGZ")

    # 4. Show total products count
    total = db.query(Product).count()
    print(f"\n📊 Total products in database: {total}")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
