"""
Regulatory analysis engine for Enterprise QSP Compliance System
Handles regulatory change tracking and impact analysis
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid
import json
import re

# Database imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, text
from ..database.models import (
    RegulatoryFramework, RegulatoryChange, Document, 
    DocumentSection, ClauseMapping, ComplianceAnalysis
)
from ..models import RegulatoryChange as RegulatoryChangeModel
from ..config import settings
from ..ai import LLMService
from ..utils import TextProcessor

logger = logging.getLogger(__name__)

class RegulatoryAnalyzer:
    """Handles regulatory change analysis and tracking"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.text_processor = TextProcessor()
        self._initialized = False
        
        # ISO 13485 clause patterns
        self.iso_clause_patterns = {
            r'\b4\.1\b': '4.1 General requirements',
            r'\b4\.2\b': '4.2 Documentation requirements',
            r'\b5\.1\b': '5.1 Management commitment',
            r'\b5\.2\b': '5.2 Customer focus',
            r'\b5\.3\b': '5.3 Quality policy',
            r'\b5\.4\b': '5.4 Planning',
            r'\b5\.5\b': '5.5 Responsibility, authority and communication',
            r'\b5\.6\b': '5.6 Management review',
            r'\b6\.1\b': '6.1 Provision of resources',
            r'\b6\.2\b': '6.2 Human resources',
            r'\b6\.3\b': '6.3 Infrastructure',
            r'\b6\.4\b': '6.4 Work environment and contamination control',
            r'\b7\.1\b': '7.1 Planning of product realization',
            r'\b7\.2\b': '7.2 Customer-related processes',
            r'\b7\.3\b': '7.3 Design and development',
            r'\b7\.4\b': '7.4 Purchasing',
            r'\b7\.5\b': '7.5 Production and service provision',
            r'\b7\.6\b': '7.6 Control of monitoring and measuring equipment',
            r'\b8\.1\b': '8.1 General',
            r'\b8\.2\b': '8.2 Monitoring and measurement',
            r'\b8\.3\b': '8.3 Control of nonconforming product',
            r'\b8\.4\b': '8.4 Analysis of data',
            r'\b8\.5\b': '8.5 Improvement'
        }
        
        # Keywords for clause mapping
        self.keyword_map = {
            '4.1': ['quality', 'management', 'system', 'requirements', 'general'],
            '4.2': ['documentation', 'document', 'control', 'records', 'procedure'],
            '5.1': ['management', 'commitment', 'leadership', 'responsibility'],
            '5.2': ['customer', 'satisfaction', 'requirements', 'feedback'],
            '5.3': ['policy', 'quality', 'objectives', 'communication'],
            '7.3': ['design', 'development', 'validation', 'verification', 'review'],
            '7.4': ['purchasing', 'supplier', 'vendor', 'evaluation', 'control'],
            '8.1': ['monitoring', 'measurement', 'analysis', 'performance'],
            '8.5': ['improvement', 'corrective', 'preventive', 'action', 'nonconformity']
        }
    
    async def initialize_system(
        self,
        user_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Initialize regulatory analysis system
        
        Args:
            user_id: User ID
            session: Database session
            
        Returns:
            Initialization status
        """
        try:
            if self._initialized:
                return {"status": "already_initialized", "message": "System already initialized"}
            
            # Initialize ISO 13485:2024 framework
            await self._initialize_iso_framework(session)
            
            # Parse existing QSP documents
            await self._parse_qsp_documents(user_id, session)
            
            # Create initial clause mappings
            mapping_count = await self._create_initial_mappings(user_id, session)
            
            self._initialized = True
            
            return {
                "status": "initialized",
                "message": "Regulatory analysis system initialized successfully",
                "clause_mappings_created": mapping_count,
                "frameworks_loaded": 1
            }
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise
    
    async def process_summary(
        self,
        framework: str,
        summary_version: str,
        user_id: str,
        session: AsyncSession
    ) -> str:
        """
        Start processing of regulatory summary
        
        Args:
            framework: Regulatory framework name
            summary_version: Version of the summary
            user_id: User ID
            session: Database session
            
        Returns:
            Task ID for background processing
        """
        try:
            # Generate task ID
            task_id = str(uuid.uuid4())
            
            # Validate framework
            if framework not in settings.SUPPORTED_FRAMEWORKS:
                raise ValueError(f"Unsupported framework: {framework}")
            
            logger.info(f"Starting regulatory summary processing: {framework} {summary_version}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to start summary processing: {e}")
            raise
    
    async def process_summary_async(
        self,
        task_id: str,
        framework: str,
        summary_version: str,
        user_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Asynchronously process regulatory summary
        
        Args:
            task_id: Task ID
            framework: Framework name
            summary_version: Summary version
            user_id: User ID
            session: Database session
            
        Returns:
            Processing results
        """
        try:
            # Get regulatory framework
            framework_obj = await self._get_framework(framework, session)
            if not framework_obj:
                raise ValueError(f"Framework not found: {framework}")
            
            # Get summary document
            summary_doc = await self._get_summary_document(
                framework, summary_version, user_id, session
            )
            
            if not summary_doc:
                raise ValueError(f"Summary document not found: {framework} {summary_version}")
            
            # Parse summary for changes
            changes = await self._parse_summary_changes(summary_doc.content, framework_obj)
            
            # Store changes in database
            change_ids = await self._store_regulatory_changes(
                changes, framework_obj.id, session
            )
            
            # Analyze impact on existing QSPs
            impact_analysis = await self._analyze_change_impact(
                change_ids, user_id, session
            )
            
            # Generate report
            report = {
                "task_id": task_id,
                "framework": framework,
                "summary_version": summary_version,
                "total_changes": len(changes),
                "new_requirements": len([c for c in changes if c["change_type"] == "added"]),
                "modified_requirements": len([c for c in changes if c["change_type"] == "modified"]),
                "impact_analysis": impact_analysis,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Regulatory summary processed successfully: {task_id}")
            return report
            
        except Exception as e:
            logger.error(f"Regulatory summary processing failed: {e}")
            raise
    
    async def get_regulatory_changes(
        self,
        framework: str,
        limit: int = 50,
        session: AsyncSession
    ) -> List[RegulatoryChangeModel]:
        """
        Get regulatory changes for a framework
        
        Args:
            framework: Framework name
            limit: Maximum number of results
            session: Database session
            
        Returns:
            List of regulatory changes
        """
        try:
            # Get framework
            framework_obj = await self._get_framework(framework, session)
            if not framework_obj:
                return []
            
            # Query changes
            query = select(RegulatoryChange).where(
                RegulatoryChange.framework_id == framework_obj.id
            ).order_by(RegulatoryChange.effective_date.desc()).limit(limit)
            
            result = await session.execute(query)
            changes = result.scalars().all()
            
            return [
                RegulatoryChangeModel(
                    change_id=str(change.id),
                    regulatory_framework=framework,
                    clause_id=change.clause_id,
                    change_type=change.change_type,
                    change_description=change.change_description,
                    effective_date=change.effective_date,
                    impact_level=change.impact_level.value,
                    affected_sections=change.affected_sections or [],
                    implementation_guidance=change.implementation_guidance,
                    source_document=change.source_document or "",
                    processed_date=change.processed_date
                )
                for change in changes
            ]
            
        except Exception as e:
            logger.error(f"Failed to get regulatory changes: {e}")
            return []
    
    # Private methods
    
    async def _initialize_iso_framework(self, session: AsyncSession):
        """Initialize ISO 13485:2024 framework"""
        try:
            # Check if framework exists
            query = select(RegulatoryFramework).where(
                RegulatoryFramework.framework_name == "ISO_13485",
                RegulatoryFramework.version == "2024"
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info("ISO 13485:2024 framework already exists")
                return
            
            # Create framework
            framework = RegulatoryFramework(
                id=uuid.uuid4(),
                framework_name="ISO_13485",
                version="2024",
                description="ISO 13485:2024 - Medical devices - Quality management systems - Requirements for regulatory purposes",
                effective_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
                is_active=True,
                framework_content={
                    "clauses": list(self.iso_clause_patterns.values()),
                    "keywords": self.keyword_map
                },
                clauses_count=len(self.iso_clause_patterns)
            )
            
            session.add(framework)
            await session.commit()
            
            logger.info("ISO 13485:2024 framework initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ISO framework: {e}")
            raise
    
    async def _parse_qsp_documents(self, user_id: str, session: AsyncSession):
        """Parse existing QSP documents for sections"""
        try:
            # Get user's QSP documents
            query = select(Document).where(
                Document.user_id == uuid.UUID(user_id),
                Document.document_type.in_(['qsp', 'procedure', 'work_instruction']),
                Document.processing_status == 'completed',
                Document.is_active == True
            )
            
            result = await session.execute(query)
            documents = result.scalars().all()
            
            logger.info(f"Found {len(documents)} QSP documents for analysis")
            
            # Documents are already parsed during upload
            # This method can be used for re-parsing if needed
            
        except Exception as e:
            logger.error(f"Failed to parse QSP documents: {e}")
            raise
    
    async def _create_initial_mappings(
        self, 
        user_id: str, 
        session: AsyncSession
    ) -> int:
        """Create initial clause mappings for QSP documents"""
        try:
            # Get ISO framework
            framework = await self._get_framework("ISO_13485", session)
            if not framework:
                raise ValueError("ISO framework not found")
            
            # Get document sections
            sections_query = select(DocumentSection).join(Document).where(
                Document.user_id == uuid.UUID(user_id),
                Document.document_type.in_(['qsp', 'procedure', 'work_instruction']),
                Document.is_active == True
            )
            
            sections_result = await session.execute(sections_query)
            sections = sections_result.scalars().all()
            
            mapping_count = 0
            
            # Create mappings using AI and keyword matching
            for section in sections:
                mappings = await self._map_section_to_clauses(
                    section, framework, session
                )
                mapping_count += len(mappings)
            
            logger.info(f"Created {mapping_count} initial clause mappings")
            return mapping_count
            
        except Exception as e:
            logger.error(f"Failed to create initial mappings: {e}")
            return 0
    
    async def _map_section_to_clauses(
        self,
        section: DocumentSection,
        framework: RegulatoryFramework,
        session: AsyncSession
    ) -> List[ClauseMapping]:
        """Map document section to regulatory clauses"""
        try:
            mappings = []
            
            # Keyword-based mapping
            keyword_matches = self._find_keyword_matches(section.content)
            
            # AI-powered mapping for high-confidence matches
            ai_matches = await self._ai_clause_mapping(
                section.title, section.content, framework
            )
            
            # Combine and validate matches
            all_matches = self._combine_mappings(keyword_matches, ai_matches)
            
            for match in all_matches:
                if match["confidence"] >= 0.6:  # Minimum confidence threshold
                    mapping = ClauseMapping(
                        id=uuid.uuid4(),
                        document_id=section.document_id,
                        section_id=section.id,
                        framework_id=framework.id,
                        clause_id=match["clause_id"],
                        clause_title=match["clause_title"],
                        confidence_score=match["confidence"],
                        evidence_text=match["evidence"][:500],  # Limit length
                        mapping_rationale=match.get("rationale", ""),
                        created_by="system"
                    )
                    
                    session.add(mapping)
                    mappings.append(mapping)
            
            await session.commit()
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to map section to clauses: {e}")
            return []
    
    def _find_keyword_matches(self, content: str) -> List[Dict[str, Any]]:
        """Find clause matches using keyword analysis"""
        matches = []
        content_lower = content.lower()
        
        for clause_id, keywords in self.keyword_map.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
            
            if keyword_count > 0:
                confidence = min(keyword_count * 0.2, 0.8)  # Max 0.8 for keyword matching
                
                # Find evidence text
                evidence_sentences = []
                sentences = content.split('.')
                
                for sentence in sentences[:5]:  # Check first 5 sentences
                    if any(keyword in sentence.lower() for keyword in keywords):
                        evidence_sentences.append(sentence.strip())
                
                if evidence_sentences:
                    matches.append({
                        "clause_id": clause_id,
                        "clause_title": self.iso_clause_patterns.get(
                            f'\\b{clause_id}\\b', f"{clause_id} Requirements"
                        ),
                        "confidence": confidence,
                        "evidence": '. '.join(evidence_sentences[:2]),
                        "method": "keyword"
                    })
        
        return matches
    
    async def _ai_clause_mapping(
        self,
        section_title: str,
        section_content: str,
        framework: RegulatoryFramework
    ) -> List[Dict[str, Any]]:
        """Use AI to map section content to regulatory clauses"""
        try:
            if not self.llm_service.is_available():
                logger.warning("LLM service not available for AI mapping")
                return []
            
            prompt = f"""
            Analyze the following QSP document section and identify which ISO 13485:2024 clauses it addresses.
            
            Section Title: {section_title}
            Section Content: {section_content[:2000]}...
            
            Available ISO 13485:2024 Clauses:
            {json.dumps(list(self.iso_clause_patterns.values()), indent=2)}
            
            For each relevant clause, provide:
            1. Clause ID (e.g., "4.1", "7.3")
            2. Confidence score (0.0 to 1.0)
            3. Brief rationale
            4. Evidence quote from the section
            
            Return as JSON array with format:
            [
                {{
                    "clause_id": "4.1",
                    "confidence": 0.85,
                    "rationale": "Section addresses quality management system requirements",
                    "evidence": "relevant quote from section"
                }}
            ]
            
            Only include clauses with confidence > 0.7.
            """
            
            response = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.1
            )
            
            # Parse JSON response
            try:
                ai_matches = json.loads(response.strip())
                
                # Validate and enrich matches
                validated_matches = []
                for match in ai_matches:
                    if (
                        isinstance(match, dict) and
                        "clause_id" in match and
                        "confidence" in match and
                        match["confidence"] > 0.7
                    ):
                        # Add clause title
                        clause_pattern = f'\\b{match["clause_id"]}\\b'
                        match["clause_title"] = self.iso_clause_patterns.get(
                            clause_pattern, f"{match['clause_id']} Requirements"
                        )
                        match["method"] = "ai"
                        validated_matches.append(match)
                
                return validated_matches
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI mapping response")
                return []
                
        except Exception as e:
            logger.error(f"AI clause mapping failed: {e}")
            return []
    
    def _combine_mappings(
        self, 
        keyword_matches: List[Dict[str, Any]], 
        ai_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine keyword and AI mappings, prioritizing higher confidence"""
        combined = {}
        
        # Add keyword matches
        for match in keyword_matches:
            clause_id = match["clause_id"]
            combined[clause_id] = match
        
        # Add or update with AI matches (they have higher priority)
        for match in ai_matches:
            clause_id = match["clause_id"]
            if (
                clause_id not in combined or 
                match["confidence"] > combined[clause_id]["confidence"]
            ):
                combined[clause_id] = match
        
        return list(combined.values())
    
    async def _get_framework(
        self, 
        framework_name: str, 
        session: AsyncSession
    ) -> Optional[RegulatoryFramework]:
        """Get regulatory framework by name"""
        query = select(RegulatoryFramework).where(
            RegulatoryFramework.framework_name == framework_name,
            RegulatoryFramework.is_active == True
        ).order_by(RegulatoryFramework.effective_date.desc())
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_summary_document(
        self,
        framework: str,
        summary_version: str,
        user_id: str,
        session: AsyncSession
    ) -> Optional[Document]:
        """Get regulatory summary document"""
        query = select(Document).where(
            Document.user_id == uuid.UUID(user_id),
            Document.document_type == 'iso_summary',
            Document.metadata['framework'].astext == framework,
            Document.metadata['version'].astext == summary_version,
            Document.is_active == True
        )
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _parse_summary_changes(
        self,
        content: str,
        framework: RegulatoryFramework
    ) -> List[Dict[str, Any]]:
        """Parse regulatory summary for changes"""
        changes = []
        
        # Use regex patterns to find changes
        change_patterns = [
            (r'NEW:\s*(.+?)(?=\n|$)', 'added'),
            (r'MODIFIED:\s*(.+?)(?=\n|$)', 'modified'),
            (r'UPDATED:\s*(.+?)(?=\n|$)', 'modified'),
            (r'ADDED:\s*(.+?)(?=\n|$)', 'added'),
            (r'CHANGED:\s*(.+?)(?=\n|$)', 'modified')
        ]
        
        for pattern, change_type in change_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                change_text = match.group(1).strip()
                
                # Try to extract clause ID
                clause_id = self._extract_clause_id(change_text)
                
                if clause_id:
                    changes.append({
                        "clause_id": clause_id,
                        "change_type": change_type,
                        "description": change_text,
                        "effective_date": datetime.now(timezone.utc),
                        "impact_level": self._assess_impact_level(change_text)
                    })
        
        return changes
    
    def _extract_clause_id(self, text: str) -> Optional[str]:
        """Extract clause ID from text"""
        # Look for patterns like "4.1", "7.3.2", etc.
        clause_pattern = r'\b(\d+\.\d+(?:\.\d+)?)\b'
        match = re.search(clause_pattern, text)
        
        if match:
            clause_id = match.group(1)
            # Simplify to main clause (e.g., "7.3.2" -> "7.3")
            parts = clause_id.split('.')
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}"
        
        return None
    
    def _assess_impact_level(self, change_text: str) -> str:
        """Assess impact level of regulatory change"""
        high_impact_keywords = [
            'mandatory', 'required', 'must', 'shall', 'critical', 
            'safety', 'risk', 'validation', 'verification'
        ]
        
        medium_impact_keywords = [
            'should', 'recommended', 'procedure', 'process', 
            'documentation', 'record'
        ]
        
        text_lower = change_text.lower()
        
        if any(keyword in text_lower for keyword in high_impact_keywords):
            return 'high'
        elif any(keyword in text_lower for keyword in medium_impact_keywords):
            return 'medium'
        else:
            return 'low'
    
    async def _store_regulatory_changes(
        self,
        changes: List[Dict[str, Any]],
        framework_id: uuid.UUID,
        session: AsyncSession
    ) -> List[uuid.UUID]:
        """Store regulatory changes in database"""
        change_ids = []
        
        try:
            for change_data in changes:
                change = RegulatoryChange(
                    id=uuid.uuid4(),
                    framework_id=framework_id,
                    clause_id=change_data["clause_id"],
                    change_type=change_data["change_type"],
                    change_description=change_data["description"],
                    impact_level=change_data["impact_level"],
                    effective_date=change_data["effective_date"],
                    announcement_date=datetime.now(timezone.utc),
                    source_document="ISO Summary"
                )
                
                session.add(change)
                change_ids.append(change.id)
            
            await session.commit()
            return change_ids
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to store regulatory changes: {e}")
            raise
    
    async def _analyze_change_impact(
        self,
        change_ids: List[uuid.UUID],
        user_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze impact of regulatory changes on existing QSPs"""
        try:
            impact_summary = {
                "total_changes": len(change_ids),
                "affected_documents": [],
                "gaps_identified": 0,
                "high_priority_actions": []
            }
            
            # Get changes
            changes_query = select(RegulatoryChange).where(
                RegulatoryChange.id.in_(change_ids)
            )
            changes_result = await session.execute(changes_query)
            changes = changes_result.scalars().all()
            
            affected_docs = set()
            
            for change in changes:
                # Find existing mappings for this clause
                mappings_query = select(ClauseMapping).join(Document).where(
                    Document.user_id == uuid.UUID(user_id),
                    ClauseMapping.clause_id == change.clause_id,
                    Document.is_active == True
                )
                
                mappings_result = await session.execute(mappings_query)
                mappings = mappings_result.scalars().all()
                
                if mappings:
                    for mapping in mappings:
                        affected_docs.add(str(mapping.document_id))
                else:
                    # No existing coverage - this is a gap
                    impact_summary["gaps_identified"] += 1
                    
                    if change.impact_level.value == 'high':
                        impact_summary["high_priority_actions"].append(
                            f"Address new requirement: {change.clause_id} - {change.change_description[:100]}..."
                        )
            
            impact_summary["affected_documents"] = list(affected_docs)
            
            return impact_summary
            
        except Exception as e:
            logger.error(f"Failed to analyze change impact: {e}")
            return {"error": str(e)}
