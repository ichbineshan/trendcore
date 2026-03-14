import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseStreamResponseHandler(ABC):
    """Base class for handling streaming responses from different AI providers."""

    def __init__(self, name: str = None):
        self.name = name or "unknown"
        self.is_sub_agent_streaming = False

    @abstractmethod
    def extract_content(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract content from the streaming event data."""
        pass

    def handle_stream_event(self, event: Dict[str, Any], agents: Dict[str, Any] = None) -> str | None:
        """Handle a streaming event and return formatted response."""
        content = self.extract_content(event)
        if content:
            tags = event.get("tags", [])
            agents = agents or {}
            if tags and any(tag in list(agents.keys()) for tag in tags):
                self.is_sub_agent_streaming = True

            if self.is_sub_agent_streaming and tags and any(tag in agents for tag in tags):
                response_type = "streaming"
            else:
                response_type = "supervisor_streaming"

            return json.dumps({
                "message": {},
                "name": self.name,
                "type": response_type,
                "content": content,
                "detail": {}
            })
        return None

    def get_provider_name(self) -> str:
        return self.__class__.__name__.replace("StreamHandler", "").lower()
