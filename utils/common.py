import functools
import typing

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import Field, BaseModel

from config.logging import logger
from utils.serializers import ResponseData


class LogData(BaseModel):
    error_type: str = Field(..., description="Type of the exception encountered")
    message: str = Field(..., description="Error message")
    detail: typing.Optional[str] = Field(None, description="Additional details")
    function: str = Field(..., description="Function where error occurred")


def handle_exceptions(
    generic_message: str = "An unexpected error occurred",
    exception_classes: typing.Union[typing.List[typing.Type[Exception]], tuple] = None
):
    """Decorator for structured logging and error response formatting."""
    exception_classes = tuple(exception_classes or ())

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except HTTPException as http_exc:
                logger.exception(
                    "HTTPException raised",
                    error_type=http_exc.__class__.__name__,
                    message=http_exc.detail,
                    status_code=http_exc.status_code,
                    function=func.__name__
                )
                raise

            except exception_classes as e:
                logger.exception("Handled exception", error=str(e), function=func.__name__)

                response_data = ResponseData.model_construct(success=False)
                response_data.message = getattr(e, "message", str(e))
                response_data.errors = [getattr(e, "detail", str(e))]

                return JSONResponse(
                    status_code=getattr(e, "status_code", status.HTTP_400_BAD_REQUEST),
                    content=jsonable_encoder(response_data)
                )

            except Exception as e:
                logger.exception("Unhandled exception", error=str(e), function=func.__name__)

                response_data = ResponseData.model_construct(success=False)
                response_data.message = generic_message
                response_data.errors = []

                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=jsonable_encoder(response_data)
                )

        return wrapper

    return decorator
