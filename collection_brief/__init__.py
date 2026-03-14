"""
Collection Brief Package

This package contains all components for the collection brief questionnaire:
- Agent: The main AI agent for conducting interviews
- Tools: LangChain tools for asking questions and saving answers

All questionnaire logic is handled through the streaming chat API.
No API endpoints needed - uses standard streaming chat.
"""

from .agent import create_collection_brief_agent
from .tools import create_collection_brief_tools

__all__ = [
    'create_collection_brief_agent',
    'create_collection_brief_tools',
]
