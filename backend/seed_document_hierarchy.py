"""
Seed Document Hierarchy for Tulip Medical
Based on actual QMS structure:
Level 1: Quality Manual (QM1 R26)
Level 2: QSPs (Quality System Procedures)
Level 3: Work Instructions (WIs)
Level 4: Forms
Level 5: Reference Documents
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Tulip Medical Document Hierarchy
# Based on the regulatory mapping provided

DOCUMENT_HIERARCHY = {
    # Level 1: Quality Manual sections mapped to regulations
    "quality_manual": {
        "id": "QM1-R26",
        "name": "Quality Manual Rev 26",
        "sections": [
            {"id": "QM1-R26-MDR", "name": "MDR Sections", "regulations": ["MDR 2017/745"]},
            {"id": "QM1-R26-FDA", "name": "FDA QSR Integration", "regulations": ["FDA 21 CFR Part 820"]},
            {"id": "QM1-R26-ISO", "name": "ISO Integration", "regulations": ["ISO 13485:2016"]},
            {"id": "QM1-R26-RISK", "name": "Risk Management Section", "regulations": ["ISO 14971:2019"]},
            {"id": "QM1-R26-BIO", "name": "Biocompatibility Integration", "regulations": ["ISO 10993"]},
            {"id": "QM1-R26-STER", "name": "Sterilization", "regulations": ["ISO 11135"]},
            {"id": "QM1-R26-PKG", "name": "Packaging & Shelf Life", "regulations": ["ISO 11607", "ASTM F1980"]},
            {"id": "QM1-R26-REC", "name": "Records Control", "regulations": ["21 CFR Part 11"]},
            {"id": "QM1-R26-GLOBAL", "name": "Global QMS Section", "regulations": ["MDSAP"]},
        ]
    },

    # Level 2: QSPs with their parent QM sections and child WIs/Forms
    "qsps": [
        {
            "id": "QSP-9.1-3",
            "name": "Technical Documentation",
            "parent_qm": "QM1-R26-MDR",
            "regulations": ["MDR 2017/745 Annex I GSPR"],
            "child_wis": ["WI-003", "WI-006"],
            "child_forms": ["Form-9.1-3-5", "Form-7.3-3-4", "Form-7.3-1-2"]
        },
        {
            "id": "QSP-7.3-3",
            "name": "Risk Management",
            "parent_qm": "QM1-R26-RISK",
            "regulations": ["ISO 14971:2019", "MDR 2017/745"],
            "child_wis": ["WI-FMEA", "WI-RISK-ANALYSIS"],
            "child_forms": ["Form-7.3-3-2", "Form-7.3-3-5"]
        },
        {
            "id": "QSP-9.4-1",
            "name": "Clinical Evaluation",
            "parent_qm": "QM1-R26-MDR",
            "regulations": ["MDR 2017/745"],
            "child_wis": [],
            "child_forms": []
        },
        {
            "id": "QSP-8.2-2",
            "name": "Complaints & Feedback",
            "parent_qm": "QM1-R26-MDR",
            "regulations": ["MDR 2017/745", "FDA 21 CFR 820.198"],
            "child_wis": [],
            "child_forms": []
        },
        {
            "id": "QSP-7.3-1",
            "name": "Design & Development",
            "parent_qm": "QM1-R26-FDA",
            "regulations": ["FDA 21 CFR Part 820.30", "ISO 13485:2016 7.3"],
            "child_wis": ["WI-003", "WI-006"],
            "child_forms": ["Form-7.3-1-2"]
        },
        {
            "id": "QSP-7.5-1",
            "name": "Production",
            "parent_qm": "QM1-R26-FDA",
            "regulations": ["FDA 21 CFR Part 820.70"],
            "child_wis": ["WI-ASSEMBLY-PKG", "WI-STER-VAL"],
            "child_forms": ["Form-8.5-1-2", "Form-8.3-1-1"]
        },
        {
            "id": "QSP-8.3-1",
            "name": "Nonconforming Product",
            "parent_qm": "QM1-R26-FDA",
            "regulations": ["FDA 21 CFR Part 820.90"],
            "child_wis": ["WI-ASSEMBLY-PKG"],
            "child_forms": ["Form-8.3-1-1"]
        },
        {
            "id": "QSP-8.5-1",
            "name": "CAPA",
            "parent_qm": "QM1-R26-FDA",
            "regulations": ["FDA 21 CFR Part 820.100"],
            "child_wis": [],
            "child_forms": ["Form-8.5-1-2"]
        },
        {
            "id": "QSP-4.2-1",
            "name": "Document Control",
            "parent_qm": "QM1-R26-ISO",
            "regulations": ["ISO 13485:2016 4.2"],
            "child_wis": ["WI-TRAINING", "WI-SUPPLIER-QUAL"],
            "child_forms": ["Form-4.2-1-1"]
        },
        {
            "id": "QSP-6.2-1",
            "name": "Training",
            "parent_qm": "QM1-R26-ISO",
            "regulations": ["ISO 13485:2016 6.2"],
            "child_wis": ["WI-TRAINING"],
            "child_forms": ["Form-6.2-1-2"]
        },
        {
            "id": "QSP-7.4-1",
            "name": "Purchasing",
            "parent_qm": "QM1-R26-ISO",
            "regulations": ["ISO 13485:2016 7.4"],
            "child_wis": ["WI-SUPPLIER-QUAL"],
            "child_forms": []
        },
        {
            "id": "QSP-8.2-1",
            "name": "Internal Audits",
            "parent_qm": "QM1-R26-ISO",
            "regulations": ["ISO 13485:2016 8.2.2"],
            "child_wis": ["WI-AUDIT-PLANNING", "WI-MDSAP-PREP"],
            "child_forms": ["Form-AUDIT-CHECKLIST"]
        },
        {
            "id": "QSP-7.5-2",
            "name": "Sterilization & Packaging",
            "parent_qm": "QM1-R26-STER",
            "regulations": ["ISO 11135", "ISO 11607"],
            "child_wis": ["WI-ETO-VAL", "WI-PKG-INTEGRITY"],
            "child_forms": ["Form-7.5-2-1", "Form-7.5-2-2"]
        },
        {
            "id": "QSP-4.2-2",
            "name": "Electronic Records",
            "parent_qm": "QM1-R26-REC",
            "regulations": ["21 CFR Part 11"],
            "child_wis": ["WI-ESIG-AUDIT"],
            "child_forms": ["Form-ELECTRONIC-APPROVAL"]
        },
        {
            "id": "QSP-8.4-1",
            "name": "Regulatory Reporting",
            "parent_qm": "QM1-R26-GLOBAL",
            "regulations": ["MDSAP"],
            "child_wis": ["WI-AUDIT-PLANNING", "WI-MDSAP-PREP"],
            "child_forms": []
        },
    ],

    # Level 3: Work Instructions
    "work_instructions": [
        {"id": "WI-003", "name": "Visual Inspection", "parent_qsps": ["QSP-7.3-1", "QSP-9.1-3"]},
        {"id": "WI-006", "name": "Cannula Pull Testing", "parent_qsps": ["QSP-7.3-1", "QSP-9.1-3"]},
        {"id": "WI-ASSEMBLY-PKG", "name": "Assembly & Packaging", "parent_qsps": ["QSP-7.5-1", "QSP-8.3-1"]},
        {"id": "WI-STER-VAL", "name": "Sterilization Validation", "parent_qsps": ["QSP-7.5-1", "QSP-7.5-2"]},
        {"id": "WI-TRAINING", "name": "Training Records", "parent_qsps": ["QSP-4.2-1", "QSP-6.2-1"]},
        {"id": "WI-SUPPLIER-QUAL", "name": "Supplier Qualification", "parent_qsps": ["QSP-4.2-1", "QSP-7.4-1"]},
        {"id": "WI-FMEA", "name": "FMEA Completion", "parent_qsps": ["QSP-7.3-3"]},
        {"id": "WI-RISK-ANALYSIS", "name": "Risk Analysis", "parent_qsps": ["QSP-7.3-3"]},
        {"id": "WI-BIO-TEST", "name": "Biocompatibility Testing", "parent_qsps": ["QSP-7.3-3"]},
        {"id": "WI-ETO-VAL", "name": "EtO Validation", "parent_qsps": ["QSP-7.5-2"]},
        {"id": "WI-PKG-INTEGRITY", "name": "Packaging Integrity Test", "parent_qsps": ["QSP-7.5-2"]},
        {"id": "WI-ESIG-AUDIT", "name": "e-signature & audit trail use", "parent_qsps": ["QSP-4.2-2"]},
        {"id": "WI-AUDIT-PLANNING", "name": "Audit Planning", "parent_qsps": ["QSP-8.2-1", "QSP-8.4-1"]},
        {"id": "WI-MDSAP-PREP", "name": "MDSAP Audit Prep", "parent_qsps": ["QSP-8.2-1", "QSP-8.4-1"]},
    ],

    # Level 4: Forms
    "forms": [
        {"id": "Form-9.1-3-5", "name": "PSUR Form", "parent_wis": ["WI-003", "WI-006"]},
        {"id": "Form-7.3-3-4", "name": "Regulatory Update Log", "parent_wis": ["WI-003", "WI-006"]},
        {"id": "Form-7.3-1-2", "name": "Design Input/Output", "parent_wis": ["WI-003", "WI-006"]},
        {"id": "Form-8.5-1-2", "name": "CAPA Form", "parent_wis": ["WI-ASSEMBLY-PKG", "WI-STER-VAL"]},
        {"id": "Form-8.3-1-1", "name": "NC Report", "parent_wis": ["WI-ASSEMBLY-PKG", "WI-STER-VAL"]},
        {"id": "Form-4.2-1-1", "name": "Document Change Form", "parent_wis": ["WI-TRAINING", "WI-SUPPLIER-QUAL"]},
        {"id": "Form-6.2-1-2", "name": "Training Record", "parent_wis": ["WI-TRAINING", "WI-SUPPLIER-QUAL"]},
        {"id": "Form-7.3-3-2", "name": "Risk Analysis Form", "parent_wis": ["WI-FMEA", "WI-RISK-ANALYSIS"]},
        {"id": "Form-7.3-3-5", "name": "Biological Eval Summary", "parent_wis": ["WI-BIO-TEST"]},
        {"id": "Form-7.5-2-1", "name": "Sterilization Record", "parent_wis": ["WI-ETO-VAL"]},
        {"id": "Form-7.5-2-2", "name": "Packaging Validation Form", "parent_wis": ["WI-PKG-INTEGRITY"]},
        {"id": "Form-ELECTRONIC-APPROVAL", "name": "Electronic Approval Log", "parent_wis": ["WI-ESIG-AUDIT"]},
        {"id": "Form-AUDIT-CHECKLIST", "name": "Audit Checklist", "parent_wis": ["WI-AUDIT-PLANNING", "WI-MDSAP-PREP"]},
    ],

    # Level 5: Reference Documents
    "reference_docs": [
        {"id": "GSPR-2024-02-R2", "name": "General Safety & Performance Requirements", "parent_forms": ["Form-9.1-3-5"]},
        {"id": "CER-002", "name": "Clinical Evaluation Report", "parent_forms": ["Form-9.1-3-5"]},
        {"id": "PMS-PLAN-25-01", "name": "Post-Market Surveillance Plan", "parent_forms": ["Form-9.1-3-5"]},
        {"id": "PMCF-25-01", "name": "Post-Market Clinical Follow-up", "parent_forms": ["Form-9.1-3-5"]},
        {"id": "PMSR-25-01", "name": "Post-Market Surveillance Report", "parent_forms": ["Form-9.1-3-5"]},
        {"id": "FDA-510K-K060089", "name": "510(k) Clearance", "parent_forms": ["Form-8.5-1-2", "Form-8.3-1-1"]},
        {"id": "DMR-INDEX", "name": "Device Master Record Index", "parent_forms": ["Form-8.5-1-2", "Form-8.3-1-1"]},
        {"id": "MDSAP-CERT", "name": "MDSAP Certificates", "parent_forms": ["Form-4.2-1-1", "Form-6.2-1-2"]},
        {"id": "SUPPLIER-CERTS", "name": "Supplier Certifications", "parent_forms": ["Form-4.2-1-1", "Form-6.2-1-2"]},
        {"id": "RSK-04.1", "name": "Risk File 04.1", "parent_forms": ["Form-7.3-3-2"]},
        {"id": "RSK-09", "name": "Design FMEA RSK-09", "parent_forms": ["Form-7.3-3-2"]},
        {"id": "RSK-15", "name": "Biological Eval RSK-15", "parent_forms": ["Form-7.3-3-2"]},
        {"id": "NAMSA-BIO-REPORTS", "name": "NAMSA Bio Evaluation Reports", "parent_forms": ["Form-7.3-3-5"]},
        {"id": "RSK-12-13-14", "name": "Bio Eval Reports RSK-12/13/14", "parent_forms": ["Form-7.3-3-5"]},
        {"id": "PROTECH-VAL", "name": "Pro-Tech Validation Reports", "parent_forms": ["Form-7.5-2-1"]},
        {"id": "STERIS-CERTS", "name": "Steris Certificates", "parent_forms": ["Form-7.5-2-1"]},
        {"id": "PVS-145", "name": "Packaging Validation Study PVS-145", "parent_forms": ["Form-7.5-2-2"]},
        {"id": "AGING-STUDIES", "name": "Accelerated Aging Studies", "parent_forms": ["Form-7.5-2-2"]},
        {"id": "FDA-COMPLIANCE-POL", "name": "FDA Compliance Policies", "parent_forms": ["Form-ELECTRONIC-APPROVAL"]},
        {"id": "AR-DISTRIBUTOR", "name": "AR/Distributor Agreements", "parent_forms": ["Form-AUDIT-CHECKLIST"]},
    ]
}


async def seed_hierarchy(tenant_id: str):
    """Seed document hierarchy for a tenant"""

    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'compliance_checker')

    if not mongo_url:
        print("❌ MONGO_URL not set")
        return

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print(f"🚀 Seeding document hierarchy for tenant: {tenant_id}")

    # Clear existing hierarchy data for this tenant
    await db.document_references.delete_many({"tenant_id": tenant_id})
    await db.regulatory_citations.delete_many({"tenant_id": tenant_id})
    await db.document_hierarchy.delete_many({"tenant_id": tenant_id})

    documents_created = 0
    references_created = 0
    citations_created = 0

    now = datetime.now(timezone.utc)

    # Seed Quality Manual
    qm = DOCUMENT_HIERARCHY["quality_manual"]
    for section in qm["sections"]:
        # Create document entry
        await db.document_hierarchy.insert_one({
            "tenant_id": tenant_id,
            "document_id": section["id"],
            "document_name": section["name"],
            "document_type": "QM",
            "level": 1,
            "parent_docs": [],
            "child_docs": [],  # Will be populated below
            "created_at": now
        })
        documents_created += 1

        # Create regulatory citations for this QM section
        for reg in section["regulations"]:
            await db.regulatory_citations.insert_one({
                "tenant_id": tenant_id,
                "document_id": section["id"],
                "document_type": "QM",
                "framework": reg,
                "citation": reg,
                "clause_id": reg,
                "confidence": 1.0,
                "created_at": now
            })
            citations_created += 1

    print(f"  ✅ Level 1 (Quality Manual): {len(qm['sections'])} sections")

    # Seed QSPs
    for qsp in DOCUMENT_HIERARCHY["qsps"]:
        await db.document_hierarchy.insert_one({
            "tenant_id": tenant_id,
            "document_id": qsp["id"],
            "document_name": qsp["name"],
            "document_type": "QSP",
            "level": 2,
            "parent_docs": [qsp["parent_qm"]],
            "child_docs": qsp["child_wis"] + qsp["child_forms"],
            "created_at": now
        })
        documents_created += 1

        # Create reference from QSP to QM
        await db.document_references.insert_one({
            "tenant_id": tenant_id,
            "source_doc_id": qsp["id"],
            "source_doc_type": "QSP",
            "target_doc_id": qsp["parent_qm"],
            "target_doc_type": "QM",
            "reference_type": "implements",
            "created_at": now
        })
        references_created += 1

        # Create regulatory citations
        for reg in qsp["regulations"]:
            await db.regulatory_citations.insert_one({
                "tenant_id": tenant_id,
                "document_id": qsp["id"],
                "document_type": "QSP",
                "framework": reg.split()[0] if ' ' in reg else reg,
                "citation": reg,
                "clause_id": reg,
                "confidence": 1.0,
                "created_at": now
            })
            citations_created += 1

    print(f"  ✅ Level 2 (QSPs): {len(DOCUMENT_HIERARCHY['qsps'])} procedures")

    # Seed Work Instructions
    for wi in DOCUMENT_HIERARCHY["work_instructions"]:
        await db.document_hierarchy.insert_one({
            "tenant_id": tenant_id,
            "document_id": wi["id"],
            "document_name": wi["name"],
            "document_type": "WI",
            "level": 3,
            "parent_docs": wi["parent_qsps"],
            "child_docs": [],  # Will get forms
            "created_at": now
        })
        documents_created += 1

        # Create references from WI to QSPs
        for qsp_id in wi["parent_qsps"]:
            await db.document_references.insert_one({
                "tenant_id": tenant_id,
                "source_doc_id": wi["id"],
                "source_doc_type": "WI",
                "target_doc_id": qsp_id,
                "target_doc_type": "QSP",
                "reference_type": "implements",
                "created_at": now
            })
            references_created += 1

    print(f"  ✅ Level 3 (Work Instructions): {len(DOCUMENT_HIERARCHY['work_instructions'])} WIs")

    # Seed Forms
    for form in DOCUMENT_HIERARCHY["forms"]:
        await db.document_hierarchy.insert_one({
            "tenant_id": tenant_id,
            "document_id": form["id"],
            "document_name": form["name"],
            "document_type": "FORM",
            "level": 4,
            "parent_docs": form["parent_wis"],
            "child_docs": [],
            "created_at": now
        })
        documents_created += 1

        # Create references from Form to WIs
        for wi_id in form["parent_wis"]:
            await db.document_references.insert_one({
                "tenant_id": tenant_id,
                "source_doc_id": form["id"],
                "source_doc_type": "FORM",
                "target_doc_id": wi_id,
                "target_doc_type": "WI",
                "reference_type": "implements",
                "created_at": now
            })
            references_created += 1

    print(f"  ✅ Level 4 (Forms): {len(DOCUMENT_HIERARCHY['forms'])} forms")

    # Seed Reference Documents
    for ref_doc in DOCUMENT_HIERARCHY["reference_docs"]:
        await db.document_hierarchy.insert_one({
            "tenant_id": tenant_id,
            "document_id": ref_doc["id"],
            "document_name": ref_doc["name"],
            "document_type": "RFD",
            "level": 5,
            "parent_docs": ref_doc["parent_forms"],
            "child_docs": [],
            "created_at": now
        })
        documents_created += 1

        # Create references from Ref Doc to Forms
        for form_id in ref_doc["parent_forms"]:
            await db.document_references.insert_one({
                "tenant_id": tenant_id,
                "source_doc_id": ref_doc["id"],
                "source_doc_type": "RFD",
                "target_doc_id": form_id,
                "target_doc_type": "FORM",
                "reference_type": "supports",
                "created_at": now
            })
            references_created += 1

    print(f"  ✅ Level 5 (Reference Docs): {len(DOCUMENT_HIERARCHY['reference_docs'])} documents")

    print(f"\n{'='*60}")
    print(f"🎉 Document hierarchy seeded successfully!")
    print(f"{'='*60}")
    print(f"  📄 Documents created: {documents_created}")
    print(f"  🔗 References created: {references_created}")
    print(f"  📋 Citations created: {citations_created}")
    print(f"\n  Hierarchy:")
    print(f"    Level 1 (QM):   {len(DOCUMENT_HIERARCHY['quality_manual']['sections'])} sections")
    print(f"    Level 2 (QSP):  {len(DOCUMENT_HIERARCHY['qsps'])} procedures")
    print(f"    Level 3 (WI):   {len(DOCUMENT_HIERARCHY['work_instructions'])} instructions")
    print(f"    Level 4 (Form): {len(DOCUMENT_HIERARCHY['forms'])} forms")
    print(f"    Level 5 (RFD):  {len(DOCUMENT_HIERARCHY['reference_docs'])} reference docs")

    client.close()


async def main():
    # Get tenant ID from command line or use default
    tenant_id = sys.argv[1] if len(sys.argv) > 1 else None

    if not tenant_id:
        # Try to get from existing tenants
        mongo_url = os.environ.get('MONGO_URL')
        if mongo_url:
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ.get('DB_NAME', 'compliance_checker')]
            tenant = await db.tenants.find_one({"name": "Tulip Medical"})
            if tenant:
                tenant_id = tenant['id']
                print(f"Found Tulip Medical tenant: {tenant_id}")
            client.close()

    if not tenant_id:
        print("Usage: python seed_document_hierarchy.py <tenant_id>")
        print("Or ensure Tulip Medical tenant exists in database")
        return

    await seed_hierarchy(tenant_id)


if __name__ == "__main__":
    asyncio.run(main())
