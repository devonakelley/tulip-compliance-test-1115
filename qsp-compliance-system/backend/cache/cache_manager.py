"""
Cache manager for Enterprise QSP System
"""

import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import asyncio
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """In-memory cache manager with TTL support"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = 3600  # 1 hour
        self._initialized = False
        
    async def initialize(self):
        """Initialize cache manager"""
        if self._initialized:
            return
            
        try:
            # Start cleanup task
            asyncio.create_task(self._cleanup_task())
            self._initialized = True
            logger.info("Cache manager initialized")
            
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if datetime.now() > entry["expires_at"]:
                del self.cache[key]
                return None
            
            # Update access time
            entry["accessed_at"] = datetime.now()
            
            return entry["value"]
            
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            self.cache[key] = {
                "value": value,
                "created_at": datetime.now(),
                "accessed_at": datetime.now(),
                "expires_at": expires_at,
                "ttl": ttl
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        try:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
            
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and not expired
        """
        value = await self.get(key)
        return value is not None
    
    async def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            True if successful
        """
        try:
            self.cache.clear()
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def get_or_set(
        self,
        key: str,
        factory_func,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or set it using factory function
        
        Args:
            key: Cache key
            factory_func: Function to generate value if not cached
            ttl: Time to live in seconds
            
        Returns:
            Cached or generated value
        """
        try:
            # Try to get from cache first
            value = await self.get(key)
            if value is not None:
                return value
            
            # Generate new value
            if asyncio.iscoroutinefunction(factory_func):
                value = await factory_func()
            else:
                value = factory_func()
            
            # Cache the value
            await self.set(key, value, ttl)
            
            return value
            
        except Exception as e:
            logger.error(f"Cache get_or_set error for key '{key}': {e}")
            # Return generated value even if caching fails
            if asyncio.iscoroutinefunction(factory_func):
                return await factory_func()
            else:
                return factory_func()
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Generated cache key
        """
        try:
            # Create a string representation
            key_data = {
                "args": args,
                "kwargs": sorted(kwargs.items())
            }
            
            key_string = json.dumps(key_data, sort_keys=True)
            
            # Hash for consistent key length
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            
            return f"cache:{key_hash}"
            
        except Exception as e:
            logger.error(f"Key generation error: {e}")
            return f"cache:error:{hash(str(args) + str(kwargs))}"
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        try:
            total_entries = len(self.cache)
            
            # Count expired entries
            expired_count = 0
            now = datetime.now()
            
            for entry in self.cache.values():
                if now > entry["expires_at"]:
                    expired_count += 1
            
            # Calculate memory usage (approximate)
            memory_usage = sum(
                len(str(entry["value"])) + len(str(key))
                for key, entry in self.cache.items()
            )
            
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_count,
                "expired_entries": expired_count,
                "memory_usage_bytes": memory_usage,
                "hit_rate": getattr(self, "_hit_rate", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup cache resources"""
        try:
            self.cache.clear()
            self._initialized = False
            logger.info("Cache manager cleaned up")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_task(self):
        """Background task to cleanup expired entries"""
        while self._initialized:
            try:
                # Sleep for 5 minutes
                await asyncio.sleep(300)
                
                # Remove expired entries
                now = datetime.now()
                expired_keys = []
                
                for key, entry in self.cache.items():
                    if now > entry["expires_at"]:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup task error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying