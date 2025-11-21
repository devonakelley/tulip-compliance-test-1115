"""
Seed catalogs with Forms and Work Instructions data
"""
import os
import asyncio
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_catalogs(tenant_id: str):
    """
    Seed forms_catalog and wi_catalog collections with initial data
    
    Args:
        tenant_id: Tenant ID to associate entries with
    """
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'compliance_checker')
    
    if not mongo_url:
        logger.error("MONGO_URL not set")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Forms catalog seed data (from user instructions)
    forms_data = [
        {"form_id": "7.3-3-1", "form_name": "Risk Management Plan", "parent_qsp": "7.3-3"},
        {"form_id": "7.3-3-2", "form_name": "Risk Analysis Form", "parent_qsp": "7.3-3"},
        {"form_id": "7.3-3-4", "form_name": "Regulatory Update Log", "parent_qsp": "7.3-3"},
        {"form_id": "4.2-1-2", "form_name": "Change Request", "parent_qsp": "4.2-1"},
        {"form_id": "4.2-4-1", "form_name": "Electronic Record Control Log", "parent_qsp": "4.2-4"},
        {"form_id": "9.1-3-5", "form_name": "PSUR", "parent_qsp": "9.1-3"},
    ]
    
    # WI catalog seed data (from user instructions)
    wi_data = [
        {"wi_id": "WI-003", "wi_name": "Visual Inspection", "parent_qsp": "9.1-3"},
        {"wi_id": "WI-006", "wi_name": "Cannula Pull Testing", "parent_qsp": "9.1-3"},
        {"wi_id": "WI-004", "wi_name": "Electronic Signature Procedure", "parent_qsp": "4.2-4"},
    ]
    
    forms_added = 0
    wis_added = 0
    
    # Insert forms
    logger.info("Seeding forms catalog...")
    for form in forms_data:
        result = await db.forms_catalog.update_one(
            {'tenant_id': tenant_id, 'form_id': form['form_id']},
            {
                '$set': {
                    'form_name': form['form_name'],
                    'parent_qsp': form.get('parent_qsp'),
                    'description': f'Form {form["form_id"]}',
                    'updated_at': datetime.utcnow()
                },
                '$setOnInsert': {
                    'tenant_id': tenant_id,
                    'form_id': form['form_id'],
                    'created_at': datetime.utcnow(),
                    'referenced_in_sections': []
                }
            },
            upsert=True
        )
        if result.upserted_id or result.modified_count > 0:
            forms_added += 1
            logger.info(f"  Added/Updated form: {form['form_id']} - {form['form_name']}")
    
    # Insert WIs
    logger.info("Seeding WI catalog...")
    for wi in wi_data:
        result = await db.wi_catalog.update_one(
            {'tenant_id': tenant_id, 'wi_id': wi['wi_id']},
            {
                '$set': {
                    'wi_name': wi['wi_name'],
                    'parent_qsp': wi.get('parent_qsp'),
                    'description': f'Work Instruction {wi["wi_id"]}',
                    'updated_at': datetime.utcnow()
                },
                '$setOnInsert': {
                    'tenant_id': tenant_id,
                    'wi_id': wi['wi_id'],
                    'created_at': datetime.utcnow(),
                    'referenced_in_sections': []
                }
            },
            upsert=True
        )
        if result.upserted_id or result.modified_count > 0:
            wis_added += 1
            logger.info(f"  Added/Updated WI: {wi['wi_id']} - {wi['wi_name']}")
    
    # Create indexes for performance
    logger.info("Creating indexes...")
    await db.forms_catalog.create_index([("tenant_id", 1), ("form_id", 1)], unique=True)
    await db.wi_catalog.create_index([("tenant_id", 1), ("wi_id", 1)], unique=True)
    
    logger.info(f"✅ Seeding complete: {forms_added} forms, {wis_added} WIs added/updated")
    client.close()


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python seed_catalogs.py <tenant_id>")
        print("Example: python seed_catalogs.py 27375e34-73c9-4adf-87bf-a94ddac6a351")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    asyncio.run(seed_catalogs(tenant_id))
