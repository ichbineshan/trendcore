"""
Collection Brief Package

This package contains all components for the collection brief questionnaire:
- Agent: The main AI agent for conducting interviews
- Tools: LangChain tools for asking questions and saving answers
- Questionnaire: Question definitions and metadata
- Forms: Form schemas for UI rendering
- Router: FastAPI routes for collection brief endpoints
- Views: API endpoint handlers
"""

from .agent import create_collection_brief_agent
from .tools import create_collection_brief_tools
from .questionnaire import (
    COLLECTION_BRIEF_QUESTIONS,
    get_question_by_number,
    get_question_by_id,
    get_total_questions
)
from .forms import get_form_schema
from .router import router

__all__ = [
    'create_collection_brief_agent',
    'create_collection_brief_tools',
    'COLLECTION_BRIEF_QUESTIONS',
    'get_question_by_number',
    'get_question_by_id',
    'get_total_questions',
    'get_form_schema',
    'router',
]
