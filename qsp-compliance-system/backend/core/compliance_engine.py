"""
Compliance analysis engine for Enterprise QSP System
Handles comprehensive compliance assessments and gap analysis
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid
import json

from ai import LLMService, AnalysisEngine
from database.models import ComplianceAnalysis, ComplianceGap, Document, DocumentSection
from models import ComplianceReport, AnalysisStatus, ComplianceLevel, SeverityLevel
from config import settings

logger = logging.getLogger(__name__)

class ComplianceEngine:
    """Advanced compliance analysis and reporting engine"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.analysis_engine = AnalysisEngine()
        
        # Analysis templates and rules
        self.compliance_frameworks = {
            "ISO_13485:2024": {
                "name": "ISO 13485:2024 - Medical Devices QMS",
                "required_clauses": [
                    "4.1", "4.2", "5.1", "5.2", "5.3", "5.4", "5.5", "5.6",
                    "6.1", "6.2", "6.3", "6.4", "7.1", "7.2", "7.3", "7.4",
                    "7.5", "7.6", "8.1", "8.2", "8.3", "8.4", "8.5"
                ],
                "critical_clauses": ["4.1", "7.3", "8.3", "8.5"],
                "risk_areas": ["design_control", "risk_management", "corrective_action"]
            }
        }
    
    async def start_compliance_analysis(
        self,
        document_ids: List[str],
        regulatory_framework: str,
        analysis_type: str,
        user_id: str,
        session
    ) -> str:
        """
        Start a comprehensive compliance analysis
        
        Args:
            document_ids: List of document IDs to analyze
            regulatory_framework: Regulatory framework to analyze against
            analysis_type: Type of analysis to perform
            user_id: User ID
            session: Database session
            
        Returns:
            Analysis ID
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            # Create analysis record
            analysis = {
                "_id": analysis_id,
                "user_id": user_id,
                "analysis_type": analysis_type,
                "regulatory_framework": regulatory_framework,
                "document_ids": document_ids,
                "status": "pending",
                "started_at": datetime.now(timezone.utc),
                "total_documents": len(document_ids),
                "analysis_parameters": {
                    "framework": regulatory_framework,
                    "type": analysis_type,
                    "ai_model": settings.DEFAULT_LLM_MODEL
                }
            }
            
            # Store in database
            await session.compliance_analyses.insert_one(analysis)
            
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
        Run compliance analysis asynchronously
        
        Args:
            analysis_id: Analysis ID
            session: Database session
            
        Returns:
            Analysis results
        """
        try:
            # Get analysis record
            analysis = await session.compliance_analyses.find_one({"_id": analysis_id})
            if not analysis:
                raise ValueError(f"Analysis not found: {analysis_id}")
            
            # Update status to running
            await session.compliance_analyses.update_one(
                {"_id": analysis_id},
                {"$set": {"status": "running", "updated_at": datetime.now(timezone.utc)}}
            )
            
            # Get documents
            documents = await self._get_analysis_documents(analysis["document_ids"], session)
            
            # Perform analysis based on type
            analysis_type = analysis.get("analysis_type", "full_compliance")
            framework = analysis.get("regulatory_framework", "ISO_13485:2024")
            
            results = None
            if analysis_type == "full_compliance":
                results = await self._run_full_compliance_analysis(documents, framework, session)
            elif analysis_type == "gap_analysis":
                results = await self._run_gap_analysis(documents, framework, session)
            elif analysis_type == "change_impact":
                results = await self._run_change_impact_analysis(documents, framework, session)
            else:
                results = await self._run_full_compliance_analysis(documents, framework, session)
            
            # Calculate overall compliance score
            overall_score = self._calculate_overall_score(results)
            compliance_level = self._determine_compliance_level(overall_score)
            
            # Store results
            final_results = {
                "analysis_id": analysis_id,
                "status": "completed",
                "completed_at": datetime.now(timezone.utc),
                "overall_compliance_score": overall_score,
                "compliance_level": compliance_level,
                "total_documents_analyzed": len(documents),
                "total_gaps_found": len(results.get("gaps", [])),
                "critical_gaps": len([g for g in results.get("gaps", []) if g.get("severity") == "critical"]),
                "detailed_results": results
            }
            
            # Update analysis record
            await session.compliance_analyses.update_one(
                {"_id": analysis_id},
                {"$set": final_results}
            )
            
            # Store individual gaps
            if results.get("gaps"):
                await self._store_compliance_gaps(analysis_id, results["gaps"], session)
            
            logger.info(f"Compliance analysis completed: {analysis_id}")
            return final_results
            
        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            
            # Update status to failed
            await session.compliance_analyses.update_one(
                {"_id": analysis_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            raise
    
    async def get_analysis_report(
        self,
        analysis_id: str,
        user_id: str,
        session
    ) -> Optional[ComplianceReport]:
        """
        Get compliance analysis report
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID (for authorization)
            session: Database session
            
        Returns:
            Compliance report or None
        """
        try:
            # Get analysis
            analysis = await session.compliance_analyses.find_one({
                "_id": analysis_id,
                "user_id": user_id
            })
            
            if not analysis:
                return None
            
            # Get gaps
            gaps_cursor = session.compliance_gaps.find({"analysis_id": analysis_id})
            gaps = await gaps_cursor.to_list(length=None)
            
            # Convert to ComplianceReport model
            report = ComplianceReport(
                analysis_id=analysis_id,
                request_id=analysis_id,
                user_id=user_id,
                status=AnalysisStatus(analysis.get("status", "pending")),
                regulatory_framework=analysis.get("regulatory_framework", ""),
                analysis_type=analysis.get("analysis_type", "full_compliance"),
                overall_compliance_score=analysis.get("overall_compliance_score"),
                compliance_level=ComplianceLevel(analysis.get("compliance_level", "requires_review")),
                total_documents=analysis.get("total_documents_analyzed", 0),
                total_sections_analyzed=analysis.get("total_sections_analyzed", 0),
                total_clauses_mapped=analysis.get("total_clauses_mapped", 0),
                gaps_by_severity=self._count_gaps_by_severity(gaps),
                started_at=analysis.get("started_at", datetime.now(timezone.utc)),
                completed_at=analysis.get("completed_at"),
                processing_time_seconds=self._calculate_processing_time(analysis),
                ai_model_used=analysis.get("analysis_parameters", {}).get("ai_model"),
                analysis_parameters=analysis.get("analysis_parameters", {}),
                compliance_gaps=[self._convert_gap_to_model(gap) for gap in gaps]
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to get analysis report: {e}")
            return None
    
    async def list_analyses(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        List user's compliance analyses
        
        Args:
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum results
            offset: Offset for pagination
            session: Database session
            
        Returns:
            List of analyses
        """
        try:
            query = {"user_id": user_id}
            
            if status:
                query["status"] = status
            
            # Get analyses with pagination
            cursor = session.compliance_analyses.find(query).sort("started_at", -1).skip(offset).limit(limit)
            analyses = await cursor.to_list(length=None)
            
            # Convert to simple format
            result = []
            for analysis in analyses:
                result.append({
                    "analysis_id": analysis["_id"],
                    "status": analysis.get("status"),
                    "regulatory_framework": analysis.get("regulatory_framework"),
                    "analysis_type": analysis.get("analysis_type"),
                    "started_at": analysis.get("started_at"),
                    "completed_at": analysis.get("completed_at"),
                    "total_documents": analysis.get("total_documents", 0),
                    "overall_compliance_score": analysis.get("overall_compliance_score"),
                    "total_gaps_found": analysis.get("total_gaps_found", 0)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list analyses: {e}")
            return []
    
    # Private methods
    
    async def _get_analysis_documents(self, document_ids: List[str], session) -> List[Dict[str, Any]]:
        """Get documents for analysis"""
        try:
            # Get documents from database
            documents = []
            
            for doc_id in document_ids:
                doc = await session.documents.find_one({"_id": doc_id})
                if doc:
                    # Get document sections
                    sections_cursor = session.document_sections.find({"document_id": doc_id})
                    sections = await sections_cursor.to_list(length=None)
                    
                    documents.append({
                        "id": doc_id,
                        "filename": doc.get("filename"),
                        "document_type": doc.get("document_type"),
                        "content": doc.get("content", ""),
                        "sections": sections
                    })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get analysis documents: {e}")
            return []
    
    async def _run_full_compliance_analysis(
        self,
        documents: List[Dict[str, Any]],
        framework: str,
        session
    ) -> Dict[str, Any]:
        """Run comprehensive compliance analysis"""
        try:
            framework_config = self.compliance_frameworks.get(framework, {})
            required_clauses = framework_config.get("required_clauses", [])
            
            # Use AI analysis engine
            if self.analysis_engine:
                analysis_results = await self.analysis_engine.perform_gap_analysis(
                    documents, framework, required_clauses
                )
                
                return {
                    "gaps": analysis_results.get("gaps_identified", []),
                    "compliance_scores": analysis_results.get("compliance_scores", {}),
                    "recommendations": analysis_results.get("recommendations", []),
                    "method": "ai_powered"
                }
            
            # Fallback to basic analysis
            return await self._fallback_compliance_analysis(documents, framework)
            
        except Exception as e:
            logger.error(f"Full compliance analysis failed: {e}")
            return await self._fallback_compliance_analysis(documents, framework)
    
    async def _run_gap_analysis(
        self,
        documents: List[Dict[str, Any]],
        framework: str,
        session
    ) -> Dict[str, Any]:
        """Run gap analysis"""
        # For now, same as full analysis but focused on gaps
        return await self._run_full_compliance_analysis(documents, framework, session)
    
    async def _run_change_impact_analysis(
        self,
        documents: List[Dict[str, Any]],
        framework: str,
        session
    ) -> Dict[str, Any]:
        """Run regulatory change impact analysis"""
        try:
            # Get recent regulatory changes
            changes_cursor = session.regulatory_changes.find({
                "effective_date": {"$gte": datetime.now(timezone.utc).replace(day=1)}
            }).sort("effective_date", -1)
            
            changes = await changes_cursor.to_list(length=None)
            
            # Analyze impact using AI
            if self.analysis_engine and changes:
                impact_results = await self.analysis_engine.analyze_regulatory_impact(
                    changes, documents
                )
                return impact_results
            
            return {
                "gaps": [],
                "impact_summary": "No recent regulatory changes found",
                "method": "change_impact"
            }
            
        except Exception as e:
            logger.error(f"Change impact analysis failed: {e}")
            return {"gaps": [], "error": str(e)}
    
    async def _fallback_compliance_analysis(
        self,
        documents: List[Dict[str, Any]],
        framework: str
    ) -> Dict[str, Any]:
        """Fallback compliance analysis without AI"""
        logger.info("Using fallback compliance analysis")
        
        gaps = []
        compliance_scores = {}
        
        framework_config = self.compliance_frameworks.get(framework, {})
        required_clauses = framework_config.get("required_clauses", [])
        critical_clauses = framework_config.get("critical_clauses", [])
        
        for doc in documents:
            content = doc.get("content", "").lower()
            doc_score = 0.0
            
            # Check for required clauses using keyword matching
            for clause in required_clauses:
                clause_found = False
                
                # Simple keyword matching for common clauses
                clause_keywords = {
                    "4.1": ["quality management system", "qms", "general requirements"],
                    "4.2": ["documentation", "document control", "records"],
                    "7.3": ["design", "development", "validation", "verification"],
                    "8.3": ["nonconforming", "non-conforming", "corrective action"],
                    "8.5": ["improvement", "corrective", "preventive"]
                }
                
                keywords = clause_keywords.get(clause, [])
                if keywords and any(keyword in content for keyword in keywords):
                    clause_found = True
                    doc_score += 4.0  # Each clause worth ~4 points (25 clauses = 100 points)
                
                if not clause_found:
                    severity = "critical" if clause in critical_clauses else "medium"
                    gaps.append({
                        "document_id": doc["id"],
                        "clause_id": clause,
                        "gap_type": "missing",
                        "severity": severity,
                        "description": f"No evidence of compliance with clause {clause}",
                        "recommendations": [f"Implement procedures for clause {clause}"]
                    })
            
            compliance_scores[doc["id"]] = min(doc_score, 100.0)
        
        return {
            "gaps": gaps,
            "compliance_scores": compliance_scores,
            "recommendations": ["Conduct detailed review of missing clauses"],
            "method": "keyword_based"
        }
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        try:
            scores = results.get("compliance_scores", {})
            if not scores:
                return 0.0
            
            return sum(scores.values()) / len(scores)
            
        except Exception:
            return 0.0
    
    def _determine_compliance_level(self, score: float) -> str:
        """Determine compliance level from score"""
        if score >= 90:
            return "compliant"
        elif score >= 70:
            return "partially_compliant"
        elif score >= 50:
            return "requires_review"
        else:
            return "non_compliant"
    
    async def _store_compliance_gaps(self, analysis_id: str, gaps: List[Dict[str, Any]], session):
        """Store compliance gaps in database"""
        try:
            if not gaps:
                return
            
            gap_records = []
            for gap in gaps:
                gap_record = {
                    "_id": str(uuid.uuid4()),
                    "analysis_id": analysis_id,
                    "regulatory_framework": "ISO_13485:2024",  # Should come from analysis
                    "clause_id": gap.get("clause_id", "unknown"),
                    "clause_title": gap.get("clause_title", ""),
                    "gap_type": gap.get("gap_type", "missing"),
                    "severity": gap.get("severity", "medium"),
                    "description": gap.get("description", ""),
                    "affected_documents": gap.get("affected_documents", [gap.get("document_id")]),
                    "recommendations": gap.get("recommendations", []),
                    "status": "open",
                    "detected_date": datetime.now(timezone.utc)
                }
                gap_records.append(gap_record)
            
            await session.compliance_gaps.insert_many(gap_records)
            logger.info(f"Stored {len(gap_records)} compliance gaps")
            
        except Exception as e:
            logger.error(f"Failed to store compliance gaps: {e}")
    
    def _count_gaps_by_severity(self, gaps: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count gaps by severity level"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for gap in gaps:
            severity = gap.get("severity", "medium")
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    def _calculate_processing_time(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Calculate analysis processing time"""
        try:
            started_at = analysis.get("started_at")
            completed_at = analysis.get("completed_at")
            
            if started_at and completed_at:
                return (completed_at - started_at).total_seconds()
            
            return None
            
        except Exception:
            return None
    
    def _convert_gap_to_model(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """Convert gap record to model format"""
        return {
            "gap_id": gap.get("_id"),
            "analysis_id": gap.get("analysis_id"),
            "regulatory_framework": gap.get("regulatory_framework"),
            "clause_id": gap.get("clause_id"),
            "clause_title": gap.get("clause_title", ""),
            "gap_type": gap.get("gap_type"),
            "severity": SeverityLevel(gap.get("severity", "medium")),
            "description": gap.get("description"),
            "affected_documents": gap.get("affected_documents", []),
            "recommendations": gap.get("recommendations", []),
            "detected_date": gap.get("detected_date"),
            "status": gap.get("status", "open")
        }