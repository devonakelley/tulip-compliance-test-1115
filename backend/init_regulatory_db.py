"""
Initialize Regulatory Knowledge Base in MongoDB
Populates database with key regulatory clauses
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from core.regulatory_knowledge_base import get_all_clauses
import os
from dotenv import load_dotenv

load_dotenv()

async def init_regulatory_db():
    """Initialize regulatory knowledge base"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🚀 Initializing Regulatory Knowledge Base...")
    
    # Get all regulatory clauses
    clauses = get_all_clauses()
    
    # Clear existing clauses (optional - remove in production)
    await db.regulatory_clauses.delete_many({})
    print(f"📝 Cleared existing clauses")
    
    # Insert clauses
    clause_docs = [clause.model_dump() for clause in clauses]
    result = await db.regulatory_clauses.insert_many(clause_docs)
    
    print(f"✅ Inserted {len(result.inserted_ids)} regulatory clauses")
    
    # Print summary by framework
    from collections import Counter
    framework_counts = Counter(c.framework.value for c in clauses)
    
    print("\n📊 Clauses by Framework:")
    for framework, count in sorted(framework_counts.items()):
        print(f"   {framework}: {count} clauses")
    
    print(f"\n🎯 Total Regulatory Clauses: {len(clauses)}")
    
    # Create indexes for performance
    await db.regulatory_clauses.create_index([("framework", 1), ("clause_id", 1)])
    await db.regulatory_clauses.create_index("keywords")
    await db.regulatory_clauses.create_index("category")
    
    await db.document_references.create_index([("tenant_id", 1), ("source_doc_id", 1)])
    await db.document_references.create_index([("tenant_id", 1), ("target_doc_id", 1)])
    
    await db.regulatory_citations.create_index([("tenant_id", 1), ("document_id", 1)])
    await db.regulatory_citations.create_index([("tenant_id", 1), ("framework", 1), ("clause_id", 1)])
    
    print("✅ Created database indexes")
    
    print("\n" + "="*70)
    print("🎉 Regulatory Knowledge Base initialization complete!")
    print("="*70)
    print("\n📋 Available Regulatory Frameworks:")
    print("   • FDA 21 CFR Part 820 (QSR)")
    print("   • ISO 13485:2016")
    print("   • MDR 2017/745 (EU)")
    print("   • ISO 14971:2019 (Risk Management)")
    print("   • ISO 10993 (Biocompatibility)")
    print("   • ISO 11135 (Sterilization)")
    print("   • ISO 11607 (Packaging)")
    print("   • 21 CFR Part 11 (E-records)")
    print("   • MDSAP")
    print("\n🔍 System is ready to extract references and build traceability!\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(init_regulatory_db())
