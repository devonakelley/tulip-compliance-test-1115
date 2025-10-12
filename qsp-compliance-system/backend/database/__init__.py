"""
Database module for Enterprise QSP Compliance System
"""

from mongodb_manager import MongoDBManager as DatabaseManager, get_db_session
# MongoDB collections - no need to import specific models

__all__ = [
    "DatabaseManager",
    "get_db_session"
]
