"""
Minimal AssistantMessageBuffer for trend-analysis streaming.

This mirrors the behavior of cortex.streaming.message_buffer.AssistantMessageBuffer
just enough for collection brief: it accumulates streaming text chunks and stores
structured tool events, then exposes a consolidated list via get_json_content().
"""

from typing import Any, Dict, List


class AssistantMessageBuffer:
  def __init__(self) -> None:
    self.current_type: str | None = None
    self.current_chunks: List[str] = []
    self.structured_events: List[Dict[str, Any]] = []

  def process_event(self, event: Dict[str, Any]) -> None:
    """Add a streaming/tool event into the buffer."""
    event_type = event.get("type")
    is_same_type = event_type == self.current_type

    if not is_same_type:
      self._flush()
      self.current_type = event_type

    if event_type in ("streaming", "supervisor_streaming"):
      # Accumulate text chunks
      self.current_chunks.append(event.get("content", ""))
    else:
      # Keep non-streaming events as-is
      self.structured_events.append(event)

  def _flush(self) -> None:
    """Flush accumulated streaming chunks into a single event."""
    if self.current_type in ("streaming", "supervisor_streaming") and self.current_chunks:
      self.structured_events.append(
        {"type": self.current_type, "content": "".join(self.current_chunks)}
      )
    self.current_chunks = []

  def get_json_content(self) -> List[Dict[str, Any]]:
    """Return all buffered events as a list (flushes any pending chunks)."""
    self._flush()
    return self.structured_events

