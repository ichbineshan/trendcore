from fastapi import status


class ThreadsError(Exception):
    """Base class for Threads-related errors."""

    def __init__(
        self,
        message: str = "An error occurred in Threads Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        custom_code: int = 4001,
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        self.custom_code = custom_code
        super().__init__(message)


class ThreadNotFoundError(ThreadsError):
    """Raised when a thread is not found."""

    def __init__(self, thread_id: str):
        super().__init__(
            message=f"Thread with ID '{thread_id}' not found.",
            detail=f"The thread you are looking for does not exist or has been deleted.",
            status_code=status.HTTP_404_NOT_FOUND,
            custom_code=4002,
        )


class ThreadMessageNotFoundError(ThreadsError):
    """Raised when a thread message is not found."""

    def __init__(self, message_id: str):
        super().__init__(
            message=f"Message with ID '{message_id}' not found.",
            detail=f"The message you are looking for does not exist or has been deleted.",
            status_code=status.HTTP_404_NOT_FOUND,
            custom_code=4003,
        )


class ThreadServiceError(ThreadsError):
    """Generic catch-all for thread service errors."""

    def __init__(self, detail: str):
        super().__init__(
            message="An unexpected thread service error occurred.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            custom_code=4099,
        )
