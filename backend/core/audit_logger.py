"""
Audit Logger - Structured logging for all tenant actions
Logs to both file and MongoDB for compliance and security auditing
"""
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

# Configure file-based audit logging
audit_log_path = Path("logs/audit.log")
audit_log_path.parent.mkdir(parents=True, exist_ok=True)

audit_file_logger = logging.getLogger("audit")
audit_file_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(audit_log_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(message)s'))
audit_file_logger.addHandler(file_handler)

class AuditLogger:
    """Audit logging service for tenant actions"""
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.collection = db["audit_logs"] if db else None
    
    def set_database(self, db: AsyncIOMotorDatabase):
        """Set database connection"""
        self.db = db
        self.collection = db["audit_logs"]
    
    async def log_action(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        target: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """
        Log an audit event
        
        Args:
            tenant_id: Tenant identifier
            user_id: User who performed the action
            action: Action type (e.g., 'upload', 'analyze', 'login')
            target: Target of the action (e.g., filename, resource)
            metadata: Additional context data
            status: Action status ('success', 'failure', 'error')
        """
        try:
            record = {
                "timestamp": datetime.now(timezone.utc),
                "tenant_id": tenant_id,
                "user_id": user_id,
                "action": action,
                "target": target,
                "status": status,
                "metadata": metadata or {}
            }
            
            # Log to file (synchronous)
            file_record = record.copy()
            file_record["timestamp"] = file_record["timestamp"].isoformat()
            audit_file_logger.info(json.dumps(file_record))
            
            # Log to MongoDB (asynchronous)
            if self.collection is not None:
                await self.collection.insert_one(record)
            
        except Exception as e:
            # Audit logging should never break the application
            logging.error(f"Audit logging failed: {e}")
    
    async def log_upload(
        self,
        tenant_id: str,
        user_id: str,
        filename: str,
        file_type: str,
        file_size: Optional[int] = None
    ):
        """Log document upload event"""
        await self.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="upload",
            target=filename,
            metadata={
                "file_type": file_type,
                "file_size": file_size
            }
        )
    
    async def log_analysis(
        self,
        tenant_id: str,
        user_id: str,
        analysis_type: str,
        document_count: int,
        report_path: Optional[str] = None
    ):
        """Log analysis execution event"""
        await self.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="analyze",
            target=analysis_type,
            metadata={
                "document_count": document_count,
                "report_path": report_path
            }
        )
    
    async def log_login(
        self,
        tenant_id: str,
        user_id: str,
        email: str,
        ip_address: Optional[str] = None
    ):
        """Log user login event"""
        await self.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="login",
            target=email,
            metadata={
                "ip_address": ip_address
            }
        )
    
    async def get_audit_logs(
        self,
        tenant_id: str,
        action: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> list:
        """
        Retrieve audit logs for a tenant
        
        Args:
            tenant_id: Tenant identifier
            action: Optional filter by action type
            limit: Maximum number of logs to return
            skip: Number of logs to skip (pagination)
            
        Returns:
            List of audit log entries
        """
        if not self.collection:
            return []
        
        try:
            query = {"tenant_id": tenant_id}
            if action:
                query["action"] = action
            
            cursor = self.collection.find(
                query,
                {"_id": 0}
            ).sort("timestamp", -1).skip(skip).limit(limit)
            
            logs = await cursor.to_list(length=limit)
            
            # Convert datetime to ISO string
            for log in logs:
                if isinstance(log.get("timestamp"), datetime):
                    log["timestamp"] = log["timestamp"].isoformat()
            
            return logs
            
        except Exception as e:
            logging.error(f"Failed to retrieve audit logs: {e}")
            return []
    
    async def get_audit_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get audit statistics for a tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Statistics dictionary
        """
        if not self.collection:
            return {}
        
        try:
            pipeline = [
                {"$match": {"tenant_id": tenant_id}},
                {"$group": {
                    "_id": "$action",
                    "count": {"$sum": 1}
                }}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=None)
            
            stats = {item["_id"]: item["count"] for item in result}
            stats["total_actions"] = sum(stats.values())
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get audit stats: {e}")
            return {}

# Global audit logger instance
audit_logger = AuditLogger()
