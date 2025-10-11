"""
Configuration management for Enterprise QSP Compliance System
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    APP_NAME: str = "Enterprise QSP Compliance System"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database settings
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "qsp_enterprise")
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Redis/Cache settings
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 1 hour
    
    # Authentication settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_DAYS: int = 7
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # File processing
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = [".docx", ".txt", ".pdf", ".xlsx"]
    UPLOAD_DIRECTORY: str = "/app/uploads"
    PROCESSED_DIRECTORY: str = "/app/processed"
    
    # AI/LLM settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    EMERGENT_LLM_KEY: str = "sk-emergent-f33C62eB0958b4547F"
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    LLM_MAX_TOKENS: int = 4000
    LLM_TEMPERATURE: float = 0.1
    
    # Google Drive integration
    GOOGLE_CREDENTIALS_PATH: Optional[str] = None
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    SYNC_ENABLED: bool = False
    
    # Monitoring and metrics
    PROMETHEUS_METRICS_PORT: int = 9090
    HEALTH_CHECK_TIMEOUT: int = 10
    METRICS_RETENTION_DAYS: int = 30
    
    # Security
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    SECURE_COOKIES: bool = True
    SESSION_TIMEOUT_MINUTES: int = 480  # 8 hours
    
    # Processing settings
    MAX_CONCURRENT_ANALYSES: int = 5
    ANALYSIS_TIMEOUT_MINUTES: int = 30
    BACKGROUND_TASK_TIMEOUT: int = 1800  # 30 minutes
    
    # Regulatory frameworks
    SUPPORTED_FRAMEWORKS: List[str] = [
        "ISO_13485:2024",
        "ISO_14971:2019", 
        "ISO_62304:2006",
        "FDA_QSR",
        "EU_MDR"
    ]
    
    # Email notifications (optional)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    
    # Backup and archival
    BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 90
    ARCHIVE_OLD_ANALYSES: bool = True
    ARCHIVE_AFTER_DAYS: int = 365
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Ensure directories exist
        os.makedirs(self.UPLOAD_DIRECTORY, exist_ok=True)
        os.makedirs(self.PROCESSED_DIRECTORY, exist_ok=True)
        os.makedirs("/app/logs", exist_ok=True)
        os.makedirs("/app/backups", exist_ok=True)
        
    @property
    def database_url_async(self) -> str:
        """Get async database URL"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL
        
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return not self.DEBUG and os.getenv("ENVIRONMENT", "development").lower() == "production"
        
    def get_llm_config(self) -> dict:
        """Get LLM configuration based on available keys"""
        config = {
            "model": self.DEFAULT_LLM_MODEL,
            "max_tokens": self.LLM_MAX_TOKENS,
            "temperature": self.LLM_TEMPERATURE
        }
        
        if self.EMERGENT_LLM_KEY:
            config["api_key"] = self.EMERGENT_LLM_KEY
            config["provider"] = "emergent"
        elif self.OPENAI_API_KEY:
            config["api_key"] = self.OPENAI_API_KEY
            config["provider"] = "openai"
        elif self.ANTHROPIC_API_KEY:
            config["api_key"] = self.ANTHROPIC_API_KEY
            config["provider"] = "anthropic"
            config["model"] = "claude-3-sonnet-20240229"
        else:
            config["provider"] = None
            
        return config
    
    def get_cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        return ":".join(str(arg) for arg in args)

# Global settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    SECURE_COOKIES: bool = False
    
class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    SECURE_COOKIES: bool = True
    RATE_LIMIT_PER_MINUTE: int = 30  # More restrictive in production
    
class TestingSettings(Settings):
    """Testing environment settings"""
    DATABASE_URL: str = "sqlite:///./test_qsp.db"
    REDIS_URL: str = "redis://localhost:6379/1"  # Different Redis DB
    CACHE_TTL: int = 60  # Shorter cache for testing
    JWT_EXPIRATION_HOURS: int = 1  # Shorter expiration for testing

def get_settings() -> Settings:
    """Get settings based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()
