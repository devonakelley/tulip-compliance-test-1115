"""
Rate limiting middleware for Enterprise QSP System
"""

import time
import logging
from typing import Dict, Any
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm"""
    
    def __init__(self, app, calls_per_minute: int = None, burst_limit: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.burst_limit = burst_limit or settings.RATE_LIMIT_BURST
        
        # Store request timestamps per client IP
        self.clients: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Store burst counts
        self.burst_counts: Dict[str, int] = defaultdict(int)
        
        # Last cleanup time
        self.last_cleanup = time.time()
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting"""
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Check if rate limited
        if self._is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for client: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.calls_per_minute} requests per minute allowed",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record the request
        self._record_request(client_ip)
        
        # Periodic cleanup
        self._cleanup_old_requests()
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited"""
        current_time = time.time()
        client_requests = self.clients[client_ip]
        
        # Remove requests older than 1 minute
        cutoff_time = current_time - 60
        while client_requests and client_requests[0] < cutoff_time:
            client_requests.popleft()
        
        # Check per-minute limit
        if len(client_requests) >= self.calls_per_minute:
            return True
        
        # Check burst limit (requests in last 10 seconds)
        burst_cutoff = current_time - 10
        burst_count = sum(1 for req_time in client_requests if req_time > burst_cutoff)
        
        if burst_count >= self.burst_limit:
            return True
        
        return False
    
    def _record_request(self, client_ip: str):
        """Record a request for the client"""
        current_time = time.time()
        self.clients[client_ip].append(current_time)
    
    def _cleanup_old_requests(self):
        """Periodic cleanup of old request records"""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self.last_cleanup < 300:
            return
        
        cutoff_time = current_time - 300  # Keep 5 minutes of history
        
        # Clean up old requests
        clients_to_remove = []
        for client_ip, requests in self.clients.items():
            # Remove old requests
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # Remove clients with no recent requests
            if not requests:
                clients_to_remove.append(client_ip)
        
        for client_ip in clients_to_remove:
            del self.clients[client_ip]
            if client_ip in self.burst_counts:
                del self.burst_counts[client_ip]
        
        self.last_cleanup = current_time
        logger.debug(f"Rate limiter cleanup completed. Active clients: {len(self.clients)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "active_clients": len(self.clients),
            "total_tracked_requests": sum(len(requests) for requests in self.clients.values()),
            "calls_per_minute_limit": self.calls_per_minute,
            "burst_limit": self.burst_limit
        }