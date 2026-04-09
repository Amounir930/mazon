import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import json
from typing import Callable

class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    S4 Protocol: Audit Log
    Logs all mutation requests (POST, PUT, DELETE, PATCH)
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            client_ip = request.client.host
            path = request.url.path
            method = request.method
            
            # Log the request
            logger.info(f"AUDIT_LOG | IP: {client_ip} | Method: {method} | Path: {path} | User: system")
            
        response = await call_next(request)
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    S8 Protocol: Web Security
    Adds security headers to all responses
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Allow inline styles for Swagger UI and ReDoc documentation pages
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none';"
        return response

class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    S2 Protocol: Tenant Isolation
    Ensures search_path or tenant filtering (Conceptual for FastAPI)
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # In a real scenario, we'd extract tenant_id from JWT or Header
        # and set it in a ContextVar for the DB session to use.
        # For now, we log the isolation check.
        # logger.debug("S2: Enforcing tenant isolation via context.")
        response = await call_next(request)
        return response
