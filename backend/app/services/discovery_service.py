from typing import List, Dict, Any
from app.services.sp_api_client import SPAPIClient
import logging

logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, client: SPAPIClient):
        self.client = client

    async def get_amazon_top_sellers(self, keywords: str = "trending", category: str = None) -> List[Dict[str, Any]]:
        """
        Discovers top selling products on Amazon using Catalog Items API.
        Stateless: Does NOT check local database.
        """
        try:
            # Step 1: Search Amazon Catalog
            # Amazon Catalog API marketplaceIds must be a comma-separated string or a list
            marketplace_id = self.client.marketplace_id
            
            params = {
                "keywords": keywords,
                "marketplaceIds": marketplace_id,
                "includedData": "summaries,salesRanks,images",
                "pageSize": 20
            }
            
            if category:
                params["classificationId"] = category

            logger.info(f"🔍 Searching Amazon Market: keywords={keywords}, marketplace={marketplace_id}")
            response = self.client._make_request("GET", "/catalog/2022-04-01/items", params=params)
            
            amazon_items = response.get("items", [])
            if not amazon_items:
                logger.warning(f"⚠️ No items found in Amazon Market for keywords: {keywords}")
                return []

            # Step 2: Format directly
            top_sellers = []
            for item in amazon_items:
                asin = item.get("asin")
                summaries = item.get("summaries", [])
                summary = summaries[0] if summaries else {}
                
                sales_ranks = item.get("salesRanks", [])
                best_rank = 999999
                if sales_ranks:
                    # Look for displayGroupRanks
                    display_ranks = sales_ranks[0].get("displayGroupRanks", [])
                    if display_ranks:
                        best_rank = min([r.get("rank", 999999) for r in display_ranks])

                images_data = item.get("images", [])
                image_url = ""
                if images_data:
                    variant_images = images_data[0].get("images", [])
                    if variant_images:
                        image_url = variant_images[0].get("link")

                top_sellers.append({
                    "asin": asin,
                    "title": summary.get("itemName", "Unknown Title"),
                    "image": image_url,
                    "rank": best_rank,
                    "brand": summary.get("brandName", "Generic"),
                    "link": f"https://www.amazon.{self.client.country_code}/dp/{asin}"
                })

            # Sort by rank
            top_sellers.sort(key=lambda x: x["rank"])
            return top_sellers

        except Exception as e:
            logger.error(f"❌ Discovery Error: {str(e)}")
            return []
