"""
Amazon Product Sync Engine
يستورد المنتجات من Amazon Seller Central → Local Database

الطريقة: تحميل تقرير "Active Listings" من Seller Central
محدّث: يستخدم curl_cffi (TLS impersonation) + CookieJar بدلاً من niquests
"""
import json
import csv
import io
import time
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from loguru import logger

from bs4 import BeautifulSoup

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.models.product import Product
from app.models.seller import Seller
from app.services.session_store import decrypt_data
from app.services.amazon_http_client import AmazonHTTPClient, SessionExpiredError


class AmazonProductSyncEngine:
    """
    محرك مزامنة المنتجات من Amazon Seller Central.
    يستخدم curl_cffi (TLS impersonation) + CookieJar بدلاً من niquests.
    """

    BASE_URLS = {
        "eg": "https://sellercentral.amazon.eg",
        "sa": "https://sellercentral.amazon.sa",
        "ae": "https://sellercentral.amazon.ae",
        "uk": "https://sellercentral.amazon.co.uk",
        "us": "https://sellercentral.amazon.com",
    }

    def __init__(self, cookies: List[Dict[str, Any]], country_code: str = "eg"):
        self.country_code = country_code
        self.base_url = self.BASE_URLS.get(country_code, self.BASE_URLS["eg"])
        # curl_cffi client with CookieJar + TLS impersonation (chrome131)
        self.client = AmazonHTTPClient(cookies, country_code)
        logger.info(f"Sync engine initialized: {self.client.cookie_jar.count()} cookies, country={country_code.upper()}, TLS=chrome131")

    def setup_cookies(self, cookies: List[Dict[str, Any]]):
        """No-op — cookies already set in AmazonHTTPClient constructor"""
        pass

    def sync_products(self) -> Dict[str, Any]:
        """
        المزامنة الرئيسية: تحميل تقرير المنتجات من Amazon وحفظها في الـ DB.
        """
        try:
            # Strategy 1: Try Inventory Report Download Page
            report_data = self._try_inventory_report()

            if report_data:
                logger.info(f"Strategy 1 succeeded: Got {len(report_data)} products from Inventory Report")
                return self._save_products_to_db(report_data)

            # Strategy 2: Try Inventory Page Scraping
            report_data = self._try_inventory_page_scraping()

            if report_data:
                logger.info(f"Strategy 2 succeeded: Got {len(report_data)} products from Inventory Page")
                return self._save_products_to_db(report_data)

            # Strategy 3: Try Reports Download
            report_data = self._try_reports_download()

            if report_data:
                logger.info(f"Strategy 3 succeeded: Got {len(report_data)} products from Reports")
                return self._save_products_to_db(report_data)

            return {
                "success": False,
                "error": "لم يتم العثور على بيانات المنتجات. تأكد من تسجيل الدخول وأن لديك منتجات على Amazon.",
                "synced": 0,
                "total": 0,
            }

        except Exception as e:
            logger.error(f"Sync error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "synced": 0,
                "total": 0,
            }

    def _try_inventory_report(self) -> Optional[List[Dict[str, Any]]]:
        """
        Strategy 1: تحميل تقرير Active Listings من Seller Central.
        URL: /inventory/download أو /fba/prodfu/download-inventory
        """
        try:
            # Try common inventory report URLs
            report_urls = [
                f"{self.base_url}/inventory/download",
                f"{self.base_url}/fba/prodfu/download-inventory",
                f"{self.base_url}/inboundinventory/report/download",
            ]

            for url in report_urls:
                logger.info(f"Trying inventory report: {url}")
                response = self.client.session.get(url, timeout=30, allow_redirects=True)

                if response.status_code == 200:
                    # Check if we got a CSV/TSV file
                    content_type = response.headers.get("content-type", "")
                    if "csv" in content_type or "text" in content_type:
                        products = self._parse_csv_response(response.text)
                        if products:
                            return products

                    # Check if it's HTML with download links
                    soup = BeautifulSoup(response.text, 'html.parser')
                    download_link = soup.find('a', href=lambda h: h and ('csv' in h.lower() or 'download' in h.lower()))

                    if download_link:
                        download_url = download_link['href']
                        if not download_url.startswith('http'):
                            download_url = f"{self.base_url}{download_url}"

                        logger.info(f"Found download link: {download_url}")
                        dl_response = self.client.session.get(download_url, timeout=30)

                        if dl_response.status_code == 200:
                            products = self._parse_csv_response(dl_response.text)
                            if products:
                                return products

            return None

        except Exception as e:
            logger.debug(f"Inventory report strategy failed: {e}")
            return None

    def _try_inventory_page_scraping(self) -> Optional[List[Dict[str, Any]]]:
        """
        Strategy 2: استخراج البيانات من صفحة Inventory.
        URL: /inventory
        """
        try:
            url = f"{self.base_url}/inventory"
            logger.info(f"Trying inventory page: {url}")

            response = self.client.session.get(url, timeout=30)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for product data in the page
            products = []

            # Strategy 2a: Look for embedded JSON
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for product data patterns
                    patterns = [
                        r'(\{[^}]*"items"[^}]*\})',
                        r'(\{[^}]*"products"[^}]*\})',
                        r'(\{[^}]*"inventory"[^}]*\})',
                    ]

                    import re
                    for pattern in patterns:
                        matches = re.findall(pattern, script.string, re.DOTALL)
                        for match in matches:
                            try:
                                data = json.loads(match)
                                if isinstance(data, dict):
                                    items = data.get('items', data.get('products', data.get('inventory', [])))
                                    if isinstance(items, list) and len(items) > 0:
                                        products.extend(items)
                            except (json.JSONDecodeError, TypeError):
                                continue

            if products:
                return self._normalize_api_products(products)

            # Strategy 2b: Try to parse table data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) == len(headers):
                            product = {}
                            for i, cell in enumerate(cells):
                                product[headers[i]] = cell.get_text(strip=True)

                            # Check if this looks like a product row
                            if any(key in product for key in ['sku', 'asin', 'item-name', 'title']):
                                products.append(product)

            return products if products else None

        except Exception as e:
            logger.debug(f"Inventory page scraping strategy failed: {e}")
            return None

    def _try_reports_download(self) -> Optional[List[Dict[str, Any]]]:
        """
        Strategy 3: تحميل تقرير من صفحة Reports.
        URL: /reports
        """
        try:
            url = f"{self.base_url}/reports"
            logger.info(f"Trying reports page: {url}")

            response = self.client.session.get(url, timeout=30)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for inventory report download links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href'].lower()
                if 'inventory' in href and ('download' in href or 'report' in href):
                    download_url = link['href']
                    if not download_url.startswith('http'):
                        download_url = f"{self.base_url}{download_url}"

                    logger.info(f"Found report download link: {download_url}")
                    dl_response = self.client.session.get(download_url, timeout=30)

                    if dl_response.status_code == 200:
                        products = self._parse_csv_response(dl_response.text)
                        if products:
                            return products

            return None

        except Exception as e:
            logger.debug(f"Reports download strategy failed: {e}")
            return None

    def _parse_csv_response(self, csv_text: str) -> Optional[List[Dict[str, Any]]]:
        """تحليل محتوى CSV/TSV"""
        try:
            # Detect delimiter
            delimiter = '\t' if '\t' in csv_text else ','

            reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
            products = []

            for row in reader:
                product = self._normalize_csv_row(row)
                if product:
                    products.append(product)

            return products if products else None

        except Exception as e:
            logger.debug(f"CSV parsing failed: {e}")
            return None

    def _normalize_csv_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """تحويل صف CSV إلى صيغة موحدة"""
        try:
            # Common Amazon CSV column names
            sku = (
                row.get('sku') or
                row.get('SKU') or
                row.get('item-sku') or
                row.get('item_sku') or
                row.get('seller-sku')
            )

            if not sku:
                return None

            return {
                'sku': sku,
                'asin': row.get('asin', row.get('ASIN', row.get('asin1', ''))),
                'title': row.get('item-name', row.get('product-name', row.get('title', ''))),
                'price': row.get('price', row.get('selling-price', row.get('your-price', '0'))),
                'quantity': row.get('quantity', row.get('available', row.get('qty', '0'))),
                'status': row.get('status', row.get('item-status', 'ACTIVE')),
                'brand': row.get('brand', row.get('brand-name', '')),
                'category': row.get('product-type', row.get('category', '')),
            }

        except Exception as e:
            logger.debug(f"CSV row normalization failed: {e}")
            return None

    def _normalize_api_products(self, products: List[Dict]) -> List[Dict[str, Any]]:
        """تطبيع بيانات المنتجات من API"""
        normalized = []

        for p in products:
            try:
                normalized.append({
                    'sku': p.get('sku', p.get('SKU', '')),
                    'asin': p.get('asin', p.get('ASIN', '')),
                    'title': p.get('title', p.get('product-name', p.get('item-name', ''))),
                    'price': str(p.get('price', p.get('selling-price', 0))),
                    'quantity': str(p.get('quantity', p.get('available', 0))),
                    'status': p.get('status', 'ACTIVE'),
                    'brand': p.get('brand', ''),
                    'category': p.get('category', p.get('product-type', '')),
                })
            except Exception:
                continue

        return normalized

    def _save_products_to_db(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """حفظ المنتجات في قاعدة البيانات"""
        db = SessionLocal()
        try:
            # Get or create seller
            seller = db.query(Seller).first()
            seller_id = seller.id if seller else None

            synced_count = 0
            updated_count = 0
            skipped_count = 0

            for product_data in products:
                sku = product_data.get('sku')
                if not sku:
                    skipped_count += 1
                    continue

                # Check if product already exists
                existing = db.query(Product).filter(Product.sku == sku).first()

                if existing:
                    # Update existing product
                    existing.name = product_data.get('title', existing.name)
                    existing.price = float(product_data.get('price', 0) or 0)
                    existing.quantity = int(product_data.get('quantity', 0) or 0)
                    existing.status = 'published'
                    existing.updated_at = datetime.utcnow()

                    # Update Amazon-specific fields
                    if product_data.get('asin'):
                        existing.asin = product_data['asin']
                    if product_data.get('brand'):
                        existing.brand = product_data['brand']
                    if product_data.get('category'):
                        existing.category = product_data['category']

                    updated_count += 1
                else:
                    # Create new product
                    product = Product(
                        seller_id=seller_id,
                        sku=sku,
                        name=product_data.get('title', sku),
                        price=float(product_data.get('price', 0) or 0),
                        quantity=int(product_data.get('quantity', 0) or 0),
                        status='published',
                        asin=product_data.get('asin', ''),
                        brand=product_data.get('brand', ''),
                        category=product_data.get('category', ''),
                    )
                    db.add(product)
                    synced_count += 1

            db.commit()

            # Update last sync time
            if seller:
                seller.last_sync_at = datetime.now(timezone.utc)
                db.commit()

            total = synced_count + updated_count

            logger.info(f"Sync complete: {synced_count} new, {updated_count} updated, {total} total")

            return {
                "success": True,
                "synced": synced_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "total": total,
                "message": f"تم استيراد {total} منتج ({synced_count} جديد، {updated_count} محدث)",
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save products: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "synced": 0,
                "total": 0,
            }
        finally:
            db.close()


def get_active_session():
    """يجيب الـ Session النشطة من الـ Database"""
    db = SessionLocal()
    try:
        session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
            AuthSession.is_valid == True,
        ).first()

        if not session or not session.cookies_json:
            return None, None

        cookies = json.loads(decrypt_data(session.cookies_json))
        country = session.country_code or "eg"

        logger.info(f"Retrieved session for sync (country: {country}, cookies: {len(cookies)})")
        return cookies, country

    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        return None, None
    finally:
        db.close()
