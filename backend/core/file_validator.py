"""
File validation utilities for secure file uploads
Validates file types using magic bytes (file signatures)
"""
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Magic bytes for supported file types
MAGIC_BYTES = {
    'pdf': {
        'signature': b'%PDF',
        'offset': 0,
        'mime': 'application/pdf',
        'extensions': ['.pdf']
    },
    'docx': {
        'signature': b'PK\x03\x04',  # ZIP archive (DOCX is a ZIP)
        'offset': 0,
        'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'extensions': ['.docx']
    },
    'xlsx': {
        'signature': b'PK\x03\x04',  # ZIP archive (XLSX is a ZIP)
        'offset': 0,
        'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'extensions': ['.xlsx']
    },
    'doc': {
        'signature': b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',  # OLE Compound Document
        'offset': 0,
        'mime': 'application/msword',
        'extensions': ['.doc']
    },
    'txt': {
        'signature': None,  # Text files don't have magic bytes
        'offset': 0,
        'mime': 'text/plain',
        'extensions': ['.txt']
    }
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    'pdf': 50 * 1024 * 1024,      # 50 MB
    'docx': 25 * 1024 * 1024,     # 25 MB
    'xlsx': 25 * 1024 * 1024,     # 25 MB
    'doc': 25 * 1024 * 1024,      # 25 MB
    'txt': 5 * 1024 * 1024,       # 5 MB
    'default': 10 * 1024 * 1024   # 10 MB default
}


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension from filename"""
    if '.' not in filename:
        return ''
    return '.' + filename.rsplit('.', 1)[-1].lower()


def detect_file_type(content: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
    """
    Detect file type using magic bytes and validate against extension

    Args:
        content: File content as bytes
        filename: Original filename

    Returns:
        Tuple of (is_valid, detected_type, error_message)
    """
    if not content:
        return False, '', 'Empty file content'

    extension = get_file_extension(filename)

    # Check each file type's magic bytes
    for file_type, config in MAGIC_BYTES.items():
        signature = config['signature']
        offset = config['offset']
        extensions = config['extensions']

        # Skip if extension doesn't match this type
        if extension not in extensions:
            continue

        # Text files don't have magic bytes - validate by checking if content is text
        if signature is None:
            try:
                # Try to decode as UTF-8
                content[:1000].decode('utf-8')
                return True, file_type, None
            except UnicodeDecodeError:
                return False, '', f'File appears to be binary, not text'

        # Check magic bytes
        if len(content) >= offset + len(signature):
            if content[offset:offset + len(signature)] == signature:
                return True, file_type, None

    # For DOCX/XLSX files, verify it's actually a valid Office document
    if extension in ['.docx', '.xlsx']:
        if content[:4] == b'PK\x03\x04':
            # It's a ZIP file, which is correct for Office docs
            # Additional check: look for Office-specific content
            if b'[Content_Types].xml' in content[:5000] or b'word/' in content[:5000] or b'xl/' in content[:5000]:
                return True, extension[1:], None
            else:
                return False, '', f'File has ZIP signature but does not appear to be a valid Office document'
        else:
            return False, '', f'File does not have valid Office document signature'

    # For PDF files
    if extension == '.pdf':
        if content[:4] == b'%PDF':
            return True, 'pdf', None
        else:
            return False, '', f'File does not have valid PDF signature'

    return False, '', f'Unsupported file type: {extension}'


def validate_file_upload(content: bytes, filename: str, allowed_types: list = None) -> Tuple[bool, str]:
    """
    Validate a file upload for security

    Args:
        content: File content as bytes
        filename: Original filename
        allowed_types: List of allowed file extensions (e.g., ['.pdf', '.docx'])

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, 'Filename is required'

    if not content:
        return False, 'File content is empty'

    extension = get_file_extension(filename)

    # Check allowed types
    if allowed_types and extension not in allowed_types:
        return False, f'File type {extension} not allowed. Allowed types: {", ".join(allowed_types)}'

    # Check file size
    file_type = extension[1:] if extension else 'default'
    max_size = MAX_FILE_SIZES.get(file_type, MAX_FILE_SIZES['default'])

    if len(content) > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = len(content) / (1024 * 1024)
        return False, f'File too large: {actual_mb:.1f}MB exceeds maximum {max_mb:.1f}MB'

    # Validate magic bytes
    is_valid, detected_type, error = detect_file_type(content, filename)

    if not is_valid:
        logger.warning(f"File validation failed for {filename}: {error}")
        return False, error or 'Invalid file type'

    logger.debug(f"File validated: {filename} ({detected_type})")
    return True, ''


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re

    # Remove directory components
    filename = filename.replace('\\', '/').split('/')[-1]

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = 255 - len(ext) - 1
        filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]

    return filename
