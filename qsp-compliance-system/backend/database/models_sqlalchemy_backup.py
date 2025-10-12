"""
SQLAlchemy ORM models for Enterprise QSP Compliance System
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, 
    JSON, ForeignKey, UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum

Base = declarative_base()

# Enums for database
class DocumentTypeEnum(enum.Enum):
    QSP = "qsp"
    REGULATORY = "regulatory"
    ISO_SUMMARY = "iso_summary"
    WORK_INSTRUCTION = "work_instruction"
    QUALITY_MANUAL = "quality_manual"
    PROCEDURE = "procedure"

class AnalysisStatusEnum(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SeverityEnum(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

# User Management
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, default=True, nullable=False)
    created_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime(timezone=True))
    preferences = Column(JSON, default=dict)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    analyses = relationship("ComplianceAnalysis", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    session_id = Column(String(255), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User")

# Document Management
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    document_type = Column(SQLEnum(DocumentTypeEnum), nullable=False, index=True)
    file_path = Column(String(1000))
    file_size = Column(Integer)
    file_hash = Column(String(64), index=True)  # SHA-256
    
    # Content
    content = Column(Text)
    processed_content = Column(JSON)  # Structured parsed content
    
    # Metadata
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    upload_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processed_date = Column(DateTime(timezone=True))
    last_modified = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Processing status
    processing_status = Column(String(20), default="pending")
    processing_error = Column(Text)
    
    # Compliance metrics
    sections_count = Column(Integer, default=0)
    clause_mappings_count = Column(Integer, default=0)
    compliance_score = Column(Float)
    last_analysis_date = Column(DateTime(timezone=True))
    
    # Organizational
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")
    clause_mappings = relationship("ClauseMapping", back_populates="document")
    
    __table_args__ = (
        Index("ix_documents_type_user", "document_type", "user_id"),
        Index("ix_documents_status", "processing_status"),
    )

class DocumentSection(Base):
    __tablename__ = "document_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    
    # Section identification
    section_number = Column(String(50))
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), index=True)  # For change detection
    
    # Hierarchy
    level = Column(Integer, default=1)
    parent_section_id = Column(UUID(as_uuid=True), ForeignKey("document_sections.id"))
    section_order = Column(Integer, default=0)
    
    # Analysis
    word_count = Column(Integer, default=0)
    confidence_score = Column(Float)
    
    # Metadata
    created_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_modified = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="sections")
    parent_section = relationship("DocumentSection", remote_side=[id])
    clause_mappings = relationship("ClauseMapping", back_populates="section")
    
    __table_args__ = (
        Index("ix_sections_document_order", "document_id", "section_order"),
    )

# Regulatory Framework Management
class RegulatoryFramework(Base):
    __tablename__ = "regulatory_frameworks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_name = Column(String(100), nullable=False, unique=True)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    effective_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Content
    framework_content = Column(JSON)  # Structured framework data
    clauses_count = Column(Integer, default=0)
    
    # Metadata
    created_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    clause_mappings = relationship("ClauseMapping", back_populates="framework")
    regulatory_changes = relationship("RegulatoryChange", back_populates="framework")
    
    __table_args__ = (
        UniqueConstraint("framework_name", "version", name="uq_framework_version"),
    )

class RegulatoryChange(Base):
    __tablename__ = "regulatory_changes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("regulatory_frameworks.id"), nullable=False)
    
    # Change identification
    clause_id = Column(String(100), nullable=False)
    change_type = Column(String(20), nullable=False)  # added, modified, deprecated, removed
    change_description = Column(Text, nullable=False)
    
    # Impact assessment
    impact_level = Column(SQLEnum(SeverityEnum), nullable=False)
    affected_sections = Column(JSON, default=list)
    implementation_guidance = Column(Text)
    
    # Timeline
    effective_date = Column(DateTime(timezone=True), nullable=False)
    announcement_date = Column(DateTime(timezone=True))
    processed_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Source
    source_document = Column(String(500))
    source_section = Column(String(100))
    
    # Relationships
    framework = relationship("RegulatoryFramework", back_populates="regulatory_changes")
    
    __table_args__ = (
        Index("ix_changes_framework_clause", "framework_id", "clause_id"),
        Index("ix_changes_effective_date", "effective_date"),
    )

# Compliance Analysis
class ComplianceAnalysis(Base):
    __tablename__ = "compliance_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Analysis configuration
    analysis_type = Column(String(50), nullable=False)
    regulatory_framework = Column(String(100), nullable=False)
    document_ids = Column(JSON, nullable=False)  # List of document IDs
    
    # Status and timing
    status = Column(SQLEnum(AnalysisStatusEnum), default=AnalysisStatusEnum.PENDING, index=True)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    processing_time_seconds = Column(Float)
    
    # Results summary
    overall_compliance_score = Column(Float)
    compliance_level = Column(String(30))
    total_sections_analyzed = Column(Integer, default=0)
    total_clauses_mapped = Column(Integer, default=0)
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)
    
    # Configuration and metadata
    analysis_parameters = Column(JSON, default=dict)
    ai_model_used = Column(String(50))
    quality_metrics = Column(JSON, default=dict)
    
    # Results storage
    detailed_results = Column(JSON)  # Full analysis results
    recommendations = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    compliance_gaps = relationship("ComplianceGap", back_populates="analysis", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_analyses_user_status", "user_id", "status"),
        Index("ix_analyses_started_at", "started_at"),
    )

class ClauseMapping(Base):
    __tablename__ = "clause_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    section_id = Column(UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("regulatory_frameworks.id"), nullable=False)
    
    # Mapping details
    clause_id = Column(String(100), nullable=False)
    clause_title = Column(String(500))
    confidence_score = Column(Float, nullable=False)
    evidence_text = Column(Text)
    mapping_rationale = Column(Text)
    
    # Validation
    created_by = Column(String(100), nullable=False)  # AI model or user ID
    created_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    validated = Column(Boolean, default=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_date = Column(DateTime(timezone=True))
    validation_notes = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="clause_mappings")
    section = relationship("DocumentSection", back_populates="clause_mappings")
    framework = relationship("RegulatoryFramework", back_populates="clause_mappings")
    validator = relationship("User")
    
    __table_args__ = (
        Index("ix_mappings_doc_clause", "document_id", "clause_id"),
        Index("ix_mappings_confidence", "confidence_score"),
    )

class ComplianceGap(Base):
    __tablename__ = "compliance_gaps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("compliance_analyses.id"), nullable=False, index=True)
    
    # Gap identification
    regulatory_framework = Column(String(100), nullable=False)
    clause_id = Column(String(100), nullable=False)
    clause_title = Column(String(500))
    gap_type = Column(String(50), nullable=False)  # missing, partial, outdated, conflicting
    severity = Column(SQLEnum(SeverityEnum), nullable=False, index=True)
    
    # Gap details
    description = Column(Text, nullable=False)
    affected_documents = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    estimated_effort = Column(String(20))  # low, medium, high
    compliance_impact = Column(Text)
    
    # Status tracking
    status = Column(String(30), default="open")  # open, in_progress, resolved, accepted_risk
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Timeline
    detected_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_date = Column(DateTime(timezone=True))
    
    # Relationships
    analysis = relationship("ComplianceAnalysis", back_populates="compliance_gaps")
    assigned_user = relationship("User")
    
    __table_args__ = (
        Index("ix_gaps_analysis_severity", "analysis_id", "severity"),
        Index("ix_gaps_status", "status"),
    )

# System Management
class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    
    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    category = Column(String(50), index=True)
    is_sensitive = Column(Boolean, default=False)
    created_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_modified = Column(DateTime(timezone=True), default=datetime.utcnow)
    modified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    modifier = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), index=True)
    
    # Request details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))
    
    # Audit data
    old_values = Column(JSON)
    new_values = Column(JSON)
    details = Column(JSON, default=dict)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("ix_audit_user_action", "user_id", "action"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )

class BackgroundTask(Base):
    __tablename__ = "background_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)
    
    # Status and progress
    status = Column(String(20), default="pending", index=True)
    progress_percent = Column(Float, default=0.0)
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Task data
    input_data = Column(JSON)
    result_data = Column(JSON)
    error_message = Column(Text)
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    user = relationship("User")
    
    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_type_status", "task_type", "status"),
    )

# Performance and Monitoring
class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    
    # Categorization
    category = Column(String(50), index=True)  # performance, usage, error
    component = Column(String(50), index=True)  # api, database, cache
    
    # Context
    tags = Column(JSON, default=dict)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_metrics_name_timestamp", "metric_name", "timestamp"),
        Index("ix_metrics_category_component", "category", "component"),
    )
