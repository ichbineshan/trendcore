from typing import Optional
from uuid import UUID

from fastapi import Query, BackgroundTasks

from file_upload.constants import SignMethod, determine_file_type_from_filename
from file_upload.schemas import SignedUrlRequest, FileUpdateRequest, FileResponse, FileListResponse
from file_upload.service import FileService
from styles.types import MCPResponse


async def get_signed_url(request: SignedUrlRequest):
    """
    Generate a signed URL for a file.
    
    Args:
        request: SignedUrlRequest containing filename, sub_folder, and expiration_hours
    
    Returns:
        MCPResponse with signed URL and CDN URL
    """
    try:
        file_service = FileService()
        
        file_type = request.file_type
        if not file_type:
            file_type = determine_file_type_from_filename(request.filename)

        result = await file_service.generate_signed_urls(
            sub_folder=request.sub_folder,
            sign_method=SignMethod.PUT,
            filenames=[request.filename],
            file_type=file_type,
            file_disposition=None
        )

        file_data = result.get(request.filename, {}).get("details", {})
        signed_url = file_data.get("signed_upload_url")
        cdn_url = file_data.get("cdn_url")
        
        if not signed_url:
            return MCPResponse(
                success=False,
                message="Failed to generate signed URL",
                data=None,
                error="Could not generate signed URL for the specified file"
            ).model_dump()
        
        return MCPResponse(
            success=True,
            message="Signed URL generated successfully",
            data={
                "filename": request.filename,
                "signed_url": signed_url,
                "cdn_url": cdn_url,
                "file_type": file_type,  # Include the determined file type in response
                "file_id": file_data.get("file_id")
            },
            error=None
        ).model_dump()
        
    except Exception as e:
        return MCPResponse(
            success=False,
            message="Error generating signed URL",
            data=None,
            error=str(e)
        ).model_dump()


