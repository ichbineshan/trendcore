"""Worker initialization for file upload temporal workflows."""

from file_upload.temporal.workers.pdf_worker import pdf_processing_worker


__all__ = [
    "pdf_processing_worker"
]