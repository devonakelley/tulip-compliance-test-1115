"""
Initialize test tenants and users for Phase 1 testing
Creates two fake tenants with test users
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from core.auth import auth_service
from models.tenant import Tenant
from models.user import User
import os
from dotenv import load_dotenv

load_dotenv()

async def init_test_data():
    """Initialize test tenants and users"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🚀 Initializing test tenants and users...")
    
    # Create Tenant 1: Tulip Medical
    tenant1 = Tenant(
        name="Tulip Medical",
        plan="pro",
        storage_limit_mb=5000
    )
    
    # Create Tenant 2: MedTech Solutions
    tenant2 = Tenant(
        name="MedTech Solutions",
        plan="free",
        storage_limit_mb=1000
    )
    
    # Clear existing test data
    await db.tenants.delete_many({"name": {"$in": ["Tulip Medical", "MedTech Solutions"]}})
    await db.users.delete_many({"email": {"$in": [
        "admin@tulipmedical.com",
        "user@tulipmedical.com",
        "admin@medtechsolutions.com",
        "user@medtechsolutions.com"
    ]}})
    
    # Insert tenants
    await db.tenants.insert_one(tenant1.model_dump())
    await db.tenants.insert_one(tenant2.model_dump())
    
    print(f"✅ Created Tenant 1: {tenant1.name} (ID: {tenant1.id})")
    print(f"✅ Created Tenant 2: {tenant2.name} (ID: {tenant2.id})")
    
    # Create users for Tenant 1
    user1_tenant1 = User(
        email="admin@tulipmedical.com",
        password_hash=auth_service.hash_password("password123"),
        tenant_id=tenant1.id,
        full_name="Admin User - Tulip Medical"
    )
    
    user2_tenant1 = User(
        email="user@tulipmedical.com",
        password_hash=auth_service.hash_password("password123"),
        tenant_id=tenant1.id,
        full_name="Regular User - Tulip Medical"
    )
    
    # Create users for Tenant 2
    user1_tenant2 = User(
        email="admin@medtechsolutions.com",
        password_hash=auth_service.hash_password("password123"),
        tenant_id=tenant2.id,
        full_name="Admin User - MedTech Solutions"
    )
    
    user2_tenant2 = User(
        email="user@medtechsolutions.com",
        password_hash=auth_service.hash_password("password123"),
        tenant_id=tenant2.id,
        full_name="Regular User - MedTech Solutions"
    )
    
    # Insert users
    await db.users.insert_one(user1_tenant1.model_dump())
    await db.users.insert_one(user2_tenant1.model_dump())
    await db.users.insert_one(user1_tenant2.model_dump())
    await db.users.insert_one(user2_tenant2.model_dump())
    
    print(f"✅ Created users for Tenant 1:")
    print(f"   - {user1_tenant1.email} (password: password123)")
    print(f"   - {user2_tenant1.email} (password: password123)")
    
    print(f"✅ Created users for Tenant 2:")
    print(f"   - {user1_tenant2.email} (password: password123)")
    print(f"   - {user2_tenant2.email} (password: password123)")
    
    print("\n" + "="*60)
    print("🎉 Test data initialization complete!")
    print("="*60)
    print("\n📝 **Test Credentials:**\n")
    print(f"**Tenant 1: Tulip Medical (ID: {tenant1.id})**")
    print(f"  Email: admin@tulipmedical.com")
    print(f"  Password: password123\n")
    
    print(f"**Tenant 2: MedTech Solutions (ID: {tenant2.id})**")
    print(f"  Email: admin@medtechsolutions.com")
    print(f"  Password: password123\n")
    
    print("🔐 Use these credentials to test multi-tenant isolation")
    print("📤 Each tenant can upload documents independently")
    print("🔍 Data will be isolated by tenant_id\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(init_test_data())
