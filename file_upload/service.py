import os
import time
from typing import Optional
from uuid import UUID

import uuid6
from fastapi import UploadFile

from config.logging import logger
from config.settings import loaded_config
from file_upload.constants import SignMethod, sign_method_signed_url_expiry_mapping
from file_upload.dao import UploadedFileDAO
from file_upload.exceptions import (
    FileListingError,
    CloudStorageError,
    InvalidFilePathError,
    FileUploadServiceError,
)
from file_upload.models import UploadedFile
from file_upload.temporal.services.pdf_extraction_service import PDFExtractionService
from utils.connection_handler import get_connection_handler_for_app
from utils.vector_db.elastic_adapter import ElasticSearchAdapter


class FileService:

    def __init__(self):
        self.cloud_storage_util = loaded_config.cloud_storage_util
        self.base_cdn_path = loaded_config.base_cdn_domain

    async def generate_signed_urls(
        self,
        sub_folder: str,
        sign_method: SignMethod,
        filenames: list[str],
        file_type: str,
        file_disposition: Optional[str] = None,
    ):

        resource_urls = self.get_resource_urls(
            sub_folder=sub_folder, filenames=filenames
        )
        expiration_time = sign_method_signed_url_expiry_mapping.get(sign_method)
        signed_urls = await self.cloud_storage_util.generate_signed_urls(
            resource_urls=resource_urls,
            expiration_time=expiration_time,
            sign_method=sign_method,
            file_disposition=file_disposition,
        )

        cdn_urls = [
            f"{self.base_cdn_path}{resource_url}" for resource_url in resource_urls
        ]



        file_ids = []
        for filename, cdn_url in zip(filenames, cdn_urls):
            file_id = await self._create_file_record(
                filename=filename,
                cdn_url=cdn_url,
                file_type=file_type,
                sub_folder=sub_folder,
            )
            file_ids.append(file_id)

        return {
            filename: {"details": {"signed_upload_url": signed_url, "cdn_url": cdn_url, "file_id": str(file_id)}}
            for filename, signed_url, cdn_url, file_id in zip(
                filenames, signed_urls, cdn_urls, file_ids
            )
        }

    @staticmethod
    async def _create_file_record(
        filename: str,
        cdn_url: str,
        file_type: str,
        sub_folder: Optional[str] = None,
    ):
        """
        Create a new file record in the database.
        For PDF files, also triggers a Temporal workflow for extraction and indexing.
        """
        extension = os.path.splitext(filename)[1].lower().lstrip(".")
        meta_data = {"extension": extension}

        async with get_connection_handler_for_app() as connection_handler:
            dao = UploadedFileDAO(connection_handler.session)
            file_id = uuid6.uuid7()

            is_pdf = extension == "pdf"
            
            if is_pdf:
                try:
                    from file_upload.temporal.temporal_client import FileUploadTemporalClient

                    base_cdn_path = loaded_config.base_cdn_domain
                    blob_path = cdn_url.replace(base_cdn_path, "")
                    
                    temporal_client = FileUploadTemporalClient()
                    workflow_id = await temporal_client.start_pdf_processing_workflow(
                        file_id=str(file_id),
                        filename=filename,
                        cdn_url=cdn_url,
                        blob_path=blob_path,
                        file_type=file_type,
                        sub_folder=sub_folder,
                        metadata={"extension": extension}
                    )
                    
                    meta_data["workflow_id"] = workflow_id
                    meta_data["workflow_status"] = "started"
                    
                    logger.info(f"Started PDF processing workflow {workflow_id} for file {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to start PDF processing workflow for {filename}: {e}", exc_info=True)
                    meta_data["workflow_error"] = str(e)
            
            await dao.create_file_record(
                file_id=file_id,
                cdn_url=cdn_url,
                filename=filename,
                file_type=file_type,
                sub_folder=sub_folder,
                meta_data=meta_data,
            )
            await connection_handler.session.commit()
            
        return file_id

    def get_resource_urls(self, sub_folder: str, filenames: list[str]):
        return [
            self.cloud_storage_util.get_file_path(
                filename=filename, sub_path=sub_folder
            )
            for filename in filenames
        ]

    async def trigger_pdf_indexing(self, file_id: UUID) -> dict:
        """
        Manually trigger PDF indexing workflow for a specific file.
        
        Args:
            file_id: UUID of the file to index
            
        Returns:
            dict containing workflow_id and status
            
        Raises:
            FileUploadServiceError: If file not found, not a PDF, or workflow start fails
        """
        async with get_connection_handler_for_app() as connection_handler:
            dao = UploadedFileDAO(connection_handler.session)
            file_record = await dao.get_file_by_id(file_id)
            
            if not file_record:
                raise FileUploadServiceError(f"File with ID {file_id} not found")
                
            if file_record.file_type != "document" or not file_record.filename.lower().endswith(".pdf"):
                raise FileUploadServiceError("File is not a PDF")

            try:
                from file_upload.temporal.temporal_client import FileUploadTemporalClient

                base_cdn_path = loaded_config.base_cdn_domain
                blob_path = file_record.cdn_url.replace(base_cdn_path, "")
                
                temporal_client = FileUploadTemporalClient()
                workflow_id = await temporal_client.start_pdf_processing_workflow(
                    file_id=str(file_id),
                    filename=file_record.filename,
                    cdn_url=file_record.cdn_url,
                    blob_path=blob_path,
                    file_type=file_record.file_type,
                    sub_folder=file_record.sub_folder,
                    metadata={"extension": "pdf"}
                )

                meta_data = file_record.meta_data or {}
                meta_data["workflow_id"] = workflow_id
                meta_data["workflow_status"] = "started"
                
                await dao.update_file_record(
                    file_id=file_id,
                    meta_data=meta_data
                )
                await connection_handler.session.commit()
                
                logger.info(f"Manually started PDF processing workflow {workflow_id} for file {file_record.filename}")
                
                return {
                    "workflow_id": workflow_id,
                    "status": "started",
                    "message": "PDF indexing workflow started successfully"
                }
                    
            except Exception as e:
                logger.error(f"Failed to start PDF processing workflow for {file_record.filename}: {e}", exc_info=True)
                raise FileUploadServiceError(f"Failed to start workflow: {str(e)}")

    @staticmethod
    def _add_epoch_prefix(filename: str) -> str:
        """
        Add epoch timestamp prefix to filename for sorting purposes.
        Format: "{epoch})_{original_filename}"
        
        Args:
            filename: Original filename
            
        Returns:
            Filename with epoch prefix
        """
        epoch_timestamp = int(time.time())
        return f"{epoch_timestamp})_{filename}"

    async def upload_file_public(
        self,
        file: UploadFile,
        sub_path: str,
        file_type: str,
        file_disposition: Optional[str] = None,
        add_epoch_prefix: bool = True,
    ) -> Optional[str]:
        """
        Uploads `file` to the bucket under `sub_path` and returns a signed URL (GET) for the uploaded file.
        Returns the signed URL if successful, or None if an error occurred.
        
        Args:
            file: File to upload
            sub_path: Subdirectory path in bucket
            file_type: MIME type of the file
            file_disposition: Content disposition header
            add_epoch_prefix: If True, add epoch timestamp prefix to filename (default: True)
        """
        try:
            original_filename = file.filename
            if add_epoch_prefix and original_filename:
                prefixed_filename = FileService._add_epoch_prefix(original_filename)
                file.filename = prefixed_filename
            
            blob_path = await self.cloud_storage_util.upload(
                file,
                sub_path,
                file_type=file_type,
                file_disposition=file_disposition,
            )
            if not blob_path:
                raise CloudStorageError("Failed to upload file to cloud storage")
            upload_file_with_cdn_base = f"{self.base_cdn_path}{blob_path}"
            return upload_file_with_cdn_base
        except Exception as e:
            logger.error(
                "Signed URL upload failed for %s: %s", file.filename, e, exc_info=True
            )
            raise FileUploadServiceError(f"File upload failed: {str(e)}")

    async def list_files(self, folder_name: str):
        """
        Lists all files in the specified folder.

        Args:
            folder_name (str): The name of the folder to list files from.

        Returns:
            list: A list of file information dictionaries containing name, size,
                  last_modified, content_type, and full_path.

        Raises:
            InvalidFilePathError: If the folder name is invalid or empty.
            FileListingError: If the listing operation fails.
            CloudStorageError: If there's an issue with cloud storage access.
        """
        try:
            if not folder_name or not folder_name.strip():
                raise InvalidFilePathError("Folder name cannot be empty")

            files = await self.cloud_storage_util.list_files(folder_path=folder_name.strip())
            return files
        except InvalidFilePathError:
            raise
        except Exception as e:
            logger.error("Failed to list files in folder %s: %s", folder_name, e, exc_info=True)
            if "storage" in str(e).lower() or "bucket" in str(e).lower():
                raise CloudStorageError(f"Cloud storage error while listing files: {str(e)}")
            else:
                raise FileListingError(f"Failed to list files in folder '{folder_name}': {str(e)}")

    @staticmethod
    async def get_all_files_with_pagination(
        file_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[list[UploadedFile], int]:
        """
        Get all uploaded files with pagination and optional file type filtering.

        Args:
            file_type: Optional filter for file type (e.g., 'wgsn', 'image', 'document')
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            Tuple of (list of UploadedFile objects, total count)
        """
        async with get_connection_handler_for_app() as connection_handler:
            dao = UploadedFileDAO(connection_handler.session)
            
            files = await dao.get_all_files(file_type=file_type, limit=limit, offset=offset)
            total_count = await dao.get_files_count(file_type=file_type)
            
            return files, total_count

    @staticmethod
    async def get_file_by_id(file_id: UUID) -> Optional[UploadedFile]:
        """
        Get a file by its ID.

        Args:
            file_id: UUID of the file

        Returns:
            UploadedFile object if found, None otherwise
        """
        async with get_connection_handler_for_app() as connection_handler:
            dao = UploadedFileDAO(connection_handler.session)
            return await dao.get_file_by_id(file_id)

    @staticmethod
    async def update_file_record(
        file_id: UUID,
        filename: Optional[str] = None,
        cdn_url: Optional[str] = None,
        file_type: Optional[str] = None,
        sub_folder: Optional[str] = None,
        meta_data: Optional[dict] = None,
    ) -> Optional[UploadedFile]:
        """
        Update a file record.

        Args:
            file_id: UUID of the file to update
            filename: Updated filename (optional)
            cdn_url: Updated CDN URL (optional)
            file_type: Updated file type (optional)
            sub_folder: Updated subfolder path (optional)
            meta_data: Updated metadata (optional)

        Returns:
            Updated UploadedFile object if found, None otherwise
        """
        async with get_connection_handler_for_app() as connection_handler:
            dao = UploadedFileDAO(connection_handler.session)
            
            file_record = await dao.update_file_record(
                file_id=file_id,
                filename=filename,
                cdn_url=cdn_url,
                file_type=file_type,
                sub_folder=sub_folder,
                meta_data=meta_data,
            )
            
            if file_record:
                await connection_handler.session.commit()
            
            return file_record

    async def delete_file_record(self, file_id: UUID) -> Optional[UploadedFile]:
        """
        Delete a file record and the associated file from cloud storage.

        Args:
            file_id: UUID of the file to delete

        Returns:
            The deleted UploadedFile object if found and deleted, None otherwise
        """
        async with get_connection_handler_for_app() as connection_handler:
            dao = UploadedFileDAO(connection_handler.session)

            file_record = await dao.get_file_by_id(file_id)
            
            if not file_record:
                return None

            cdn_url = file_record.cdn_url
            blob_path = cdn_url.replace(self.base_cdn_path, "")

            try:
                await self.cloud_storage_util.delete_file(blob_path)
                logger.info(f"Successfully deleted file from cloud storage: {blob_path}")
            except Exception as e:
                logger.error(f"Failed to delete file from cloud storage: {blob_path}, error: {e}")

            deleted = await dao.delete_file_record(file_id)
            
            if deleted:
                await connection_handler.session.commit()
                return file_record
            
            
            return None

    @staticmethod
    async def delete_file_from_elastic_background(cdn_url: str):
        """
        Background task to delete file documents from Elasticsearch by CDN URL.
        
        Args:
            cdn_url: CDN URL of the file to delete
        """
        elastic_adapter = None
        try:
            logger.info(f"Starting background deletion from Elasticsearch for CDN URL: {cdn_url}")
            
            elastic_adapter = ElasticSearchAdapter()
            index_name = PDFExtractionService.ELASTICSEARCH_INDEX

            deleted_count = await elastic_adapter.delete_document_by_term(
                index_name=index_name,
                term="cdn_url",
                value=cdn_url
            )
            
            logger.info(f"Background task completed: deleted {deleted_count} chunks/pages from ES for {cdn_url}")
            
        except Exception as e:
            logger.error(f"Background task failed to delete from Elasticsearch: {e}", exc_info=True)
        finally:
            if elastic_adapter:
                await elastic_adapter.close()


