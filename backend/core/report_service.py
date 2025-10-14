"""
Report Service - Persistence and retrieval for compliance analysis reports
Saves reports to local storage or S3 and maintains metadata in MongoDB
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class ReportService:
    """Service for managing compliance analysis reports"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["reports"]
        self.base_dir = os.getenv("LOCAL_UPLOAD_DIR", "uploads")
        self.reports_dir = "_reports"
    
    async def save_report(
        self,
        tenant_id: str,
        user_id: str,
        filename: str,
        analysis_type: str,
        results: Dict[str, Any]
    ) -> str:
        """
        Save compliance analysis report
        
        Args:
            tenant_id: Tenant identifier
            user_id: User who ran the analysis
            filename: Original document filename
            analysis_type: Type of analysis (e.g., 'compliance_map', 'gap_analysis')
            results: Analysis results dictionary
            
        Returns:
            Path to saved report file
        """
        try:
            # Generate unique report filename
            timestamp = datetime.now(timezone.utc).isoformat().replace(':', '').replace('-', '').split('.')[0]
            report_name = f"{analysis_type}_{timestamp}.json"
            
            # Create tenant-specific report directory
            report_path = Path(self.base_dir) / self.reports_dir / tenant_id
            report_path.mkdir(parents=True, exist_ok=True)
            
            full_path = report_path / report_name
            
            # Save report JSON to file
            with open(full_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            
            # Extract summary data
            summary = results.get("summary", "")
            if isinstance(summary, dict):
                summary = summary.get("message", str(summary))
            
            alignment_score = results.get("overall_score", results.get("alignment_score", 0.0))
            
            # Save metadata to MongoDB
            report_doc = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "filename": filename,
                "analysis_type": analysis_type,
                "report_path": str(full_path),
                "summary": str(summary)[:500],  # Truncate for storage
                "alignment_score": float(alignment_score),
                "total_documents": results.get("total_documents_processed", results.get("total_documents", 0)),
                "gaps_found": results.get("gaps_found", len(results.get("gaps", []))),
                "created_at": datetime.now(timezone.utc)
            }
            
            await self.collection.insert_one(report_doc)
            
            logger.info(f"Report saved: {report_name} for tenant {tenant_id}")
            return str(full_path)
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise
    
    async def list_reports(
        self,
        tenant_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all reports for a tenant
        
        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of reports to return
            skip: Number of reports to skip (for pagination)
            
        Returns:
            List of report metadata dictionaries
        """
        try:
            cursor = self.collection.find(
                {"tenant_id": tenant_id},
                {"_id": 0}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            reports = await cursor.to_list(length=limit)
            
            # Convert datetime objects to ISO strings
            for report in reports:
                if isinstance(report.get("created_at"), datetime):
                    report["created_at"] = report["created_at"].isoformat()
            
            return reports
            
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []
    
    async def get_report(
        self,
        tenant_id: str,
        report_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific report's content
        
        Args:
            tenant_id: Tenant identifier (for security check)
            report_path: Path to the report file
            
        Returns:
            Report content as dictionary, or None if not found
        """
        try:
            # Verify the report belongs to the tenant
            report_meta = await self.collection.find_one({
                "tenant_id": tenant_id,
                "report_path": report_path
            })
            
            if not report_meta:
                logger.warning(f"Report not found or access denied: {report_path}")
                return None
            
            # Read report file
            if os.path.exists(report_path):
                with open(report_path, "r") as f:
                    return json.load(f)
            else:
                logger.error(f"Report file not found: {report_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve report: {e}")
            return None
    
    async def get_report_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics about reports for a tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Statistics dictionary
        """
        try:
            total_reports = await self.collection.count_documents({"tenant_id": tenant_id})
            
            # Get average alignment score
            pipeline = [
                {"$match": {"tenant_id": tenant_id}},
                {"$group": {
                    "_id": None,
                    "avg_score": {"$avg": "$alignment_score"},
                    "total_gaps": {"$sum": "$gaps_found"}
                }}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            
            stats = {
                "total_reports": total_reports,
                "average_alignment_score": result[0]["avg_score"] if result else 0.0,
                "total_gaps_identified": result[0]["total_gaps"] if result else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get report stats: {e}")
            return {
                "total_reports": 0,
                "average_alignment_score": 0.0,
                "total_gaps_identified": 0
            }
