"""
Feed Service — Single Client
Handles Amazon feed XML generation and submission
"""
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.models.listing import Listing
from app.models.seller import Seller
from app.models.product import Product
from app.services.amazon_api import AmazonAPIClient
from loguru import logger


class FeedService:
    """Handle Amazon feed generation and submission (single client)"""

    @staticmethod
    def generate_product_xml(product: dict, seller: Seller) -> bytes:
        """Generate Amazon SP-API compliant XML for product listing"""
        envelope = ET.Element("AmazonEnvelope", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "amzn-envelope.xsd",
        })

        header = ET.SubElement(envelope, "Header")
        ET.SubElement(header, "DocumentVersion").text = "1.01"
        ET.SubElement(header, "MerchantIdentifier").text = seller.amazon_seller_id

        ET.SubElement(envelope, "MessageType").text = "Product"
        ET.SubElement(envelope, "PurgeAndReplace").text = "false"

        message = ET.SubElement(envelope, "Message")
        ET.SubElement(message, "MessageID").text = "1"
        ET.SubElement(message, "OperationType").text = "Update"

        product_elem = ET.SubElement(message, "Product")
        ET.SubElement(product_elem, "SKU").text = product.get("sku", "")

        # Standard Product ID (UPC/EAN)
        standard_id = ET.SubElement(product_elem, "StandardProductID")
        if product.get("upc"):
            ET.SubElement(standard_id, "Type").text = "UPC"
            ET.SubElement(standard_id, "Value").text = product["upc"]
        elif product.get("ean"):
            ET.SubElement(standard_id, "Type").text = "EAN"
            ET.SubElement(standard_id, "Value").text = product["ean"]

        # Description Data
        desc_data = ET.SubElement(product_elem, "DescriptionData")
        ET.SubElement(desc_data, "Title").text = product.get("name", "")
        if product.get("brand"):
            ET.SubElement(desc_data, "Brand").text = product["brand"]
        if product.get("description"):
            ET.SubElement(desc_data, "Description").text = product["description"]

        for bullet in product.get("bullet_points", []):
            ET.SubElement(desc_data, "BulletPoint").text = bullet

        # Manufacturer info
        if product.get("manufacturer"):
            ET.SubElement(desc_data, "Manufacturer").text = product["manufacturer"]
        if product.get("model_number"):
            ET.SubElement(desc_data, "MfrPartNumber").text = product["model_number"]
        if product.get("country_of_origin"):
            ET.SubElement(desc_data, "CountryOfOrigin").text = product["country_of_origin"]

        # Product Type (required by Amazon)
        if product.get("product_type"):
            ET.SubElement(product_elem, "ProductType").text = product["product_type"]

        # Condition Data (required by Amazon)
        condition_data = ET.SubElement(product_elem, "ConditionData")
        ET.SubElement(condition_data, "ConditionType").text = product.get("condition", "New")

        # Fulfillment Channel
        if product.get("fulfillment_channel"):
            fulfillment_data = ET.SubElement(product_elem, "FulfillmentChannelData")
            ET.SubElement(fulfillment_data, "FulfillmentChannel").text = product["fulfillment_channel"]

        # Handling Time
        if product.get("handling_time") is not None and product.get("handling_time") > 0:
            ET.SubElement(product_elem, "HandlingTime").text = str(product["handling_time"])

        # Package Quantity
        if product.get("package_quantity") is not None and product.get("package_quantity") > 1:
            ET.SubElement(product_elem, "PackageQuantity").text = str(product["package_quantity"])

        # Images
        images = product.get("images", [])
        if images:
            image_data = ET.SubElement(product_elem, "ImageData")
            for idx, img_url in enumerate(images[:8]):  # Amazon allows max 8 images
                suffix = "" if idx == 0 else str(idx + 1)
                ET.SubElement(image_data, f"ImageLocation{suffix}", {"MIMEType": "image/jpeg"}).text = img_url

        # Pricing Data
        if product.get("price"):
            pricing_data = ET.SubElement(product_elem, "PricingData")
            standard_price = ET.SubElement(pricing_data, "StandardPrice")
            standard_price.set("currency", product.get("currency", "EGP"))
            standard_price.text = str(product["price"])

        # Weight
        if product.get("weight"):
            weight_elem = ET.SubElement(product_elem, "Weight")
            weight_elem.set("unitOfMeasure", "KG")
            weight_elem.text = str(product["weight"])

        # Dimensions
        dimensions = product.get("dimensions")
        if dimensions and isinstance(dimensions, dict):
            dim_data = ET.SubElement(product_elem, "DimensionData")
            if dimensions.get("length"):
                item_length = ET.SubElement(dim_data, "ItemLength")
                item_length.set("unitOfMeasure", "CM")
                item_length.text = str(dimensions["length"])
            if dimensions.get("width"):
                item_width = ET.SubElement(dim_data, "ItemWidth")
                item_width.set("unitOfMeasure", "CM")
                item_width.text = str(dimensions["width"])
            if dimensions.get("height"):
                item_height = ET.SubElement(dim_data, "ItemHeight")
                item_height.set("unitOfMeasure", "CM")
                item_height.text = str(dimensions["height"])

        # Quantity
        if product.get("quantity") is not None:
            ET.SubElement(product_elem, "Quantity").text = str(product["quantity"])

        return ET.tostring(envelope, encoding="UTF-8", xml_declaration=True)

    @staticmethod
    async def submit_listing_to_amazon(db: Session, listing: Listing, seller: Seller) -> bool:
        """Submit a single listing to Amazon via SP-API"""
        try:
            product = listing.product
            product_data = {
                "sku": product.sku,
                "name": product.name,
                "brand": product.brand,
                "description": product.description,
                "bullet_points": _parse_json_safe(product.bullet_points, []),
                "price": float(product.price) if product.price else 0,
                "quantity": product.quantity or 0,
                "currency": product.currency or "EGP",
                "upc": product.upc,
                "ean": product.ean,
                "condition": product.condition or "New",
                "fulfillment_channel": product.fulfillment_channel or "MFN",
                "handling_time": product.handling_time or 0,
                "product_type": product.product_type or "",
                "manufacturer": product.manufacturer or "",
                "model_number": product.model_number or "",
                "country_of_origin": product.country_of_origin or "",
                "package_quantity": product.package_quantity or 1,
                "images": _parse_json_safe(product.images, []),
                "weight": float(product.weight) if product.weight else None,
                "dimensions": _parse_json_safe(product.dimensions, {}),
            }

            xml_data = FeedService.generate_product_xml(product_data, seller)

            # Real SP-API integration
            client = AmazonAPIClient(
                seller_id=seller.amazon_seller_id,
                refresh_token=seller.lwa_refresh_token
            )
            
            feed_id = await client.submit_feed(
                feed_type="POST_PRODUCT_DATA",
                feed_data=xml_data,
                marketplace_ids=[seller.marketplace_id]
            )

            listing.feed_submission_id = feed_id
            listing.status = "submitted"
            listing.submitted_at = datetime.utcnow()

            db.commit()
            logger.info(f"Listing submitted to SP-API: {listing.id} (Feed ID: {feed_id})")
            return True

        except Exception as e:
            listing.status = "failed"
            listing.error_message = str(e)
            db.commit()
            logger.error(f"Listing submission failed: {listing.id}: {str(e)}")
            return False

    @staticmethod
    def check_feed_status(db: Session, feed_id: str) -> dict:
        """Check the processing status of a feed (single client)"""
        listing = db.query(Listing).filter(
            Listing.feed_submission_id == feed_id
        ).first()

        if not listing:
            raise ValueError(f"Feed not found: {feed_id}")

        # Real status check should be implemented here in a background task
        # For Phase 2, we keep the tracking structure but mark it for future sync
        return {
            "feed_id": feed_id,
            "status": listing.status,
            "error_message": listing.error_message,
        }

    @staticmethod
    def get_feed_results(db: Session, feed_id: str) -> dict:
        """Get detailed results of a processed feed (single client)"""
        listing = db.query(Listing).filter(
            Listing.feed_submission_id == feed_id
        ).first()

        if not listing:
            raise ValueError(f"Feed not found: {feed_id}")

        return {
            "feed_id": feed_id,
            "status": listing.status,
            "asin": listing.amazon_asin,
            "error_message": listing.error_message,
        }

    @staticmethod
    def refresh_all_feed_statuses(db: Session) -> int:
        """Refresh status of all submitted feeds (single client)"""
        pending = db.query(Listing).filter(
            Listing.status.in_(["submitted", "processing"]),
            Listing.feed_submission_id.isnot(None),
        ).all()

        # TODO: Query real SP-API for each feed
        refreshed_count = len(pending)
        return refreshed_count

    @staticmethod
    def list_feeds(db: Session, status: Optional[str] = None) -> list:
        """List all feed submissions"""
        query = db.query(Listing).filter(Listing.feed_submission_id.isnot(None))
        if status:
            query = query.filter(Listing.status == status)
        feeds = query.order_by(Listing.created_at.desc()).all()
        return [
            {
                "feed_id": l.feed_submission_id,
                "listing_id": l.id,
                "product_id": l.product_id,
                "status": l.status,
                "error_message": l.error_message,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in feeds
        ]


def _parse_json_safe(value: str, default):
    import json
    if value is None:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default
