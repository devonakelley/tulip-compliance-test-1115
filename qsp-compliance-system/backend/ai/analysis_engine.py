"""
AI Analysis Engine for Enterprise QSP System
Advanced AI-powered compliance analysis and insights
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import uuid
import json
import re

from .llm_service import LLMService
from utils import TextProcessor
from config import settings

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """Advanced AI analysis engine for compliance checking"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.text_processor = TextProcessor()
        
        # Analysis templates
        self.analysis_templates = {
            "gap_analysis": """
            Perform a comprehensive gap analysis between the QSP document and {framework} requirements.
            
            Focus on identifying:
            1. Missing regulatory requirements
            2. Incomplete implementations
            3. Non-compliant procedures
            4. Areas requiring updates
            
            Document Content: {content}
            
            Required Clauses: {required_clauses}
            """,
            
            "compliance_assessment": """
            Assess the compliance level of this QSP document against {framework}.
            
            Evaluate:
            1. Coverage of regulatory requirements
            2. Quality of implementation
            3. Effectiveness of procedures
            4. Risk mitigation adequacy
            
            Document: {content}
            
            Provide detailed assessment with scoring.
            """,
            
            "change_impact": """
            Analyze the impact of these regulatory changes on the existing QSP documents.
            
            Changes: {changes}
            
            Existing QSP Sections: {qsp_sections}
            
            Identify:
            1. Which sections are affected
            2. What updates are needed
            3. Priority of changes
            4. Implementation recommendations
            """
        }
    
    async def perform_gap_analysis(
        self,
        documents: List[Dict[str, Any]],
        framework: str = "ISO_13485:2024",
        required_clauses: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive gap analysis
        
        Args:
            documents: List of document data
            framework: Regulatory framework
            required_clauses: List of required regulatory clauses
            
        Returns:
            Gap analysis results
        """
        try:
            if not self.llm_service.is_available():
                return await self._fallback_gap_analysis(documents, framework)
            
            results = {
                "analysis_id": str(uuid.uuid4()),
                "framework": framework,
                "total_documents": len(documents),
                "gaps_identified": [],
                "compliance_scores": {},
                "recommendations": [],
                "summary": {},
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Analyze each document
            for doc in documents:
                doc_gaps = await self._analyze_document_gaps(
                    doc, framework, required_clauses
                )
                
                results["gaps_identified"].extend(doc_gaps["gaps"])
                results["compliance_scores"][doc["id"]] = doc_gaps["compliance_score"]
                results["recommendations"].extend(doc_gaps["recommendations"])
            
            # Generate overall summary
            results["summary"] = await self._generate_gap_summary(results)
            
            logger.info(f"Gap analysis completed for {len(documents)} documents")
            return results
            
        except Exception as e:
            logger.error(f"Gap analysis failed: {e}")
            return {"error": str(e)}
    
    async def assess_compliance_level(
        self,
        document_content: str,
        document_type: str,
        framework: str = "ISO_13485:2024"
    ) -> Dict[str, Any]:
        """
        Assess compliance level of a document
        
        Args:
            document_content: Document text
            document_type: Type of document
            framework: Regulatory framework
            
        Returns:
            Compliance assessment
        """
        try:
            if not self.llm_service.is_available():
                return await self._fallback_compliance_assessment(document_content)
            
            # Use LLM for detailed analysis
            analysis = await self.llm_service.analyze_document(
                document_content=document_content,
                analysis_type="compliance",
                framework=framework
            )
            
            if "error" in analysis:
                return analysis
            
            # Enhance with additional processing
            enhanced_analysis = await self._enhance_compliance_analysis(
                analysis, document_content, document_type
            )
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Compliance assessment failed: {e}")
            return {"error": str(e)}
    
    async def analyze_regulatory_impact(
        self,
        regulatory_changes: List[Dict[str, Any]],
        existing_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze impact of regulatory changes on existing documents
        
        Args:
            regulatory_changes: List of regulatory changes
            existing_documents: List of existing QSP documents
            
        Returns:
            Impact analysis results
        """
        try:
            results = {
                "analysis_id": str(uuid.uuid4()),
                "total_changes": len(regulatory_changes),
                "total_documents": len(existing_documents),
                "impact_matrix": {},
                "high_priority_updates": [],
                "affected_documents": set(),
                "recommendations": [],
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Analyze impact for each change
            for change in regulatory_changes:
                change_impact = await self._analyze_single_change_impact(
                    change, existing_documents
                )
                
                change_id = change.get("id", change.get("clause_id"))
                results["impact_matrix"][change_id] = change_impact
                
                # Collect affected documents
                results["affected_documents"].update(
                    change_impact.get("affected_documents", [])
                )
                
                # Add high priority updates
                if change_impact.get("severity") == "high":
                    results["high_priority_updates"].extend(
                        change_impact.get("required_updates", [])
                    )
            
            results["affected_documents"] = list(results["affected_documents"])
            
            # Generate recommendations
            results["recommendations"] = await self._generate_impact_recommendations(
                results["impact_matrix"], results["affected_documents"]
            )
            
            logger.info(f"Regulatory impact analysis completed for {len(regulatory_changes)} changes")
            return results
            
        except Exception as e:
            logger.error(f"Regulatory impact analysis failed: {e}")
            return {"error": str(e)}
    
    async def generate_compliance_report(
        self,
        analysis_results: List[Dict[str, Any]],
        document_metadata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report
        
        Args:
            analysis_results: Results from various analyses
            document_metadata: Document metadata
            
        Returns:
            Compliance report
        """
        try:
            report = {
                "report_id": str(uuid.uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "executive_summary": {},
                "detailed_findings": {},
                "recommendations": [],
                "metrics": {},
                "appendices": {}
            }
            
            # Generate executive summary
            report["executive_summary"] = await self._generate_executive_summary(
                analysis_results, document_metadata
            )
            
            # Compile detailed findings
            report["detailed_findings"] = await self._compile_detailed_findings(
                analysis_results
            )
            
            # Generate metrics
            report["metrics"] = self._calculate_compliance_metrics(analysis_results)
            
            # Generate recommendations
            report["recommendations"] = await self._generate_report_recommendations(
                analysis_results
            )
            
            logger.info("Compliance report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {"error": str(e)}
    
    # Private methods
    
    async def _analyze_document_gaps(
        self,
        document: Dict[str, Any],
        framework: str,
        required_clauses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze gaps in a single document"""
        try:
            content = document.get("content", "")
            
            # Use LLM for gap analysis
            prompt = self.analysis_templates["gap_analysis"].format(
                framework=framework,
                content=content[:3000],  # Limit content length
                required_clauses=json.dumps(required_clauses or [], indent=2)
            )
            
            response = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.1,
                system_prompt="You are an expert regulatory compliance auditor. Provide detailed gap analysis in JSON format."
            )
            
            try:
                analysis = json.loads(response.strip())
                return analysis
            except json.JSONDecodeError:
                # Fallback to structured parsing
                return self._parse_gap_analysis_text(response, document["id"])
                
        except Exception as e:
            logger.error(f"Document gap analysis failed: {e}")
            return {
                "gaps": [],
                "compliance_score": 0.5,
                "recommendations": [f"Manual review required for document {document.get('id', 'unknown')}"]
            }
    
    async def _enhance_compliance_analysis(
        self,
        base_analysis: Dict[str, Any],
        document_content: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Enhance compliance analysis with additional processing"""
        enhanced = base_analysis.copy()
        
        # Add text-based analysis
        key_phrases = self.text_processor.extract_key_phrases(document_content)
        enhanced["key_phrases"] = key_phrases
        
        # Add document type specific insights
        if document_type == "qsp":
            enhanced["qsp_specific"] = await self._qsp_specific_analysis(document_content)
        elif document_type == "regulatory":
            enhanced["regulatory_specific"] = await self._regulatory_specific_analysis(document_content)
        
        # Calculate enhanced metrics
        enhanced["enhanced_metrics"] = {
            "content_length": len(document_content),
            "section_count": document_content.count('\n\n') + 1,
            "key_phrase_count": len(key_phrases),
            "complexity_score": self._calculate_complexity_score(document_content)
        }
        
        return enhanced
    
    async def _analyze_single_change_impact(
        self,
        change: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze impact of a single regulatory change"""
        impact = {
            "change_id": change.get("id"),
            "clause_id": change.get("clause_id"),
            "severity": change.get("impact_level", "medium"),
            "affected_documents": [],
            "required_updates": [],
            "risk_level": "medium"
        }
        
        # Simple keyword-based impact assessment
        change_keywords = self._extract_keywords(change.get("description", ""))
        
        for doc in documents:
            doc_content = doc.get("content", "").lower()
            doc_keywords = self._extract_keywords(doc_content)
            
            # Calculate keyword overlap
            overlap = len(set(change_keywords).intersection(set(doc_keywords)))
            
            if overlap > 2:  # Threshold for relevance
                impact["affected_documents"].append(doc["id"])
                impact["required_updates"].append({
                    "document_id": doc["id"],
                    "update_type": "content_review",
                    "priority": impact["severity"],
                    "description": f"Review document against change: {change.get('clause_id')}"
                })
        
        return impact
    
    async def _fallback_gap_analysis(
        self,
        documents: List[Dict[str, Any]],
        framework: str
    ) -> Dict[str, Any]:
        """Fallback gap analysis without LLM"""
        logger.info("Using fallback gap analysis (LLM not available)")
        
        # Basic keyword-based analysis
        results = {
            "analysis_id": str(uuid.uuid4()),
            "framework": framework,
            "method": "keyword_based",
            "total_documents": len(documents),
            "gaps_identified": [],
            "compliance_scores": {},
            "recommendations": []
        }
        
        # ISO 13485 required keywords
        required_keywords = {
            "quality_management": ["quality", "management", "system"],
            "documentation": ["document", "procedure", "record"],
            "design_control": ["design", "development", "validation"],
            "risk_management": ["risk", "hazard", "analysis"]
        }
        
        for doc in documents:
            content = doc.get("content", "").lower()
            doc_score = 0.0
            missing_areas = []
            
            for area, keywords in required_keywords.items():
                if any(keyword in content for keyword in keywords):
                    doc_score += 25.0  # Each area worth 25 points
                else:
                    missing_areas.append(area)
                    results["gaps_identified"].append({
                        "document_id": doc["id"],
                        "gap_type": "missing_area",
                        "description": f"No evidence of {area} requirements",
                        "severity": "medium"
                    })
            
            results["compliance_scores"][doc["id"]] = doc_score
            
            if missing_areas:
                results["recommendations"].append(
                    f"Document {doc['id']}: Address missing areas - {', '.join(missing_areas)}"
                )
        
        return results
    
    async def _fallback_compliance_assessment(
        self, document_content: str
    ) -> Dict[str, Any]:
        """Fallback compliance assessment without LLM"""
        logger.info("Using fallback compliance assessment")
        
        # Basic assessment based on content analysis
        content_lower = document_content.lower()
        
        compliance_indicators = {
            "procedures": ["procedure", "process", "method"],
            "records": ["record", "documentation", "log"],
            "controls": ["control", "verify", "validate"],
            "responsibilities": ["responsible", "authority", "role"]
        }
        
        score = 0.0
        found_indicators = []
        
        for category, keywords in compliance_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                score += 25.0
                found_indicators.append(category)
        
        return {
            "compliance_score": score,
            "method": "keyword_based",
            "found_indicators": found_indicators,
            "assessment": "Basic compliance assessment completed",
            "limitations": "Full AI analysis not available"
        }
    
    def _extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in set(words) if len(word) >= min_length]
    
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate content complexity score"""
        # Simple complexity metrics
        word_count = len(content.split())
        sentence_count = len(re.findall(r'[.!?]+', content))
        
        if sentence_count == 0:
            return 0.0
        
        avg_sentence_length = word_count / sentence_count
        
        # Normalize to 0-100 scale
        complexity = min(avg_sentence_length / 20.0 * 100, 100.0)
        return complexity
    
    def _parse_gap_analysis_text(
        self, text: str, document_id: str
    ) -> Dict[str, Any]:
        """Parse gap analysis from unstructured text"""
        # Basic text parsing for gap analysis
        gaps = []
        
        # Look for gap indicators
        gap_patterns = [
            r'missing:?\s*(.+?)(?=\n|$)',
            r'gap:?\s*(.+?)(?=\n|$)',
            r'not found:?\s*(.+?)(?=\n|$)'
        ]
        
        for pattern in gap_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                gaps.append({
                    "document_id": document_id,
                    "description": match.group(1).strip(),
                    "type": "identified_gap",
                    "severity": "medium"
                })
        
        # Extract compliance score if mentioned
        score_pattern = r'score:?\s*(\d+(?:\.\d+)?)'
        score_match = re.search(score_pattern, text, re.IGNORECASE)
        compliance_score = float(score_match.group(1)) if score_match else 50.0
        
        return {
            "gaps": gaps,
            "compliance_score": compliance_score,
            "recommendations": ["Manual review recommended"],
            "method": "text_parsing"
        }
    
    async def _qsp_specific_analysis(self, content: str) -> Dict[str, Any]:
        """QSP-specific analysis"""
        return {
            "qsp_structure": "standard" if "procedure" in content.lower() else "non_standard",
            "has_approval": "approval" in content.lower() or "approved" in content.lower(),
            "has_revision": "revision" in content.lower() or "version" in content.lower()
        }
    
    async def _regulatory_specific_analysis(self, content: str) -> Dict[str, Any]:
        """Regulatory document specific analysis"""
        return {
            "regulatory_type": "summary" if "summary" in content.lower() else "full",
            "has_changes": "change" in content.lower() or "update" in content.lower(),
            "effective_date_mentioned": bool(re.search(r'\d{4}', content))
        }