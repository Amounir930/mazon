"""
Legacy Tkinter Client API Wrapper
Makes the old Tkinter UI communicate with FastAPI backend
"""
import requests
from datetime import datetime
from typing import Optional


class AmazonBotAPIClient:
    """
    Thin wrapper to make Tkinter UI communicate with FastAPI backend.
    This allows gradual migration from Tkinter to web interface.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.seller_id: Optional[str] = None
    
    def set_seller(self, seller_id: str):
        """Set the current seller context"""
        self.seller_id = seller_id
    
    # ========== Product Operations ==========
    
    def create_product(self, product_data: dict) -> dict:
        """Create product via API"""
        response = requests.post(
            f"{self.api_base_url}/api/v1/products/",
            json=product_data,
            params={"seller_id": self.seller_id},
        )
        response.raise_for_status()
        return response.json()
    
    def get_product(self, product_id: str) -> dict:
        """Get product by ID"""
        response = requests.get(
            f"{self.api_base_url}/api/v1/products/{product_id}",
        )
        response.raise_for_status()
        return response.json()
    
    def list_products(self, status: Optional[str] = None, page: int = 1) -> dict:
        """List products with pagination"""
        params = {
            "seller_id": self.seller_id,
            "page": page,
            "page_size": 50,
        }
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.api_base_url}/api/v1/products/",
            params=params,
        )
        response.raise_for_status()
        return response.json()
    
    def update_product(self, product_id: str, update_data: dict) -> dict:
        """Update product"""
        response = requests.put(
            f"{self.api_base_url}/api/v1/products/{product_id}",
            json=update_data,
        )
        response.raise_for_status()
        return response.json()
    
    def delete_product(self, product_id: str) -> dict:
        """Delete product"""
        response = requests.delete(
            f"{self.api_base_url}/api/v1/products/{product_id}",
        )
        response.raise_for_status()
        return response.json()
    
    # ========== Listing Operations ==========
    
    def submit_listing(self, product_id: str) -> dict:
        """Submit listing to queue"""
        response = requests.post(
            f"{self.api_base_url}/api/v1/listings/submit/",
            json={"product_id": product_id, "seller_id": self.seller_id},
        )
        response.raise_for_status()
        return response.json()
    
    def get_listings_queue(self, status: Optional[str] = None) -> list:
        """Get current listings queue"""
        params = {"seller_id": self.seller_id}
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.api_base_url}/api/v1/listings/",
            params=params,
        )
        response.raise_for_status()
        return response.json()
    
    def retry_listing(self, listing_id: str) -> dict:
        """Retry a failed listing"""
        response = requests.post(
            f"{self.api_base_url}/api/v1/listings/{listing_id}/retry",
        )
        response.raise_for_status()
        return response.json()
    
    def bulk_submit_listings(self, product_ids: list[str]) -> list:
        """Submit multiple listings"""
        response = requests.post(
            f"{self.api_base_url}/api/v1/listings/bulk-submit/",
            json={"product_ids": product_ids},
            params={"seller_id": self.seller_id},
        )
        response.raise_for_status()
        return response.json()
    
    # ========== Seller Operations ==========
    
    def register_seller(self, seller_data: dict) -> dict:
        """Register a new seller account"""
        response = requests.post(
            f"{self.api_base_url}/api/v1/sellers/register",
            json=seller_data,
        )
        response.raise_for_status()
        return response.json()
    
    def get_seller(self, seller_id: str) -> dict:
        """Get seller details"""
        response = requests.get(
            f"{self.api_base_url}/api/v1/sellers/{seller_id}",
        )
        response.raise_for_status()
        return response.json()
    
    # ========== Feed Operations ==========
    
    def get_feed_status(self, feed_id: str) -> dict:
        """Check feed status"""
        response = requests.get(
            f"{self.api_base_url}/api/v1/feeds/{feed_id}/status",
            params={"seller_id": self.seller_id},
        )
        response.raise_for_status()
        return response.json()
    
    # ========== Health Check ==========
    
    def health_check(self) -> dict:
        """Check API health"""
        response = requests.get(f"{self.api_base_url}/health")
        response.raise_for_status()
        return response.json()
    
    # ========== Migration Helpers ==========
    
    def migrate_from_json(self, json_file: str) -> int:
        """
        Migrate products from old JSON file to new database.
        Returns number of products migrated.
        """
        import json
        import os
        
        if not os.path.exists(json_file):
            return 0
        
        with open(json_file, "r", encoding="utf-8") as f:
            products_data = json.load(f)
        
        migrated_count = 0
        for product in products_data:
            try:
                # Transform old format to new format if needed
                new_product_data = {
                    "sku": product.get("sku", ""),
                    "name": product.get("name", ""),
                    "category": product.get("category"),
                    "brand": product.get("brand"),
                    "upc": product.get("upc"),
                    "ean": product.get("ean"),
                    "description": product.get("description"),
                    "bullet_points": product.get("bullet_points", []),
                    "keywords": product.get("keywords", []),
                    "price": float(product.get("price", 0)),
                    "compare_price": float(product["compare_price"]) if product.get("compare_price") else None,
                    "cost": float(product["cost"]) if product.get("cost") else None,
                    "quantity": int(product.get("quantity", 0)),
                    "weight": float(product["weight"]) if product.get("weight") else None,
                    "images": product.get("images", []),
                    "attributes": product.get("attributes", {}),
                }
                
                self.create_product(new_product_data)
                migrated_count += 1
                
            except Exception as e:
                print(f"Error migrating product {product.get('sku')}: {str(e)}")
                continue
        
        return migrated_count
