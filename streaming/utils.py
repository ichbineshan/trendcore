import json
from streaming.serializers import StreamEventType
from config.settings import loaded_config


def format_stream_event(event_type: StreamEventType, content: str, **kwargs) -> str:
    """Format a stream event for SSE."""
    event_data = {
        "type": event_type.value,
        "content": content,
        **kwargs
    }
    return f"{loaded_config.stream_token}: {json.dumps(event_data)}\n"
