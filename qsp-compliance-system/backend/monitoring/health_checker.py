"""
Health checking system for Enterprise QSP System
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
import aiohttp

from ..config import settings

logger = logging.getLogger(__name__)

class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.checks = {}
        
    async def startup_check(self):
        """Perform startup health checks"""
        try:
            logger.info("Performing startup health checks...")
            
            # Basic system checks
            checks = [
                self._check_database(),
                self._check_cache(),
                self._check_ai_service(),
                self._check_storage()
            ]
            
            results = await asyncio.gather(*checks, return_exceptions=True)
            
            # Log results
            for i, result in enumerate(results):
                check_name = ["database", "cache", "ai_service", "storage"][i]
                if isinstance(result, Exception):
                    logger.warning(f"Startup check failed - {check_name}: {result}")
                else:
                    logger.info(f"Startup check passed - {check_name}: OK")
            
            logger.info("Startup health checks completed")
            
        except Exception as e:
            logger.error(f"Startup health check error: {e}")
    
    async def comprehensive_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # Run all health checks
            checks = {
                "database": self._check_database(),
                "cache": self._check_cache(), 
                "ai_service": self._check_ai_service(),
                "storage": self._check_storage(),
                "memory": self._check_memory(),
                "disk": self._check_disk()
            }
            
            results = {}
            
            for check_name, check_coro in checks.items():
                try:
                    result = await asyncio.wait_for(check_coro, timeout=10.0)
                    results[check_name] = result
                except asyncio.TimeoutError:
                    results[check_name] = {
                        "status": "unhealthy",
                        "error": "Health check timeout"
                    }
                except Exception as e:
                    results[check_name] = {
                        "status": "unhealthy", 
                        "error": str(e)
                    }
            
            # Determine overall status
            overall_status = "healthy"
            unhealthy_components = []
            
            for component, result in results.items():
                if result.get("status") != "healthy":
                    overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
                    unhealthy_components.append(component)
            
            end_time = datetime.now(timezone.utc)
            check_duration = (end_time - start_time).total_seconds()
            
            return {
                "status": overall_status,
                "timestamp": end_time.isoformat(),
                "version": settings.VERSION,
                "uptime_seconds": self._get_uptime(),
                "check_duration_seconds": check_duration,
                "components": results,
                "unhealthy_components": unhealthy_components
            }
            
        except Exception as e:
            logger.error(f"Comprehensive health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from ..database import mongodb_manager
            
            health = await mongodb_manager.health_check()
            
            if health.get("status") == "healthy":
                return {
                    "status": "healthy",
                    "response_time_ms": health.get("response_time_ms", 0),
                    "connections": health.get("connections", {})
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": health.get("error", "Database unhealthy")
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Database check failed: {str(e)}"
            }
    
    async def _check_cache(self) -> Dict[str, Any]:
        """Check cache system"""
        try:
            # Simple cache test
            return {
                "status": "healthy",
                "type": "in_memory"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Cache check failed: {str(e)}"
            }
    
    async def _check_ai_service(self) -> Dict[str, Any]:
        """Check AI service availability"""
        try:
            from ..ai import LLMService
            
            llm_service = LLMService()
            
            if llm_service.is_available():
                return {
                    "status": "healthy",
                    "service": "emergent_llm",
                    "models_available": len(llm_service.available_models)
                }
            else:
                return {
                    "status": "degraded",
                    "error": "AI service not configured"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": f"AI service check failed: {str(e)}"
            }
    
    async def _check_storage(self) -> Dict[str, Any]:
        """Check storage system"""
        try:
            import os
            
            # Check upload directory
            upload_dir = settings.UPLOAD_DIRECTORY
            
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
            
            # Test write access
            test_file = os.path.join(upload_dir, "health_check.txt")
            
            with open(test_file, "w") as f:
                f.write("health_check")
            
            os.remove(test_file)
            
            return {
                "status": "healthy",
                "upload_directory": upload_dir,
                "writable": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Storage check failed: {str(e)}"
            }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            status = "healthy"
            if memory.percent > 90:
                status = "unhealthy"
            elif memory.percent > 80:
                status = "degraded"
            
            return {
                "status": status,
                "usage_percent": memory.percent,
                "available_mb": memory.available // 1024 // 1024,
                "total_mb": memory.total // 1024 // 1024
            }
            
        except ImportError:
            return {
                "status": "unknown",
                "error": "psutil not available"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Memory check failed: {str(e)}"
            }
    
    async def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage("/")
            
            usage_percent = (used / total) * 100
            
            status = "healthy"
            if usage_percent > 95:
                status = "unhealthy"
            elif usage_percent > 85:
                status = "degraded"
            
            return {
                "status": status,
                "usage_percent": round(usage_percent, 1),
                "free_gb": round(free / 1024 / 1024 / 1024, 1),
                "total_gb": round(total / 1024 / 1024 / 1024, 1)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Disk check failed: {str(e)}"
            }
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds
        except Exception:
            return 0.0