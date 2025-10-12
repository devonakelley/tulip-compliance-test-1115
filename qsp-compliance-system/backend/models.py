"""
Pydantic models for Enterprise QSP Compliance System
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid

class DocumentType(str, Enum):
    """Supported document types"""
    QSP = "qsp"
    REGULATORY = "regulatory"
    ISO_SUMMARY = "iso_summary"
    WORK_INSTRUCTION = "work_instruction"
    QUALITY_MANUAL = "quality_manual"
    PROCEDURE = "procedure"

class AnalysisType(str, Enum):
    """Types of compliance analysis"""
    FULL_COMPLIANCE = "full_compliance"
    GAP_ANALYSIS = "gap_analysis"
    CHANGE_IMPACT = "change_impact"
    CLAUSE_MAPPING = "clause_mapping"
    RISK_ASSESSMENT = "risk_assessment"

class AnalysisStatus(str, Enum):
    """Analysis processing status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ComplianceLevel(str, Enum):
    """Compliance assessment levels"""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    NOT_APPLICABLE = "not_applicable"

class SeverityLevel(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

# Request/Response Models
class UploadRequest(BaseModel):
    """Document upload request"""
    filename: str
    document_type: DocumentType
    file_data: bytes = Field(..., description="Base64 encoded file content")
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        return v.strip()

class UploadResponse(BaseModel):
    """Document upload response"""
    document_id: str
    filename: str
    document_type: DocumentType
    status: str = "uploaded"
    message: str
    processing_started: bool = False
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)

class DocumentMetadata(BaseModel):
    """Document metadata"""
    document_id: str
    filename: str
    document_type: DocumentType
    file_size: int
    upload_date: datetime
    processed_date: Optional[datetime] = None
    user_id: str
    status: str
    sections_count: Optional[int] = None
    clause_mappings_count: Optional[int] = None
    compliance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    last_analysis_date: Optional[datetime] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class DocumentSection(BaseModel):
    """Parsed document section"""
    section_id: str
    document_id: str
    section_number: Optional[str] = None
    title: str
    content: str
    level: int = 1
    parent_section_id: Optional[str] = None
    subsections: List[str] = []
    word_count: int
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class ClauseMapping(BaseModel):
    """QSP section to regulatory clause mapping"""
    mapping_id: str
    document_id: str
    section_id: str
    regulatory_framework: str
    clause_id: str
    clause_title: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    evidence_text: str
    mapping_rationale: Optional[str] = None
    created_by: str  # AI model or user
    created_date: datetime = Field(default_factory=datetime.utcnow)
    validated: bool = False
    validation_notes: Optional[str] = None

class ComplianceGap(BaseModel):
    """Identified compliance gap"""
    gap_id: str
    analysis_id: str
    regulatory_framework: str
    clause_id: str
    clause_title: str
    gap_type: str  # missing, partial, outdated, conflicting
    severity: SeverityLevel
    description: str
    affected_documents: List[str] = []
    recommendations: List[str] = []
    estimated_effort: Optional[str] = None  # low, medium, high
    compliance_impact: Optional[str] = None
    detected_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "open"  # open, in_progress, resolved, accepted_risk

class AnalysisRequest(BaseModel):
    """Compliance analysis request"""
    document_ids: List[str] = Field(..., min_items=1)
    regulatory_framework: str = "ISO_13485:2024"
    analysis_type: AnalysisType = AnalysisType.FULL_COMPLIANCE
    include_gap_analysis: bool = True
    include_risk_assessment: bool = False
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    ai_model_preference: Optional[str] = None
    custom_parameters: Dict[str, Any] = {}
    
    @validator('document_ids')
    def validate_document_ids(cls, v):
        if not v:
            raise ValueError('At least one document ID is required')
        return list(set(v))  # Remove duplicates

class ComplianceReport(BaseModel):
    """Comprehensive compliance analysis report"""
    analysis_id: str
    request_id: str
    user_id: str
    status: AnalysisStatus
    regulatory_framework: str
    analysis_type: AnalysisType
    
    # Documents analyzed
    documents_analyzed: List[DocumentMetadata] = []
    total_documents: int = 0
    
    # Analysis results
    overall_compliance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    compliance_level: Optional[ComplianceLevel] = None
    
    # Detailed findings
    clause_mappings: List[ClauseMapping] = []
    compliance_gaps: List[ComplianceGap] = []
    
    # Statistics
    total_sections_analyzed: int = 0
    total_clauses_mapped: int = 0
    gaps_by_severity: Dict[str, int] = {}
    coverage_by_framework: Dict[str, float] = {}
    
    # Timestamps
    started_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    
    # Metadata
    ai_model_used: Optional[str] = None
    analysis_parameters: Dict[str, Any] = {}
    quality_metrics: Dict[str, Any] = {}
    
    # Recommendations
    priority_actions: List[str] = []
    next_review_date: Optional[datetime] = None
    
    @validator('overall_compliance_score')
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Compliance score must be between 0 and 100')
        return v

class RegulatoryChange(BaseModel):
    """Regulatory framework change"""
    change_id: str
    regulatory_framework: str
    clause_id: str
    change_type: str  # added, modified, deprecated, removed
    change_description: str
    effective_date: datetime
    impact_level: SeverityLevel
    affected_sections: List[str] = []
    implementation_guidance: Optional[str] = None
    source_document: str
    processed_date: datetime = Field(default_factory=datetime.utcnow)
    
# System Models
class SystemHealth(BaseModel):
    """Individual system component health"""
    component: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = {}

class SystemStatus(BaseModel):
    """Overall system status"""
    status: str  # healthy, degraded, unhealthy
    version: str
    uptime_seconds: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Component health
    components: List[SystemHealth] = []
    
    # System metrics
    total_documents: int = 0
    active_analyses: int = 0
    completed_analyses_today: int = 0
    average_analysis_time_minutes: Optional[float] = None
    
    # Resource usage
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    
    # Database metrics
    database_connections: Optional[int] = None
    database_response_time_ms: Optional[float] = None
    
    # Cache metrics
    cache_hit_rate: Optional[float] = None
    cache_size_mb: Optional[float] = None

class UserProfile(BaseModel):
    """User profile model"""
    user_id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"  # user, admin, analyst
    permissions: List[str] = []
    created_date: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    preferences: Dict[str, Any] = {}
    
class AuthToken(BaseModel):
    """Authentication token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    refresh_token: Optional[str] = None
    user_profile: UserProfile

# API Response Models
class ApiResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

class PaginatedResponse(BaseModel):
    """Paginated API response"""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 50
    has_next: bool = False
    has_previous: bool = False

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

# Task and Background Job Models
class TaskStatus(BaseModel):
    """Background task status"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    started_at: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

# Configuration Models
class AnalysisConfig(BaseModel):
    """Analysis configuration parameters"""
    ai_model: str = "gpt-4o"
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: int = 4000
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    include_evidence: bool = True
    parallel_processing: bool = True
    cache_results: bool = True
    
class NotificationSettings(BaseModel):
    """User notification preferences"""
    email_enabled: bool = True
    analysis_complete: bool = True
    high_severity_gaps: bool = True
    system_alerts: bool = False
    weekly_summary: bool = False
    
# Audit and Compliance Models
class AuditLog(BaseModel):
    """System audit log entry"""
    log_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = {}
    
class ComplianceHistory(BaseModel):
    """Historical compliance tracking"""
    history_id: str
    document_id: str
    regulatory_framework: str
    compliance_score: float
    assessment_date: datetime
    gaps_count: int
    critical_gaps: int
    notes: Optional[str] = None
    assessor: str  # user_id or 'system'
