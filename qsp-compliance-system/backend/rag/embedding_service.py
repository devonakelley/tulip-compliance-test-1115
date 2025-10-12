"""
Embedding service for generating vector representations of text
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import asyncio
import time

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings from text"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        self._initialized = False
        self.embedding_dimension = 384  # Default for all-MiniLM-L6-v2
        
    async def initialize(self):
        """Initialize the embedding model"""
        if self._initialized:
            return
            
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            
            # Load model in thread pool to avoid blocking
            self.model = await asyncio.to_thread(
                SentenceTransformer, self.model_name
            )
            
            # Get actual embedding dimension
            test_embedding = self.model.encode(["test"])
            self.embedding_dimension = len(test_embedding[0])
            
            self._initialized = True
            logger.info(f"Embedding service initialized. Dimension: {self.embedding_dimension}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            NumPy array of embeddings
        """
        if not self._initialized:
            await self.initialize()
            
        if not texts:
            return np.array([])
            
        try:
            start_time = time.time()
            
            # Generate embeddings in thread pool
            embeddings = await asyncio.to_thread(
                self.model.encode, 
                texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            duration = time.time() - start_time
            logger.debug(f"Generated {len(texts)} embeddings in {duration:.2f}s")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            NumPy array embedding
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if len(embeddings) > 0 else np.array([])
    
    async def similarity_search(
        self,
        query_text: str,
        candidate_texts: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find most similar texts to a query
        
        Args:
            query_text: Query text
            candidate_texts: List of candidate texts
            top_k: Number of top results to return
            
        Returns:
            List of similarity results with text and score
        """
        if not candidate_texts:
            return []
            
        try:
            # Generate embeddings
            query_embedding = await self.generate_single_embedding(query_text)
            candidate_embeddings = await self.generate_embeddings(candidate_texts)
            
            # Calculate cosine similarities
            similarities = self._cosine_similarity(query_embedding, candidate_embeddings)
            
            # Get top-k results
            results = []
            for i, similarity in enumerate(similarities):
                results.append({
                    'text': candidate_texts[i],
                    'similarity_score': float(similarity),
                    'index': i
                })
            
            # Sort by similarity score (descending)
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def _cosine_similarity(self, query_embedding: np.ndarray, candidate_embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and candidate embeddings"""
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        candidate_norms = candidate_embeddings / np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
        
        # Calculate dot product (cosine similarity for normalized vectors)
        similarities = np.dot(candidate_norms, query_norm)
        
        return similarities
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the embedding service"""
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'initialized': self._initialized
        }
    
    async def cleanup(self):
        """Cleanup embedding service resources"""
        self.model = None
        self._initialized = False
        logger.info("Embedding service cleaned up")