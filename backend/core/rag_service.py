"""
RAG Service for Regulatory Compliance
Uses OpenAI text-embedding-3-large for high-accuracy semantic matching
ChromaDB for vector storage
"""
import logging
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service using OpenAI text-embedding-3-large for highest accuracy semantic matching"""
    
    def __init__(self):
        self.emergent_key = None
        self.openai_client = None
        self.embedding_model = "text-embedding-3-large"  # 3072 dimensions, highest accuracy
        
        # Initialize ChromaDB with persistent storage
        persist_dir = os.getenv("CHROMADB_DIR", "./chromadb_data")
        
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB initialized at {persist_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding using OpenAI API
        Uses text-embedding-3-large (3072 dimensions) for highest accuracy
        """
        try:
            # Lazy load OpenAI client
            if self.openai_client is None:
                # Use dedicated OpenAI key for embeddings
                openai_key = os.getenv("OPENAI_API_KEY")
                if not openai_key:
                    raise Exception("OPENAI_API_KEY not found in environment")
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized for embeddings")
            
            # Clean text - remove excessive whitespace
            text = ' '.join(text.split())
            
            # Truncate if too long (8191 tokens max for embeddings)
            if len(text) > 8000:
                text = text[:8000]
            
            # Get embedding from OpenAI
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text before chunking to remove noise
        
        - Removes excessive whitespace
        - Removes page numbers and common footers
        - Normalizes line breaks
        - Removes non-content patterns
        """
        import re
        
        # Remove page numbers (e.g., "Page 5 of 20", "- 5 -")
        text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'-\s*\d+\s*-', '', text)
        text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
        
        # Remove common headers/footers (e.g., "ISO 13485:2016", "© 2024")
        text = re.sub(r'©\s*\d{4}', '', text)
        text = re.sub(r'All rights reserved', '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace while preserving paragraph structure
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = ' '.join(line.split())  # Collapse multiple spaces
            if line:  # Keep non-empty lines
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remove very short lines that are likely artifacts (< 10 chars)
        lines = text.split('\n')
        meaningful_lines = [line for line in lines if len(line.strip()) >= 10 or line.strip().endswith(':')]
        text = '\n'.join(meaningful_lines)
        
        return text
    
    def _is_section_header(self, text: str) -> bool:
        """
        Detect if text is a section header
        Common patterns:
        - "4.2 Document Control"
        - "Clause 7: Product realization"
        - "Section 3 - Requirements"
        """
        import re
        
        # Check for numbered sections
        if re.match(r'^\d+\.?\d*\.?\d*\s+[A-Z]', text.strip()):
            return True
        
        # Check for "Clause", "Section", "Article" keywords
        if re.match(r'^(Clause|Section|Article|Chapter)\s+\d+', text.strip(), flags=re.IGNORECASE):
            return True
        
        # Check if it's short and title-case (likely a heading)
        if len(text.strip()) < 80 and text.strip().istitle():
            return True
        
        return False
    
    def _chunk_document_improved(
        self, 
        text: str, 
        chunk_size: int = 1000,  # Increased from 500 for better semantic coherence
        overlap: int = 200,      # Increased overlap for better context
        min_chunk_size: int = 300  # Minimum viable chunk size
    ) -> List[Dict[str, Any]]:
        """
        Improved chunking strategy for regulatory documents
        
        Features:
        - Sentence-aware chunking (breaks at sentence boundaries)
        - Section-aware chunking (preserves section structure)
        - Larger chunks for better semantic coherence
        - Smart overlap to maintain context
        - Filters out non-content elements
        
        Args:
            text: Document text
            chunk_size: Target characters per chunk (default 1000)
            overlap: Overlap between chunks (default 200)
            min_chunk_size: Minimum chunk size to avoid tiny fragments
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        import re
        
        # Clean text first
        text = self._clean_text(text)
        
        chunks = []
        chunk_id = 0
        
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        if len(paragraphs) == 1:
            # If no double newlines, split by single newlines
            paragraphs = text.split('\n')
        
        current_chunk = ""
        current_start = 0
        section_header = ""
        
        for para_idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para or len(para) < 10:
                continue
            
            # Check if this is a section header
            if self._is_section_header(para):
                section_header = para
                
                # If current chunk is substantial, save it before starting new section
                if len(current_chunk) >= min_chunk_size:
                    # Try to break at sentence boundary
                    sentences = self._split_into_sentences(current_chunk)
                    if len(sentences) > 0:
                        # Add chunk
                        chunk_text = ' '.join(sentences).strip()
                        if chunk_text:
                            chunks.append({
                                'text': chunk_text,
                                'chunk_id': chunk_id,
                                'start_char': current_start,
                                'end_char': current_start + len(chunk_text),
                                'length': len(chunk_text),
                                'section_header': section_header,
                                'semantic_unit': 'section'
                            })
                            chunk_id += 1
                    
                    current_chunk = section_header + "\n"
                    current_start = current_start + len(current_chunk)
                else:
                    current_chunk += para + "\n"
                
                continue
            
            # Add paragraph to current chunk
            potential_chunk = current_chunk + para + "\n"
            
            if len(potential_chunk) >= chunk_size:
                # Chunk is large enough, try to break at sentence boundary
                sentences = self._split_into_sentences(current_chunk + para)
                
                if len(sentences) > 1:
                    # Take sentences until we reach target size
                    accumulated = ""
                    remaining = []
                    for sent in sentences:
                        if len(accumulated) < chunk_size:
                            accumulated += sent + " "
                        else:
                            remaining.append(sent)
                    
                    # Add chunk
                    chunk_text = accumulated.strip()
                    if len(chunk_text) >= min_chunk_size:
                        chunks.append({
                            'text': chunk_text,
                            'chunk_id': chunk_id,
                            'start_char': current_start,
                            'end_char': current_start + len(chunk_text),
                            'length': len(chunk_text),
                            'section_header': section_header,
                            'semantic_unit': 'paragraph_group'
                        })
                        chunk_id += 1
                    
                    # Start new chunk with overlap (last few sentences)
                    if len(remaining) > 0:
                        # Include last sentence from previous chunk for context
                        overlap_sentences = sentences[-2:] if len(sentences) >= 2 else sentences[-1:]
                        current_chunk = ' '.join(overlap_sentences + remaining) + "\n"
                        current_start = current_start + len(accumulated) - len(' '.join(overlap_sentences))
                    else:
                        current_chunk = ' '.join(remaining) + "\n"
                        current_start = current_start + len(accumulated)
                else:
                    # Single long sentence/paragraph, chunk it
                    current_chunk = potential_chunk
            else:
                current_chunk = potential_chunk
        
        # Add remaining chunk
        if len(current_chunk.strip()) >= min_chunk_size:
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_id': chunk_id,
                'start_char': current_start,
                'end_char': current_start + len(current_chunk),
                'length': len(current_chunk),
                'section_header': section_header,
                'semantic_unit': 'final'
            })
        
        logger.info(f"Created {len(chunks)} chunks (avg size: {sum(c['length'] for c in chunks) // max(len(chunks), 1)} chars)")
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using simple heuristics
        Handles common abbreviations and edge cases
        """
        import re
        
        # Replace common abbreviations to avoid false splits
        text = text.replace('Dr.', 'Dr').replace('Mr.', 'Mr').replace('Mrs.', 'Mrs')
        text = text.replace('e.g.', 'eg').replace('i.e.', 'ie').replace('etc.', 'etc')
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Restore abbreviations
        sentences = [
            s.replace('Dr', 'Dr.').replace('Mr', 'Mr.').replace('Mrs', 'Mrs.')
             .replace('eg', 'e.g.').replace('ie', 'i.e.').replace('etc', 'etc.')
            for s in sentences
        ]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _chunk_document(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Legacy chunking method - redirects to improved version
        Kept for backward compatibility
        """
        logger.info("Using improved chunking strategy")
        return self._chunk_document_improved(text, chunk_size=1000, overlap=200)
    
    def add_regulatory_document(
        self,
        tenant_id: str,
        doc_id: str,
        doc_name: str,
        content: str,
        framework: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add regulatory document to RAG system
        
        Args:
            tenant_id: Tenant ID
            doc_id: Document ID
            doc_name: Document name
            content: Document content
            framework: Regulatory framework (ISO_13485, FDA_21CFR820, etc.)
            metadata: Additional metadata
            
        Returns:
            Summary of chunks added
        """
        try:
            # Get or create collection for tenant
            collection_name = f"regulatory_{tenant_id}".replace("-", "_")
            
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"tenant_id": tenant_id}
                )
            
            # Chunk the document
            chunks = self._chunk_document(content)
            
            # Prepare data for ChromaDB
            chunk_ids = []
            chunk_texts = []
            chunk_embeddings = []
            chunk_metadatas = []
            
            for chunk in chunks:
                chunk_id = f"{doc_id}_chunk_{chunk['chunk_id']}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk['text'])
                
                # Generate embedding
                embedding = self._get_embedding(chunk['text'])
                chunk_embeddings.append(embedding)
                
                # Metadata
                chunk_meta = {
                    'doc_id': doc_id,
                    'doc_name': doc_name,
                    'framework': framework,
                    'chunk_id': chunk['chunk_id'],
                    'start_char': chunk['start_char'],
                    'end_char': chunk['end_char'],
                    'tenant_id': tenant_id,
                    'section_header': chunk.get('section_header', ''),
                    'semantic_unit': chunk.get('semantic_unit', 'paragraph')
                }
                if metadata:
                    chunk_meta.update(metadata)
                
                chunk_metadatas.append(chunk_meta)
            
            # Add to ChromaDB
            collection.add(
                ids=chunk_ids,
                embeddings=chunk_embeddings,
                documents=chunk_texts,
                metadatas=chunk_metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks for document {doc_id}")
            
            return {
                'doc_id': doc_id,
                'chunks_added': len(chunks),
                'total_chars': len(content),
                'collection': collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to add regulatory document: {e}")
            raise
    
    def search_regulatory_requirements(
        self,
        tenant_id: str,
        query_text: str,
        framework: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant regulatory requirements
        
        Args:
            tenant_id: Tenant ID
            query_text: Search query
            framework: Filter by framework (optional)
            n_results: Number of results
            
        Returns:
            List of matching chunks with scores
        """
        try:
            collection_name = f"regulatory_{tenant_id}".replace("-", "_")
            
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                logger.warning(f"No regulatory documents found for tenant {tenant_id}")
                return []
            
            # Generate query embedding
            query_embedding = self._get_embedding(query_text)
            
            # Build where filter
            where_filter = None
            if framework:
                where_filter = {"framework": framework}
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter
            )
            
            # Format results
            matches = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    matches.append({
                        'chunk_id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            return matches
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def compare_documents(
        self,
        tenant_id: str,
        qsp_content: str,
        framework: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Compare QSP against regulatory requirements
        
        Args:
            tenant_id: Tenant ID
            qsp_content: QSP document content
            framework: Regulatory framework to check against
            threshold: Similarity threshold
            
        Returns:
            Compliance analysis with matches and gaps
        """
        try:
            # Chunk the QSP
            qsp_chunks = self._chunk_document(qsp_content, chunk_size=300)
            
            matches = []
            covered_requirements = set()
            
            # Search for each QSP chunk
            for chunk in qsp_chunks:
                results = self.search_regulatory_requirements(
                    tenant_id=tenant_id,
                    query_text=chunk['text'],
                    framework=framework,
                    n_results=3
                )
                
                for result in results:
                    if result.get('distance', 1.0) < (1 - threshold):
                        matches.append({
                            'qsp_chunk': chunk['text'][:200],
                            'regulatory_text': result['text'][:200],
                            'doc_name': result['metadata'].get('doc_name'),
                            'confidence': 1 - result.get('distance', 1.0)
                        })
                        covered_requirements.add(result['chunk_id'])
            
            # Calculate coverage
            collection_name = f"regulatory_{tenant_id}".replace("-", "_")
            try:
                collection = self.chroma_client.get_collection(collection_name)
                total_chunks = collection.count()
                coverage = len(covered_requirements) / total_chunks if total_chunks > 0 else 0
            except:
                total_chunks = 0
                coverage = 0
            
            return {
                'framework': framework,
                'matches_found': len(matches),
                'unique_requirements_covered': len(covered_requirements),
                'total_requirements': total_chunks,
                'coverage_percentage': round(coverage * 100, 2),
                'matches': matches[:10]  # Top 10 matches
            }
            
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            raise
    
    def delete_document(
        self,
        tenant_id: str,
        doc_id: str
    ) -> bool:
        """
        Delete regulatory document from RAG system
        """
        try:
            collection_name = f"regulatory_{tenant_id}".replace("-", "_")
            collection = self.chroma_client.get_collection(collection_name)
            
            # Get all chunk IDs for this document
            results = collection.get(
                where={"doc_id": doc_id}
            )
            
            if results['ids']:
                collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {doc_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def list_regulatory_documents(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        List all regulatory documents for tenant
        """
        try:
            collection_name = f"regulatory_{tenant_id}".replace("-", "_")
            
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                return []
            
            # Get all documents
            results = collection.get()
            
            # Group by doc_id
            docs = {}
            for i, metadata in enumerate(results['metadatas']):
                doc_id = metadata['doc_id']
                if doc_id not in docs:
                    docs[doc_id] = {
                        'doc_id': doc_id,
                        'doc_name': metadata['doc_name'],
                        'framework': metadata['framework'],
                        'chunk_count': 0
                    }
                docs[doc_id]['chunk_count'] += 1
            
            return list(docs.values())
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

# Singleton instance
rag_service = RAGService()
