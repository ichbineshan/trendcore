from typing import Dict, Any, Optional

from .base_stream import BaseStreamResponseHandler


class OpenAIStreamHandler(BaseStreamResponseHandler):
    """Stream response handler for OpenAI models."""

    def __init__(self, name: str = None):
        super().__init__(name or "openai_agent")

    def extract_content(self, event: Dict[str, Any]) -> Optional[str]:
        try:
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content"):
                return chunk.content if chunk.content else ""
            return None
        except (KeyError, AttributeError, TypeError):
            return None
