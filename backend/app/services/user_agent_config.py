"""
Amazon User-Agent Configuration (Centralized)

This ensures ALL modules (Playwright, niquests, requests) use the EXACT SAME User-Agent.
Mismatched User-Agents will cause Amazon WAF to reject sessions.
"""

# =============================================
# Centralized User-Agent (MUST match everywhere)
# =============================================
AMAZON_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# =============================================
# Browser Headers Template (for niquests/requests)
# =============================================
BROWSER_HEADERS_TEMPLATE = {
    "User-Agent": AMAZON_USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def get_browser_headers(origin: str, referer: str) -> dict:
    """
    Get browser headers with dynamic Origin and Referer.

    Args:
        origin: e.g. "https://sellercentral.amazon.eg"
        referer: e.g. "https://sellercentral.amazon.eg/hz/merchant-listings/add-product.html"

    Returns:
        Headers dict ready for niquests/requests
    """
    headers = BROWSER_HEADERS_TEMPLATE.copy()
    headers["Origin"] = origin
    headers["Referer"] = referer
    return headers
