"""
Regulatory models for multi-framework compliance system
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class RegulatoryFramework(str, Enum):
    """Supported regulatory frameworks"""
    FDA_21CFR820 = "FDA_21CFR820"
    ISO_13485 = "ISO_13485"
    MDR_2017_745 = "MDR_2017_745"
    ISO_14971 = "ISO_14971"
    ISO_10993 = "ISO_10993"
    ISO_11135 = "ISO_11135"
    ISO_11607 = "ISO_11607"
    CFR_PART_11 = "21CFR_PART11"
    MDSAP = "MDSAP"

class DocumentType(str, Enum):
    """Document hierarchy types"""
    QUALITY_MANUAL = "QM"  # Level 1
    QSP = "QSP"  # Level 2
    WORK_INSTRUCTION = "WI"  # Level 3
    FORM = "FORM"  # Level 4
    REFERENCE_DOC = "RFD"  # Level 5
    EVIDENCE = "EVIDENCE"  # Level 6

class RegulatoryClause(BaseModel):
    """Individual regulatory clause/requirement"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework: RegulatoryFramework
    clause_id: str  # e.g., "7.3", "820.30", "Article 15"
    title: str
    requirement_text: str
    category: str  # e.g., "Design", "Risk Management", "Production"
    criticality: str = "medium"  # high, medium, low
    references: List[str] = Field(default_factory=list)  # Related clauses
    keywords: List[str] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentReference(BaseModel):
    """Extracted reference from document to another document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    source_doc_id: str
    source_doc_type: DocumentType
    target_doc_id: str  # e.g., "QSP 7.3-1", "WI-ENG-003"
    target_doc_type: Optional[DocumentType] = None
    reference_type: str  # "implements", "references", "uses", "supports"
    context: Optional[str] = None  # Surrounding text
    extracted_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RegulatoryCitation(BaseModel):
    """Extracted regulatory citation from document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    document_id: str
    document_type: DocumentType
    framework: RegulatoryFramework
    citation: str  # e.g., "ISO 13485:2016 Clause 7.3"
    clause_id: str  # e.g., "7.3"
    context: Optional[str] = None
    confidence: float = 1.0  # For regex: 1.0, for AI: 0.0-1.0
    extracted_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentHierarchy(BaseModel):
    """Document hierarchy and relationships"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    document_id: str
    document_name: str
    document_type: DocumentType
    level: int  # 1-6
    parent_docs: List[str] = Field(default_factory=list)  # Documents this implements
    child_docs: List[str] = Field(default_factory=list)  # Documents that implement this
    regulatory_citations: List[str] = Field(default_factory=list)  # Regulation citations
    implements_clauses: List[Dict[str, str]] = Field(default_factory=list)  # {framework, clause_id}
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ComplianceMatrix(BaseModel):
    """Compliance matrix showing regulation to document mappings"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    framework: RegulatoryFramework
    clause_id: str
    implementing_documents: List[Dict[str, Any]] = Field(default_factory=list)
    coverage_score: float = 0.0  # 0.0-1.0
    gaps: List[str] = Field(default_factory=list)
    last_analyzed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ImpactAnalysis(BaseModel):
    """Impact analysis for regulatory changes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    change_description: str
    affected_framework: RegulatoryFramework
    affected_clauses: List[str]
    impacted_documents: List[Dict[str, Any]] = Field(default_factory=list)  # {doc_id, doc_type, impact_type}
    cascade_depth: int = 0  # How many levels deep the impact goes
    total_documents_affected: int = 0
    analysis_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
