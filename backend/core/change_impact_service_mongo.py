"""
Change Impact Detection Service - MongoDB Version
Simplified version that works without Postgres/pgvector
Uses in-memory vectors for demo or can be extended to MongoDB
"""
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from datetime import datetime
import uuid
import numpy as np

logger = logging.getLogger(__name__)


class ChangeImpactServiceMongo:
    """
    Change impact detection using MongoDB and in-memory vectors
    Compatible with Emergent deployment (no Postgres/ML dependencies)
    """
    
    def __init__(self):
        """Initialize service with OpenAI client"""
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.openai_client = OpenAI(api_key=openai_key)
        
        self.embedding_model = "text-embedding-3-large"
        self.embedding_dimensions = 1536
        self.impact_threshold = 0.55
        
        # In-memory storage for demo
        self.qsp_sections = {}  # tenant_id -> list of sections with embeddings
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            text = ' '.join(text.split())
            if len(text) > 8000:
                text = text[:8000]
            
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model,
                dimensions=self.embedding_dimensions
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def ingest_qsp_document(
        self,
        tenant_id: str,
        doc_id: str,
        doc_name: str,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ingest QSP document sections and generate embeddings
        Stores in memory for demo (can be extended to MongoDB)
        """
        try:
            embedded_count = 0
            
            if tenant_id not in self.qsp_sections:
                self.qsp_sections[tenant_id] = []
            
            for section in sections:
                full_text = f"{section['heading']}: {section['text']}"
                embedding = self._get_embedding(full_text)
                
                self.qsp_sections[tenant_id].append({
                    'section_id': str(uuid.uuid4()),
                    'doc_id': doc_id,
                    'doc_name': doc_name,
                    'section_path': section.get('section_path', ''),
                    'heading': section['heading'],
                    'text': section['text'],
                    'version': section.get('version', 'unknown'),
                    'embedding': embedding
                })
                
                embedded_count += 1
            
            logger.info(f"Ingested {embedded_count} sections for doc {doc_name}")
            
            return {
                'success': True,
                'doc_id': doc_id,
                'doc_name': doc_name,
                'sections_embedded': embedded_count
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest QSP document: {e}")
            raise
    
    def detect_impacts(
        self,
        tenant_id: str,
        deltas: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Detect which QSP sections are impacted by regulatory changes
        Uses in-memory vector search
        """
        try:
            run_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            all_impacts = []
            
            # Get QSP sections for this tenant
            qsp_sections = self.qsp_sections.get(tenant_id, [])
            
            if not qsp_sections:
                logger.warning(f"No QSP sections found for tenant {tenant_id}")
                return {
                    'success': True,
                    'run_id': run_id,
                    'total_changes_analyzed': len(deltas),
                    'total_impacts_found': 0,
                    'threshold': self.impact_threshold,
                    'impacts': [],
                    'warning': 'No QSP sections ingested. Please upload QSP sections first.'
                }
            
            # Process each delta
            for delta in deltas:
                clause_id = delta['clause_id']
                change_text = delta['change_text']
                change_type = delta.get('change_type', 'modified')
                
                logger.info(f"Analyzing impact for {clause_id}")
                
                # Generate embedding for change
                change_embedding = self._get_embedding(change_text)
                
                # Calculate similarity with all QSP sections
                similarities = []
                for qsp in qsp_sections:
                    similarity = self._cosine_similarity(change_embedding, qsp['embedding'])
                    if similarity > self.impact_threshold:
                        similarities.append({
                            'section': qsp,
                            'confidence': similarity
                        })
                
                # Sort by confidence and take top-k
                similarities.sort(key=lambda x: x['confidence'], reverse=True)
                top_matches = similarities[:top_k]
                
                # Generate impacts
                for match in top_matches:
                    section = match['section']
                    confidence = match['confidence']
                    
                    # Generate rationale
                    if confidence > 0.75:
                        strength = "strong"
                    elif confidence > 0.65:
                        strength = "moderate"
                    else:
                        strength = "potential"
                    
                    rationale = (
                        f"The change to {clause_id} has a {strength} semantic match "
                        f"(confidence: {confidence:.2f}) with QSP section '{section['heading']}'. "
                        f"This suggests the internal procedure may need review."
                    )
                    
                    all_impacts.append({
                        'impact_id': str(uuid.uuid4()),
                        'clause_id': clause_id,
                        'change_type': change_type,
                        'qsp_doc': section['doc_name'],
                        'section_path': section['section_path'],
                        'heading': section['heading'],
                        'confidence': round(confidence, 3),
                        'rationale': rationale
                    })
                
                logger.info(f"Found {len(top_matches)} impacts for {clause_id}")
            
            logger.info(f"✅ Impact analysis complete: run_id={run_id}, {len(all_impacts)} impacts")
            
            return {
                'success': True,
                'run_id': run_id,
                'total_changes_analyzed': len(deltas),
                'total_impacts_found': len(all_impacts),
                'threshold': self.impact_threshold,
                'impacts': all_impacts
            }
            
        except Exception as e:
            logger.error(f"Impact detection failed: {e}")
            raise
    
    def get_report(
        self,
        run_id: str,
        tenant_id: str,
        format: str = 'json'
    ) -> Any:
        """
        Get report (simplified - returns message for demo)
        In production, this would query MongoDB for stored results
        """
        return {
            'run_id': run_id,
            'status': 'demo_mode',
            'message': 'Demo mode: Reports are generated on-demand. Run analysis to see results.',
            'note': 'In production, results would be stored in MongoDB and retrieved here.'
        }


# Singleton instance
change_impact_service_mongo = None

def get_change_impact_service():
    """Get singleton instance"""
    global change_impact_service_mongo
    if change_impact_service_mongo is None:
        change_impact_service_mongo = ChangeImpactServiceMongo()
    return change_impact_service_mongo
