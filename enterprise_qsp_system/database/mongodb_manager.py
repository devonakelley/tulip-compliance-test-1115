"""
MongoDB manager for Enterprise QSP Compliance System
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import uuid

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from ..config import settings

logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB connection and operations manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.sync_client: Optional[MongoClient] = None
        self.sync_database = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize MongoDB connections"""
        if self._initialized:
            logger.info("MongoDB already initialized")
            return
            
        try:
            # Get MongoDB URL from environment
            mongo_url = settings.MONGO_URL
            db_name = getattr(settings, 'DB_NAME', 'qsp_enterprise')
            
            # Create async client
            self.client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=settings.DATABASE_POOL_SIZE
            )
            
            # Get database
            self.database = self.client[db_name]
            
            # Create sync client for admin operations
            self.sync_client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            self.sync_database = self.sync_client[db_name]
            
            # Test connection
            await self._test_connection()
            
            # Initialize collections and indexes
            await self._initialize_collections()
            
            self._initialized = True
            logger.info(f"MongoDB initialized successfully - Database: {db_name}")
            
        except Exception as e:
            logger.error(f"MongoDB initialization failed: {e}")
            raise
    
    async def _test_connection(self):
        """Test MongoDB connectivity"""
        try:
            # Ping the database
            await self.client.admin.command('ping')
            logger.info("MongoDB connection test successful")
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")
            raise
    
    async def _initialize_collections(self):
        """Initialize collections and create indexes"""
        try:
            # Collections to create
            collections = [
                'users', 'user_sessions', 'documents', 'document_sections',
                'regulatory_frameworks', 'regulatory_changes', 'compliance_analyses',
                'clause_mappings', 'compliance_gaps', 'system_configurations',
                'audit_logs', 'background_tasks', 'system_metrics'
            ]
            
            # Create collections if they don't exist
            existing_collections = await self.database.list_collection_names()
            
            for collection_name in collections:
                if collection_name not in existing_collections:
                    await self.database.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")
            
            # Create indexes
            await self._create_indexes()
            
            # Initialize system configuration
            await self._initialize_system_config()
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Users
            await self.database.users.create_index("username", unique=True)
            await self.database.users.create_index("email", unique=True)
            
            # Documents
            await self.database.documents.create_index([("user_id", 1), ("document_type", 1)])
            await self.database.documents.create_index("file_hash")
            await self.database.documents.create_index("processing_status")
            
            # Document sections
            await self.database.document_sections.create_index([("document_id", 1), ("section_order", 1)])
            
            # Compliance analyses
            await self.database.compliance_analyses.create_index([("user_id", 1), ("status", 1)])
            await self.database.compliance_analyses.create_index("started_at")
            
            # Clause mappings
            await self.database.clause_mappings.create_index([("document_id", 1), ("clause_id", 1)])
            await self.database.clause_mappings.create_index("confidence_score")
            
            # Regulatory changes
            await self.database.regulatory_changes.create_index([("framework_id", 1), ("clause_id", 1)])
            await self.database.regulatory_changes.create_index("effective_date")
            
            # Audit logs
            await self.database.audit_logs.create_index([("user_id", 1), ("action", 1)])
            await self.database.audit_logs.create_index("timestamp")
            
            # System metrics
            await self.database.system_metrics.create_index([("metric_name", 1), ("timestamp", 1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")
    
    async def _initialize_system_config(self):
        """Initialize default system configuration"""
        try:
            # Check if config exists
            config_count = await self.database.system_configurations.count_documents({})
            
            if config_count == 0:
                # Insert default configurations
                default_configs = [
                    {
                        "key": "system.version",
                        "value": {"version": settings.VERSION},
                        "description": "System version",
                        "category": "system",
                        "is_sensitive": False,
                        "created_date": datetime.now(timezone.utc),
                        "last_modified": datetime.now(timezone.utc)
                    },
                    {
                        "key": "analysis.default_model",
                        "value": {"model": settings.DEFAULT_LLM_MODEL},
                        "description": "Default LLM model for analysis",
                        "category": "analysis",
                        "is_sensitive": False,
                        "created_date": datetime.now(timezone.utc),
                        "last_modified": datetime.now(timezone.utc)
                    },
                    {
                        "key": "compliance.frameworks",
                        "value": {"frameworks": settings.SUPPORTED_FRAMEWORKS},
                        "description": "Supported regulatory frameworks",
                        "category": "compliance", 
                        "is_sensitive": False,
                        "created_date": datetime.now(timezone.utc),
                        "last_modified": datetime.now(timezone.utc)
                    }
                ]
                
                await self.database.system_configurations.insert_many(default_configs)
                logger.info("Default system configuration initialized")
                
        except Exception as e:
            logger.warning(f"Failed to initialize system config: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
        """Get MongoDB database session"""
        if not self._initialized:
            await self.initialize()
            
        try:
            yield self.database
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
    
    def get_sync_session(self):
        """Get synchronous MongoDB database"""
        if not self._initialized or not self.sync_database:
            raise RuntimeError("MongoDB not initialized")
        return self.sync_database
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB health"""
        try:
            if not self._initialized:
                return {"status": "not_initialized"}
            
            start_time = asyncio.get_event_loop().time()
            
            # Ping database
            await self.client.admin.command('ping')
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Get server status
            server_status = await self.client.admin.command("serverStatus")
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connections": {
                    "current": server_status.get("connections", {}).get("current", 0),
                    "available": server_status.get("connections", {}).get("available", 0)
                },
                "version": server_status.get("version", "unknown")
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get MongoDB statistics"""
        try:
            if not self._initialized:
                return {}
            
            stats = {}
            
            # Document counts
            stats["total_documents"] = await self.database.documents.count_documents({})
            
            # Analysis counts
            stats["total_analyses"] = await self.database.compliance_analyses.count_documents({})
            
            # Active users
            stats["active_users"] = await self.database.users.count_documents({"is_active": True})
            
            # Recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            stats["analyses_last_24h"] = await self.database.compliance_analyses.count_documents({
                "started_at": {"$gte": yesterday}
            })
            
            # Database stats
            db_stats = await self.database.command("dbStats")
            stats["database_size_mb"] = round(db_stats.get("dataSize", 0) / 1024 / 1024, 2)
            stats["index_size_mb"] = round(db_stats.get("indexSize", 0) / 1024 / 1024, 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get MongoDB stats: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup MongoDB connections"""
        try:
            if self.client:
                self.client.close()
                
            if self.sync_client:
                self.sync_client.close()
                
            self._initialized = False
            logger.info("MongoDB connections cleaned up")
            
        except Exception as e:
            logger.error(f"MongoDB cleanup failed: {e}")
    
    async def backup_database(self, backup_path: str = None) -> str:
        """Create MongoDB backup using mongodump"""
        import subprocess
        import os
        from datetime import datetime
        
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"/app/backups/qsp_backup_{timestamp}"
            
            # Ensure backup directory exists
            os.makedirs(backup_path, exist_ok=True)
            
            # Extract MongoDB URI components
            mongo_url = settings.MONGO_URL
            db_name = getattr(settings, 'DB_NAME', 'qsp_enterprise')
            
            # Run mongodump
            result = subprocess.run([
                "mongodump",
                "--uri", mongo_url,
                "--db", db_name,
                "--out", backup_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"MongoDB backup created: {backup_path}")
                return backup_path
            else:
                raise Exception(f"mongodump failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"MongoDB backup failed: {e}")
            raise
    
    async def execute_maintenance(self):
        """Execute routine MongoDB maintenance"""
        try:
            # Clean old audit logs (older than 90 days)
            cutoff_90_days = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_90_days = cutoff_90_days.replace(day=cutoff_90_days.day - 90)
            
            result = await self.database.audit_logs.delete_many({
                "timestamp": {"$lt": cutoff_90_days}
            })
            logger.info(f"Cleaned {result.deleted_count} old audit logs")
            
            # Clean old background tasks (completed/failed older than 7 days)
            cutoff_7_days = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_7_days = cutoff_7_days.replace(day=cutoff_7_days.day - 7)
            
            result = await self.database.background_tasks.delete_many({
                "status": {"$in": ["completed", "failed"]},
                "completed_at": {"$lt": cutoff_7_days}
            })
            logger.info(f"Cleaned {result.deleted_count} old background tasks")
            
            # Clean old system metrics (older than 30 days)
            cutoff_30_days = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_30_days = cutoff_30_days.replace(day=cutoff_30_days.day - 30)
            
            result = await self.database.system_metrics.delete_many({
                "timestamp": {"$lt": cutoff_30_days}
            })
            logger.info(f"Cleaned {result.deleted_count} old system metrics")
            
            logger.info("MongoDB maintenance completed")
            
        except Exception as e:
            logger.error(f"MongoDB maintenance failed: {e}")
            raise

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()

# Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """FastAPI dependency for MongoDB database session"""
    async with mongodb_manager.get_session() as db:
        yield db