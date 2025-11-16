"""
Dashboard Metrics API
Provides real-time metrics from MongoDB for dashboard display
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.auth_utils import get_current_user_from_token
import logging
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Database will be injected
db = None

def set_database(database):
    """Set database instance"""
    global db
    db = database

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user using shared auth function"""
    return await get_current_user_from_token(credentials, db)


@router.get("/metrics")
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    """
    Get real-time dashboard metrics for current tenant
    
    Returns:
    - total_documents: Count of uploaded QSP documents
    - total_diffs: Count of regulatory diffs generated
    - total_gaps: Count of compliance gaps identified
    - total_reviewed: Count of gaps marked as reviewed
    - total_users: Count of users in tenant
    - compliance_score: Calculated compliance percentage
    - last_analysis_date: Most recent gap analysis timestamp
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        # Count QSP documents
        total_documents = await db.qsp_sections.distinct("doc_id", {"tenant_id": tenant_id})
        total_documents_count = len(total_documents)
        
        # Count regulatory diffs
        total_diffs = await db.diff_results.count_documents({"tenant_id": tenant_id})
        
        # Count total gaps from analysis results
        gap_results = await db.gap_results.find({"tenant_id": tenant_id}).to_list(length=None)
        total_gaps = len(gap_results)
        
        # Count reviewed gaps
        total_reviewed = await db.gap_results.count_documents({
            "tenant_id": tenant_id,
            "is_reviewed": True
        })
        
        # Count users in tenant
        total_users = await db.users.count_documents({"tenant_id": tenant_id})
        
        # Calculate compliance score
        if total_gaps > 0:
            compliance_score = round((total_reviewed / total_gaps) * 100)
        else:
            compliance_score = 100  # No gaps = 100% compliant
        
        # Get last analysis date
        last_analysis = await db.gap_results.find_one(
            {"tenant_id": tenant_id},
            sort=[("created_at", -1)]
        )
        last_analysis_date = last_analysis["created_at"] if last_analysis else None
        
        # Count new vs modified clauses from diffs
        new_clauses_count = 0
        modified_clauses_count = 0
        
        diff_result = await db.diff_results.find_one(
            {"tenant_id": tenant_id},
            sort=[("created_at", -1)]
        )
        
        if diff_result and diff_result.get("deltas"):
            for delta in diff_result["deltas"]:
                change_type = delta.get("change_type", "").lower()
                if change_type in ["added", "new"]:
                    new_clauses_count += 1
                elif change_type == "modified":
                    modified_clauses_count += 1
        
        # Get total mappings (clauses mapped)
        total_mappings = await db.qsp_sections.count_documents({"tenant_id": tenant_id})
        
        logger.info(f"Dashboard metrics retrieved for tenant {tenant_id}")
        
        return {
            "success": True,
            "total_documents": total_documents_count,
            "total_diffs": total_diffs,
            "total_gaps": total_gaps,
            "total_reviewed": total_reviewed,
            "total_users": total_users,
            "compliance_score": compliance_score,
            "gaps_count": total_gaps,
            "new_clauses_count": new_clauses_count,
            "modified_clauses_count": modified_clauses_count,
            "total_mappings": total_mappings,
            "last_analysis_date": last_analysis_date,
            "iso_summary_loaded": total_diffs > 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
