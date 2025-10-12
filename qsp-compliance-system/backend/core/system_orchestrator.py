"""
System orchestrator for Enterprise QSP Compliance System
Coordinates all system components and workflows
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from document_processor import DocumentProcessor
from regulatory_analyzer import RegulatoryAnalyzer
from compliance_engine import ComplianceEngine
from cache import CacheManager
from models import SystemStatus
from config import settings

logger = logging.getLogger(__name__)

class SystemOrchestrator:
    """Central orchestrator for system operations"""
    
    def __init__(
        self,
        document_processor: DocumentProcessor,
        regulatory_analyzer: RegulatoryAnalyzer,
        compliance_engine: ComplianceEngine,
        cache_manager: CacheManager
    ):
        self.document_processor = document_processor
        self.regulatory_analyzer = regulatory_analyzer
        self.compliance_engine = compliance_engine
        self.cache_manager = cache_manager
        
        # Task tracking
        self.active_tasks = {}
        self.task_history = []
        
    async def get_system_status(self, session) -> SystemStatus:
        """
        Get comprehensive system status
        
        Args:
            session: Database session
            
        Returns:
            System status
        """
        try:
            from database import mongodb_manager
            
            # Get database stats
            db_stats = await mongodb_manager.get_stats()
            
            # Get cache stats
            cache_stats = self.cache_manager.get_stats() if hasattr(self.cache_manager, 'get_stats') else {}
            
            # Calculate system metrics
            uptime_seconds = self._get_system_uptime()
            
            status = SystemStatus(
                status="healthy",
                version=settings.VERSION,
                uptime_seconds=uptime_seconds,
                total_documents=db_stats.get("total_documents", 0),
                active_analyses=len([t for t in self.active_tasks.values() if t.get("type") == "analysis"]),
                completed_analyses_today=db_stats.get("analyses_last_24h", 0),
                average_analysis_time_minutes=self._calculate_avg_analysis_time(),
                database_response_time_ms=db_stats.get("response_time_ms", 0),
                cache_hit_rate=cache_stats.get("hit_rate", 0.0),
                cache_size_mb=cache_stats.get("memory_usage_bytes", 0) / 1024 / 1024
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return SystemStatus(
                status="unhealthy",
                version=settings.VERSION,
                uptime_seconds=0
            )
    
    async def process_document_async(
        self,
        document_id: str,
        session
    ) -> bool:
        """
        Process document asynchronously
        
        Args:
            document_id: Document ID
            session: Database session
            
        Returns:
            Success status
        """
        task_id = f"doc_process_{document_id}"
        
        try:
            # Track task
            self.active_tasks[task_id] = {
                "type": "document_processing",
                "document_id": document_id,
                "started_at": datetime.now(timezone.utc),
                "status": "processing"
            }
            
            # Process document
            success = await self.document_processor.process_document_async(document_id, session)
            
            # Update task status
            self.active_tasks[task_id]["status"] = "completed" if success else "failed"
            self.active_tasks[task_id]["completed_at"] = datetime.now(timezone.utc)
            
            # Move to history
            self.task_history.append(self.active_tasks.pop(task_id))
            
            # Limit history size
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-1000:]
            
            logger.info(f"Document processing {'succeeded' if success else 'failed'}: {document_id}")
            return success
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            
            # Update task status
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)
                self.active_tasks[task_id]["completed_at"] = datetime.now(timezone.utc)
                self.task_history.append(self.active_tasks.pop(task_id))
            
            return False
    
    async def start_compliance_analysis(
        self,
        document_ids: List[str],
        regulatory_framework: str,
        analysis_type: str,
        user_id: str,
        session
    ) -> str:
        """
        Start compliance analysis workflow
        
        Args:
            document_ids: Document IDs to analyze
            regulatory_framework: Regulatory framework
            analysis_type: Type of analysis
            user_id: User ID
            session: Database session
            
        Returns:
            Analysis ID
        """
        try:
            # Start compliance analysis
            analysis_id = await self.compliance_engine.start_compliance_analysis(
                document_ids, regulatory_framework, analysis_type, user_id, session
            )
            
            # Track task
            task_id = f"analysis_{analysis_id}"
            self.active_tasks[task_id] = {
                "type": "analysis",
                "analysis_id": analysis_id,
                "document_ids": document_ids,
                "user_id": user_id,
                "started_at": datetime.now(timezone.utc),
                "status": "started"
            }
            
            logger.info(f"Compliance analysis started: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Failed to start compliance analysis: {e}")
            raise
    
    async def run_analysis_async(
        self,
        analysis_id: str,
        session
    ) -> Dict[str, Any]:
        """
        Run analysis asynchronously
        
        Args:
            analysis_id: Analysis ID
            session: Database session
            
        Returns:
            Analysis results
        """
        task_id = f"analysis_{analysis_id}"
        
        try:
            # Update task status
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "running"
            
            # Run analysis
            results = await self.compliance_engine.run_analysis_async(analysis_id, session)
            
            # Update task status
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "completed"
                self.active_tasks[task_id]["completed_at"] = datetime.now(timezone.utc)
                self.task_history.append(self.active_tasks.pop(task_id))
            
            logger.info(f"Analysis completed successfully: {analysis_id}")
            return results
            
        except Exception as e:
            logger.error(f"Analysis execution error: {e}")
            
            # Update task status
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)
                self.active_tasks[task_id]["completed_at"] = datetime.now(timezone.utc)
                self.task_history.append(self.active_tasks.pop(task_id))
            
            raise
    
    async def process_regulatory_changes(
        self,
        framework: str,
        summary_version: str,
        user_id: str,
        session
    ) -> Dict[str, Any]:
        """
        Process regulatory changes and analyze impact
        
        Args:
            framework: Regulatory framework
            summary_version: Summary version
            user_id: User ID
            session: Database session
            
        Returns:
            Processing results
        """
        task_id = f"reg_change_{framework}_{summary_version}"
        
        try:
            # Track task
            self.active_tasks[task_id] = {
                "type": "regulatory_processing",
                "framework": framework,
                "summary_version": summary_version,
                "user_id": user_id,
                "started_at": datetime.now(timezone.utc),
                "status": "processing"
            }
            
            # Process regulatory summary
            summary_task_id = await self.regulatory_analyzer.process_summary(
                framework, summary_version, user_id, session
            )
            
            # Run background processing
            results = await self.regulatory_analyzer.process_summary_async(
                summary_task_id, framework, summary_version, user_id, session
            )
            
            # Update task status
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["completed_at"] = datetime.now(timezone.utc)
            self.active_tasks[task_id]["results"] = results
            
            # Move to history
            self.task_history.append(self.active_tasks.pop(task_id))
            
            logger.info(f"Regulatory changes processed: {framework} {summary_version}")
            return results
            
        except Exception as e:
            logger.error(f"Regulatory processing error: {e}")
            
            # Update task status
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)
                self.active_tasks[task_id]["completed_at"] = datetime.now(timezone.utc)
                self.task_history.append(self.active_tasks.pop(task_id))
            
            raise
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of active tasks
        
        Returns:
            List of active tasks
        """
        return list(self.active_tasks.values())
    
    async def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get task history
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of historical tasks
        """
        return self.task_history[-limit:]
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel an active task
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was cancelled
        """
        try:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task["status"] = "cancelled"
                task["completed_at"] = datetime.now(timezone.utc)
                
                self.task_history.append(self.active_tasks.pop(task_id))
                
                logger.info(f"Task cancelled: {task_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        try:
            # Remove tasks older than 24 hours
            cutoff_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_time = cutoff_time.replace(day=cutoff_time.day - 1)
            
            original_count = len(self.task_history)
            self.task_history = [
                task for task in self.task_history
                if task.get("completed_at", datetime.now(timezone.utc)) > cutoff_time
            ]
            
            cleaned_count = original_count - len(self.task_history)
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old tasks")
            
        except Exception as e:
            logger.error(f"Task cleanup error: {e}")
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            return {
                "active_tasks": len(self.active_tasks),
                "task_history_count": len(self.task_history),
                "tasks_by_type": self._count_tasks_by_type(),
                "avg_task_duration": self._calculate_avg_task_duration(),
                "system_uptime_seconds": self._get_system_uptime()
            }
            
        except Exception as e:
            logger.error(f"Failed to get orchestrator stats: {e}")
            return {}
    
    # Private helper methods
    
    def _get_system_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds
        except Exception:
            return 0.0
    
    def _calculate_avg_analysis_time(self) -> Optional[float]:
        """Calculate average analysis time in minutes"""
        try:
            analysis_tasks = [
                task for task in self.task_history
                if task.get("type") == "analysis" and task.get("completed_at")
            ]
            
            if not analysis_tasks:
                return None
            
            total_duration = 0
            count = 0
            
            for task in analysis_tasks[-50:]:  # Last 50 analyses
                started = task.get("started_at")
                completed = task.get("completed_at")
                
                if started and completed:
                    duration = (completed - started).total_seconds() / 60  # Minutes
                    total_duration += duration
                    count += 1
            
            return total_duration / count if count > 0 else None
            
        except Exception:
            return None
    
    def _count_tasks_by_type(self) -> Dict[str, int]:
        """Count tasks by type"""
        counts = {}
        
        # Count active tasks
        for task in self.active_tasks.values():
            task_type = task.get("type", "unknown")
            counts[f"active_{task_type}"] = counts.get(f"active_{task_type}", 0) + 1
        
        # Count recent history (last 100)
        for task in self.task_history[-100:]:
            task_type = task.get("type", "unknown")
            counts[f"recent_{task_type}"] = counts.get(f"recent_{task_type}", 0) + 1
        
        return counts
    
    def _calculate_avg_task_duration(self) -> Optional[float]:
        """Calculate average task duration in seconds"""
        try:
            completed_tasks = [
                task for task in self.task_history[-100:]  # Last 100 tasks
                if task.get("completed_at") and task.get("started_at")
            ]
            
            if not completed_tasks:
                return None
            
            total_duration = 0
            for task in completed_tasks:
                duration = (task["completed_at"] - task["started_at"]).total_seconds()
                total_duration += duration
            
            return total_duration / len(completed_tasks)
            
        except Exception:
            return None