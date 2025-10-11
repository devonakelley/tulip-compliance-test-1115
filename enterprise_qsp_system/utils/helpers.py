"""
General helper utilities for Enterprise QSP System
"""

import uuid
import re
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
import json
import logging

logger = logging.getLogger(__name__)

def generate_id() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())

def validate_uuid(uuid_string: str) -> bool:
    """Validate if string is a valid UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False

def format_datetime(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Format datetime to string"""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime(format_str)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim and ensure not empty
    sanitized = sanitized.strip('._')
    if not sanitized:
        sanitized = 'unnamed'
    
    # Limit length
    name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}.{ext}" if ext else name

def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON with fallback"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(data: Any, default: str = '{}') -> str:
    """Safely serialize to JSON with fallback"""
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return default

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    # Replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text"""
    pattern = r'-?\d+(?:\.\d+)?'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches]

def calculate_hash(data: Any) -> str:
    """Calculate hash for any data"""
    import hashlib
    
    if isinstance(data, str):
        content = data
    elif isinstance(data, (dict, list)):
        content = json.dumps(data, sort_keys=True)
    else:
        content = str(data)
    
    return hashlib.sha256(content.encode()).hexdigest()

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Recursively merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def get_nested_value(data: Dict, key_path: str, default: Any = None, separator: str = '.') -> Any:
    """Get nested dictionary value using dot notation"""
    try:
        keys = key_path.split(separator)
        value = data
        
        for key in keys:
            value = value[key]
        
        return value
    except (KeyError, TypeError):
        return default

def set_nested_value(data: Dict, key_path: str, value: Any, separator: str = '.') -> Dict:
    """Set nested dictionary value using dot notation"""
    keys = key_path.split(separator)
    current = data
    
    # Navigate to the parent of the target key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the value
    current[keys[-1]] = value
    return data

def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first/last characters"""
    if not data or len(data) <= visible_chars * 2:
        return mask_char * len(data) if data else ''
    
    visible_start = data[:visible_chars]
    visible_end = data[-visible_chars:]
    masked_middle = mask_char * (len(data) - visible_chars * 2)
    
    return f"{visible_start}{masked_middle}{visible_end}"

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def retry_operation(operation, max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying operations"""
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed.")
            
            raise last_exception
        
        return wrapper
    return decorator

class Timer:
    """Simple context manager for timing operations"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"{self.description} completed in {duration:.2f}s")
    
    @property
    def duration(self) -> Optional[float]:
        """Get duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None