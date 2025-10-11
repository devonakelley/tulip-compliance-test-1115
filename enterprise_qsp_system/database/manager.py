"""
Database manager for Enterprise QSP Compliance System
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    async_sessionmaker
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from ..config import settings
from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.async_engine = None
        self.async_session_factory = None
        self.sync_engine = None
        self.sync_session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connections and create tables"""
        if self._initialized:
            logger.info("Database already initialized")
            return
            
        try:
            # Create async engine
            self.async_engine = create_async_engine(
                settings.database_url_async,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                pool_pre_ping=True,
                echo=settings.DEBUG,
                future=True
            )
            
            # Create sync engine for migrations and admin tasks
            self.sync_engine = create_engine(
                settings.DATABASE_URL,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_pre_ping=True,
                echo=settings.DEBUG
            )
            
            # Create session factories
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.sync_session_factory = sessionmaker(
                bind=self.sync_engine
            )
            
            # Test connection
            await self._test_connection()
            
            # Create tables if they don't exist
            await self._create_tables()
            
            # Initialize system configurations
            await self._initialize_system_config()
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _test_connection(self):
        """Test database connectivity"""
        try:
            async with self.async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        try:
            async with self.async_engine.begin() as conn:
                # Import models to register them
                from .models import Base
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def _initialize_system_config(self):
        """Initialize default system configuration"""
        try:
            from .models import SystemConfiguration
            
            async with self.get_session() as session:
                # Check if config exists
                result = await session.execute(
                    text("SELECT COUNT(*) FROM system_configurations")
                )
                count = result.scalar()
                
                if count == 0:
                    # Insert default configurations
                    default_configs = [
                        SystemConfiguration(
                            key="system.version",
                            value={"version": settings.VERSION},
                            description="System version",
                            category="system"
                        ),
                        SystemConfiguration(
                            key="analysis.default_model",
                            value={"model": settings.DEFAULT_LLM_MODEL},
                            description="Default LLM model for analysis",
                            category="analysis"
                        ),
                        SystemConfiguration(
                            key="compliance.frameworks",
                            value={"frameworks": settings.SUPPORTED_FRAMEWORKS},
                            description="Supported regulatory frameworks",
                            category="compliance"
                        )
                    ]
                    
                    for config in default_configs:
                        session.add(config)
                    
                    await session.commit()
                    logger.info("Default system configuration initialized")
                    
        except Exception as e:
            logger.warning(f"Failed to initialize system config: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        if not self._initialized:
            await self.initialize()
            
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_session(self):
        """Get synchronous database session"""
        if not self.sync_session_factory:
            raise RuntimeError("Database not initialized")
        return self.sync_session_factory()
    
    async def health_check(self) -> dict:
        """Check database health"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Get connection pool info
            pool_info = {
                "size": self.async_engine.pool.size(),
                "checked_in": self.async_engine.pool.checkedin(),
                "checked_out": self.async_engine.pool.checkedout(),
            }
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "pool_info": pool_info
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_stats(self) -> dict:
        """Get database statistics"""
        try:
            async with self.get_session() as session:
                stats = {}
                
                # Document counts
                result = await session.execute(text("SELECT COUNT(*) FROM documents"))
                stats["total_documents"] = result.scalar()
                
                # Analysis counts
                result = await session.execute(text("SELECT COUNT(*) FROM compliance_analyses"))
                stats["total_analyses"] = result.scalar()
                
                # Active users
                result = await session.execute(
                    text("SELECT COUNT(*) FROM users WHERE is_active = true")
                )
                stats["active_users"] = result.scalar()
                
                # Recent activity (last 24 hours)
                result = await session.execute(
                    text("""
                        SELECT COUNT(*) FROM compliance_analyses 
                        WHERE started_at > NOW() - INTERVAL '24 hours'
                    """)
                )
                stats["analyses_last_24h"] = result.scalar()
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup database connections"""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
                
            if self.sync_engine:
                self.sync_engine.dispose()
                
            self._initialized = False
            logger.info("Database connections cleaned up")
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
    
    async def backup_database(self, backup_path: str = None) -> str:
        """Create database backup"""
        import subprocess
        import os
        from datetime import datetime
        
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"/app/backups/qsp_backup_{timestamp}.sql"
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Extract connection info
            db_url = settings.DATABASE_URL
            # Parse connection string to get components
            # This is a simplified version - you might want to use urllib.parse
            
            # For now, use environment variables for pg_dump
            env = os.environ.copy()
            
            # Run pg_dump
            result = subprocess.run([
                "pg_dump",
                "--no-password",
                "--clean",
                "--create",
                "--file", backup_path,
                db_url.split('/')[-1]  # database name
            ], env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                return backup_path
            else:
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    async def execute_maintenance(self):
        """Execute routine database maintenance"""
        try:
            async with self.get_session() as session:
                # Clean old audit logs (older than 90 days)
                await session.execute(
                    text("""
                        DELETE FROM audit_logs 
                        WHERE timestamp < NOW() - INTERVAL '90 days'
                    """)
                )
                
                # Clean old background tasks (completed/failed older than 7 days)
                await session.execute(
                    text("""
                        DELETE FROM background_tasks 
                        WHERE status IN ('completed', 'failed') 
                        AND completed_at < NOW() - INTERVAL '7 days'
                    """)
                )
                
                # Clean old system metrics (older than 30 days)
                await session.execute(
                    text("""
                        DELETE FROM system_metrics 
                        WHERE timestamp < NOW() - INTERVAL '30 days'
                    """)
                )
                
                await session.commit()
                logger.info("Database maintenance completed")
                
        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            raise

# Global database manager instance
database_manager = DatabaseManager()

# Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    async with database_manager.get_session() as session:
        yield session
