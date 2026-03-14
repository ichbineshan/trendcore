from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config.logging import logger
#from mcp_tools.types import MCPResponse


def validation_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Custom exception handler for 422 Unprocessable Entity errors.
    
    Catches Pydantic validation errors and returns a structured response
    with detailed error information for debugging.
    """
    if isinstance(exc, RequestValidationError):
        validation_errors = exc.errors()
        
        error_details = []
        for error in validation_errors:
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.error(
            "validation_error",
            method=request.method,
            path=request.url.path,
            error_count=len(error_details),
            errors=error_details
        )
        
        response = MCPResponse(
            success=False,
            message="Request validation failed",
            data={"validation_errors": error_details},
            error="The request payload does not match the expected schema"
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump()
        )
    
    return generic_exception_handler(request, exc)


def generic_validation_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Handler for generic Pydantic ValidationError exceptions.
    """
    if isinstance(exc, ValidationError):
        logger.error(
            "pydantic_validation_error",
            method=request.method,
            path=request.url.path,
            errors=exc.errors()
        )
        
        response = MCPResponse(
            success=False,
            message="Data validation failed",
            data={"validation_errors": exc.errors()},
            error=str(exc)
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump()
        )
    
    return generic_exception_handler(request, exc)


def http_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Handler for HTTP exceptions (4xx, 5xx errors).
    """
    if isinstance(exc, StarletteHTTPException):
        logger.warning(
            "http_exception",
            method=request.method,
            path=request.url.path,
            status_code=exc.status_code,
            detail=exc.detail
        )
        
        response = MCPResponse(
            success=False,
            message=exc.detail or "HTTP error occurred",
            data=None,
            error=f"HTTP {exc.status_code}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump()
        )
    
    return generic_exception_handler(request, exc)


def generic_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Catch-all exception handler for unexpected errors.
    
    Logs the error with structured logging and returns a generic error response
    without exposing internal details to the client.
    """
    logger.error(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        exc_info=True
    )
    
    response = MCPResponse(
        success=False,
        message="An unexpected error occurred",
        data=None,
        error="Internal server error"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )
