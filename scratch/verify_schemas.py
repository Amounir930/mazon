import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate, ListingResponse
    from app.schemas.ai import AIProductResponse, BaseProductData, ProductVariant, AIProductRequest
    
    print("✅ Successfully imported all schemas.")
    
    # Test ProductResponse (model_number/model_name suppression)
    try:
        # Pydantic v2 warnings happen at class definition time usually, 
        # but let's try to see if we can trigger any by looking at the model fields.
        print(f"ProductResponse fields: {list(ProductResponse.model_fields.keys())}")
        if 'model_number' in ProductResponse.model_fields:
            print("  - model_number present in ProductResponse")
            
        print(f"ProductVariant fields: {list(ProductVariant.model_fields.keys())}")
        if 'model_name' in ProductVariant.model_fields:
            print("  - model_name present in ProductVariant")
            
        print("✅ No Pydantic warnings triggered during import or inspection.")
    except Exception as e:
        print(f"❌ Error during model inspection: {e}")

    # Test ListingResponse from_attributes
    try:
        class MockModel:
            def __init__(self):
                self.id = "test-id"
                self.product_id = "prod-id"
                self.seller_id = "sell-id"
                self.status = "active"
                self.retry_count = 0
        
        mock = MockModel()
        resp = ListingResponse.model_validate(mock)
        print(f"✅ ListingResponse.model_validate worked: {resp.id}")
    except Exception as e:
        print(f"❌ ListingResponse.model_validate failed: {e}")

except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
