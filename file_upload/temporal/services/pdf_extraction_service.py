"""Service for extracting text and metadata from PDF files."""
from typing import Dict, Any, Optional
from uuid import UUID

import fitz

from config.logging import logger
from config.settings import loaded_config
from file_upload.temporal.services.index_config import (
    get_pdf_index_mappings,
    get_pdf_index_settings
)
from utils.vector_db.elastic_adapter import ElasticSearchAdapter
from utils.vector_db.embeddings import EmbeddingGenerator


class PDFExtractionService:
    """Service for extracting and indexing PDF content to Elasticsearch."""
    
    ELASTICSEARCH_INDEX = "designer-wgsn-upload"
    
    def __init__(self, elastic_adapter: ElasticSearchAdapter | None):
        """
        Initialize PDF extraction service.
        
        Args:
            elastic_adapter: Injected ElasticSearchAdapter instance
        """
        self.cloud_storage = loaded_config.cloud_storage_util
        self.elastic_adapter = elastic_adapter
        self.embedding_generator = EmbeddingGenerator(
            api_key=loaded_config.openai_gpt4_key
        )
    
    async def download_pdf(self, blob_path: str) -> bytes:
        """
        Download PDF from Google Cloud Storage.
        
        Args:
            blob_path: Full blob path in GCS
            
        Returns:
            PDF file bytes
        """
        try:
            pdf_bytes = await self.cloud_storage.download_file(blob_path)
            logger.info(f"Downloaded PDF from {blob_path}, size: {len(pdf_bytes)} bytes")
            return pdf_bytes
        except Exception as e:
            logger.error(f"Failed to download PDF from {blob_path}: {e}", exc_info=True)
            raise

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text content and metadata from PDF bytes using PyMuPDF.
        
        Args:
            pdf_bytes: Raw PDF file bytes
            
        Returns:
            Dictionary containing extracted text, page count, and metadata
        """
        if fitz is None:
            logger.warning("PyMuPDF not installed, returning empty extraction")
            return {
                "text": "",
                "page_count": 0,
                "metadata": {},
                "pages": []
            }
        
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            metadata = pdf_document.metadata
            cleaned_metadata = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
            }

            pages = []
            full_text = []
            
            for page_num in range(len(pdf_document)):
                try:
                    page = pdf_document[page_num]
                    page_text = page.get_text()
                    
                    pages.append({
                        "page_number": page_num + 1,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                    full_text.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    pages.append({
                        "page_number": page_num + 1,
                        "text": "",
                        "char_count": 0,
                        "error": str(e)
                    })
            
            pdf_document.close()
            
            combined_text = "\n\n".join(full_text)
            
            result = {
                "text": combined_text,
                "page_count": len(pages),
                "metadata": cleaned_metadata,
                "pages": pages,
                "total_chars": len(combined_text)
            }
            
            logger.info(
                f"Extracted {len(combined_text)} characters from {len(pages)} pages"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}", exc_info=True)
            raise
    
    async def index_pages_to_elasticsearch(
        self,
        file_id: UUID,
        filename: str,
        cdn_url: str,
        extracted_data: Dict[str, Any],
        file_type: str,
        sub_folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index each PDF page as a separate chunk to Elasticsearch.
        
        Args:
            file_id: UUID of the file record
            filename: Original filename
            cdn_url: CDN URL of the file
            extracted_data: Extracted text and metadata from PDF
            file_type: File type (should be 'document' for PDFs)
            sub_folder: Subfolder path in storage
            metadata: Additional metadata
            
        Returns:
            Dictionary with indexing results
        """
        try:
            pages = extracted_data.get("pages", [])
            pdf_metadata = extracted_data.get("metadata", {})
            
            if not pages:
                logger.warning(f"No pages found in PDF {filename}")
                return {
                    "success": False,
                    "pages_indexed": 0,
                    "pages_failed": 0,
                    "total_pages": 0
                }
            
            indexed_count = 0
            failed_count = 0

            mappings = get_pdf_index_mappings()
            settings = get_pdf_index_settings()
            await self.elastic_adapter.ensure_index_exists(
                index_name=self.ELASTICSEARCH_INDEX,
                mappings=mappings,
                settings=settings
            )

            for page_data in pages:
                page_number = page_data.get("page_number")
                page_text = page_data.get("text", "")

                if not page_text.strip():
                    logger.info(f"Skipping empty page {page_number} of {filename}")
                    continue
                
                try:
                    embedding = await self.embedding_generator.generate_embedding(page_text)

                    chunk_id = f"{file_id}_page_{page_number}"

                    document = {
                        "file_id": str(file_id),
                        "filename": filename,
                        "cdn_url": cdn_url,
                        "file_type": file_type,
                        "sub_folder": sub_folder,
                        "page_number": page_number,
                        "text_content": page_text,
                        "embeddings": embedding,
                        "char_count": page_data.get("char_count", len(page_text)),
                        "total_pages": extracted_data.get("page_count", 0),
                        "pdf_metadata": pdf_metadata,
                        "custom_metadata": metadata or {},
                        "chunk_type": "page",
                        "indexed_at": None
                    }

                    response = await self.elastic_adapter.client.index(
                        index=self.ELASTICSEARCH_INDEX,
                        id=chunk_id,
                        document=document
                    )
                    
                    if response["result"] in ["created", "updated"]:
                        indexed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to index page {page_number} of {filename}: {e}",
                        exc_info=True
                    )
            
            logger.info(
                f"Indexed {indexed_count}/{len(pages)} pages from {filename} "
                f"({failed_count} failed)"
            )
            
            return {
                "success": indexed_count > 0,
                "pages_indexed": indexed_count,
                "pages_failed": failed_count,
                "total_pages": len(pages)
            }
            
        except Exception as e:
            logger.error(
                f"Failed to index pages from {filename} to Elasticsearch: {e}",
                exc_info=True
            )
            return {
                "success": False,
                "pages_indexed": 0,
                "pages_failed": extracted_data.get("page_count", 0),
                "total_pages": extracted_data.get("page_count", 0),
                "error": str(e)
            }
    
    async def process_pdf_file(
        self,
        file_id: UUID,
        filename: str,
        cdn_url: str,
        blob_path: str,
        file_type: str,
        sub_folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline: download, extract, and index.
        
        Args:
            file_id: UUID of the file record
            filename: Original filename
            cdn_url: CDN URL of the file
            blob_path: GCS blob path
            file_type: File type
            sub_folder: Subfolder path
            metadata: Additional metadata
            
        Returns:
            Processing result with status and details
        """
        try:
            # Download PDF
            pdf_bytes = await self.download_pdf(blob_path)

            extracted_data = PDFExtractionService.extract_text_from_pdf(pdf_bytes)

            indexing_result = await self.index_pages_to_elasticsearch(
                file_id=file_id,
                filename=filename,
                cdn_url=cdn_url,
                extracted_data=extracted_data,
                file_type=file_type,
                sub_folder=sub_folder,
                metadata=metadata
            )
            
            return {
                "status": "success" if indexing_result["success"] else "failed",
                "file_id": str(file_id),
                "filename": filename,
                "page_count": extracted_data.get("page_count", 0),
                "total_chars": extracted_data.get("total_chars", 0),
                "pages_indexed": indexing_result["pages_indexed"],
                "pages_failed": indexing_result["pages_failed"],
                "indexed": indexing_result["success"]
            }
            
        except Exception as e:
            logger.error(
                f"Failed to process PDF file {filename}: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "file_id": str(file_id),
                "filename": filename,
                "error": str(e)
            }
