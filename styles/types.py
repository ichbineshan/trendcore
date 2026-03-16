"""Type definitions for MCP tools."""

from typing import Literal, List

from pydantic import BaseModel, Field

AspectRatio = Literal["16:9", "9:16", "4:3", "1:1"]
ImageSize = Literal["1K", "2K", "4K"]
StatusType = Literal["pushed_for_garment_generation", "failed", "completed", "ppt_generation", "design_generation_failed"]

class Filters(BaseModel):
    category: List[Literal["men", "women", "kids"]] | None
    year: Literal["24-25","25-26","26-27","27-28","29-30"] | None
    season: Literal["Autumn-Winter", "Spring-Summer"] | None


class MCPResponse(BaseModel):
    """
    Standard response schema for all MCP tools.
    
    Provides a consistent structure with success, message, data, and error fields.
    """
    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message describing the result")
    data: list | dict | str | None = Field(None, description="Response data payload, None if error occurred")
    error: str | None = Field(None, description="Error message if operation failed, None if successful")


