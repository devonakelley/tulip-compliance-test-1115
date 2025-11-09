"""
Authentication API endpoints
Register, login, logout, get current user
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import UserCreate, UserLogin, Token, UserResponse, User
from core.auth_utils import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    decode_access_token,
    validate_password_strength
)
from datetime import datetime, timezone
import logging
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Database will be injected
db = None

def set_db(database):
    """Set database instance"""
    global db
    db = database


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validate JWT token and return current user
    Used as dependency for protected routes
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Fetch user from database
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Verify current user is admin
    Used for admin-only routes
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Register a new user (admin-only)
    Creates user linked to admin's tenant
    """
    try:
        # Validate password strength
        is_valid, error_msg = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user linked to admin's tenant
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        new_user = {
            "id": user_id,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "role": user_data.role,
            "tenant_id": admin_user["tenant_id"],  # Same tenant as admin
            "company_name": user_data.company_name or admin_user.get("company_name"),
            "full_name": user_data.full_name,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None
        }
        
        await db.users.insert_one(new_user)
        logger.info(f"New user registered: {user_data.email} by admin {admin_user['email']}")
        
        # Return user without password
        return UserResponse(
            id=new_user["id"],
            email=new_user["email"],
            role=new_user["role"],
            tenant_id=new_user["tenant_id"],
            company_name=new_user.get("company_name"),
            full_name=new_user.get("full_name"),
            created_at=datetime.fromisoformat(new_user["created_at"]),
            last_login=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT token
    """
    try:
        # Find user by email
        user = await db.users.find_one({"email": credentials.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Verify password
        if not verify_password(credentials.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        
        # Update last login
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": user["id"],
                "email": user["email"],
                "tenant_id": user["tenant_id"],
                "role": user.get("role", "user")
            }
        )
        
        logger.info(f"User logged in: {credentials.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user["id"],
            tenant_id=user["tenant_id"],
            email=user["email"],
            role=user.get("role", "user"),
            company_name=user.get("company_name")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current logged-in user information
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user.get("role", "user"),
        tenant_id=current_user["tenant_id"],
        company_name=current_user.get("company_name"),
        full_name=current_user.get("full_name"),
        created_at=datetime.fromisoformat(current_user["created_at"]),
        last_login=datetime.fromisoformat(current_user["last_login"]) if current_user.get("last_login") else None
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client-side token removal)
    Server-side: Could blacklist token if needed
    """
    logger.info(f"User logged out: {current_user['email']}")
    return {"message": "Successfully logged out"}
