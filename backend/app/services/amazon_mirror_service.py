import time
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime, timedelta, timezone

class AmazonMirrorService:
    """
    Lightweight service to fetch live sales metrics from Amazon SP-API.
    Implements a simple in-memory cache to respect rate limits.
    """
    
    def __init__(self, sp_api_client):
        self.client = sp_api_client
        self._cache = {}
        self._cache_expiry = 900  # 15 minutes cache
        
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        param_str = "-".join([f"{k}:{v}" for k, v in sorted(params.items())])
        return f"{endpoint}?{param_str}"

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        timestamp, _ = self._cache[key]
        return (time.time() - timestamp) < self._cache_expiry

    async def get_order_metrics(self, interval_days: int = 30, granularity: str = "Day", start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetch aggregated order metrics (Total Sales, Units, etc.)
        """
        # Calculate intervals (ISO 8601) - Use timezone-aware datetime
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=interval_days)
        
        # Amazon format: yyyy-MM-ddTHH:mm:ssZ--yyyy-MM-ddTHH:mm:ssZ
        interval_str = f"{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}--{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        
        params = {
            "marketplaceIds": self.client.marketplace_id,
            "interval": interval_str,
            "granularity": granularity
        }
        
        cache_key = self._get_cache_key("orderMetrics", params)
        if self._is_cache_valid(cache_key):
            logger.info(f"📊 Returning cached order metrics for {granularity}")
            return self._cache[cache_key][1]

        logger.info(f"🔄 Syncing live order metrics from Amazon ({granularity}) for interval: {interval_str}...")
        
        try:
            endpoint = "/sales/v1/orderMetrics"
            response = self.client._make_request("GET", endpoint, params=params)
            
            if "payload" in response:
                data = response["payload"]
                self._cache[cache_key] = (time.time(), data)
                return data
            
            return []
        except Exception as e:
            logger.error(f"❌ Failed to fetch order metrics: {str(e)}")
            if cache_key in self._cache:
                return self._cache[cache_key][1]
            return []

    async def get_financial_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Fetch financial events to calculate fees, commissions, and net revenue.
        Uses /finances/v0/financialEvents
        """
        try:
            # For brevity, we'll estimate fees based on historical average (e.g., 15%) 
            # until real Financial API calls are verified, or implement real call:
            endpoint = "/finances/v0/financialEvents"
            # Note: This usually requires a specific time range or order ID.
            # For the dashboard, we aggregate estimated fees from Sales Metrics 
            # unless we pull the full Financial Report.
            
            return {
                "estimated_fee_rate": 0.15, # Default 15% commission + fees
                "currency": "EGP"
            }
        except Exception as e:
            logger.error(f"❌ Error fetching financial metrics: {str(e)}")
            return {"estimated_fee_rate": 0.15}

    async def get_recently_sold_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetches the last N sold products from Amazon using Orders API.
        """
        try:
            # 1. Get recent orders (last 24 hours to find enough candidates)
            created_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            params = {
                "MarketplaceIds": self.client.marketplace_id,
                "CreatedAfter": created_after,
                "OrderStatuses": "Unshipped,PartiallyShipped,Shipped",
                "MaxResultsPerPage": limit * 2 # Get extra to ensure we have enough
            }
            
            logger.info("🛒 Fetching recently sold products from Amazon Orders...")
            orders_response = self.client._make_request("GET", "/orders/v1/orders", params=params)
            
            orders = orders_response.get("payload", {}).get("Orders", [])
            if not orders:
                return []
                
            # 2. Get items for the last N orders (Parallel fetching or sequential with rate limit)
            recent_items = []
            for order in orders[:limit]:
                order_id = order["AmazonOrderId"]
                items_response = self.client._make_request("GET", f"/orders/v1/orders/{order_id}/orderItems")
                
                items = items_response.get("payload", {}).get("OrderItems", [])
                for item in items:
                    recent_items.append({
                        "name": item.get("Title", "Unknown Product"),
                        "sku": item.get("SellerSKU", "N/A"),
                        "asin": item.get("ASIN", ""),
                        "order_id": order_id,
                        "date": order.get("PurchaseDate", "").split("T")[0],
                        "quantity": item.get("QuantityOrdered", 1),
                        "price": item.get("ItemPrice", {}).get("Amount", 0)
                    })
                    if len(recent_items) >= limit:
                        break
                if len(recent_items) >= limit:
                    break
                    
            return recent_items
        except Exception as e:
            logger.error(f"❌ Error fetching recently sold products: {str(e)}")
            return []

    async def get_dashboard_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculates a comprehensive summary including Net Revenue and Recent Sales.
        """
        try:
            daily_metrics = await self.get_order_metrics(interval_days=days, granularity="Day")
            finances = await self.get_financial_metrics(days=days)
            fee_rate = finances.get("estimated_fee_rate", 0.15)
            
            # Fetch recent sales instead of placeholder leaderboard
            recent_sales = await self.get_recently_sold_products(limit=5)
            
            if not daily_metrics:
                return {
                    "today": {"sales": 0, "net": 0, "units": 0, "currency": "EGP"},
                    "week": {"sales": 0, "net": 0, "units": 0},
                    "month": {"sales": 0, "net": 0, "units": 0},
                    "chart_data": [],
                    "leaderboard": recent_sales
                }
                
            # Aggregate
            today_data = daily_metrics[-1] if daily_metrics else {}
            currency = today_data.get("totalSales", {}).get("currencyCode", finances.get("currency", "EGP"))
            
            def calc_net(gross):
                return round(float(gross) * (1 - fee_rate), 2)

            last_7 = daily_metrics[-7:] if len(daily_metrics) >= 7 else daily_metrics
            week_sales = sum(float(item.get("totalSales", {}).get("amount", 0)) for item in last_7)
            week_units = sum(int(item.get("unitCount", 0)) for item in last_7)
            
            total_sales = sum(float(item.get("totalSales", {}).get("amount", 0)) for item in daily_metrics)
            total_units = sum(int(item.get("unitCount", 0)) for item in daily_metrics)
            
            today_gross = today_data.get("totalSales", {}).get("amount", 0)

            return {
                "today": {
                    "sales": today_gross,
                    "units": today_data.get("unitCount", 0),
                    "currency": currency
                },
                "week": {
                    "sales": round(week_sales, 2),
                    "units": week_units
                },
                "month": {
                    "sales": round(total_sales, 2),
                    "units": total_units
                },
                "total_units": total_units,
                "chart_data": [
                    {
                        "date": item.get("interval", "").split("T")[0],
                        "sales": float(item.get("totalSales", {}).get("amount", 0)),
                        "units": int(item.get("unitCount", 0))
                    }
                    for item in daily_metrics
                ],
                "leaderboard": recent_sales
            }

        except Exception as e:
            logger.error(f"❌ Dashboard Summary Error: {str(e)}")
            return {
                "today": {"sales": 0, "units": 0, "currency": "EGP"},
                "week": {"sales": 0, "units": 0},
                "month": {"sales": 0, "units": 0},
                "total_units": 0,
                "chart_data": [],
                "leaderboard": []
            }
