"""
MongoDB models and type definitions for Enterprise QSP Compliance System
This file provides type hints and enums - actual data is stored in MongoDB collections
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Enums for database
class DocumentTypeEnum(str, Enum):
    QSP = "qsp"
    REGULATORY = "regulatory"
    ISO_SUMMARY = "iso_summary"
    WORK_INSTRUCTION = "work_instruction"
    QUALITY_MANUAL = "quality_manual"
    PROCEDURE = "procedure"

class AnalysisStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

# Pydantic models for MongoDB documents (for type hints and validation)
class User(BaseModel):
    """User model for MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)

class UserSession(BaseModel):
    """User session model for MongoDB"""
    session_id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True

class Document(BaseModel):
    """Document model for MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    document_type: str
    content: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    user_id: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    processing_status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class DocumentSection(BaseModel):
    """Document section model for MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    content: str
    order_index: int = 0
    parent_section_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_date: datetime = Field(default_factory=datetime.utcnow)

class ComplianceAnalysis(BaseModel):
    """Compliance analysis model for MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    analysis_type: str
    status: str = "pending"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    compliance_score: Optional[float] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    user_id: str
    
class ComplianceGap(BaseModel):
    """Compliance gap model for MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str
    document_id: str
    section_id: Optional[str] = None
    regulatory_clause: str
    gap_description: str
    severity: str
    required_actions: List[str] = Field(default_factory=list)
    impact_assessment: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.utcnow)
