"""
Production-grade Pydantic models for QSP Compliance Checker
Designed for regulated medical device QA/RA work
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import uuid4


# ============================================================================
# Retrieval & Mapping Models
# ============================================================================

class MappingSignal(BaseModel):
    """
    Retrieval signals used to compute confidence score
    """
    bm25: float = Field(..., ge=0.0, description="BM25/keyword match score")
    vector: float = Field(..., ge=0.0, le=1.0, description="Vector similarity score (0-1)")
    rerank: float = Field(..., ge=0.0, le=1.0, description="Cross-encoder rerank score (0-1)")
    clause_id_match: bool = Field(..., description="Whether clause IDs matched exactly")


class ClauseMapping(BaseModel):
    """
    Mapping between external regulatory requirement and internal QSP section
    """
    mapping_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique mapping ID")
    run_id: str = Field(..., description="Analysis run ID")
    tenant_id: str = Field(..., description="Tenant ID")
    
    # External (regulatory) side
    external_doc_id: str = Field(..., description="External document ID (ISO, FDA, etc.)")
    external_doc_name: str = Field(..., description="External document name")
    external_clause_id: Optional[str] = Field(None, description="Clause ID (e.g., '4.2.2', '§820.70')")
    external_section_path: Optional[str] = Field(None, description="Section path (e.g., '4.2.2.b')")
    external_text: str = Field(..., max_length=2000, description="Text span from external doc")
    
    # Internal (QSP) side  
    internal_doc_id: str = Field(..., description="Internal QSP document ID")
    internal_doc_name: str = Field(..., description="Internal document name")
    internal_section_path: str = Field(..., description="Internal section path")
    internal_text: str = Field(..., max_length=2000, description="Text span from internal doc")
    
    # Confidence & signals
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score (0-1)")
    signals: MappingSignal = Field(..., description="Raw retrieval signals")
    
    # Rationale
    rationale: str = Field(..., max_length=500, description="2-3 sentence explanation (LLM-generated)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User or system that created mapping")
    
    # Review status
    reviewer_status: Literal["unreviewed", "accepted", "rejected", "needs_followup"] = "unreviewed"
    reviewer_id: Optional[str] = None
    reviewer_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class Gap(BaseModel):
    """
    Gap in coverage between external regulatory requirement and internal QSPs
    FLAG-ONLY - no automated rewriting or suggestions
    """
    gap_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique gap ID")
    run_id: str = Field(..., description="Analysis run ID")
    tenant_id: str = Field(..., description="Tenant ID")
    
    # External requirement
    external_doc_id: str = Field(..., description="External document ID")
    external_doc_name: str = Field(..., description="External document name")
    external_clause_id: Optional[str] = Field(None, description="Clause ID if available")
    external_section_path: Optional[str] = Field(None, description="Section path")
    external_text: str = Field(..., max_length=2000, description="Text of requirement")
    
    # Gap classification
    status: Literal["covered", "partial", "missing", "conflict"] = Field(
        ..., 
        description="Coverage status: covered (full), partial (some elements), missing (none), conflict (contradictory)"
    )
    missing_elements: List[str] = Field(
        default_factory=list, 
        description="Specific sub-requirements that are missing (for 'partial' status)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in gap classification")
    
    # References (for 'covered' and 'partial')
    internal_references: List[str] = Field(
        default_factory=list,
        description="List of internal doc IDs that address this requirement"
    )
    
    # Review
    reviewer_status: Literal["unreviewed", "accepted", "rejected", "needs_followup"] = "unreviewed"
    reviewer_id: Optional[str] = None
    reviewer_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Audit Trail Models
# ============================================================================

class AuditEvent(BaseModel):
    """
    Immutable audit event for traceability and tamper-evidence
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")
    tenant_id: str = Field(..., description="Tenant ID")
    
    # Actor & action
    actor: str = Field(..., description="User ID or 'system'")
    action: str = Field(..., description="Action type (e.g., 'upload', 'map', 'review', 'approve')")
    
    # Target
    doc_id: Optional[str] = Field(None, description="Document ID if applicable")
    mapping_id: Optional[str] = Field(None, description="Mapping ID if applicable")
    gap_id: Optional[str] = Field(None, description="Gap ID if applicable")
    
    # Payload & hash chain
    payload: dict = Field(default_factory=dict, description="Event-specific data")
    payload_sha256: str = Field(..., description="SHA-256 hash of payload")
    prev_event_sha256: Optional[str] = Field(None, description="Hash of previous event (blockchain-style)")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        # Make audit events immutable after creation
        frozen = True


# ============================================================================
# Document Models
# ============================================================================

class DocumentSection(BaseModel):
    """
    Structured section from parsed regulatory or QSP document
    """
    section_id: str = Field(default_factory=lambda: str(uuid4()))
    doc_id: str = Field(..., description="Parent document ID")
    
    # Structure
    section_path: str = Field(..., description="Hierarchical path (e.g., '4.2.2.b')")
    clause_id: Optional[str] = Field(None, description="Extracted clause ID if present")
    heading: str = Field(..., description="Section heading/title")
    text: str = Field(..., description="Section text content")
    
    # Location
    page: Optional[int] = Field(None, description="Page number in source document")
    start_char: Optional[int] = Field(None, description="Character offset start")
    end_char: Optional[int] = Field(None, description="Character offset end")
    
    # Metadata
    doc_type: Literal["ISO", "CFR", "MDR", "QSP", "SOP", "FORM", "OTHER"] = Field(..., description="Document type")
    doc_version: str = Field(..., description="Document version")
    source: str = Field(..., description="Source filename")
    rev_date: Optional[datetime] = Field(None, description="Revision date if available")
    
    # Processing
    parent_section_id: Optional[str] = Field(None, description="Parent section ID for hierarchy")
    depth: int = Field(0, description="Nesting depth in document structure")


class DocumentMetadata(BaseModel):
    """
    Metadata for uploaded document
    """
    doc_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str = Field(..., description="Tenant ID")
    
    # Document info
    filename: str = Field(..., description="Original filename")
    doc_type: Literal["ISO", "CFR", "MDR", "QSP", "SOP", "FORM", "OTHER"]
    doc_version: str = Field(..., description="Document version (e.g., 'ISO 13485:2024')")
    title: str = Field(..., description="Document title")
    
    # Processing status
    status: Literal["uploaded", "parsing", "parsed", "indexing", "indexed", "error"]
    error_message: Optional[str] = None
    
    # Stats
    total_sections: int = 0
    total_pages: Optional[int] = None
    total_chunks: int = 0
    
    # Storage
    storage_path: str = Field(..., description="Path to stored file (S3 or local)")
    parsed_json_path: Optional[str] = Field(None, description="Path to parsed JSON")
    
    # Audit
    uploaded_by: str = Field(..., description="User ID")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    indexed_at: Optional[datetime] = None


# ============================================================================
# Analysis Run Models
# ============================================================================

class AnalysisRun(BaseModel):
    """
    Metadata for a compliance mapping analysis run
    """
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str = Field(..., description="Tenant ID")
    
    # Input documents
    external_doc_ids: List[str] = Field(..., description="External regulatory document IDs")
    internal_doc_ids: List[str] = Field(..., description="Internal QSP document IDs")
    
    # Status
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)
    
    # Results
    total_mappings: int = 0
    total_gaps: int = 0
    avg_confidence: float = 0.0
    
    # Timing
    started_by: str = Field(..., description="User ID")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Report
    report_json_path: Optional[str] = None
    report_csv_path: Optional[str] = None
