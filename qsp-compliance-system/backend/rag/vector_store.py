"""
Vector store for QSP document embeddings using ChromaDB
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import asyncio
import json
from datetime import datetime, timezone

from document_chunker import DocumentChunk

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector storage and retrieval system for QSP documents
    """
    
    def __init__(self, persist_directory: str = "/app/vector_db"):
        """
        Initialize vector store
        
        Args:
            persist_directory: Directory to persist vector database
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collections = {}
        self._initialized = False
        
    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        if self._initialized:
            return
            
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Initialize collections
            await self._initialize_collections()
            
            self._initialized = True
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def _initialize_collections(self):
        """Initialize vector database collections"""
        try:
            # QSP Documents collection
            self.collections['qsp_documents'] = self.client.get_or_create_collection(
                name="qsp_documents",
                metadata={
                    "description": "QSP document chunks with semantic embeddings",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # ISO Change summaries collection
            self.collections['iso_changes'] = self.client.get_or_create_collection(
                name="iso_changes",
                metadata={
                    "description": "ISO regulatory change summaries",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Regulatory mappings collection
            self.collections['regulatory_mappings'] = self.client.get_or_create_collection(
                name="regulatory_mappings",
                metadata={
                    "description": "Known mappings between QSP sections and regulatory clauses",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"Initialized {len(self.collections)} vector collections")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    async def store_document_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Store document chunks with embeddings
        
        Args:
            chunks: List of document chunks
            embeddings: Corresponding embeddings
            
        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()
            
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")
            
        try:
            collection = self.collections['qsp_documents']
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            chunk_embeddings = []
            
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = f"{chunk.document_id}_chunk_{chunk.chunk_index}"
                ids.append(chunk_id)
                documents.append(chunk.content)
                
                # Prepare metadata (ChromaDB doesn't support nested objects)
                metadata = {
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index,
                    'section_number': chunk.section_number or '',
                    'section_title': chunk.section_title or '',
                    'chunk_type': chunk.chunk_type,
                    'token_count': chunk.token_count,
                    'has_form_references': chunk.metadata.get('has_form_references', False),
                    'has_regulatory_references': chunk.metadata.get('has_regulatory_references', False),
                    'content_themes': json.dumps(chunk.metadata.get('content_themes', [])),
                    'created_at': chunk.metadata.get('created_at', datetime.now(timezone.utc).isoformat())
                }
                metadatas.append(metadata)
                chunk_embeddings.append(embedding)
            
            # Store in ChromaDB
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=chunk_embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(chunks)} document chunks in vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document chunks: {e}")
            return False
    
    async def store_iso_changes(
        self,
        changes: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Store ISO change summaries with embeddings
        
        Args:
            changes: List of ISO change data
            embeddings: Corresponding embeddings
            
        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            collection = self.collections['iso_changes']
            
            ids = []
            documents = []
            metadatas = []
            
            for change, embedding in zip(changes, embeddings):
                change_id = change.get('id', str(uuid.uuid4()))
                ids.append(change_id)
                
                # Use change description as document text
                document_text = change.get('description', change.get('summary', ''))
                documents.append(document_text)
                
                # Prepare metadata
                metadata = {
                    'change_id': change_id,
                    'clause_id': change.get('clause_id', ''),
                    'clause_title': change.get('clause_title', ''),
                    'change_type': change.get('change_type', 'modification'),
                    'impact_level': change.get('impact_level', 'medium'),
                    'effective_date': change.get('effective_date', ''),
                    'framework': change.get('framework', 'ISO_13485:2024'),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                metadatas.append(metadata)
            
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(changes)} ISO changes in vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store ISO changes: {e}")
            return False
    
    async def search_similar_qsp_sections(
        self,
        query_embedding: List[float],
        document_ids: Optional[List[str]] = None,
        section_types: Optional[List[str]] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar QSP sections
        
        Args:
            query_embedding: Query vector embedding
            document_ids: Filter by specific document IDs
            section_types: Filter by section types
            n_results: Number of results to return
            
        Returns:
            List of similar sections with metadata
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            collection = self.collections['qsp_documents']
            
            # Prepare filters
            where_filter = {}
            
            if document_ids:
                where_filter['document_id'] = {'$in': document_ids}
                
            if section_types:
                where_filter['chunk_type'] = {'$in': section_types}
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                }
                
                # Parse content themes back from JSON
                if 'content_themes' in result['metadata']:
                    try:
                        result['metadata']['content_themes'] = json.loads(
                            result['metadata']['content_themes']
                        )
                    except:
                        result['metadata']['content_themes'] = []
                
                formatted_results.append(result)
            
            logger.debug(f"Found {len(formatted_results)} similar QSP sections")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar QSP sections: {e}")
            return []
    
    async def search_relevant_iso_changes(
        self,
        query_embedding: List[float],
        framework: str = "ISO_13485:2024",
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant ISO changes
        
        Args:
            query_embedding: Query vector embedding  
            framework: ISO framework
            n_results: Number of results to return
            
        Returns:
            List of relevant ISO changes
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            collection = self.collections['iso_changes']
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={'framework': framework},
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i]
                }
                formatted_results.append(result)
            
            logger.debug(f"Found {len(formatted_results)} relevant ISO changes")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search ISO changes: {e}")
            return []
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored documents"""
        if not self._initialized:
            await self.initialize()
            
        try:
            stats = {}
            
            for collection_name, collection in self.collections.items():
                count = collection.count()
                stats[collection_name] = {
                    'total_chunks': count,
                    'collection_name': collection_name
                }
            
            # Get QSP-specific statistics
            if 'qsp_documents' in self.collections:
                qsp_collection = self.collections['qsp_documents']
                
                # Get unique document count
                all_results = qsp_collection.get(include=['metadatas'])
                unique_docs = set()
                
                if all_results['metadatas']:
                    for metadata in all_results['metadatas']:
                        unique_docs.add(metadata.get('document_id', 'unknown'))
                
                stats['qsp_documents']['unique_documents'] = len(unique_docs)
                stats['qsp_documents']['document_ids'] = list(unique_docs)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get document statistics: {e}")
            return {}
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            collection = self.collections['qsp_documents']
            
            # Get all chunks for this document
            results = collection.get(
                where={'document_id': document_id},
                include=['ids']
            )
            
            if results['ids']:
                collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"No chunks found for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup vector store resources"""
        self.client = None
        self.collections = {}
        self._initialized = False
        logger.info("Vector store cleaned up")