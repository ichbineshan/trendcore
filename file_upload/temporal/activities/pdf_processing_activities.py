"""Activities for PDF processing workflows."""
from typing import Dict, Any

from temporalio import activity

from config.logging import logger
from config.settings import loaded_config
from file_upload.temporal.services import PDFExtractionService
from file_upload.temporal.services.index_config import (
    get_pdf_index_mappings,
    get_pdf_index_settings
)
from utils.vector_db.elastic_adapter import ElasticSearchAdapter
from utils.vector_db.embeddings import EmbeddingGenerator


@activity.defn
async def extract_pdf_chunks_activity(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Activity to download PDF and extract text from each page as chunks.
    
    Args:
        file_data: Dictionary containing:
            - file_id: UUID of the file
            - filename: Original filename
            - cdn_url: CDN URL of the file
            - blob_path: GCS blob path
            - file_type: File type
            - sub_folder: Subfolder path (optional)
            - metadata: Additional metadata (optional)
    
    Returns:
        Dictionary with extracted chunks and metadata
    """
    try:
        logger.info(f"Extracting PDF chunks for {file_data.get('filename')}")
        
        service = PDFExtractionService(elastic_adapter=None)

        pdf_bytes = await service.download_pdf(file_data["blob_path"])

        extracted_data = PDFExtractionService.extract_text_from_pdf(pdf_bytes)

        chunks = []
        for page_data in extracted_data.get("pages", []):
            page_text = page_data.get("text", "")

            if not page_text.strip():
                continue
            
            chunks.append({
                "file_id": file_data["file_id"],
                "filename": file_data["filename"],
                "cdn_url": file_data["cdn_url"],
                "file_type": file_data.get("file_type", "document"),
                "sub_folder": file_data.get("sub_folder"),
                "page_number": page_data["page_number"],
                "page_text": page_text,
                "char_count": page_data["char_count"],
                "total_pages": extracted_data.get("page_count", 0),
                "pdf_metadata": extracted_data.get("metadata", {}),
                "custom_metadata": file_data.get("metadata", {})
            })
        
        logger.info(
            f"Extracted {len(chunks)} chunks from {file_data.get('filename')} "
            f"({extracted_data.get('page_count', 0)} total pages)"
        )
        
        return {
            "status": "success",
            "file_id": file_data["file_id"],
            "filename": file_data["filename"],
            "chunks": chunks,
            "total_pages": extracted_data.get("page_count", 0),
            "total_chars": extracted_data.get("total_chars", 0)
        }
        
    except Exception as e:
        logger.error(
            f"PDF extraction activity failed for {file_data.get('filename')}: {e}",
            exc_info=True
        )
        return {
            "status": "error",
            "file_id": file_data.get("file_id"),
            "filename": file_data.get("filename"),
            "error": str(e),
            "chunks": []
        }


@activity.defn
async def index_pdf_chunk_activity(chunk_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Activity to generate embedding and index a single PDF page chunk to Elasticsearch.
    This activity is designed to be called concurrently by the workflow.
    
    Args:
        chunk_data: Dictionary containing chunk information
    
    Returns:
        Indexing result for this chunk
    """
    elastic_adapter = None
    try:
        file_id = chunk_data["file_id"]
        filename = chunk_data["filename"]
        page_number = chunk_data["page_number"]
        page_text = chunk_data["page_text"]

        elastic_adapter = ElasticSearchAdapter()
        await elastic_adapter.connect()
        
        # Ensure index exists before indexing with proper mappings
        mappings = get_pdf_index_mappings()
        settings = get_pdf_index_settings()
        await elastic_adapter.ensure_index_exists(
            index_name=PDFExtractionService.ELASTICSEARCH_INDEX,
            mappings=mappings,
            settings=settings
        )

        embedding_generator = EmbeddingGenerator(api_key=loaded_config.openai_gpt4_key)
        embedding = await embedding_generator.generate_embedding(page_text)
        

        chunk_id = f"{file_id}_page_{page_number}"

        document = {
            "file_id": str(file_id),
            "filename": filename,
            "cdn_url": chunk_data["cdn_url"],
            "file_type": chunk_data["file_type"],
            "sub_folder": chunk_data.get("sub_folder"),
            "page_number": page_number,
            "text_content": page_text,
            "embeddings": embedding,
            "char_count": chunk_data["char_count"],
            "total_pages": chunk_data["total_pages"],
            "pdf_metadata": chunk_data["pdf_metadata"],
            "custom_metadata": chunk_data["custom_metadata"],
            "chunk_type": "page",
            "indexed_at": None
        }

        response = await elastic_adapter.client.index(
            index=PDFExtractionService.ELASTICSEARCH_INDEX,
            id=chunk_id,
            document=document
        )
        
        success = response["result"] in ["created", "updated"]
        
        logger.info(
            f"Indexed page {page_number} of {filename}: {response['result']}"
        )
        
        return {
            "success": success,
            "page_number": page_number,
            "chunk_id": chunk_id,
            "result": response["result"]
        }
        
    except Exception as e:
        logger.error(
            f"Failed to index chunk {chunk_data.get('page_number')} of {chunk_data.get('filename')}: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "page_number": chunk_data.get("page_number"),
            "error": str(e)
        }
    finally:
        if elastic_adapter:
            await elastic_adapter.close()
