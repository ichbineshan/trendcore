from fastapi import status


class StreamingError(Exception):
    """Base class for Streaming-related errors."""

    def __init__(
        self,
        message: str = "An error occurred in Streaming Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        custom_code: int = 5001,
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        self.custom_code = custom_code
        super().__init__(message)


class StreamGenerationError(StreamingError):
    """Raised when stream generation fails."""

    def __init__(self, detail: str):
        super().__init__(
            message="Failed to generate streaming response.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            custom_code=5001,
        )


class AgentConfigurationError(StreamingError):
    """Raised when agent configuration is invalid or missing."""

    def __init__(self, detail: str):
        super().__init__(
            message="Invalid or missing agent configuration.",
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            custom_code=5002,
        )


class StreamingServiceError(StreamingError):
    """Generic catch-all for other streaming service errors."""

    def __init__(self, detail: str):
        super().__init__(
            message="An unexpected streaming service error occurred.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            custom_code=5099,
        )
