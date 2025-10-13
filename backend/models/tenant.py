"""
Tenant model for multi-tenant isolation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class Tenant(BaseModel):
    """Tenant model for multi-tenant system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    plan: str = "free"  # free, pro, enterprise
    storage_limit_mb: int = 1000  # Default 1GB
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
class TenantCreate(BaseModel):
    """Schema for creating a new tenant"""
    name: str
    plan: str = "free"
