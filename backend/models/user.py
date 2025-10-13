"""
User model with tenant association
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid

class User(BaseModel):
    """User model with tenant_id for multi-tenancy"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    tenant_id: str  # Links user to tenant
    full_name: Optional[str] = None
    is_active: bool = True
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    password: str
    tenant_id: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str
    email: str
