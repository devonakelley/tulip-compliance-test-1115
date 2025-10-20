"""
Production Hybrid Retrieval Service
Combines BM25 (pg_trgm) + Vector (pgvector) + Cross-encoder reranker
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple
import logging
from openai import OpenAI
import os
from sentence_transformers import CrossEncoder
import numpy as np

logger = logging.getLogger(__name__)


class HybridRetrievalService:
    """
    Production-grade hybrid retrieval for regulatory compliance
    
    Workflow:
    1. BM25 search (pg_trgm) - keyword/phrase matching → top-50
    2. Vector search (pgvector) - semantic similarity → top-50  
    3. Merge & deduplicate
    4. Cross-encoder rerank → final top-k with confidence
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize retrieval service
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string or os.getenv(
            "POSTGRES_URL",
            "postgresql://qsp_user:qsp_secure_pass@localhost:5432/qsp_compliance"
        )
        
        # OpenAI for embeddings
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.openai_client = OpenAI(api_key=openai_key)
        
        # Load cross-encoder reranker
        logger.info("Loading cross-encoder reranker...")
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
        logger.info("✅ Reranker loaded")
        
        self.embedding_model = "text-embedding-3-large"
        self.embedding_dimensions = 1536  # Reduced from 3072 for pgvector compatibility
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI text-embedding-3-large
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector (1536 dimensions)
        """
        try:
            # Clean text
            text = ' '.join(text.split())
            
            # Truncate if too long
            if len(text) > 8000:
                text = text[:8000]
            
            # Get embedding with dimension reduction
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model,
                dimensions=self.embedding_dimensions
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def bm25_search(
        self,
        query: str,
        tenant_id: str,
        doc_type: Optional[str] = None,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        BM25-style keyword search using pg_trgm
        
        Searches:
        - Clause IDs (exact and fuzzy)
        - Section headings  
        - Document text
        
        Args:
            query: Search query
            tenant_id: Tenant ID for isolation
            doc_type: Optional document type filter (ISO, CFR, QSP, etc.)
            top_k: Number of results to return
            
        Returns:
            List of matching sections with BM25 scores
        """
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # pg_trgm similarity search
                    # Weights: clause_id (highest), heading (medium), text (lower)
                    sql = """
                        SELECT 
                            section_id::text,
                            doc_id::text,
                            section_path,
                            clause_id,
                            heading,
                            text,
                            doc_type,
                            doc_version,
                            source,
                            page,
                            -- Calculate BM25-like score (weighted similarity)
                            (
                                COALESCE(similarity(clause_id, %s), 0) * 3.0 +
                                COALESCE(similarity(heading, %s), 0) * 2.0 +
                                COALESCE(similarity(text, %s), 0) * 1.0
                            ) as bm25_score
                        FROM document_sections
                        WHERE tenant_id = %s::uuid
                            AND (
                                clause_id %% %s OR
                                heading %% %s OR
                                text %% %s
                            )
                            {doc_type_filter}
                        ORDER BY bm25_score DESC
                        LIMIT %s;
                    """
                    
                    # Add doc_type filter if specified
                    doc_type_filter = ""
                    params = [query, query, query, tenant_id, query, query, query]
                    
                    if doc_type:
                        doc_type_filter = "AND doc_type = %s"
                        params.append(doc_type)
                    
                    params.append(top_k)
                    
                    sql = sql.format(doc_type_filter=doc_type_filter)
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    logger.debug(f"BM25 search returned {len(results)} results")
                    return [dict(row) for row in results]
                    
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            raise
    
    def vector_search(
        self,
        query: str,
        tenant_id: str,
        doc_type: Optional[str] = None,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search using pgvector
        
        Args:
            query: Search query
            tenant_id: Tenant ID for isolation
            doc_type: Optional document type filter
            top_k: Number of results to return
            
        Returns:
            List of matching sections with vector similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Vector similarity search using cosine distance
                    sql = """
                        SELECT 
                            ds.section_id::text,
                            ds.doc_id::text,
                            ds.section_path,
                            ds.clause_id,
                            ds.heading,
                            ds.text,
                            ds.doc_type,
                            ds.doc_version,
                            ds.source,
                            ds.page,
                            -- Cosine similarity score (1 - cosine_distance)
                            (1 - (se.embedding <=> %s::vector)) as vector_score
                        FROM document_sections ds
                        JOIN section_embeddings se ON ds.section_id = se.section_id
                        WHERE ds.tenant_id = %s::uuid
                            {doc_type_filter}
                        ORDER BY se.embedding <=> %s::vector
                        LIMIT %s;
                    """
                    
                    # Add doc_type filter if specified
                    doc_type_filter = ""
                    params = [query_embedding, tenant_id, query_embedding]
                    
                    if doc_type:
                        doc_type_filter = "AND ds.doc_type = %s"
                        params.insert(2, doc_type)
                        params.append(doc_type)
                    
                    params.append(top_k)
                    
                    sql = sql.format(doc_type_filter=doc_type_filter)
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    logger.debug(f"Vector search returned {len(results)} results")
                    return [dict(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    def merge_and_deduplicate(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge BM25 and vector results, keeping best score for duplicates
        
        Args:
            bm25_results: Results from BM25 search
            vector_results: Results from vector search
            
        Returns:
            Merged and deduplicated results
        """
        # Use section_id as key
        merged = {}
        
        # Add BM25 results
        for result in bm25_results:
            section_id = result['section_id']
            merged[section_id] = {
                **result,
                'bm25_score': result.get('bm25_score', 0.0),
                'vector_score': 0.0  # Will be updated if found in vector results
            }
        
        # Merge vector results
        for result in vector_results:
            section_id = result['section_id']
            if section_id in merged:
                # Update vector score
                merged[section_id]['vector_score'] = result.get('vector_score', 0.0)
            else:
                # Add new result
                merged[section_id] = {
                    **result,
                    'bm25_score': 0.0,
                    'vector_score': result.get('vector_score', 0.0)
                }
        
        return list(merged.values())
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder
        
        Args:
            query: Original query
            candidates: Candidate sections from hybrid search
            top_k: Number of final results
            
        Returns:
            Reranked results with rerank scores
        """
        if not candidates:
            return []
        
        try:
            # Prepare query-document pairs
            pairs = []
            for candidate in candidates:
                # Combine heading + text for better context
                doc_text = f"{candidate['heading']}: {candidate['text'][:500]}"
                pairs.append([query, doc_text])
            
            # Get rerank scores
            rerank_scores = self.reranker.predict(pairs, show_progress_bar=False)
            
            # Add scores to candidates
            for i, candidate in enumerate(candidates):
                candidate['rerank_score'] = float(rerank_scores[i])
            
            # Sort by rerank score
            candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            return candidates[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return candidates sorted by vector score
            candidates.sort(key=lambda x: x.get('vector_score', 0), reverse=True)
            return candidates[:top_k]
    
    def calculate_confidence(
        self,
        bm25_score: float,
        vector_score: float,
        rerank_score: float,
        clause_id_match: bool
    ) -> float:
        """
        Calculate calibrated confidence score from signals
        
        Formula (weighted average):
        - BM25: 20%
        - Vector: 30%
        - Rerank: 45%
        - Clause ID match: +5% bonus
        
        Args:
            bm25_score: BM25 similarity score
            vector_score: Vector similarity score (0-1)
            rerank_score: Cross-encoder score (typically -10 to 10)
            clause_id_match: Whether clause IDs matched exactly
            
        Returns:
            Confidence score (0-1)
        """
        # Normalize rerank score (sigmoid)
        rerank_norm = 1 / (1 + np.exp(-rerank_score))
        
        # Normalize BM25 score (typically 0-6, normalize to 0-1)
        bm25_norm = min(bm25_score / 6.0, 1.0)
        
        # Weighted average
        confidence = (
            0.20 * bm25_norm +
            0.30 * vector_score +
            0.45 * rerank_norm
        )
        
        # Bonus for exact clause ID match
        if clause_id_match:
            confidence = min(confidence + 0.05, 1.0)
        
        return round(confidence, 3)
    
    def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        doc_type: Optional[str] = None,
        top_k: int = 10,
        bm25_top_k: int = 50,
        vector_top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Full hybrid retrieval pipeline
        
        Workflow:
        1. BM25 search → top-50
        2. Vector search → top-50
        3. Merge & deduplicate
        4. Cross-encoder rerank → top-k
        5. Calculate confidence scores
        
        Args:
            query: Search query
            tenant_id: Tenant ID
            doc_type: Optional document type filter
            top_k: Number of final results
            bm25_top_k: Candidates from BM25
            vector_top_k: Candidates from vector search
            
        Returns:
            Ranked results with confidence scores
        """
        logger.info(f"Hybrid search: query='{query[:50]}...', tenant={tenant_id}, doc_type={doc_type}")
        
        # Step 1: BM25 search
        logger.debug("Running BM25 search...")
        bm25_results = self.bm25_search(query, tenant_id, doc_type, bm25_top_k)
        
        # Step 2: Vector search
        logger.debug("Running vector search...")
        vector_results = self.vector_search(query, tenant_id, doc_type, vector_top_k)
        
        # Step 3: Merge
        logger.debug("Merging results...")
        merged_results = self.merge_and_deduplicate(bm25_results, vector_results)
        logger.info(f"Merged to {len(merged_results)} unique candidates")
        
        # Step 4: Rerank
        logger.debug("Reranking with cross-encoder...")
        reranked_results = self.rerank(query, merged_results, top_k)
        
        # Step 5: Calculate confidence
        for result in reranked_results:
            # Check if clause IDs match (if query contains clause ID pattern)
            clause_id_match = False
            if result.get('clause_id'):
                # Simple check: if query contains the clause ID
                clause_id_match = result['clause_id'].lower() in query.lower()
            
            result['confidence'] = self.calculate_confidence(
                bm25_score=result.get('bm25_score', 0.0),
                vector_score=result.get('vector_score', 0.0),
                rerank_score=result.get('rerank_score', 0.0),
                clause_id_match=clause_id_match
            )
            result['clause_id_match'] = clause_id_match
        
        logger.info(f"✅ Hybrid search complete: {len(reranked_results)} results, avg confidence: {np.mean([r['confidence'] for r in reranked_results]) if reranked_results else 0:.3f}")
        
        return reranked_results


# Singleton instance
hybrid_retrieval_service = None

def get_hybrid_retrieval_service() -> HybridRetrievalService:
    """Get singleton instance of hybrid retrieval service"""
    global hybrid_retrieval_service
    if hybrid_retrieval_service is None:
        hybrid_retrieval_service = HybridRetrievalService()
    return hybrid_retrieval_service
