"""
Database module for Enterprise QSP Compliance System
"""

from .mongodb_manager import MongoDBManager as DatabaseManager, get_db_session
from .models import (
    Base,
    User, UserSession,
    Document, DocumentSection,
    RegulatoryFramework, RegulatoryChange,
    ComplianceAnalysis, ClauseMapping, ComplianceGap,
    SystemConfiguration, AuditLog, BackgroundTask, SystemMetric
)

__all__ = [
    "DatabaseManager",
    "get_db_session", 
    "Base",
    "User", "UserSession",
    "Document", "DocumentSection", 
    "RegulatoryFramework", "RegulatoryChange",
    "ComplianceAnalysis", "ClauseMapping", "ComplianceGap",
    "SystemConfiguration", "AuditLog", "BackgroundTask", "SystemMetric"
]
