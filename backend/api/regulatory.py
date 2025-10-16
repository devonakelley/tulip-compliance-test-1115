"""
Regulatory Compliance API
Endpoints for document hierarchy, traceability, and impact analysis
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Dict, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.auth import get_current_user
from core.reference_extractor import reference_extractor
from core.traceability_engine import TraceabilityEngine
from core.regulatory_knowledge_base import get_all_clauses, get_clauses_by_framework, get_clause_by_id
from core.audit_logger import audit_logger
from models.regulatory import (
    RegulatoryFramework, DocumentType, DocumentReference, 
    RegulatoryCitation, ComplianceMatrix, ImpactAnalysis
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regulatory", tags=["regulatory"])

# Database will be injected from main server
db: AsyncIOMotorDatabase = None

def set_database(database):
    """Set database instance"""
    global db
    db = database

@router.get("/frameworks")
async def list_frameworks(current_user: dict = Depends(get_current_user)):
    """List all supported regulatory frameworks"""
    frameworks = [
        {
            "id": fw.value,
            "name": fw.value.replace("_", " "),
            "description": _get_framework_description(fw)
        }
        for fw in RegulatoryFramework
    ]
    return {"frameworks": frameworks}

@router.get("/frameworks/{framework}/clauses")
async def get_framework_clauses(
    framework: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all clauses for a specific framework"""
    try:
        fw_enum = RegulatoryFramework(framework)
        clauses = get_clauses_by_framework(fw_enum)
        
        return {
            "framework": framework,
            "total_clauses": len(clauses),
            "clauses": [
                {
                    "clause_id": c.clause_id,
                    "title": c.title,
                    "requirement_text": c.requirement_text,
                    "category": c.category,
                    "criticality": c.criticality,
                    "keywords": c.keywords
                }
                for c in clauses
            ]
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Framework not found")

@router.post("/extract-references")
async def extract_document_references(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Extract document references and regulatory citations from uploaded document
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        # Extract references
        doc_refs = reference_extractor.extract_document_references(text_content)
        reg_cits = reference_extractor.extract_regulatory_citations(text_content)
        
        # Log audit
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="extract_references",
            target=file.filename,
            metadata={
                "doc_references": len(doc_refs),
                "reg_citations": len(reg_cits)
            }
        )
        
        return {
            "filename": file.filename,
            "document_references": doc_refs,
            "regulatory_citations": reg_cits,
            "summary": {
                "total_doc_refs": len(doc_refs),
                "total_reg_cits": len(reg_cits),
                "frameworks_found": list(set(c['framework'] for c in reg_cits))
            }
        }
        
    except Exception as e:
        logger.error(f"Error extracting references: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-document")
async def process_document_for_traceability(
    document_id: str,
    document_content: str,
    document_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Process document and store references and citations for traceability
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        # Determine document type
        if not document_type:
            det_type = reference_extractor.determine_document_type(document_id)
            document_type = det_type.value if det_type else DocumentType.REFERENCE_DOC.value
        
        # Extract references
        doc_refs = reference_extractor.extract_document_references(document_content)
        reg_cits = reference_extractor.extract_regulatory_citations(document_content)
        
        # Store document references
        ref_ids = []
        for ref in doc_refs:
            target_type = reference_extractor.determine_document_type(ref['reference'])
            
            doc_ref = DocumentReference(
                tenant_id=tenant_id,
                source_doc_id=document_id,
                source_doc_type=DocumentType(document_type),
                target_doc_id=ref['reference'],
                target_doc_type=target_type,
                reference_type="references",
                context=ref.get('context')
            )
            
            result = await db.document_references.insert_one(doc_ref.model_dump())
            ref_ids.append(str(result.inserted_id))
        
        # Store regulatory citations
        cit_ids = []
        for cit in reg_cits:
            reg_citation = RegulatoryCitation(
                tenant_id=tenant_id,
                document_id=document_id,
                document_type=DocumentType(document_type),
                framework=RegulatoryFramework(cit['framework']),
                citation=cit['citation'],
                clause_id=cit['clause_id'],
                context=cit.get('context'),
                confidence=1.0
            )
            
            result = await db.regulatory_citations.insert_one(reg_citation.model_dump())
            cit_ids.append(str(result.inserted_id))
        
        # Log audit
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="process_document_traceability",
            target=document_id,
            metadata={
                "references_stored": len(ref_ids),
                "citations_stored": len(cit_ids)
            }
        )
        
        return {
            "document_id": document_id,
            "references_stored": len(ref_ids),
            "citations_stored": len(cit_ids),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hierarchy")
async def get_document_hierarchy(current_user: dict = Depends(get_current_user)):
    """Get document hierarchy tree for tenant"""
    try:
        tenant_id = current_user["tenant_id"]
        
        engine = TraceabilityEngine(db)
        tree = await engine.get_hierarchy_tree(tenant_id)
        
        return {
            "status": "success",
            "hierarchy": tree
        }
        
    except Exception as e:
        logger.error(f"Error building hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/impact-analysis/{document_id}")
async def analyze_document_impact(
    document_id: str,
    direction: str = "downstream",
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze impact of changes to a document
    
    direction: 'downstream' (what implements this) or 'upstream' (what this implements)
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        engine = TraceabilityEngine(db)
        impacted = await engine.find_impacted_documents(tenant_id, document_id, direction)
        
        # Format results
        impact_summary = []
        total_impacted = 0
        
        for level, doc_ids in sorted(impacted.items()):
            impact_summary.append({
                "level": level,
                "level_name": _get_level_name(level),
                "document_count": len(doc_ids),
                "documents": list(doc_ids)
            })
            total_impacted += len(doc_ids)
        
        return {
            "document_id": document_id,
            "direction": direction,
            "total_impacted_documents": total_impacted,
            "impact_by_level": impact_summary
        }
        
    except Exception as e:
        logger.error(f"Error analyzing impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance-matrix")
async def get_compliance_matrix(
    framework: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get compliance matrix showing regulation to document mappings"""
    try:
        tenant_id = current_user["tenant_id"]
        
        engine = TraceabilityEngine(db)
        matrix = await engine.build_compliance_matrix(tenant_id)
        
        # Filter by framework if specified
        if framework:
            matrix = {framework: matrix.get(framework, {})}
        
        # Format for display
        formatted_matrix = []
        for fw, clauses in matrix.items():
            for clause_id, doc_ids in clauses.items():
                formatted_matrix.append({
                    "framework": fw,
                    "clause_id": clause_id,
                    "implementing_documents": doc_ids,
                    "document_count": len(doc_ids)
                })
        
        return {
            "status": "success",
            "total_mappings": len(formatted_matrix),
            "matrix": formatted_matrix
        }
        
    except Exception as e:
        logger.error(f"Error building compliance matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coverage-analysis/{framework}")
async def analyze_regulatory_coverage(
    framework: str,
    current_user: dict = Depends(get_current_user)
):
    """Analyze regulatory coverage and identify gaps"""
    try:
        tenant_id = current_user["tenant_id"]
        fw_enum = RegulatoryFramework(framework)
        
        engine = TraceabilityEngine(db)
        analysis = await engine.analyze_coverage_gaps(tenant_id, fw_enum)
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except ValueError:
        raise HTTPException(status_code=404, detail="Framework not found")
    except Exception as e:
        logger.error(f"Error analyzing coverage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regulatory-impact/{framework}/{clause_id}")
async def get_regulatory_clause_impact(
    framework: str,
    clause_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Find all documents implementing a specific regulatory clause"""
    try:
        tenant_id = current_user["tenant_id"]
        fw_enum = RegulatoryFramework(framework)
        
        engine = TraceabilityEngine(db)
        documents = await engine.find_regulatory_impact(tenant_id, fw_enum, clause_id)
        
        # Get clause details
        clause = get_clause_by_id(fw_enum, clause_id)
        
        return {
            "framework": framework,
            "clause_id": clause_id,
            "clause_title": clause.title if clause else "Unknown",
            "implementing_documents": documents,
            "total_documents": len(documents)
        }
        
    except ValueError:
        raise HTTPException(status_code=404, detail="Framework not found")
    except Exception as e:
        logger.error(f"Error getting regulatory impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_framework_description(framework: RegulatoryFramework) -> str:
    """Get framework description"""
    descriptions = {
        RegulatoryFramework.FDA_21CFR820: "FDA Quality System Regulation (USA)",
        RegulatoryFramework.ISO_13485: "Medical Devices Quality Management Systems",
        RegulatoryFramework.MDR_2017_745: "EU Medical Device Regulation",
        RegulatoryFramework.ISO_14971: "Risk Management for Medical Devices",
        RegulatoryFramework.ISO_10993: "Biological Evaluation of Medical Devices",
        RegulatoryFramework.ISO_11135: "Sterilization of Health Care Products - Ethylene Oxide",
        RegulatoryFramework.ISO_11607: "Packaging for Terminally Sterilized Medical Devices",
        RegulatoryFramework.CFR_PART_11: "Electronic Records and Electronic Signatures",
        RegulatoryFramework.MDSAP: "Medical Device Single Audit Program"
    }
    return descriptions.get(framework, framework.value)

def _get_level_name(level: int) -> str:
    """Get level name"""
    names = {
        1: "Quality Manual",
        2: "Quality System Procedures (QSP)",
        3: "Work Instructions (WI)",
        4: "Forms",
        5: "Reference Documents (RFD)",
        6: "Evidence/Technical Documentation"
    }
    return names.get(level, f"Level {level}")
