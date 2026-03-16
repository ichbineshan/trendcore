from typing import Dict, Any

from config.settings import loaded_config
from utils.temporal.temporal_client import TemporalClient


async def get_pdf_processing_progress(workflow_id: str) -> Dict[str, Any]:
    """
    Query the progress of a PDF processing workflow.
    
    Args:
        workflow_id: The workflow ID (typically the file_id)
    
    Returns:
        Dictionary with progress information:
        {
            "status": "extracting" | "indexing" | "completed" | "extraction_failed",
            "total_pages": 100,
            "pages_indexed": 45,
            "pages_failed": 2,
            "pages_remaining": 53,
            "progress_percentage": 47.0
        }
    """
    try:
        temporal_client = TemporalClient(
            namespace=loaded_config.temporal_namespace
        )
        
        progress = await temporal_client.query_workflow(
            workflow_id=workflow_id,
            query_name="get_progress"
        )
        
        return progress
        
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
            "total_pages": 0,
            "pages_indexed": 0,
            "pages_failed": 0,
            "pages_remaining": 0,
            "progress_percentage": 0
        }


async def get_multiple_pdf_progress(workflow_ids: list[str]) -> Dict[str, Dict[str, Any]]:
    """
    Query progress for multiple PDF processing workflows.
    
    Args:
        workflow_ids: List of workflow IDs
    
    Returns:
        Dictionary mapping workflow_id to progress info
    """
    import asyncio
    
    results = await asyncio.gather(
        *[get_pdf_processing_progress(wf_id) for wf_id in workflow_ids],
        return_exceptions=True
    )
    
    return {
        wf_id: result if not isinstance(result, Exception) else {"status": "error", "error": str(result)}
        for wf_id, result in zip(workflow_ids, results)
    }
