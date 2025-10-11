"""
Metrics collection middleware for Enterprise QSP System
"""

import time
import logging
from typing import Dict, Any
from collections import defaultdict, Counter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Metrics collection middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Metrics storage
        self.request_count = Counter()
        self.response_times = defaultdict(list)
        self.status_codes = Counter()
        self.endpoints = Counter()
        
        # Error tracking
        self.errors = defaultdict(int)
        
        # Start time for uptime calculation
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and collect metrics"""
        
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        # Count request
        self.request_count[f"{method} {path}"] += 1
        self.endpoints[path] += 1
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record metrics
            self.response_times[path].append(response_time)
            self.status_codes[response.status_code] += 1
            
            # Keep only recent response times (last 1000 per endpoint)
            if len(self.response_times[path]) > 1000:
                self.response_times[path] = self.response_times[path][-1000:]
            
            return response
            
        except Exception as e:
            # Record error
            error_type = type(e).__name__
            self.errors[f"{path}:{error_type}"] += 1
            self.status_codes[500] += 1
            
            response_time = time.time() - start_time
            self.response_times[path].append(response_time)
            
            logger.error(f"Request error on {method} {path}: {e}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        
        # Calculate response time statistics
        avg_response_times = {}
        for endpoint, times in self.response_times.items():
            if times:
                avg_response_times[endpoint] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
        
        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime_seconds,
            "total_requests": sum(self.request_count.values()),
            "requests_by_endpoint": dict(self.request_count),
            "status_codes": dict(self.status_codes),
            "avg_response_times": avg_response_times,
            "errors": dict(self.errors),
            "top_endpoints": dict(self.endpoints.most_common(10))
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        
        metrics = []
        
        # Request counter
        metrics.append("# HELP http_requests_total Total HTTP requests")
        metrics.append("# TYPE http_requests_total counter")
        for endpoint, count in self.request_count.items():
            method, path = endpoint.split(" ", 1)
            metrics.append(f'http_requests_total{{method="{method}",path="{path}"}} {count}')
        
        # Response time histogram
        metrics.append("# HELP http_request_duration_seconds HTTP request duration")
        metrics.append("# TYPE http_request_duration_seconds histogram")
        for endpoint, times in self.response_times.items():
            if times:
                avg_time = sum(times) / len(times)
                metrics.append(f'http_request_duration_seconds{{path="{endpoint}"}} {avg_time}')
        
        # Status codes
        metrics.append("# HELP http_responses_total Total HTTP responses by status code")
        metrics.append("# TYPE http_responses_total counter")
        for status_code, count in self.status_codes.items():
            metrics.append(f'http_responses_total{{status_code="{status_code}"}} {count}')
        
        # Errors
        metrics.append("# HELP http_errors_total Total HTTP errors")
        metrics.append("# TYPE http_errors_total counter")
        for error, count in self.errors.items():
            endpoint, error_type = error.split(":", 1)
            metrics.append(f'http_errors_total{{endpoint="{endpoint}",error_type="{error_type}"}} {count}')
        
        # Uptime
        uptime = time.time() - self.start_time
        metrics.append("# HELP system_uptime_seconds System uptime in seconds")
        metrics.append("# TYPE system_uptime_seconds gauge")
        metrics.append(f"system_uptime_seconds {uptime}")
        
        return "\n".join(metrics)