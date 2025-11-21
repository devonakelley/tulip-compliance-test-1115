"""
Change Impact Detection API
FastAPI router for regulatory change impact analysis
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import json
from core.change_impact_service_mongo import get_change_impact_service
from core.auth_utils import get_current_user_from_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/impact", tags=["change_impact"])
security = HTTPBearer()

# Database will be injected
db = None

def set_database(database):
    """Set database instance"""
    global db
    db = database

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user using shared auth function"""
    return await get_current_user_from_token(credentials, db)


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
    Fetches full diff_results from MongoDB to get old/new regulatory text
    Saves results to gap_results collection for persistence
    
    Request body:
    {
        "deltas": [
            {
                "clause_id": "4.2.4",
                "change_text": "Organizations must now maintain electronic records...",
                "change_type": "modified"
            }
        ],
        "top_k": 5,
        "diff_id": "uuid-of-diff-result"  # Optional - if provided, will fetch from MongoDB
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
        
        # Try to enrich deltas with full diff data from MongoDB
        # Look for the most recent diff_result for this tenant
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'compliance_checker')
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[db_name]
        
        # Find most recent diff_result for this tenant
        diff_result = await mongo_client[db_name].diff_results.find_one(
            {'tenant_id': tenant_id},
            sort=[('created_at', -1)]
        )
        
        if diff_result and diff_result.get('deltas'):
            logger.info(f"Found diff_result with {len(diff_result['deltas'])} deltas, enriching analysis data")
            
            # Create a lookup dict by clause_id
            diff_lookup = {d['clause_id']: d for d in diff_result['deltas']}
            
            # Enrich each delta with old/new text and other metadata
            for delta in deltas:
                clause_id = delta.get('clause_id')
                if clause_id in diff_lookup:
                    diff_data = diff_lookup[clause_id]
                    # Add old/new text (limit to 1000 chars)
                    delta['old_text'] = diff_data.get('old_text', '')[:1000] if diff_data.get('old_text') else ''
                    delta['new_text'] = diff_data.get('new_text', '')[:1000] if diff_data.get('new_text') else ''
                    delta['regulatory_doc'] = diff_data.get('regulatory_doc', 'ISO 14971:2020')
                    delta['reg_title'] = diff_data.get('reg_title', diff_data.get('title', ''))
        
        # Use analyze_with_cascade to include downstream impacts (Forms/WIs)
        cascade_result = await service.analyze_with_cascade(
            tenant_id=tenant_id,
            deltas=deltas,
            include_downstream=True
        )
        
        # Extract impacts from the nested structure
        impacts_list = cascade_result.get('impacts', {}).get('qsp_sections', [])
        run_id = cascade_result.get('run_id')
        
        # Create response in the format the frontend expects
        result = {
            'success': True,
            'run_id': run_id,
            'total_impacts_found': len(impacts_list),
            'impacts': impacts_list
        }
        
        # Save results to gap_results collection for persistence
        if impacts_list:
            import uuid
            from datetime import datetime, timezone
            
            # Save each impact as a separate document for easy updates
            for idx, impact in enumerate(impacts_list):
                gap_result = {
                    'id': str(uuid.uuid4()),
                    'run_id': run_id,
                    'tenant_id': tenant_id,
                    'user_id': current_user['id'],
                    'impact_index': idx,
                    'regulatory_clause': impact.get('regulatory_clause'),
                    'reg_clause': impact.get('reg_clause'),
                    'change_type': impact.get('change_type'),
                    'impact_level': impact.get('impact_level'),
                    'qsp_doc': impact.get('qsp_doc'),
                    'qsp_clause': impact.get('qsp_clause'),
                    'qsp_text': impact.get('qsp_text'),
                    'qsp_text_full': impact.get('qsp_text_full'),
                    'old_text': impact.get('old_text'),
                    'new_text': impact.get('new_text'),
                    'rationale': impact.get('rationale'),
                    'similarity_score': impact.get('similarity_score'),
                    'downstream_impacts': impact.get('downstream_impacts', {'forms': [], 'work_instructions': []}),  # NEW: Save cascade data
                    'is_reviewed': False,  # Default to not reviewed
                    'custom_rationale': '',  # Empty by default
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Upsert to avoid duplicates on re-run
                await mongo_client[db_name].gap_results.update_one(
                    {
                        'tenant_id': tenant_id,
                        'run_id': run_id,
                        'impact_index': idx
                    },
                    {'$set': gap_result},
                    upsert=True
                )
            
            logger.info(f"Saved {len(impacts_list)} gap results (with downstream impacts) to database")
        
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
    Note: In demo mode, runs are not persisted
    """
    try:
        # In production, this would query MongoDB for stored runs
        return {
            "success": True,
            "runs": [],
            "note": "Demo mode: Runs are not persisted. Results are shown immediately after analysis."
        }
        
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/update_result/{result_id}")
async def update_gap_result(
    result_id: str,
    is_reviewed: bool = None,
    custom_rationale: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Update gap analysis result review status and custom rationale
    Used for persisting user's review work
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        tenant_id = current_user["tenant_id"]
        
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'compliance_checker')
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[db_name]
        
        # Build update dict
        update_data = {}
        if is_reviewed is not None:
            update_data['is_reviewed'] = is_reviewed
        if custom_rationale is not None:
            update_data['custom_rationale'] = custom_rationale
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Add updated timestamp
        from datetime import datetime, timezone
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update in database
        result = await db.gap_results.update_one(
            {
                'id': result_id,
                'tenant_id': tenant_id  # Ensure tenant isolation
            },
            {'$set': update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Gap result not found")
        
        logger.info(f"Updated gap result {result_id} for tenant {tenant_id}")
        
        return {
            'success': True,
            'result_id': result_id,
            'updated_fields': list(update_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update gap result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{run_id}")
async def get_gap_results(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get saved gap analysis results for a specific run
    Includes review status and custom rationales
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        tenant_id = current_user["tenant_id"]
        
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'compliance_checker')
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[db_name]
        
        # Fetch all results for this run
        results = await db.gap_results.find({
            'run_id': run_id,
            'tenant_id': tenant_id
        }).sort('impact_index', 1).to_list(length=None)
        
        if not results:
            raise HTTPException(status_code=404, detail="No results found for this run")
        
        logger.info(f"Retrieved {len(results)} gap results for run {run_id}")
        
        return {
            'success': True,
            'run_id': run_id,
            'total_impacts_found': len(results),
            'impacts': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get gap results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

