"""
Collection Brief Package

This package contains all components for the collection brief questionnaire:
- Agent: LangGraph-based agent (create_react_agent), aligned with ai-genetic pattern
- Tools: LangChain tools for asking questions and saving answers
- Registry: Tool metadata and response_format for streaming/handlers

All questionnaire logic is handled through the streaming chat API.
"""

from .agent import create_collection_brief_agent
from .models import ChipOption, FormConfig, FormField, FieldType
from .tools import create_collection_brief_tools
from .registry import tools_registry
from .system_prompt import collection_brief_prompt

__all__ = [
    "create_collection_brief_agent",
    "ChipOption",
    "FormConfig",
    "FormField",
    "FieldType",
    "create_collection_brief_tools",
    "tools_registry",
    "collection_brief_prompt",
]
