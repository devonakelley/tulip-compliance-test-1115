"""
RAG (Retrieval Augmented Generation) engine for QSP compliance analysis
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import uuid
import json

from .vector_store import VectorStore
from .document_chunker import DocumentChunker, DocumentChunk
from .embedding_service import EmbeddingService
from ..ai.llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    RAG engine for intelligent QSP compliance analysis
    Combines retrieval and generation for accurate regulatory impact assessment
    """
    
    def __init__(self):
        """Initialize RAG engine components"""
        self.vector_store = VectorStore()
        self.document_chunker = DocumentChunker()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self._initialized = False
    
    async def initialize(self):
        """Initialize all RAG components"""
        if self._initialized:
            return
            
        try:
            logger.info("Initializing RAG engine...")
            
            # Initialize components
            await self.vector_store.initialize()
            await self.embedding_service.initialize()
            
            self._initialized = True
            logger.info("RAG engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            raise
    
    async def process_qsp_document(
        self,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a QSP document for semantic search
        
        Args:
            document: Document with content and metadata
            
        Returns:
            Processing results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            document_id = document.get('_id', document.get('id', str(uuid.uuid4())))
            
            logger.info(f"Processing QSP document: {document_id}")
            
            # 1. Chunk the document
            chunks = await self.document_chunker.chunk_document(document)
            
            if not chunks:
                logger.warning(f"No chunks created for document {document_id}")
                return {
                    'success': False,
                    'error': 'No chunks created',
                    'document_id': document_id
                }
            
            # 2. Enhance chunks with metadata
            enhanced_chunks = self.document_chunker.enhance_chunk_metadata(chunks)
            
            # 3. Generate embeddings for chunks
            chunk_texts = [chunk.content for chunk in enhanced_chunks]
            embeddings = await self.embedding_service.generate_embeddings(chunk_texts)
            
            # 4. Store chunks and embeddings in vector store
            success = await self.vector_store.store_document_chunks(
                enhanced_chunks, embeddings.tolist()
            )
            
            if not success:
                return {
                    'success': False,
                    'error': 'Failed to store chunks',
                    'document_id': document_id
                }
            
            return {
                'success': True,
                'document_id': document_id,
                'chunks_created': len(chunks),
                'total_tokens': sum(chunk.token_count for chunk in chunks),
                'sections_identified': len(set(chunk.section_number for chunk in chunks if chunk.section_number))
            }
            
        except Exception as e:
            logger.error(f"Failed to process QSP document: {e}")
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
    
    async def process_iso_changes(
        self,
        changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process ISO regulatory changes for semantic search
        
        Args:
            changes: List of ISO change summaries
            
        Returns:
            Processing results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            logger.info(f"Processing {len(changes)} ISO changes")
            
            # Generate embeddings for change descriptions
            change_texts = []
            for change in changes:
                # Create rich text from change data
                text = f"{change.get('clause_title', '')} {change.get('description', '')}"
                change_texts.append(text)
            
            embeddings = await self.embedding_service.generate_embeddings(change_texts)
            
            # Store changes in vector store
            success = await self.vector_store.store_iso_changes(
                changes, embeddings.tolist()
            )
            
            return {
                'success': success,
                'changes_processed': len(changes),
                'error': None if success else 'Failed to store ISO changes'
            }
            
        except Exception as e:
            logger.error(f"Failed to process ISO changes: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes_processed': 0
            }
    
    async def analyze_regulatory_impact(
        self,
        iso_change: Dict[str, Any],
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze impact of regulatory change on QSP documents
        
        Args:
            iso_change: ISO regulatory change data
            document_ids: Optional list to limit analysis to specific documents
            
        Returns:
            Impact analysis results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            logger.info(f"Analyzing impact of ISO change: {iso_change.get('clause_id', 'unknown')}")
            
            # 1. Generate embedding for the regulatory change
            change_text = f"{iso_change.get('clause_title', '')} {iso_change.get('description', '')}"
            change_embedding = await self.embedding_service.generate_single_embedding(change_text)
            
            # 2. Find relevant QSP sections
            relevant_sections = await self.vector_store.search_similar_qsp_sections(
                query_embedding=change_embedding.tolist(),
                document_ids=document_ids,
                n_results=20  # Get more candidates for analysis
            )
            
            # 3. Filter by relevance threshold
            high_relevance_sections = [
                section for section in relevant_sections 
                if section['similarity_score'] > 0.7  # Configurable threshold
            ]
            
            # 4. Use LLM to analyze impact on relevant sections
            impact_results = []
            
            for section in high_relevance_sections:
                impact = await self._analyze_section_impact(iso_change, section)
                if impact:
                    impact_results.append(impact)
            
            # 5. Generate summary and recommendations
            summary = await self._generate_impact_summary(iso_change, impact_results)
            
            return {
                'success': True,
                'iso_change': {
                    'clause_id': iso_change.get('clause_id'),
                    'clause_title': iso_change.get('clause_title'),
                    'description': iso_change.get('description')
                },
                'total_sections_analyzed': len(relevant_sections),
                'high_relevance_sections': len(high_relevance_sections),
                'impacted_sections': len(impact_results),
                'impacts': impact_results,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze regulatory impact: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _analyze_section_impact(
        self,
        iso_change: Dict[str, Any],
        qsp_section: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze impact of ISO change on specific QSP section"""
        
        if not self.llm_service.is_available():
            # Fallback to rule-based analysis
            return self._fallback_impact_analysis(iso_change, qsp_section)
        
        try:
            # Create focused prompt for impact analysis
            system_prompt = """You are an expert in ISO 13485 medical device quality management systems. 
            Analyze the impact of a regulatory change on a specific QSP section and provide structured output."""
            
            analysis_prompt = f"""
            Analyze the impact of this regulatory change on the QSP section:

            REGULATORY CHANGE:
            Clause: {iso_change.get('clause_id', 'N/A')}
            Title: {iso_change.get('clause_title', 'N/A')}
            Change Description: {iso_change.get('description', 'N/A')}
            Impact Level: {iso_change.get('impact_level', 'medium')}

            QSP SECTION:
            Document ID: {qsp_section['metadata'].get('document_id', 'N/A')}
            Section: {qsp_section['metadata'].get('section_number', 'N/A')} - {qsp_section['metadata'].get('section_title', 'N/A')}
            Content: {qsp_section['content'][:1000]}...

            Provide analysis in this JSON format:
            {{
                "impact_detected": true/false,
                "impact_level": "high/medium/low",
                "impact_description": "Detailed description of the impact",
                "required_actions": ["List of specific actions needed"],
                "affected_elements": ["List of specific QSP elements that need updates"],
                "compliance_risk": "Description of compliance risk if not addressed",
                "confidence_score": 0.0-1.0
            }}
            
            Only return JSON, no other text.
            """
            
            response = await self.llm_service.generate(
                prompt=analysis_prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse JSON response
            try:
                impact_analysis = json.loads(response.strip())
                
                # Only return if impact is detected and confidence is reasonable
                if (impact_analysis.get('impact_detected', False) and 
                    impact_analysis.get('confidence_score', 0) > 0.6):
                    
                    return {
                        'document_id': qsp_section['metadata'].get('document_id'),
                        'section_number': qsp_section['metadata'].get('section_number'),
                        'section_title': qsp_section['metadata'].get('section_title'),
                        'similarity_score': qsp_section['similarity_score'],
                        **impact_analysis
                    }
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM impact analysis response")
        
        except Exception as e:
            logger.error(f"LLM impact analysis failed: {e}")
        
        return None
    
    def _fallback_impact_analysis(
        self,
        iso_change: Dict[str, Any],
        qsp_section: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fallback impact analysis without LLM"""
        
        # Simple keyword-based impact detection
        change_keywords = set(iso_change.get('description', '').lower().split())
        section_content = qsp_section['content'].lower()
        
        # Calculate keyword overlap
        overlap_count = sum(1 for keyword in change_keywords if keyword in section_content)
        
        if overlap_count >= 2 and qsp_section['similarity_score'] > 0.75:
            return {
                'document_id': qsp_section['metadata'].get('document_id'),
                'section_number': qsp_section['metadata'].get('section_number'),
                'section_title': qsp_section['metadata'].get('section_title'),
                'similarity_score': qsp_section['similarity_score'],
                'impact_detected': True,
                'impact_level': 'medium',
                'impact_description': f"Potential impact detected based on content similarity ({qsp_section['similarity_score']:.2f}) and keyword overlap",
                'required_actions': ['Manual review required to determine specific changes needed'],
                'affected_elements': ['Content review needed'],
                'compliance_risk': 'Manual assessment required',
                'confidence_score': min(qsp_section['similarity_score'], 0.8),
                'analysis_method': 'fallback_keyword'
            }
        
        return None
    
    async def _generate_impact_summary(
        self,
        iso_change: Dict[str, Any],
        impact_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of regulatory impact analysis"""
        
        if not impact_results:
            return {
                'overall_impact': 'no_impact',
                'message': 'No significant impact detected on analyzed QSP sections',
                'recommendation': 'No immediate action required'
            }
        
        # Count impacts by level
        impact_levels = {}
        affected_documents = set()
        total_actions = 0
        
        for impact in impact_results:
            level = impact.get('impact_level', 'medium')
            impact_levels[level] = impact_levels.get(level, 0) + 1
            affected_documents.add(impact.get('document_id'))
            total_actions += len(impact.get('required_actions', []))
        
        # Determine overall impact level
        if impact_levels.get('high', 0) > 0:
            overall_impact = 'high'
        elif impact_levels.get('medium', 0) > 2:
            overall_impact = 'high'
        elif impact_levels.get('medium', 0) > 0:
            overall_impact = 'medium'
        else:
            overall_impact = 'low'
        
        return {
            'overall_impact': overall_impact,
            'affected_documents': len(affected_documents),
            'total_impacted_sections': len(impact_results),
            'impact_breakdown': impact_levels,
            'total_required_actions': total_actions,
            'message': f"ISO change impacts {len(impact_results)} sections across {len(affected_documents)} QSP documents",
            'recommendation': f"{'Immediate' if overall_impact == 'high' else 'Planned'} review and updates required for affected sections"
        }
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        if not self._initialized:
            await self.initialize()
            
        try:
            vector_stats = await self.vector_store.get_document_statistics()
            embedding_info = self.embedding_service.get_embedding_info()
            
            return {
                'rag_engine_initialized': self._initialized,
                'vector_store': vector_stats,
                'embedding_service': embedding_info,
                'llm_service_available': self.llm_service.is_available()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system statistics: {e}")
            return {'error': str(e)}
    
    async def cleanup(self):
        """Cleanup RAG engine resources"""
        if self.vector_store:
            await self.vector_store.cleanup()
        if self.embedding_service:
            await self.embedding_service.cleanup()
        
        self._initialized = False
        logger.info("RAG engine cleaned up")