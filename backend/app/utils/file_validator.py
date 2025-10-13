"""
Enhanced file validation utility for secure file uploads
"""

import logging
import mimetypes
from typing import Tuple, Dict, Any
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Allowed file types and their extensions
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/heic': ['.heic'],
    'image/webp': ['.webp'],
    'image/tiff': ['.tiff', '.tif']
}

# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_FILE_SIZE = 1024  # 1KB

# Security patterns to detect potentially malicious files
SUSPICIOUS_PATTERNS = [
    b'<?php',
    b'<script',
    b'javascript:',
    b'vbscript:',
    b'onload=',
    b'onerror=',
    b'<iframe',
    b'<object',
    b'<embed'
]

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass

def validate_image_file(file_content: bytes, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Enhanced file validation with comprehensive security checks
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        
    Returns:
        Tuple of (is_valid, message, validation_details)
    """
    validation_details = {
        "filename": filename,
        "file_size": len(file_content),
        "checks_performed": []
    }
    
    try:
        # Check 1: File size validation
        validation_details["checks_performed"].append("file_size")
        if len(file_content) > MAX_FILE_SIZE:
            return False, f"File size ({len(file_content)} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)", validation_details
        
        if len(file_content) < MIN_FILE_SIZE:
            return False, f"File size ({len(file_content)} bytes) is too small (minimum {MIN_FILE_SIZE} bytes)", validation_details
        
        # Check 2: Filename validation
        validation_details["checks_performed"].append("filename")
        if not filename or len(filename.strip()) == 0:
            return False, "Filename cannot be empty", validation_details
        
        # Check for suspicious filename patterns
        suspicious_filename_patterns = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        for pattern in suspicious_filename_patterns:
            if pattern in filename:
                return False, f"Filename contains suspicious pattern: {pattern}", validation_details
        
        # Check 3: File extension validation
        validation_details["checks_performed"].append("file_extension")
        file_ext = Path(filename).suffix.lower()
        if not file_ext:
            return False, "File must have an extension", validation_details
        
        # Check if extension is in allowed list
        allowed_extensions = []
        for mime_type, extensions in ALLOWED_IMAGE_TYPES.items():
            allowed_extensions.extend(extensions)
        
        if file_ext not in allowed_extensions:
            return False, f"File extension '{file_ext}' not allowed. Allowed: {', '.join(allowed_extensions)}", validation_details
        
        validation_details["detected_extension"] = file_ext
        
        # Check 4: MIME type detection using mimetypes library
        validation_details["checks_performed"].append("mime_type")
        guessed_mime_type, _ = mimetypes.guess_type(filename)
        validation_details["guessed_mime_type"] = guessed_mime_type
        
        if guessed_mime_type and guessed_mime_type not in ALLOWED_IMAGE_TYPES:
            return False, f"MIME type '{guessed_mime_type}' not allowed", validation_details
        
        # Check 5: File signature validation (magic numbers)
        validation_details["checks_performed"].append("file_signature")
        file_signature = _get_file_signature(file_content)
        validation_details["file_signature"] = file_signature
        
        if not _is_valid_image_signature(file_content):
            return False, "File signature does not match expected image format", validation_details
        
        # Check 6: Content security scan
        validation_details["checks_performed"].append("content_security")
        if _contains_suspicious_content(file_content):
            return False, "File contains potentially malicious content", validation_details
        
        # Check 7: Image header validation
        validation_details["checks_performed"].append("image_header")
        header_validation = _validate_image_header(file_content, file_ext)
        if not header_validation["valid"]:
            return False, f"Invalid image header: {header_validation['reason']}", validation_details
        
        validation_details["image_format"] = header_validation.get("format")
        
        # All checks passed
        validation_details["validation_status"] = "passed"
        return True, "File validation successful", validation_details
        
    except Exception as e:
        logger.error(f"File validation error for {filename}: {e}")
        validation_details["validation_error"] = str(e)
        return False, f"File validation error: {str(e)}", validation_details

def _get_file_signature(file_content: bytes) -> str:
    """Get file signature (first 16 bytes) as hex string"""
    return file_content[:16].hex().upper()

def _is_valid_image_signature(file_content: bytes) -> bool:
    """Check if file has valid image signature (magic numbers)"""
    if len(file_content) < 4:
        return False
    
    # Common image file signatures
    image_signatures = {
        b'\xFF\xD8\xFF': 'JPEG',
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'GIF87a': 'GIF87a',
        b'GIF89a': 'GIF89a',
        b'RIFF': 'WEBP',  # WebP files start with RIFF
        b'II*\x00': 'TIFF_LE',  # TIFF little endian
        b'MM\x00*': 'TIFF_BE',  # TIFF big endian
        b'\x00\x00\x00\x18ftypheic': 'HEIC',  # HEIC (simplified check)
        b'\x00\x00\x00\x20ftypheic': 'HEIC',  # HEIC variant
    }
    
    # Check for JPEG
    if file_content.startswith(b'\xFF\xD8\xFF'):
        return True
    
    # Check for PNG
    if file_content.startswith(b'\x89PNG\r\n\x1a\n'):
        return True
    
    # Check for GIF
    if file_content.startswith(b'GIF87a') or file_content.startswith(b'GIF89a'):
        return True
    
    # Check for WebP (RIFF container with WEBP)
    if file_content.startswith(b'RIFF') and b'WEBP' in file_content[:12]:
        return True
    
    # Check for TIFF
    if file_content.startswith(b'II*\x00') or file_content.startswith(b'MM\x00*'):
        return True
    
    # Check for HEIC (simplified - actual HEIC detection is more complex)
    if b'ftyp' in file_content[:32] and (b'heic' in file_content[:32] or b'mif1' in file_content[:32]):
        return True
    
    return False

def _contains_suspicious_content(file_content: bytes) -> bool:
    """Check for suspicious content patterns that might indicate malicious files"""
    # Convert to lowercase for case-insensitive matching
    content_lower = file_content.lower()
    
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in content_lower:
            logger.warning(f"Suspicious pattern found: {pattern}")
            return True
    
    return False

def _validate_image_header(file_content: bytes, file_ext: str) -> Dict[str, Any]:
    """Validate image header structure"""
    result = {"valid": True, "reason": "", "format": ""}
    
    if len(file_content) < 10:
        result["valid"] = False
        result["reason"] = "File too small to contain valid image header"
        return result
    
    try:
        if file_ext in ['.jpg', '.jpeg']:
            # JPEG validation
            if not file_content.startswith(b'\xFF\xD8\xFF'):
                result["valid"] = False
                result["reason"] = "Invalid JPEG header"
                return result
            result["format"] = "JPEG"
            
        elif file_ext == '.png':
            # PNG validation
            if not file_content.startswith(b'\x89PNG\r\n\x1a\n'):
                result["valid"] = False
                result["reason"] = "Invalid PNG header"
                return result
            result["format"] = "PNG"
            
        elif file_ext == '.webp':
            # WebP validation
            if not (file_content.startswith(b'RIFF') and b'WEBP' in file_content[:12]):
                result["valid"] = False
                result["reason"] = "Invalid WebP header"
                return result
            result["format"] = "WebP"
            
        elif file_ext in ['.tiff', '.tif']:
            # TIFF validation
            if not (file_content.startswith(b'II*\x00') or file_content.startswith(b'MM\x00*')):
                result["valid"] = False
                result["reason"] = "Invalid TIFF header"
                return result
            result["format"] = "TIFF"
            
        elif file_ext == '.heic':
            # HEIC validation (simplified)
            if not (b'ftyp' in file_content[:32] and (b'heic' in file_content[:32] or b'mif1' in file_content[:32])):
                result["valid"] = False
                result["reason"] = "Invalid HEIC header"
                return result
            result["format"] = "HEIC"
            
    except Exception as e:
        result["valid"] = False
        result["reason"] = f"Header validation error: {str(e)}"
    
    return result

def get_file_info(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    return {
        "filename": filename,
        "size_bytes": len(file_content),
        "size_mb": round(len(file_content) / (1024 * 1024), 2),
        "extension": Path(filename).suffix.lower(),
        "signature": _get_file_signature(file_content),
        "mime_type": mimetypes.guess_type(filename)[0],
        "is_valid_image": _is_valid_image_signature(file_content)
    }

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove path components
    filename = Path(filename).name
    
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name_part = Path(filename).stem[:200]
        ext_part = Path(filename).suffix
        filename = f"{name_part}{ext_part}"
    
    return filename

# Export main validation function
__all__ = ['validate_image_file', 'FileValidationError', 'get_file_info', 'sanitize_filename']