from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from file_upload.models import UploadedFile
from utils.dao import BaseDAO


class UploadedFileDAO(BaseDAO):
    """
    Data Access Object for WGSNUploadedFile model.
    Provides CRUD operations for WGSN uploaded file records.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, db_model=UploadedFile)

    async def create_file_record(
        self,
        file_id: UUID,
        cdn_url: str,
        filename: str,
        file_type: str,
        sub_folder: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> UploadedFile:
        """
        Create a new uploaded file record.

        Args:
            file_id: UUID7 for the file record
            cdn_url: CDN URL of the uploaded file
            filename: Original filename
            file_type: Type of file (e.g., 'wgsn', 'image', 'document')
            sub_folder: Storage subfolder path (optional)
            meta_data: Additional metadata (optional)

        Returns:
            UploadedFile object after creation
        """
        file_record = self.add_object(
            file_id=file_id,
            cdn_url=cdn_url,
            filename=filename,
            file_type=file_type,
            sub_folder=sub_folder,
            meta_data=meta_data,
        )
        await self._flush()
        return file_record

    async def get_file_by_id(self, file_id: UUID) -> Optional[UploadedFile]:
        """
        Get a file record by its UUID.

        Args:
            file_id: UUID of the file to retrieve

        Returns:
            UploadedFile object if found, None otherwise
        """
        query = select(UploadedFile).where(UploadedFile.file_id == file_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def get_all_files(
        self, 
        file_type: Optional[str] = None,
        limit: int = 10, 
        offset: int = 0
    ) -> list[UploadedFile]:
        """
        Get all uploaded files with pagination and optional filtering.

        Args:
            file_type: Optional filter for file type (e.g., 'wgsn', 'image')
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            List of UploadedFile objects
        """
        query = select(UploadedFile)
        
        if file_type is not None:
            query = query.where(UploadedFile.file_type == file_type)
        
        query = (
            query
            .order_by(UploadedFile.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._execute_query(query)
        return result.scalars().all()

    async def get_files_count(self, file_type: Optional[str] = None) -> int:
        """
        Get total count of uploaded files.

        Args:
            file_type: Optional filter for file type

        Returns:
            Total count of files
        """
        query = select(func.count()).select_from(UploadedFile)
        
        if file_type is not None:
            query = query.where(UploadedFile.file_type == file_type)
        
        result = await self._execute_query(query)
        return result.scalar() or 0

    async def update_file_record(
        self,
        file_id: UUID,
        cdn_url: Optional[str] = None,
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
        sub_folder: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[UploadedFile]:
        """
        Update an existing uploaded file record.

        Args:
            file_id: UUID of the file to update
            cdn_url: Updated CDN URL (optional)
            filename: Updated filename (optional)
            file_type: Updated file type (optional)
            sub_folder: Updated subfolder path (optional)
            meta_data: Updated metadata (optional)

        Returns:
            Updated UploadedFile object if found, None otherwise
        """
        query = select(UploadedFile).where(UploadedFile.file_id == file_id)
        result = await self._execute_query(query)
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            return None

        if cdn_url is not None:
            file_record.cdn_url = cdn_url
            self.flag_modified(file_record, "cdn_url")

        if filename is not None:
            file_record.filename = filename
            self.flag_modified(file_record, "filename")

        if file_type is not None:
            file_record.file_type = file_type
            self.flag_modified(file_record, "file_type")

        if sub_folder is not None:
            file_record.sub_folder = sub_folder
            self.flag_modified(file_record, "sub_folder")

        if meta_data is not None:
            file_record.meta_data = meta_data
            self.flag_modified(file_record, "meta_data")

        await self._flush()
        return file_record

    async def delete_file_record(self, file_id: UUID) -> bool:
        """
        Delete an uploaded file record by its UUID.

        Args:
            file_id: UUID of the file to delete

        Returns:
            True if file was deleted, False if not found
        """
        query = select(UploadedFile).where(UploadedFile.file_id == file_id)
        result = await self._execute_query(query)
        file_record = result.scalar_one_or_none()
        
        if file_record:
            await self.session.delete(file_record)
            await self._flush()
            return True
        return False

