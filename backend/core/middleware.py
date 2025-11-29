"""
Middleware for request logging, timing, and security
"""
import time
import logging
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests with timing information
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]

        # Get client IP (handle proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host

        # Log request start
        start_time = time.time()

        # Skip logging for health check endpoints
        skip_paths = ["/health", "/ready", "/metrics", "/favicon.ico"]
        should_log = request.url.path not in skip_paths

        if should_log:
            logger.info(
                f"[{request_id}] --> {request.method} {request.url.path} "
                f"from {client_ip}"
            )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            if should_log:
                # Log response with timing
                log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
                logger.log(
                    log_level,
                    f"[{request_id}] <-- {response.status_code} "
                    f"{request.method} {request.url.path} "
                    f"({duration_ms:.1f}ms)"
                )

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] !!! {request.method} {request.url.path} "
                f"ERROR: {str(e)} ({duration_ms:.1f}ms)"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only set HSTS in production (when not localhost)
        if "localhost" not in str(request.url) and "127.0.0.1" not in str(request.url):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
