"""Temporal client for file upload workflows."""
from datetime import timedelta
from typing import Dict, Any, Optional

from file_upload.temporal.constants import TemporalQueue
from file_upload.temporal.workflow import PDFProcessingWorkflow
from utils.temporal.temporal_client import TemporalClient


class FileUploadTemporalClient(TemporalClient):
    """Temporal client for file upload workflow operations."""
    
    async def start_pdf_processing_workflow(
        self,
        file_id: str,
        filename: str,
        cdn_url: str,
        blob_path: str,
        file_type: str,
        sub_folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None
    ) -> str:
        """
        Start a PDF processing workflow.
        
        Args:
            file_id: UUID of the file record
            filename: Original filename
            cdn_url: CDN URL of the file
            blob_path: GCS blob path
            file_type: File type
            sub_folder: Subfolder path (optional)
            metadata: Additional metadata (optional)
            workflow_id: Custom workflow ID (optional)
        
        Returns:
            Workflow execution ID
        """
        file_data = {
            "file_id": file_id,
            "filename": filename,
            "cdn_url": cdn_url,
            "blob_path": blob_path,
            "file_type": file_type,
            "sub_folder": sub_folder,
            "metadata": metadata or {}
        }
        
        if not workflow_id:
            workflow_id = f"pdf-processing-{file_id}"
        
        return await self.start_workflow(
            workflow_class=PDFProcessingWorkflow,
            workflow_method=PDFProcessingWorkflow.run,
            args=[file_data],
            workflow_id=workflow_id,
            task_queue=TemporalQueue.PDF_PROCESSING.value,
            execution_timeout=timedelta(minutes=30),
            run_timeout=timedelta(minutes=20)
        )
