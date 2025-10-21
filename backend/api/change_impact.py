"""
Change Impact Detection API
FastAPI router for regulatory change impact analysis
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import json
from core.change_impact_service import get_change_impact_service
from core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/impact", tags=["change_impact"])


# Pydantic models
class ChangeDelta(BaseModel):
    clause_id: str
    change_text: str
    change_type: str = "modified"  # modified, new, deleted


class AnalyzeRequest(BaseModel):
    deltas: List[ChangeDelta]
    top_k: int = 5


class QSPSection(BaseModel):
    section_path: str
    heading: str
    text: str
    version: Optional[str] = None


class IngestQSPRequest(BaseModel):
    doc_name: str
    sections: List[QSPSection]


@router.post("/ingest_qsp")
async def ingest_qsp_document(
    request: IngestQSPRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ingest a QSP document and generate embeddings for impact detection
    
    Request body:
    {
        "doc_name": "QSP 4.2 Document Control R5",
        "sections": [
            {
                "section_path": "4.2.1",
                "heading": "General Requirements",
                "text": "The organization shall establish...",
                "version": "R5"
            }
        ]
    }
    """
    try:
        tenant_id = current_user["tenant_id"]
        service = get_change_impact_service()
        
        # Generate doc_id
        import uuid
        doc_id = str(uuid.uuid4())
        
        logger.info(f"Ingesting QSP document: {request.doc_name} ({len(request.sections)} sections)")
        
        # Convert Pydantic models to dicts
        sections = [s.dict() for s in request.sections]
        
        result = service.ingest_qsp_document(
            tenant_id=tenant_id,
            doc_id=doc_id,
            doc_name=request.doc_name,
            sections=sections
        )
        
        return {
            "success": True,
            "message": f"Successfully ingested {result['sections_embedded']} sections",
            "doc_id": doc_id,
            "doc_name": request.doc_name,
            "sections_embedded": result['sections_embedded']
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest QSP document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_change_impact(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze which QSP sections are impacted by regulatory changes
    
    Request body:
    {
        "deltas": [
            {
                "clause_id": "4.2.4",
                "change_text": "Organizations must now maintain electronic records with 21 CFR Part 11 compliance...",
                "change_type": "modified"
            },
            {
                "clause_id": "7.5.1.1",
                "change_text": "New requirement for risk-based validation of production processes...",
                "change_type": "new"
            }
        ],
        "top_k": 5
    }
    
    Returns:
    {
        "success": true,
        "run_id": "uuid",
        "total_changes_analyzed": 2,
        "total_impacts_found": 8,
        "impacts": [...]
    }
    """
    try:
        tenant_id = current_user["tenant_id"]
        service = get_change_impact_service()
        
        if not request.deltas:
            raise HTTPException(status_code=400, detail="No deltas provided")
        
        logger.info(f"Analyzing {len(request.deltas)} regulatory changes for tenant {tenant_id}")
        
        # Convert Pydantic models to dicts
        deltas = [d.dict() for d in request.deltas]
        
        result = service.detect_impacts(
            tenant_id=tenant_id,
            deltas=deltas,
            top_k=request.top_k
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{run_id}")
async def get_impact_report(
    run_id: str,
    format: str = "json",
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve impact analysis report
    
    Query params:
    - format: 'json' or 'csv'
    
    Returns JSON report or CSV file
    """
    try:
        tenant_id = current_user["tenant_id"]
        service = get_change_impact_service()
        
        if format not in ['json', 'csv']:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        logger.info(f"Fetching report for run_id={run_id}, format={format}")
        
        result = service.get_report(
            run_id=run_id,
            tenant_id=tenant_id,
            format=format
        )
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        if format == 'csv':
            from fastapi.responses import Response
            return Response(
                content=result,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=impact_report_{run_id}.csv"
                }
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_json")
async def upload_deltas_json(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a JSON file containing change deltas
    
    File format:
    [
        {"clause_id": "4.2.4", "change_text": "...", "change_type": "modified"},
        {"clause_id": "7.5.1", "change_text": "...", "change_type": "new"}
    ]
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        # Read file
        content = await file.read()
        deltas = json.loads(content)
        
        if not isinstance(deltas, list):
            raise HTTPException(status_code=400, detail="JSON must be an array of deltas")
        
        # Validate deltas
        validated_deltas = []
        for delta in deltas:
            if not all(k in delta for k in ['clause_id', 'change_text']):
                raise HTTPException(status_code=400, detail="Each delta must have 'clause_id' and 'change_text'")
            validated_deltas.append(ChangeDelta(**delta))
        
        logger.info(f"Uploaded {len(validated_deltas)} deltas from file {file.filename}")
        
        # Run analysis
        service = get_change_impact_service()
        result = service.detect_impacts(
            tenant_id=tenant_id,
            deltas=[d.dict() for d in validated_deltas],
            top_k=5
        )
        
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
async def list_analysis_runs(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    List recent impact analysis runs
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import os
        
        conn_str = os.getenv(
            "POSTGRES_URL",
            "postgresql://qsp_user:qsp_secure_pass@localhost:5432/qsp_compliance"
        )
        
        with psycopg2.connect(conn_str) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        run_id::text, run_type, status, total_impacts,
                        started_at, completed_at
                    FROM analysis_runs
                    WHERE tenant_id = %s
                    ORDER BY started_at DESC
                    LIMIT %s
                """, (tenant_id, limit))
                
                runs = cur.fetchall()
                
                return {
                    "success": True,
                    "runs": [dict(row) for row in runs]
                }
        
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
