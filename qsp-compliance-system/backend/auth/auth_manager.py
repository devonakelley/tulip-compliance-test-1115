"""
Authentication manager for Enterprise QSP System
"""

import jwt
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
import uuid

from ..config import settings
from ..database.models import User, UserSession

logger = logging.getLogger(__name__)

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate user and return JWT token
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            JWT token if successful, None otherwise
        """
        try:
            # For now, create a simple demo user authentication
            # In production, this would check against the database
            
            if username == "admin" and password == "admin":
                # Create JWT token
                payload = {
                    "user_id": str(uuid.uuid4()),
                    "username": username,
                    "email": "admin@example.com", 
                    "role": "admin",
                    "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
                    "iat": datetime.now(timezone.utc)
                }
                
                token = jwt.encode(
                    payload,
                    settings.JWT_SECRET_KEY,
                    algorithm=settings.JWT_ALGORITHM
                )
                
                logger.info(f"User authenticated: {username}")
                return token
            
            # If no match, return None
            logger.warning(f"Authentication failed for user: {username}")
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return user info
        
        Args:
            token: JWT token
            
        Returns:
            User info if valid, None otherwise
        """
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check expiration
            exp_timestamp = payload.get("exp")
            if exp_timestamp and datetime.now(timezone.utc).timestamp() > exp_timestamp:
                logger.warning("Token expired")
                return None
            
            # Return user info
            user_info = {
                "id": payload.get("user_id"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "role": payload.get("role", "user")
            }
            
            return user_info
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    async def refresh_token(self, user_id: str) -> str:
        """
        Generate new JWT token for user
        
        Args:
            user_id: User ID
            
        Returns:
            New JWT token
        """
        try:
            # For demo purposes, create new token
            payload = {
                "user_id": user_id,
                "username": "admin",  # In production, fetch from database
                "email": "admin@example.com",
                "role": "admin",
                "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
                "iat": datetime.now(timezone.utc)
            }
            
            token = jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            logger.info(f"Token refreshed for user: {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    async def create_user(self, username: str, email: str, password: str, role: str = "user") -> str:
        """
        Create new user (placeholder - would use database in production)
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            role: User role
            
        Returns:
            User ID
        """
        try:
            # Hash password
            password_hash = self.hash_password(password)
            
            # In production, save to database
            user_id = str(uuid.uuid4())
            
            logger.info(f"User created: {username} ({email})")
            return user_id
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            raise
    
    async def check_permissions(self, user: Dict[str, Any], required_permission: str) -> bool:
        """
        Check if user has required permission
        
        Args:
            user: User info
            required_permission: Required permission
            
        Returns:
            True if user has permission
        """
        try:
            user_role = user.get("role", "user")
            
            # Simple role-based permissions
            permissions = {
                "admin": ["read", "write", "delete", "admin"],
                "analyst": ["read", "write", "analyze"],
                "user": ["read"]
            }
            
            user_permissions = permissions.get(user_role, [])
            return required_permission in user_permissions
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False