"""
Change Impact Detection Service
Identifies which internal QSP sections are affected by regulatory changes

Input: JSON deltas (clause_id, change_text, change_type)
Output: Ranked QSP sections with confidence scores
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI
import os
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ChangeImpactService:
    """
    Detects which QSP sections are impacted by regulatory changes
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize change impact service
        
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
        
        self.embedding_model = "text-embedding-3-large"
        self.embedding_dimensions = 1536
        
        # Impact detection threshold
        self.impact_threshold = 0.55  # Cosine similarity > 0.55 = potential impact
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for change text
        
        Args:
            text: Change description
            
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
    
    def ingest_qsp_document(
        self,
        tenant_id: str,
        doc_id: str,
        doc_name: str,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ingest QSP document sections and generate embeddings
        
        Args:
            tenant_id: Tenant ID
            doc_id: Document ID
            doc_name: Document name
            sections: List of sections with {section_path, heading, text}
            
        Returns:
            Ingestion summary
        """
        try:
            embedded_count = 0
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    for section in sections:
                        section_id = str(uuid.uuid4())
                        
                        # Combine heading + text for better semantic search
                        full_text = f"{section['heading']}: {section['text']}"
                        
                        # Generate embedding
                        embedding = self._get_embedding(full_text)
                        
                        # Insert section
                        cur.execute("""
                            INSERT INTO document_sections (
                                section_id, doc_id, tenant_id,
                                section_path, heading, text,
                                doc_type, doc_version, source
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (section_id) DO NOTHING
                        """, (
                            section_id, doc_id, tenant_id,
                            section.get('section_path', ''),
                            section['heading'],
                            section['text'],
                            'QSP',
                            section.get('version', 'unknown'),
                            doc_name
                        ))
                        
                        # Insert embedding
                        cur.execute("""
                            INSERT INTO section_embeddings (
                                section_id, tenant_id, embedding
                            ) VALUES (%s, %s, %s)
                            ON CONFLICT (section_id) DO UPDATE 
                            SET embedding = EXCLUDED.embedding
                        """, (section_id, tenant_id, embedding))
                        
                        embedded_count += 1
                    
                    conn.commit()
            
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
        
        Args:
            tenant_id: Tenant ID
            deltas: List of changes [{clause_id, change_text, change_type}]
            top_k: Number of top matches to return per change
            
        Returns:
            Analysis results with run_id and impacts
        """
        try:
            run_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            all_impacts = []
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Create analysis run record
                    cur.execute("""
                        INSERT INTO analysis_runs (
                            run_id, tenant_id, run_type, status, started_at
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (run_id, tenant_id, 'change_impact', 'running', timestamp))
                    
                    # Process each delta
                    for delta in deltas:
                        clause_id = delta['clause_id']
                        change_text = delta['change_text']
                        change_type = delta.get('change_type', 'modified')
                        
                        logger.info(f"Analyzing impact for {clause_id}: {change_text[:100]}...")
                        
                        # Generate embedding for change
                        change_embedding = self._get_embedding(change_text)
                        
                        # Vector search for similar QSP sections
                        cur.execute("""
                            SELECT 
                                ds.section_id::text,
                                ds.doc_id::text,
                                ds.section_path,
                                ds.heading,
                                ds.text,
                                ds.source as qsp_doc,
                                (1 - (se.embedding <=> %s::vector)) as confidence
                            FROM document_sections ds
                            JOIN section_embeddings se ON ds.section_id = se.section_id
                            WHERE ds.tenant_id = %s::uuid
                                AND ds.doc_type = 'QSP'
                                AND (1 - (se.embedding <=> %s::vector)) > %s
                            ORDER BY se.embedding <=> %s::vector
                            LIMIT %s
                        """, (
                            change_embedding, tenant_id, 
                            change_embedding, self.impact_threshold,
                            change_embedding, top_k
                        ))
                        
                        matches = cur.fetchall()
                        
                        # Store impact results
                        for match in matches:
                            impact_id = str(uuid.uuid4())
                            
                            # Generate rationale
                            rationale = self._generate_rationale(
                                clause_id, change_text, 
                                match['heading'], match['text'][:200],
                                match['confidence']
                            )
                            
                            # Insert impact result
                            cur.execute("""
                                INSERT INTO impact_results (
                                    impact_id, run_id, tenant_id,
                                    clause_id, change_text, change_type,
                                    qsp_doc, section_path, heading,
                                    confidence, rationale,
                                    created_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                impact_id, run_id, tenant_id,
                                clause_id, change_text, change_type,
                                match['qsp_doc'], match['section_path'], match['heading'],
                                float(match['confidence']), rationale,
                                timestamp
                            ))
                            
                            all_impacts.append({
                                'impact_id': impact_id,
                                'clause_id': clause_id,
                                'change_type': change_type,
                                'qsp_doc': match['qsp_doc'],
                                'section_path': match['section_path'],
                                'heading': match['heading'],
                                'confidence': round(float(match['confidence']), 3),
                                'rationale': rationale
                            })
                        
                        logger.info(f"Found {len(matches)} potential impacts for {clause_id}")
                    
                    # Update run status
                    cur.execute("""
                        UPDATE analysis_runs 
                        SET status = %s, completed_at = %s, total_impacts = %s
                        WHERE run_id = %s
                    """, ('completed', datetime.utcnow(), len(all_impacts), run_id))
                    
                    conn.commit()
            
            logger.info(f"✅ Impact analysis complete: run_id={run_id}, {len(all_impacts)} impacts found")
            
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
    
    def _generate_rationale(
        self,
        clause_id: str,
        change_text: str,
        qsp_heading: str,
        qsp_snippet: str,
        confidence: float
    ) -> str:
        """
        Generate human-readable rationale for impact match
        
        Args:
            clause_id: Regulatory clause ID
            change_text: Change description
            qsp_heading: QSP section heading
            qsp_snippet: QSP text snippet
            confidence: Confidence score
            
        Returns:
            Rationale text
        """
        # Simple template-based rationale (can upgrade to LLM-generated later)
        if confidence > 0.75:
            strength = "strong"
        elif confidence > 0.65:
            strength = "moderate"
        else:
            strength = "potential"
        
        return (
            f"The change to {clause_id} has a {strength} semantic match "
            f"(confidence: {confidence:.2f}) with the QSP section '{qsp_heading}'. "
            f"This suggests the internal procedure may need review to ensure alignment "
            f"with the updated regulatory requirement."
        )
    
    def get_report(
        self,
        run_id: str,
        tenant_id: str,
        format: str = 'json'
    ) -> Any:
        """
        Retrieve impact analysis report
        
        Args:
            run_id: Analysis run ID
            tenant_id: Tenant ID
            format: 'json' or 'csv'
            
        Returns:
            Report data
        """
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get run metadata
                    cur.execute("""
                        SELECT * FROM analysis_runs
                        WHERE run_id = %s AND tenant_id = %s
                    """, (run_id, tenant_id))
                    
                    run_info = cur.fetchone()
                    
                    if not run_info:
                        return {'error': 'Run not found'}
                    
                    # Get impacts
                    cur.execute("""
                        SELECT 
                            clause_id, change_type, qsp_doc, section_path,
                            heading, confidence, rationale, created_at
                        FROM impact_results
                        WHERE run_id = %s AND tenant_id = %s
                        ORDER BY confidence DESC
                    """, (run_id, tenant_id))
                    
                    impacts = cur.fetchall()
                    
                    if format == 'json':
                        return {
                            'run_id': run_id,
                            'status': run_info['status'],
                            'started_at': run_info['started_at'].isoformat() if run_info['started_at'] else None,
                            'completed_at': run_info['completed_at'].isoformat() if run_info['completed_at'] else None,
                            'total_impacts': len(impacts),
                            'impacts': [dict(row) for row in impacts]
                        }
                    else:
                        # CSV format
                        import csv
                        import io
                        
                        output = io.StringIO()
                        writer = csv.DictWriter(output, fieldnames=[
                            'clause_id', 'change_type', 'qsp_doc', 'section_path',
                            'heading', 'confidence', 'rationale'
                        ])
                        writer.writeheader()
                        for row in impacts:
                            writer.writerow({
                                'clause_id': row['clause_id'],
                                'change_type': row['change_type'],
                                'qsp_doc': row['qsp_doc'],
                                'section_path': row['section_path'],
                                'heading': row['heading'],
                                'confidence': row['confidence'],
                                'rationale': row['rationale']
                            })
                        
                        return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to retrieve report: {e}")
            raise


# Singleton instance
change_impact_service = None

def get_change_impact_service() -> ChangeImpactService:
    """Get singleton instance of change impact service"""
    global change_impact_service
    if change_impact_service is None:
        change_impact_service = ChangeImpactService()
    return change_impact_service
