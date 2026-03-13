from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ResponseData(BaseModel):
    """Standard API response format."""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    errors: List[str] = Field(default_factory=list)
