import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseStreamResponseHandler(ABC):
    """Base class for handling streaming responses from AI providers."""

    def __init__(self, name: str = None):
        self.name = name or "unknown"

    @abstractmethod
    def extract_content(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract content from the streaming event data."""
        pass

    def handle_stream_event(self, event: Dict[str, Any]) -> str | None:
        """Handle a streaming event and return formatted response."""
        content = self.extract_content(event)
        if content:
            return json.dumps({
                "message": {},
                "name": self.name,
                "type": "supervisor_streaming",
                "content": content,
                "detail": {}
            })
        return None
