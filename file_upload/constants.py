import os
from enum import Enum

SIGNED_URL_DEFAULT_EXPIRATION_TIME = 60 * 60 * 24 * 7  # 1 week
SIGNED_URL_REDIS_EXPIRATION_TIME = 60 * 60 * 24 * 6  # 6 days


class SignMethod(str, Enum):
    GET = "get"
    PUT = "put"


sign_method_signed_url_expiry_mapping = {
    SignMethod.GET: SIGNED_URL_DEFAULT_EXPIRATION_TIME,
    SignMethod.PUT: 60 * 60  # 1 hour
}


# File type mapping based on file extensions
FILE_TYPE_MAPPING = {
    # Images
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
    "gif": "image",
    "bmp": "image",
    "svg": "image",
    "webp": "image",
    "ico": "image",
    
    # Documents
    "pdf": "document",
    "doc": "document",
    "docx": "document",
    "txt": "document",
    "rtf": "document",
    "odt": "document",
    
    # Spreadsheets
    "xls": "spreadsheet",
    "xlsx": "spreadsheet",
    "csv": "spreadsheet",
    "ods": "spreadsheet",
    
    # Presentations
    "ppt": "presentation",
    "pptx": "presentation",
    "odp": "presentation",
    
    # Videos
    "mp4": "video",
    "avi": "video",
    "mov": "video",
    "wmv": "video",
    "flv": "video",
    "mkv": "video",
    "webm": "video",
    
    # Audio
    "mp3": "audio",
    "wav": "audio",
    "ogg": "audio",
    "flac": "audio",
    "aac": "audio",
    "m4a": "audio",
    
    # Archives
    "zip": "archive",
    "rar": "archive",
    "7z": "archive",
    "tar": "archive",
    "gz": "archive",
    
    # Code
    "py": "code",
    "js": "code",
    "java": "code",
    "cpp": "code",
    "c": "code",
    "html": "code",
    "css": "code",
    "json": "code",
    "xml": "code",
    "yaml": "code",
    "yml": "code",
}


def determine_file_type_from_filename(filename: str) -> str:
    """
    Determine the file type from the filename extension.
    
    Args:
        filename: The name of the file
        
    Returns:
        The file type string (e.g., 'image', 'document', 'wgsn', etc.)
        Returns 'other' if the extension is not recognized
    """
    # Extract the file extension
    _, ext = os.path.splitext(filename)
    ext = ext.lower().lstrip(".")
    
    # Return the mapped file type or 'other' if not found
    return FILE_TYPE_MAPPING.get(ext, "other")
