from typing import Optional

from .base_stream import BaseStreamResponseHandler
from .openai_stream import OpenAIStreamHandler
from .anthropic_stream import AnthropicStreamHandler


class StreamHandlerFactory:
    """Factory for stream handlers by provider/model."""

    MODEL_PROVIDERS = {
        "gpt-4o": "openai",
        "gpt-4o-mini": "openai",
        "gpt-o1-mini": "openai",
        "gpt-o1-preview": "openai",
        "gpt-o1": "openai",
        "gpt-4": "openai",
        "gpt-4-turbo": "openai",
        "gpt-3.5-turbo": "openai",
        "gpt-4.1": "openai",
        "gpt-5.1": "openai",
        "gpt-5.2": "openai",
        "claude-sonnet-4-20250514": "anthropic",
        "claude-3-7-sonnet-20250219": "anthropic",
        "claude-3-5-sonnet-20240620": "anthropic",
        "claude-3-opus-20240229": "anthropic",
        "claude-3-sonnet": "anthropic",
        "claude-3-haiku": "anthropic",
        "claude-2": "anthropic",
        "claude-opus-4-5": "anthropic",
        "claude-opus-4-6": "anthropic",
    }

    @classmethod
    def create_handler(
        cls,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        name: Optional[str] = None,
    ) -> BaseStreamResponseHandler:
        if not provider and model_name:
            provider = cls.MODEL_PROVIDERS.get(model_name)
        if not provider:
            provider = "openai"
        if provider and provider.lower() == "anthropic":
            return AnthropicStreamHandler(name)
        return OpenAIStreamHandler(name)
