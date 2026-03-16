from typing import Optional

from .base_stream import BaseStreamResponseHandler
from .openai_stream import OpenAIStreamHandler


class StreamHandlerFactory:
    """Factory for stream handlers."""

    @classmethod
    def create_handler(
        cls,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        name: Optional[str] = None,
    ) -> BaseStreamResponseHandler:
        return OpenAIStreamHandler(name)
