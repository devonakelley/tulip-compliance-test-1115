"""
Database initialization and seeding
Creates default tenant and admin user on first run
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from core.auth_utils import get_password_hash
from datetime import datetime, timezone
import os
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'compliance_checker')

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@tulipmedical.com"
DEFAULT_ADMIN_PASSWORD = "Tulip123!"
DEFAULT_COMPANY_NAME = "Tulip Medical Products"


async def seed_default_admin():
    """
    Seed default admin user and tenant if database is empty
    """
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Check if any users exist
        user_count = await db.users.count_documents({})
        
        if user_count == 0:
            logger.info("No users found. Creating default tenant and admin user...")
            
            # Create default tenant
            tenant_id = str(uuid.uuid4())
            tenant = {
                "id": tenant_id,
                "name": DEFAULT_COMPANY_NAME,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }
            
            # Check if tenant exists
            existing_tenant = await db.tenants.find_one({"name": DEFAULT_COMPANY_NAME})
            if not existing_tenant:
                await db.tenants.insert_one(tenant)
                logger.info(f"✅ Created default tenant: {DEFAULT_COMPANY_NAME}")
            else:
                tenant_id = existing_tenant["id"]
                logger.info(f"Using existing tenant: {DEFAULT_COMPANY_NAME}")
            
            # Create admin user
            admin_id = str(uuid.uuid4())
            hashed_password = get_password_hash(DEFAULT_ADMIN_PASSWORD)
            
            admin_user = {
                "id": admin_id,
                "email": DEFAULT_ADMIN_EMAIL,
                "hashed_password": hashed_password,
                "role": "admin",
                "tenant_id": tenant_id,
                "company_name": DEFAULT_COMPANY_NAME,
                "full_name": "Admin User",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": None
            }
            
            await db.users.insert_one(admin_user)
            
            logger.info("=" * 60)
            logger.info("✅ DEFAULT ADMIN USER CREATED")
            logger.info("=" * 60)
            logger.info(f"Email:    {DEFAULT_ADMIN_EMAIL}")
            logger.info(f"Password: {DEFAULT_ADMIN_PASSWORD}")
            logger.info(f"Company:  {DEFAULT_COMPANY_NAME}")
            logger.info(f"Role:     admin")
            logger.info("=" * 60)
            logger.info("⚠️  IMPORTANT: Change this password after first login!")
            logger.info("=" * 60)
            
        else:
            logger.info(f"Database already initialized with {user_count} user(s)")
            
    except Exception as e:
        logger.error(f"Error seeding admin user: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_default_admin())
