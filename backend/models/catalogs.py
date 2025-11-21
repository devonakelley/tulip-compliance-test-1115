"""
Catalog models for Forms and Work Instructions
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class FormCatalogEntry(BaseModel):
    """Form catalog entry"""
    tenant_id: str
    form_id: str  # e.g., "7.3-3-1"
    form_name: str  # e.g., "Risk Analysis Form"
    parent_qsp: Optional[str] = None  # e.g., "7.3-3"
    description: Optional[str] = None
    referenced_in_sections: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WICatalogEntry(BaseModel):
    """Work Instruction catalog entry"""
    tenant_id: str
    wi_id: str  # e.g., "WI-003"
    wi_name: str  # e.g., "Visual Inspection"
    parent_qsp: Optional[str] = None  # e.g., "9.1-3"
    description: Optional[str] = None
    referenced_in_sections: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
