"""
Authentication API endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from models.user import User, UserCreate, UserLogin, Token
from models.tenant import Tenant, TenantCreate
from core.auth import auth_service, get_current_user
from core.audit_logger import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# This will be injected from main server
db: AsyncIOMotorDatabase = None

def set_database(database):
    """Set database instance"""
    global db
    db = database

@router.post("/register", response_model=Token)
async def register(user_create: UserCreate):
    """
    Register a new user
    Requires a valid tenant_id
    """
    try:
        # Check if tenant exists
        tenant = await db.tenants.find_one({"id": user_create.tenant_id})
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_create.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            email=user_create.email,
            password_hash=auth_service.hash_password(user_create.password),
            tenant_id=user_create.tenant_id,
            full_name=user_create.full_name
        )
        
        # Save to database
        user_dict = user.model_dump()
        await db.users.insert_one(user_dict)
        
        # Create access token
        token = auth_service.create_access_token(
            data={
                "user_id": user.id,
                "tenant_id": user.tenant_id,
                "email": user.email
            }
        )
        
        logger.info(f"User registered: {user.email} (tenant: {user.tenant_id})")
        
        return Token(
            access_token=token,
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with email and password
    Returns JWT token with user_id and tenant_id
    """
    try:
        # Find user by email
        user_data = await db.users.find_one({"email": credentials.email})
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = User(**user_data)
        
        # Verify password
        if not auth_service.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Update last login
        await db.users.update_one(
            {"id": user.id},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create access token
        token = auth_service.create_access_token(
            data={
                "user_id": user.id,
                "tenant_id": user.tenant_id,
                "email": user.email
            }
        )
        
        logger.info(f"User logged in: {user.email} (tenant: {user.tenant_id})")
        
        # Log audit event
        await audit_logger.log_login(
            tenant_id=user.tenant_id,
            user_id=user.id,
            email=user.email
        )
        
        return Token(
            access_token=token,
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information from JWT token
    """
    try:
        user_data = await db.users.find_one({"id": current_user["user_id"]})
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Don't return password hash
        user_data.pop("password_hash", None)
        user_data.pop("_id", None)
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user info"
        )

@router.post("/tenant/create", response_model=Tenant)
async def create_tenant(tenant_create: TenantCreate):
    """
    Create a new tenant
    (In production, this would be admin-only)
    """
    try:
        tenant = Tenant(
            name=tenant_create.name,
            plan=tenant_create.plan
        )
        
        tenant_dict = tenant.model_dump()
        await db.tenants.insert_one(tenant_dict)
        
        logger.info(f"Tenant created: {tenant.name} ({tenant.id})")
        
        return tenant
        
    except Exception as e:
        logger.error(f"Tenant creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant"
        )
