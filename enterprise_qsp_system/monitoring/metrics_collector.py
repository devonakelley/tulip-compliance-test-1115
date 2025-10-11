"""
Metrics collection system for Enterprise QSP System
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from collections import defaultdict, deque
import time

logger = logging.getLogger(__name__)

class MetricsCollector:
    """System metrics collection and reporting"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        
        # Keep metrics for 24 hours
        self.retention_seconds = 24 * 3600
        self._initialized = False
        
    async def initialize(self):
        """Initialize metrics collector"""
        if self._initialized:
            return
            
        try:
            # Start metrics collection task
            asyncio.create_task(self._collection_task())
            self._initialized = True
            logger.info("Metrics collector initialized")
            
        except Exception as e:
            logger.error(f"Metrics collector initialization failed: {e}")
            raise
    
    def increment(self, metric_name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        try:
            full_name = self._build_metric_name(metric_name, tags)
            self.counters[full_name] += value
        except Exception as e:
            logger.error(f"Error incrementing metric {metric_name}: {e}")
    
    def set_gauge(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        try:
            full_name = self._build_metric_name(metric_name, tags)
            self.gauges[full_name] = value
            
            # Also store in time series
            timestamp = time.time()
            self.metrics[full_name].append((timestamp, value))
            
        except Exception as e:
            logger.error(f"Error setting gauge {metric_name}: {e}")
    
    def record_histogram(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        try:
            full_name = self._build_metric_name(metric_name, tags)
            self.histograms[full_name].append(value)
            
            # Keep only recent values (last 1000)
            if len(self.histograms[full_name]) > 1000:
                self.histograms[full_name] = self.histograms[full_name][-1000:]
                
        except Exception as e:
            logger.error(f"Error recording histogram {metric_name}: {e}")
    
    def record_timing(self, metric_name: str, duration_seconds: float, tags: Dict[str, str] = None):
        """Record a timing metric"""
        self.record_histogram(f"{metric_name}.duration", duration_seconds, tags)
    
    async def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        try:
            metrics = []
            
            # Counters
            metrics.append("# Counters")
            for metric_name, value in self.counters.items():
                metrics.append(f"# TYPE {metric_name} counter")
                metrics.append(f"{metric_name} {value}")
            
            # Gauges  
            metrics.append("\n# Gauges")
            for metric_name, value in self.gauges.items():
                metrics.append(f"# TYPE {metric_name} gauge")
                metrics.append(f"{metric_name} {value}")
            
            # Histograms
            metrics.append("\n# Histograms")
            for metric_name, values in self.histograms.items():
                if values:
                    metrics.append(f"# TYPE {metric_name} histogram")
                    metrics.append(f"{metric_name}_count {len(values)}")
                    metrics.append(f"{metric_name}_sum {sum(values)}")
                    
                    # Calculate percentiles
                    sorted_values = sorted(values)
                    count = len(sorted_values)
                    
                    if count > 0:
                        p50 = sorted_values[int(count * 0.5)]
                        p95 = sorted_values[int(count * 0.95)]
                        p99 = sorted_values[int(count * 0.99)]
                        
                        metrics.append(f"{metric_name}_p50 {p50}")
                        metrics.append(f"{metric_name}_p95 {p95}")
                        metrics.append(f"{metric_name}_p99 {p99}")
            
            # System metrics
            await self._collect_system_metrics()
            
            return "\n".join(metrics)
            
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            return "# Error generating metrics"
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            summary = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {}
            }
            
            # Summarize histograms
            for metric_name, values in self.histograms.items():
                if values:
                    summary["histograms"][metric_name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values)
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    def timer(self, metric_name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations"""
        return MetricTimer(self, metric_name, tags)
    
    async def _collection_task(self):
        """Background task to collect system metrics"""
        while self._initialized:
            try:
                await self._collect_system_metrics()
                
                # Clean old metrics
                self._cleanup_old_metrics()
                
                # Sleep for 60 seconds
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection task error: {e}")
                await asyncio.sleep(30)
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # Memory metrics
            try:
                import psutil
                memory = psutil.virtual_memory()
                self.set_gauge("system.memory.usage_percent", memory.percent)
                self.set_gauge("system.memory.available_mb", memory.available / 1024 / 1024)
                
                # CPU metrics
                cpu_percent = psutil.cpu_percent()
                self.set_gauge("system.cpu.usage_percent", cpu_percent)
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.set_gauge("system.disk.usage_percent", disk_percent)
                
            except ImportError:
                pass  # psutil not available
            
            # Application metrics
            from ..database import mongodb_manager
            
            if mongodb_manager._initialized:
                db_stats = await mongodb_manager.get_stats()
                
                for stat_name, value in db_stats.items():
                    if isinstance(value, (int, float)):
                        self.set_gauge(f"database.{stat_name}", value)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _build_metric_name(self, metric_name: str, tags: Dict[str, str] = None) -> str:
        """Build full metric name with tags"""
        if not tags:
            return metric_name
            
        tag_string = ",".join(f"{key}={value}" for key, value in sorted(tags.items()))
        return f"{metric_name}{{{tag_string}}}"
    
    def _cleanup_old_metrics(self):
        """Remove old metric data points"""
        try:
            cutoff_time = time.time() - self.retention_seconds
            
            for metric_name, data_points in self.metrics.items():
                while data_points and data_points[0][0] < cutoff_time:
                    data_points.popleft()
                    
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

class MetricTimer:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, tags: Dict[str, str] = None):
        self.collector = collector
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_timing(self.metric_name, duration, self.tags)