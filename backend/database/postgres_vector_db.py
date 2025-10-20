"""
PostgreSQL + pgvector database manager for production RAG system
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class PostgresVectorDB:
    """
    Manages PostgreSQL database with pgvector extension for hybrid retrieval
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            connection_string: PostgreSQL connection string (defaults to POSTGRES_URL env var)
        """
        self.connection_string = connection_string or os.getenv(
            "POSTGRES_URL", 
            "postgresql://postgres:postgres@localhost:5432/qsp_compliance"
        )
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = False
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def initialize_schema(self):
        """
        Create tables and extensions for production RAG system
        """
        try:
            with self.conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Enable pg_trgm for BM25-like text search
                cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                
                # Document sections table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS document_sections (
                        section_id UUID PRIMARY KEY,
                        doc_id UUID NOT NULL,
                        tenant_id UUID NOT NULL,
                        
                        -- Structure
                        section_path TEXT NOT NULL,
                        clause_id TEXT,
                        heading TEXT NOT NULL,
                        text TEXT NOT NULL,
                        
                        -- Location
                        page INTEGER,
                        start_char INTEGER,
                        end_char INTEGER,
                        
                        -- Metadata
                        doc_type TEXT NOT NULL,
                        doc_version TEXT NOT NULL,
                        source TEXT NOT NULL,
                        rev_date TIMESTAMP,
                        
                        -- Hierarchy
                        parent_section_id UUID,
                        depth INTEGER DEFAULT 0,
                        
                        -- Timestamps
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Indexes for tenant isolation
                        CONSTRAINT fk_parent FOREIGN KEY (parent_section_id) 
                            REFERENCES document_sections(section_id) ON DELETE CASCADE
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_sections_tenant 
                        ON document_sections(tenant_id);
                    CREATE INDEX IF NOT EXISTS idx_sections_doc 
                        ON document_sections(doc_id);
                    CREATE INDEX IF NOT EXISTS idx_sections_clause 
                        ON document_sections(clause_id) WHERE clause_id IS NOT NULL;
                    
                    -- Full-text search index using pg_trgm
                    CREATE INDEX IF NOT EXISTS idx_sections_text_trgm 
                        ON document_sections USING gin (text gin_trgm_ops);
                    CREATE INDEX IF NOT EXISTS idx_sections_heading_trgm 
                        ON document_sections USING gin (heading gin_trgm_ops);
                """)
                
                # Vector embeddings table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS section_embeddings (
                        embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        section_id UUID NOT NULL REFERENCES document_sections(section_id) ON DELETE CASCADE,
                        tenant_id UUID NOT NULL,
                        
                        -- Vector embedding (3072 dimensions for text-embedding-3-large)
                        -- Note: HNSW only supports up to 2000 dims, so we use IVFFlat
                        embedding vector(3072) NOT NULL,
                        
                        -- Metadata
                        model_name TEXT DEFAULT 'text-embedding-3-large',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        UNIQUE(section_id)
                    );
                    
                    -- IVFFlat index for vector similarity search (supports 3072 dimensions)
                    -- Using 100 lists for good balance between speed and accuracy
                    CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
                        ON section_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                    
                    CREATE INDEX IF NOT EXISTS idx_embeddings_tenant 
                        ON section_embeddings(tenant_id);
                """)
                
                # Clause mappings table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS clause_mappings_prod (
                        mapping_id UUID PRIMARY KEY,
                        run_id UUID NOT NULL,
                        tenant_id UUID NOT NULL,
                        
                        -- External (regulatory) side
                        external_doc_id UUID NOT NULL,
                        external_doc_name TEXT NOT NULL,
                        external_clause_id TEXT,
                        external_section_path TEXT,
                        external_text TEXT NOT NULL,
                        
                        -- Internal (QSP) side
                        internal_doc_id UUID NOT NULL,
                        internal_doc_name TEXT NOT NULL,
                        internal_section_path TEXT NOT NULL,
                        internal_text TEXT NOT NULL,
                        
                        -- Confidence & signals
                        confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                        bm25_score FLOAT,
                        vector_score FLOAT,
                        rerank_score FLOAT,
                        clause_id_match BOOLEAN DEFAULT FALSE,
                        
                        -- Rationale
                        rationale TEXT NOT NULL,
                        
                        -- Review
                        reviewer_status TEXT DEFAULT 'unreviewed',
                        reviewer_id UUID,
                        reviewer_comment TEXT,
                        reviewed_at TIMESTAMP,
                        
                        -- Metadata
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT NOT NULL
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_mappings_run 
                        ON clause_mappings_prod(run_id);
                    CREATE INDEX IF NOT EXISTS idx_mappings_tenant 
                        ON clause_mappings_prod(tenant_id);
                """)
                
                # Gaps table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS gaps_prod (
                        gap_id UUID PRIMARY KEY,
                        run_id UUID NOT NULL,
                        tenant_id UUID NOT NULL,
                        
                        -- External requirement
                        external_doc_id UUID NOT NULL,
                        external_doc_name TEXT NOT NULL,
                        external_clause_id TEXT,
                        external_section_path TEXT,
                        external_text TEXT NOT NULL,
                        
                        -- Gap classification
                        status TEXT NOT NULL CHECK (status IN ('covered', 'partial', 'missing', 'conflict')),
                        missing_elements JSONB DEFAULT '[]',
                        confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                        internal_references JSONB DEFAULT '[]',
                        
                        -- Review
                        reviewer_status TEXT DEFAULT 'unreviewed',
                        reviewer_id UUID,
                        reviewer_comment TEXT,
                        reviewed_at TIMESTAMP,
                        
                        -- Metadata
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_gaps_run 
                        ON gaps_prod(run_id);
                    CREATE INDEX IF NOT EXISTS idx_gaps_tenant 
                        ON gaps_prod(tenant_id);
                    CREATE INDEX IF NOT EXISTS idx_gaps_status 
                        ON gaps_prod(status);
                """)
                
                # Audit events table (append-only)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS audit_events_prod (
                        event_id UUID PRIMARY KEY,
                        tenant_id UUID NOT NULL,
                        
                        -- Actor & action
                        actor TEXT NOT NULL,
                        action TEXT NOT NULL,
                        
                        -- Target
                        doc_id UUID,
                        mapping_id UUID,
                        gap_id UUID,
                        
                        -- Payload & hash chain
                        payload JSONB DEFAULT '{}',
                        payload_sha256 TEXT NOT NULL,
                        prev_event_sha256 TEXT,
                        
                        -- Timestamp
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- No updates or deletes allowed
                        CHECK (timestamp <= CURRENT_TIMESTAMP)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_audit_tenant 
                        ON audit_events_prod(tenant_id);
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                        ON audit_events_prod(timestamp DESC);
                    CREATE INDEX IF NOT EXISTS idx_audit_actor 
                        ON audit_events_prod(actor);
                """)
                
                self.conn.commit()
                logger.info("PostgreSQL schema initialized successfully")
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton instance
def get_postgres_db():
    """Get PostgreSQL database instance"""
    return PostgresVectorDB()
