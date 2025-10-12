"""
Regulatory Impact Analyzer for QSP documents
Uses RAG system to identify specific impacts of regulatory changes
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from ..rag import RAGEngine
from ..ai import LLMService

logger = logging.getLogger(__name__)

class ImpactAnalyzer:
    """
    Analyzes impact of regulatory changes on QSP documents
    Generates specific alerts like "ISO change detected that impacts QSP doc X in section X"
    """
    
    def __init__(self):
        """Initialize impact analyzer"""
        self.rag_engine = RAGEngine()
        self.llm_service = LLMService()
        
    async def analyze_regulatory_change_impact(
        self,
        regulatory_change: Dict[str, Any],
        target_documents: Optional[List[str]] = None,
        session=None
    ) -> Dict[str, Any]:
        """
        Analyze impact of a regulatory change on QSP documents
        
        Args:
            regulatory_change: Regulatory change data with description, clause_id, etc.
            target_documents: Optional list of document IDs to analyze (None = all documents)
            session: Database session
            
        Returns:
            Impact analysis results with specific alerts
        """
        try:
            logger.info(f"Analyzing impact of regulatory change: {regulatory_change.get('clause_id', 'unknown')}")
            
            # Initialize RAG engine if needed
            if not self.rag_engine._initialized:
                await self.rag_engine.initialize()
            
            # Use RAG engine to analyze impact
            impact_analysis = await self.rag_engine.analyze_regulatory_impact(
                iso_change=regulatory_change,
                document_ids=target_documents
            )
            
            if not impact_analysis.get('success'):
                return impact_analysis
            
            # Generate specific alerts
            alerts = await self._generate_specific_alerts(
                regulatory_change, impact_analysis, session
            )
            
            # Store impact analysis results
            analysis_record = {
                "_id": str(uuid.uuid4()),
                "regulatory_change": regulatory_change,
                "analysis_date": datetime.now(timezone.utc),
                "target_documents": target_documents,
                "impact_summary": impact_analysis.get('summary', {}),
                "total_impacts": len(impact_analysis.get('impacts', [])),
                "alerts_generated": len(alerts),
                "impacts": impact_analysis.get('impacts', []),
                "alerts": alerts
            }
            
            if session:
                await session.regulatory_impact_analyses.insert_one(analysis_record)
                logger.info(f"Stored impact analysis: {analysis_record['_id']}")
            
            return {
                'success': True,
                'analysis_id': analysis_record['_id'],
                'regulatory_change': regulatory_change,
                'impact_summary': impact_analysis.get('summary', {}),
                'total_impacted_sections': len(impact_analysis.get('impacts', [])),
                'alerts': alerts,
                'detailed_impacts': impact_analysis.get('impacts', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze regulatory change impact: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_specific_alerts(
        self,
        regulatory_change: Dict[str, Any],
        impact_analysis: Dict[str, Any],
        session=None
    ) -> List[Dict[str, Any]]:
        """Generate specific alerts for each detected impact"""
        
        alerts = []
        impacts = impact_analysis.get('impacts', [])
        
        for impact in impacts:
            # Skip low confidence or low impact detections
            if (impact.get('confidence_score', 0) < 0.7 or 
                impact.get('impact_level') == 'low'):
                continue
            
            # Get document details if session available
            document_title = "Unknown Document"
            if session and impact.get('document_id'):
                try:
                    doc = await session.documents.find_one(
                        {"_id": impact['document_id']},
                        {"filename": 1, "document_type": 1}
                    )
                    if doc:
                        document_title = doc.get('filename', 'Unknown Document')
                except Exception as e:
                    logger.warning(f"Failed to get document details: {e}")
            
            # Create specific alert message
            section_ref = ""
            if impact.get('section_number') and impact.get('section_title'):
                section_ref = f" in section {impact['section_number']} ({impact['section_title']})"
            elif impact.get('section_number'):
                section_ref = f" in section {impact['section_number']}"
            
            alert_message = (
                f"ISO change detected that impacts {document_title}{section_ref}. "
                f"Regulatory change in clause {regulatory_change.get('clause_id', 'N/A')} "
                f"({regulatory_change.get('clause_title', 'N/A')}) requires review and potential updates."
            )
            
            alert = {
                "alert_id": str(uuid.uuid4()),
                "alert_type": "regulatory_impact",
                "priority": self._map_impact_to_priority(impact.get('impact_level', 'medium')),
                "message": alert_message,
                "regulatory_change": {
                    "clause_id": regulatory_change.get('clause_id'),
                    "clause_title": regulatory_change.get('clause_title'),
                    "description": regulatory_change.get('description')
                },
                "affected_document": {
                    "document_id": impact.get('document_id'),
                    "document_title": document_title,
                    "section_number": impact.get('section_number'),
                    "section_title": impact.get('section_title')
                },
                "impact_details": {
                    "impact_level": impact.get('impact_level'),
                    "confidence_score": impact.get('confidence_score'),
                    "similarity_score": impact.get('similarity_score'),
                    "required_actions": impact.get('required_actions', []),
                    "compliance_risk": impact.get('compliance_risk', '')
                },
                "created_at": datetime.now(timezone.utc),
                "status": "open",
                "requires_human_review": True
            }
            
            alerts.append(alert)
        
        return alerts
    
    def _map_impact_to_priority(self, impact_level: str) -> str:
        """Map impact level to alert priority"""
        mapping = {
            'high': 'critical',
            'medium': 'high', 
            'low': 'medium'
        }
        return mapping.get(impact_level.lower(), 'medium')
    
    async def batch_analyze_regulatory_changes(
        self,
        regulatory_changes: List[Dict[str, Any]],
        target_documents: Optional[List[str]] = None,
        session=None
    ) -> Dict[str, Any]:
        """
        Analyze multiple regulatory changes in batch
        
        Args:
            regulatory_changes: List of regulatory change summaries
            target_documents: Optional list of document IDs
            session: Database session
            
        Returns:
            Batch analysis results
        """
        try:
            logger.info(f"Batch analyzing {len(regulatory_changes)} regulatory changes")
            
            # Process ISO changes first (if not already in vector store)
            if regulatory_changes:
                await self.rag_engine.process_iso_changes(regulatory_changes)
            
            # Analyze each change
            all_alerts = []
            analysis_results = []
            
            for change in regulatory_changes:
                try:
                    result = await self.analyze_regulatory_change_impact(
                        change, target_documents, session
                    )
                    
                    if result.get('success'):
                        analysis_results.append(result)
                        all_alerts.extend(result.get('alerts', []))
                    else:
                        logger.warning(f"Failed to analyze change {change.get('clause_id', 'unknown')}: {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"Error analyzing change {change.get('clause_id', 'unknown')}: {e}")
            
            # Generate summary
            summary = {
                'total_changes_analyzed': len(regulatory_changes),
                'successful_analyses': len(analysis_results),
                'total_alerts_generated': len(all_alerts),
                'alert_priorities': self._count_alert_priorities(all_alerts),
                'affected_documents': len(set(
                    alert['affected_document']['document_id'] 
                    for alert in all_alerts 
                    if alert.get('affected_document', {}).get('document_id')
                ))
            }
            
            return {
                'success': True,
                'summary': summary,
                'analysis_results': analysis_results,
                'all_alerts': all_alerts,
                'processed_at': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Batch regulatory analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _count_alert_priorities(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count alerts by priority level"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for alert in alerts:
            priority = alert.get('priority', 'medium')
            if priority in counts:
                counts[priority] += 1
        
        return counts
    
    async def get_document_impact_history(
        self,
        document_id: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get impact analysis history for a specific document
        
        Args:
            document_id: Document ID
            session: Database session
            
        Returns:
            List of impact analyses affecting this document
        """
        if not session:
            return []
        
        try:
            # Find analyses that generated alerts for this document
            cursor = session.regulatory_impact_analyses.find(
                {"alerts.affected_document.document_id": document_id}
            ).sort("analysis_date", -1)
            
            analyses = await cursor.to_list(length=None)
            
            # Filter alerts for this specific document
            filtered_analyses = []
            for analysis in analyses:
                relevant_alerts = [
                    alert for alert in analysis.get('alerts', [])
                    if alert.get('affected_document', {}).get('document_id') == document_id
                ]
                
                if relevant_alerts:
                    filtered_analyses.append({
                        'analysis_id': analysis['_id'],
                        'analysis_date': analysis['analysis_date'],
                        'regulatory_change': analysis['regulatory_change'],
                        'relevant_alerts': relevant_alerts,
                        'alert_count': len(relevant_alerts)
                    })
            
            return filtered_analyses
            
        except Exception as e:
            logger.error(f"Failed to get document impact history: {e}")
            return []
    
    async def get_open_alerts(
        self,
        document_id: Optional[str] = None,
        priority_filter: Optional[str] = None,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get open regulatory impact alerts
        
        Args:
            document_id: Optional filter by document ID
            priority_filter: Optional filter by priority (critical, high, medium, low)
            session: Database session
            
        Returns:
            List of open alerts
        """
        if not session:
            return []
        
        try:
            # Build query filter
            query_filter = {}
            
            # Filter by document
            if document_id:
                query_filter["alerts.affected_document.document_id"] = document_id
            
            # Get analyses with open alerts
            cursor = session.regulatory_impact_analyses.find(query_filter)
            analyses = await cursor.to_list(length=None)
            
            # Extract and filter alerts
            open_alerts = []
            for analysis in analyses:
                for alert in analysis.get('alerts', []):
                    if alert.get('status') == 'open':
                        # Apply priority filter
                        if priority_filter and alert.get('priority') != priority_filter:
                            continue
                        
                        # Apply document filter (if not already in query)
                        if (document_id and 
                            alert.get('affected_document', {}).get('document_id') != document_id):
                            continue
                        
                        # Add analysis context
                        alert['analysis_id'] = analysis['_id']
                        alert['analysis_date'] = analysis['analysis_date']
                        
                        open_alerts.append(alert)
            
            # Sort by priority and creation date
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            open_alerts.sort(
                key=lambda x: (
                    priority_order.get(x.get('priority', 'medium'), 2),
                    x.get('created_at', datetime.min.replace(tzinfo=timezone.utc))
                )
            )
            
            return open_alerts
            
        except Exception as e:
            logger.error(f"Failed to get open alerts: {e}")
            return []