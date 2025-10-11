"""
File handling utilities for Enterprise QSP System
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List
import magic
import logging

logger = logging.getLogger(__name__)

class FileUtils:
    """File operations and utilities"""
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)
    
    def get_file_type(self, file_path: str) -> str:
        """Get file MIME type"""
        try:
            return self.mime.from_file(file_path)
        except Exception:
            # Fallback to mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or 'application/octet-stream'
    
    def get_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash"""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        path = Path(file_path)
        stat = path.stat()
        
        return {
            'size': stat.st_size,
            'mime_type': self.get_file_type(file_path),
            'extension': path.suffix.lower(),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'hash': self.get_file_hash(file_path)
        }
    
    def ensure_directory(self, directory: str) -> Path:
        """Ensure directory exists"""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def safe_filename(self, filename: str) -> str:
        """Generate safe filename"""
        import re
        # Remove unsafe characters
        safe = re.sub(r'[^\w\-_\.]', '_', filename)
        # Remove multiple underscores
        safe = re.sub(r'_+', '_', safe)
        # Ensure it's not empty
        if not safe or safe == '.':
            safe = 'unnamed_file'
        return safe[:255]  # Limit length
    
    def copy_file(self, src: str, dst: str) -> bool:
        """Safely copy file"""
        try:
            # Ensure destination directory exists
            self.ensure_directory(Path(dst).parent)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"Failed to copy file {src} to {dst}: {e}")
            return False
    
    def move_file(self, src: str, dst: str) -> bool:
        """Safely move file"""
        try:
            # Ensure destination directory exists
            self.ensure_directory(Path(dst).parent)
            shutil.move(src, dst)
            return True
        except Exception as e:
            logger.error(f"Failed to move file {src} to {dst}: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """Safely delete file"""
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def cleanup_directory(self, directory: str, older_than_days: int = 30) -> int:
        """Clean up old files in directory"""
        import time
        
        cleaned = 0
        cutoff = time.time() - (older_than_days * 24 * 3600)
        
        try:
            for file_path in Path(directory).rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                    if self.delete_file(str(file_path)):
                        cleaned += 1
        except Exception as e:
            logger.error(f"Error cleaning directory {directory}: {e}")
        
        return cleaned
    
    def validate_file_size(self, file_path: str, max_size_mb: int) -> bool:
        """Validate file size"""
        try:
            size = Path(file_path).stat().st_size
            max_size_bytes = max_size_mb * 1024 * 1024
            return size <= max_size_bytes
        except Exception:
            return False
    
    def validate_file_type(self, file_path: str, allowed_types: List[str]) -> bool:
        """Validate file type against allowed list"""
        try:
            extension = Path(file_path).suffix.lower()
            mime_type = self.get_file_type(file_path)
            
            return (
                extension in allowed_types or 
                mime_type in allowed_types
            )
        except Exception:
            return False