async def get_files(
    file_type: Optional[str] = Query(None, description="Filter by file type (e.g., 'wgsn', 'image', 'document')"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of files to return"),
    offset: int = Query(default=0, ge=0, description="Number of files to skip for pagination")
):
    """
    Get all uploaded files with optional file type filtering and pagination.
    
    Args:
        file_type: Optional filter for file type
        limit: Maximum number of files to return (default: 10, max: 100)
        offset: Number of files to skip (default: 0)
    
    Returns:
        MCPResponse with list of files and pagination info
    """
    try:
        files, total_count = await FileService.get_all_files_with_pagination(
            file_type=file_type,
            limit=limit,
            offset=offset
        )
        
        files_data = [FileResponse.model_validate(file).model_dump() for file in files]
        
        return MCPResponse(
            success=True,
            message=f"Retrieved {len(files_data)} file(s)",
            data=FileListResponse(
                files=files_data,
                count=len(files_data),
                total_count=total_count,
                limit=limit,
                offset=offset
            ).model_dump(),
            error=None
        ).model_dump()
        
    except Exception as e:
        return MCPResponse(
            success=False,
            message="Error retrieving files",
            data=None,
            error=str(e)
        ).model_dump()


async def get_file_by_id(file_id: UUID):
    """
    Get a single file by its ID.
    
    Args:
        file_id: UUID of the file to retrieve
    
    Returns:
        MCPResponse with file data
    """
    try:
        file_record = await FileService.get_file_by_id(file_id)
        
        if not file_record:
            return MCPResponse(
                success=False,
                message="File not found",
                data=None,
                error=f"No file found with ID: {str(file_id)}"
            ).model_dump()
        
        return MCPResponse(
            success=True,
            message="File retrieved successfully",
            data=FileResponse.model_validate(file_record).model_dump(),
            error=None
        ).model_dump()
        
    except ValueError as e:
        return MCPResponse(
            success=False,
            message="Invalid file ID format",
            data=None,
            error=f"Invalid UUID format: {str(e)}"
        ).model_dump()
    except Exception as e:
        return MCPResponse(
            success=False,
            message="Error retrieving file",
            data=None,
            error=str(e)
        ).model_dump()


async def update_file(file_id: UUID, request: FileUpdateRequest):
    """
    Update a file record.
    
    Args:
        file_id: UUID of the file to update
        request: FileUpdateRequest containing updated fields
    
    Returns:
        MCPResponse with updated file data
    """
    try:
        file_record = await FileService.update_file_record(
            file_id=file_id,
            filename=request.filename,
            cdn_url=request.cdn_url,
            file_type=request.file_type,
            sub_folder=request.sub_folder,
            meta_data=request.meta_data,
        )
        
        if not file_record:
            return MCPResponse(
                success=False,
                message="File not found",
                data=None,
                error=f"No file found with ID: {str(file_id)}"
            ).model_dump()
        
        return MCPResponse(
            success=True,
            message="File record updated successfully",
            data=FileResponse.model_validate(file_record).model_dump(),
            error=None
        ).model_dump()
        
    except ValueError as e:
        return MCPResponse(
            success=False,
            message="Invalid file ID format",
            data=None,
            error=f"Invalid UUID format: {str(e)}"
        ).model_dump()
    except Exception as e:
        return MCPResponse(
            success=False,
            message="Error updating file record",
            data=None,
            error=str(e)
        ).model_dump()


async def delete_file(file_id: UUID, background_tasks: BackgroundTasks):
    """
    Delete a file record from the database and the associated file from cloud storage.
    Also removes the file from Elasticsearch if indexed.
    
    Args:
        file_id: UUID of the file to delete
        background_tasks: FastAPI BackgroundTasks for async operations
    
    Returns:
        MCPResponse indicating success or failure
    """
    try:
        file_service = FileService()
        
        deleted_record = await file_service.delete_file_record(file_id)
        
        if not deleted_record:
            return MCPResponse(
                success=False,
                message="File not found",
                data=None,
                error=f"No file found with ID: {str(file_id)}"
            ).model_dump()

        if deleted_record and deleted_record.cdn_url:
            background_tasks.add_task(
                FileService.delete_file_from_elastic_background,
                deleted_record.cdn_url
            )
        
        return MCPResponse(
            success=True,
            message="File record and cloud file deleted successfully",
            data={"file_id": str(file_id)},
            error=None
        ).model_dump()
        
    except ValueError as e:
        return MCPResponse(
            success=False,
            message="Invalid file ID format",
            data=None,
            error=f"Invalid UUID format: {str(e)}"
        ).model_dump()
    except Exception as e:
        return MCPResponse(
            success=False,
            message="Error deleting file record",
            data=None,
            error=str(e)
        ).model_dump()


async def get_pdf_processing_progress(file_id: UUID):
    """
    Get real-time processing progress for a PDF file.
    
    Args:
        file_id: UUID of the file being processed
    
    Returns:
        MCPResponse with progress information including:
        - status: Current processing stage
        - progress_percentage: Completion percentage
        - pages_indexed: Number of pages successfully indexed
        - pages_failed: Number of pages that failed
        - pages_remaining: Number of pages yet to process
        - total_pages: Total number of pages in the PDF
    """
    try:
        from file_upload.temporal.progress_query import get_pdf_processing_progress as query_progress
        
        progress = await query_progress(str(file_id))
        
        if progress.get("status") == "unknown":
            return MCPResponse(
                success=False,
                message="Workflow not found or not started",
                data=None,
                error=progress.get("error", "Workflow does not exist or has already completed")
            ).model_dump()
        
        return MCPResponse(
            success=True,
            message="Progress retrieved successfully",
            data={
                "file_id": str(file_id),
                "processing_status": progress["status"],
                "progress": {
                    "percentage": progress["progress_percentage"],
                    "pages_indexed": progress["pages_indexed"],
                    "pages_failed": progress["pages_failed"],
                    "pages_remaining": progress["pages_remaining"],
                    "total_pages": progress["total_pages"]
                }
            },
            error=None
        ).model_dump()
        

    except Exception as e:
        return MCPResponse(
            success=False,
            message="Error retrieving processing progress",
            data=None,
            error=str(e)
        ).model_dump()


async def start_pdf_indexing(file_id: UUID):
    """
    Manually trigger PDF indexing for a specific file.
    
    Args:
        file_id: UUID of the file to index
    
    Returns:
        MCPResponse with workflow details
    """
    try:
        file_service = FileService()
        result = await file_service.trigger_pdf_indexing(file_id)
        
        return MCPResponse(
            success=True,
            message=result["message"],
            data=result,
            error=None
        ).model_dump()
        
    except Exception as e:
        return MCPResponse(
            success=False,
            message="Error starting PDF indexing",
            data=None,
            error=str(e)
        ).model_dump()






