"""
User model with tenant association and authentication
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid

class User(BaseModel):
    """User model with tenant_id for multi-tenancy"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashed_password: str
    role: str = "user"  # "user" | "admin" | "qa_reviewer"
    tenant_id: str  # Links user to tenant
    company_name: Optional[str] = None  # Display name for tenant
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    """Schema for creating a new user (admin-only)"""
    email: EmailStr
    password: str
    role: str = "user"
    company_name: Optional[str] = None
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
    role: str
    company_name: Optional[str] = None

class UserResponse(BaseModel):
    """User response (without password)"""
    id: str
    email: EmailStr
    role: str
    tenant_id: str
    company_name: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

