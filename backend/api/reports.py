"""
Reports API - Endpoints for retrieving compliance analysis reports
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.auth import get_current_user
from core.report_service import ReportService
from core.audit_logger import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

# Database will be injected from main server
db: AsyncIOMotorDatabase = None

def set_database(database):
    """Set database instance"""
    global db
    db = database

@router.get("", response_model=Dict[str, Any])
async def list_reports(
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    List all compliance reports for the current tenant
    
    Query params:
        - limit: Maximum number of reports (default: 50)
        - skip: Number of reports to skip for pagination (default: 0)
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        report_service = ReportService(db)
        reports = await report_service.list_reports(tenant_id, limit=limit, skip=skip)
        
        # Log audit event
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=current_user["user_id"],
            action="view_reports",
            target="reports_list",
            metadata={"count": len(reports)}
        )
        
        return {
            "status": "success",
            "count": len(reports),
            "reports": reports
        }
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")

@router.get("/stats", response_model=Dict[str, Any])
async def get_report_stats(current_user: dict = Depends(get_current_user)):
    """
    Get report statistics for the current tenant
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        report_service = ReportService(db)
        stats = await report_service.get_report_stats(tenant_id)
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting report stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report statistics")

@router.get("/audit-logs", response_model=Dict[str, Any])
async def get_audit_logs(
    action: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit logs for the current tenant
    
    Query params:
        - action: Filter by action type (optional)
        - limit: Maximum number of logs (default: 100)
        - skip: Number of logs to skip for pagination (default: 0)
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        logs = await audit_logger.get_audit_logs(
            tenant_id=tenant_id,
            action=action,
            limit=limit,
            skip=skip
        )
        
        return {
            "status": "success",
            "count": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")

@router.get("/audit-stats", response_model=Dict[str, Any])
async def get_audit_stats(current_user: dict = Depends(get_current_user)):
    """
    Get audit statistics for the current tenant
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        stats = await audit_logger.get_audit_stats(tenant_id)
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting audit stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit statistics")
