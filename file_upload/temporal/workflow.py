"""Temporal workflow for PDF file processing."""
import asyncio
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from file_upload.temporal.constants import TemporalQueue

with workflow.unsafe.imports_passed_through():
    from file_upload.temporal.activities import (
        extract_pdf_chunks_activity,
        index_pdf_chunk_activity,
    )


@workflow.defn
class PDFProcessingWorkflow:
    """
    Workflow for processing uploaded PDF files.
    
    This workflow:
    1. Extracts text from each page as chunks
    2. Orchestrates concurrent processing of all chunks (embedding + indexing)
    3. Provides real-time progress tracking via queries
    """
    
    def __init__(self):
        """Initialize workflow state for progress tracking."""
        self.total_pages = 0
        self.pages_indexed = 0
        self.pages_failed = 0
        self.current_status = "initializing"
    
    @workflow.query
    def get_progress(self) -> Dict[str, Any]:
        """
        Query to get current processing progress.
        
        Returns:
            Dictionary with progress information
        """
        if self.total_pages == 0:
            percentage = 0
        else:
            percentage = round((self.pages_indexed + self.pages_failed) / self.total_pages * 100, 2)
        
        return {
            "status": self.current_status,
            "total_pages": self.total_pages,
            "pages_indexed": self.pages_indexed,
            "pages_failed": self.pages_failed,
            "pages_remaining": self.total_pages - (self.pages_indexed + self.pages_failed),
            "progress_percentage": percentage
        }
    
    @workflow.run
    async def run(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the PDF processing workflow.
        
        Args:
            file_data: Dictionary containing file information:
                - file_id: UUID of the file
                - filename: Original filename
                - cdn_url: CDN URL of the file
                - blob_path: GCS blob path
                - file_type: File type
                - sub_folder: Subfolder path (optional)
                - metadata: Additional metadata (optional)
        
        Returns:
            Processing result dictionary
        """
        workflow.logger.info(
            f"Starting PDF processing workflow for {file_data.get('filename')}"
        )
        
        self.current_status = "extracting"
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2,
            maximum_attempts=3,
            maximum_interval=timedelta(minutes=2)
        )

        # Step 1: Extract PDF into chunks
        extraction_result = await workflow.execute_activity(
            activity=extract_pdf_chunks_activity,
            arg=file_data,
            task_queue=TemporalQueue.PDF_PROCESSING.value,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        if extraction_result.get("status") != "success":
            self.current_status = "extraction_failed"
            workflow.logger.error(
                f"PDF extraction failed for {file_data.get('filename')}"
            )
            return extraction_result
        
        chunks = extraction_result.get("chunks", [])
        self.total_pages = len(chunks)
        
        if not chunks:
            self.current_status = "completed"
            workflow.logger.warning(
                f"No chunks extracted from {file_data.get('filename')}"
            )
            return {
                "status": "success",
                "file_id": file_data.get("file_id"),
                "filename": file_data.get("filename"),
                "pages_indexed": 0,
                "pages_failed": 0,
                "total_pages": extraction_result.get("total_pages", 0)
            }
        
        self.current_status = "indexing"
        
        workflow.logger.info(
            f"Processing {len(chunks)} chunks concurrently for {file_data.get('filename')}"
        )

        indexing_tasks = [
            workflow.execute_activity(
                activity=index_pdf_chunk_activity,
                arg=chunk,
                task_queue=TemporalQueue.PDF_PROCESSING.value,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy
            )
            for chunk in chunks
        ]

        results = await asyncio.gather(*indexing_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict) and result.get("success"):
                self.pages_indexed += 1
            else:
                self.pages_failed += 1
        
        self.current_status = "completed"
        
        workflow.logger.info(
            f"PDF processing completed for {file_data.get('filename')}: "
            f"{self.pages_indexed}/{len(chunks)} pages indexed ({self.pages_failed} failed)"
        )
        
        return {
            "status": "success" if self.pages_indexed > 0 else "failed",
            "file_id": file_data.get("file_id"),
            "filename": file_data.get("filename"),
            "pages_indexed": self.pages_indexed,
            "pages_failed": self.pages_failed,
            "total_pages": extraction_result.get("total_pages", 0),
            "total_chars": extraction_result.get("total_chars", 0)
        }
