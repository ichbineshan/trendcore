from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field


class SignedUrlRequest(BaseModel):
    """
    Schema for requesting a signed URL for a file.
    """
    filename: str = Field(..., description="Name of the file to generate signed URL for")
    file_type: Optional[str] = Field(None, description="Type of file (e.g., 'wgsn', 'image', 'document'). If not provided, will be automatically determined from file extension.")
    sub_folder: str = Field(default="wgsn-reports/wgsn-uploaded", description="Subfolder path where the file is located")


class FileCreateRequest(BaseModel):
    """
    Schema for creating a file record.
    """
    filename: str = Field(..., description="Original filename")
    cdn_url: str = Field(..., description="CDN URL of the uploaded file")
    file_type: str = Field(..., description="Type of file (e.g., 'wgsn', 'image', 'document')")
    sub_folder: Optional[str] = Field(None, description="Storage subfolder path")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FileUpdateRequest(BaseModel):
    """
    Schema for updating a file record.
    """
    filename: Optional[str] = Field(None, description="Updated filename")
    cdn_url: Optional[str] = Field(None, description="Updated CDN URL")
    file_type: Optional[str] = Field(None, description="Updated file type")
    sub_folder: Optional[str] = Field(None, description="Updated subfolder path")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class FileResponse(BaseModel):
    """
    Schema for file record response.
    """
    file_id: UUID = Field(..., description="UUID of the file")
    filename: str = Field(..., description="Original filename")
    cdn_url: str = Field(..., description="CDN URL of the file")
    file_type: str = Field(..., description="Type of file")
    sub_folder: Optional[str] = Field(None, description="Storage subfolder path")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: int = Field(..., description="Creation timestamp (epoch)")
    updated_at: int = Field(..., description="Last update timestamp (epoch)")

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """
    Schema for paginated file list response.
    """
    files: List[FileResponse] = Field(..., description="List of file records")
    count: int = Field(..., description="Number of files in current page")
    total_count: int = Field(..., description="Total number of files matching filters")
    limit: int = Field(..., description="Maximum files per page")
    offset: int = Field(..., description="Number of files skipped")
