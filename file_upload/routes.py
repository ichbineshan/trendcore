from fastapi import APIRouter

from file_upload.views import (
    get_signed_url,
    get_files,
    get_file_by_id,
    update_file,
    delete_file,
    get_pdf_processing_progress,
    start_pdf_indexing,
)

router = APIRouter(prefix="/file-upload")


router.add_api_route(
    path="/signed-url",
    endpoint=get_signed_url,
    methods=["POST"],
    description="Generate a signed URL for file upload"
)

router.add_api_route(
    path="/files",
    endpoint=get_files,
    methods=["GET"],
    description="Get all uploaded files with optional file_type filtering and pagination"
)

router.add_api_route(
    path="/files/{file_id}",
    endpoint=get_file_by_id,
    methods=["GET"],
    description="Get a single file by its ID"
)

router.add_api_route(
    path="/files/{file_id}",
    endpoint=update_file,
    methods=["PUT"],
    description="Update a file record"
)

router.add_api_route(
    path="/files/{file_id}",
    endpoint=delete_file,
    methods=["DELETE"],
    description="Delete a file record"
)


router.add_api_route(
    path="/files/{file_id}/processing-progress",
    endpoint=get_pdf_processing_progress,
    methods=["GET"],
    description="Get real-time PDF processing progress"
)

router.add_api_route(
    path="/files/{file_id}/index",
    endpoint=start_pdf_indexing,
    methods=["POST"],
    description="Manually trigger PDF indexing for a specific file"
)
