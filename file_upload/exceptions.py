from fastapi import status


class FileUploadError(Exception):
    """
    Base class for File Upload-related errors.
    Provides a consistent interface to store a message, detail, and status code.
    """

    def __init__(
        self,
        message: str = "An error occurred in File Upload Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        custom_code: int = 6001,
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        self.custom_code = custom_code
        super().__init__(message)


class FileListingError(FileUploadError):
    """Raised when file listing operation fails."""

    def __init__(self, detail: str):
        super().__init__(
            message="Failed to list files.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            custom_code=6002,
        )


class CloudStorageError(FileUploadError):
    """Raised when cloud storage operations fail."""

    def __init__(self, detail: str):
        super().__init__(
            message="Cloud storage operation failed.",
            detail=detail,
            status_code=status.HTTP_502_BAD_GATEWAY,
            custom_code=6003,
        )


class SignedURLGenerationError(FileUploadError):
    """Raised when signed URL generation fails."""

    def __init__(self, detail: str):
        super().__init__(
            message="Failed to generate signed URL.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            custom_code=6004,
        )


class FileNotFoundError(FileUploadError):
    """Raised when requested file or folder is not found."""

    def __init__(self, detail: str):
        super().__init__(
            message="File or folder not found.",
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            custom_code=6005,
        )


class InvalidFilePathError(FileUploadError):
    """Raised when file path is invalid or malformed."""

    def __init__(self, detail: str):
        super().__init__(
            message="Invalid file path provided.",
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            custom_code=6006,
        )


class FileUploadServiceError(FileUploadError):
    """Generic catch-all for other file upload service errors."""

    def __init__(self, detail: str):
        super().__init__(
            message="An unexpected file upload service error occurred.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            custom_code=6099,
        ) 