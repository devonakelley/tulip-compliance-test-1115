"""
Change Impact Detection Service - MongoDB Version
Stores QSP sections in MongoDB for persistence
"""
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from datetime import datetime
import uuid
import numpy as np
import re
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class ChangeImpactServiceMongo:
    """
    Change impact detection using MongoDB for persistent storage
    Compatible with Emergent deployment
    """
    
    def __init__(self):
        """Initialize service with OpenAI client and MongoDB"""
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.openai_client = OpenAI(api_key=openai_key)
        
        self.embedding_model = "text-embedding-3-large"
        self.embedding_dimensions = 1536
        self.impact_threshold = 0.55
        
        # MongoDB connection for persistent storage
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'compliance_checker')
        
        if mongo_url:
            self.mongo_client = AsyncIOMotorClient(mongo_url)
            self.db = self.mongo_client[db_name]
            logger.info("✅ Change Impact Service connected to MongoDB for persistent storage")
        else:
            self.mongo_client = None
            self.db = None
            logger.warning("⚠️ MongoDB not configured, using in-memory storage (not persistent)")
        
        # In-memory cache (for backwards compatibility and performance)
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
        Stores in MongoDB for persistence (with in-memory cache for performance)
        """
        try:
            embedded_count = 0
            
            if tenant_id not in self.qsp_sections:
                self.qsp_sections[tenant_id] = []
            
            embedded_sections = []
            
            for section in sections:
                full_text = f"{section['heading']}: {section['text']}"
                embedding = self._get_embedding(full_text)
                
                section_data = {
                    'section_id': str(uuid.uuid4()),
                    'doc_id': doc_id,
                    'doc_name': doc_name,
                    'section_path': section.get('section_path', ''),
                    'heading': section['heading'],
                    'text': section['text'],
                    'version': section.get('version', 'unknown'),
                    'embedding': embedding,
                    'tenant_id': tenant_id,
                    'created_at': datetime.utcnow()
                }
                
                # Add to in-memory cache
                self.qsp_sections[tenant_id].append(section_data)
                embedded_sections.append(section_data)
                embedded_count += 1
            
            # Persist to MongoDB if available
            if self.db is not None:
                # Store for async processing - we'll handle this in the calling async function
                self._pending_mongo_operations = {
                    'tenant_id': tenant_id,
                    'doc_id': doc_id,
                    'sections': embedded_sections,
                    'count': embedded_count
                }
                logger.info(f"✅ Prepared {embedded_count} sections for MongoDB persistence")
            
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
    
    async def detect_impacts_async(
        self,
        tenant_id: str,
        deltas: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Async version: Detect which QSP sections are impacted by regulatory changes
        Uses MongoDB for persistent storage with in-memory cache
        """
        try:
            run_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            all_impacts = []
            
            # Get QSP sections for this tenant (try in-memory first, then MongoDB)
            qsp_sections = self.qsp_sections.get(tenant_id, [])
            
            # If not in cache and MongoDB available, load from DB
            if not qsp_sections and self.db is not None:
                logger.info(f"Loading QSP sections from MongoDB for tenant {tenant_id}")
                cursor = self.db.qsp_sections.find({'tenant_id': tenant_id})
                qsp_sections = await cursor.to_list(length=None)
                
                # Cache for future use
                if qsp_sections:
                    self.qsp_sections[tenant_id] = qsp_sections
                    logger.info(f"✅ Loaded {len(qsp_sections)} QSP sections from MongoDB")
            
            # Call the core detection logic
            return await self._detect_impacts_core(tenant_id, deltas, qsp_sections, top_k)
            
        except Exception as e:
            logger.error(f"Async impact detection failed: {e}")
            raise
    
    def detect_impacts(
        self,
        tenant_id: str,
        deltas: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for detect_impacts_async
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run_until_complete
                # Return an error and let the caller use the async version
                raise RuntimeError("Cannot call synchronous detect_impacts from async context. Use detect_impacts_async instead.")
            return loop.run_until_complete(self.detect_impacts_async(tenant_id, deltas, top_k))
        except RuntimeError:
            # Create new event loop if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.detect_impacts_async(tenant_id, deltas, top_k))
                return result
            finally:
                loop.close()
                
    async def _detect_impacts_core(
        self,
        tenant_id: str,
        deltas: List[Dict[str, Any]],
        qsp_sections: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Core impact detection logic"""
        run_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        all_impacts = []
        
        if not qsp_sections:
            logger.warning(f"No QSP sections found for tenant {tenant_id}")
            return {
                'success': False,
                'run_id': run_id,
                'total_changes_analyzed': len(deltas),
                'total_impacts_found': 0,
                'threshold': self.impact_threshold,
                'impacts': [],
                'error': 'No QSP sections found. Please upload and map QSP documents in Tab 2 first.'
            }
        
        logger.info(f"Using {len(qsp_sections)} QSP sections for impact analysis")
        
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
            
            # Generate impacts with new unified structure
            for match in top_matches:
                section = match['section']
                confidence = match['confidence']
                
                # Extract document number from doc_name (e.g., "7.3-3 QSP 7.3-3 R9..." -> "7.3-3")
                doc_name = section['doc_name']
                doc_number_match = re.match(r'^(\d+\.\d+-\d+|\d+\.\d+)', doc_name)
                qsp_doc = doc_number_match.group(1) if doc_number_match else doc_name.split()[0]
                
                # Generate rationale without confidence score
                if confidence > 0.75:
                    strength = "Strong"
                elif confidence > 0.65:
                    strength = "Moderate"
                else:
                    strength = "Potential"
                
                # Create human-readable rationale
                if change_type.lower() == 'added' or change_type.lower() == 'new':
                    rationale = (
                        f"{strength} match: New regulatory requirement introduced in clause {clause_id}. "
                        f"Review QSP section '{section['heading']}' to ensure alignment with new requirements."
                    )
                elif change_type.lower() == 'modified':
                    rationale = (
                        f"{strength} match: Regulatory clause {clause_id} has been modified. "
                        f"QSP section '{section['heading']}' may require updates to maintain compliance."
                    )
                elif change_type.lower() == 'deleted':
                    rationale = (
                        f"{strength} match: Regulatory clause {clause_id} has been removed. "
                        f"Review QSP section '{section['heading']}' for potential simplification or removal."
                    )
                else:
                    rationale = (
                        f"{strength} match: Change to regulatory clause {clause_id}. "
                        f"Review QSP section '{section['heading']}' for consistency."
                    )
                
                # New unified structure (without confidence)
                all_impacts.append({
                    'reg_clause': clause_id,
                    'change_type': change_type.capitalize(),
                    'qsp_doc': qsp_doc,
                    'qsp_clause': section['section_path'] if section['section_path'] else 'Unknown',
                    'qsp_text': section['text'][:200] if len(section['text']) > 200 else section['text'],  # Preview (first 200 chars)
                    'qsp_text_full': section['text'],  # Full text for modal/expansion
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
