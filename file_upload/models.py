import uuid6
from sqlalchemy import Column, String, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from utils.sqlalchemy import Base, EpochTimestampMixin


class UploadedFile(Base, EpochTimestampMixin):
    """
    Model for storing uploaded file metadata.
    
    Attributes:
        file_id: UUID7 primary key for the file record
        cdn_url: CDN URL of the uploaded file
        filename: Original filename
        file_type: Type of file (e.g., 'wgsn', 'image', 'document')
        sub_folder: Storage subfolder path
        meta_data: JSONB field containing additional metadata
        created_at: Timestamp when record was created (from EpochTimestampMixin)
        updated_at: Timestamp when record was last updated (from EpochTimestampMixin)
    """
    __tablename__ = "uploaded_files"
    
    file_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid6.uuid7)
    cdn_url = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    sub_folder = Column(String, nullable=True)
    meta_data = Column(JSONB, nullable=True)

    # Index on created_at for sorting by upload time
    # Index on file_type for filtering by type
    __table_args__ = (
        Index('ix_uploaded_files_created_at', 'created_at'),
        Index('ix_uploaded_files_file_type', 'file_type'),
    )
    
    def __repr__(self):
        return f"<UploadedFile(file_id={self.file_id}, filename={self.filename}, file_type={self.file_type})>"

