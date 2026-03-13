"""
Collection Brief Tools

Tools for the collection brief agent to interact with the questionnaire.
"""

from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class AskQuestionInput(BaseModel):
    """Input for asking a question."""
    question_number: int = Field(description="The question number to ask")
    question_id: str = Field(description="The question ID (e.g., 'collection_snapshot')")
    question_data: Dict[str, Any] = Field(description="The complete question data as JSON including title, fields, etc.")


class AskQuestionTool(BaseTool):
    """Tool to ask a questionnaire question."""

    name: str = "ask_question"
    description: str = """
    Use this tool to ask the next question in the collection brief questionnaire.

    You must provide:
    - question_number: The question number (e.g., 1, 2, 3...)
    - question_id: The question ID from the questionnaire (e.g., 'collection_snapshot', 'customer_persona')
    - question_data: The complete question data as JSON with the structure:
      {
        "title": "Question title",
        "description": "Question description",
        "sections": [
          {
            "fields": [
              {
                "id": "field_id",
                "type": "text|textarea|radio|checkbox",
                "label": "Field label",
                "placeholder": "Placeholder text",
                "required": true|false,
                "options": [...] (for radio/checkbox)
              }
            ]
          }
        ]
      }

    The tool will format and return the question for display.
    """
    args_schema: type[BaseModel] = AskQuestionInput

    def _run(self, question_number: int, question_id: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ask a question by number, ID, and data."""
        # Return the question data with metadata
        return {
            "type": "form",
            "question_number": question_number,
            "question_id": question_id,
            "form_schema": question_data
        }

    async def _arun(self, question_number: int, question_id: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Async version."""
        return self._run(question_number, question_id, question_data)


class SaveAnswerInput(BaseModel):
    """Input for saving an answer."""
    question_id: str = Field(description="The ID of the question being answered")
    question_number: int = Field(description="The question number")
    answer_text: str = Field(description="The user's answer text")


class SaveAnswerTool(BaseTool):
    """Tool to save a questionnaire answer."""

    name: str = "save_answer"
    description: str = """
    Use this tool to save the user's answer to a question.
    Call this immediately after the user provides an answer.

    You must provide:
    - question_id: The ID of the question (e.g., 'collection_snapshot')
    - question_number: The question number
    - answer_text: The exact text the user provided
    """
    args_schema: type[BaseModel] = SaveAnswerInput
    thread_meta: Dict[str, Any] = Field(default_factory=dict)

    def _run(self, question_id: str, question_number: int, answer_text: str) -> Dict[str, Any]:
        """Save an answer."""
        # This will be called by the streaming service to actually update the thread
        # For now, just return confirmation
        return {
            "type": "answer_saved",
            "question_id": question_id,
            "question_number": question_number,
            "answer_text": answer_text,
            "message": f"Answer to question {question_number} saved successfully"
        }

    async def _arun(self, question_id: str, question_number: int, answer_text: str) -> Dict[str, Any]:
        """Async version."""
        return self._run(question_id, question_number, answer_text)


class ReadAnswersInput(BaseModel):
    """Input for reading answers."""
    pass


class ReadAnswersTool(BaseTool):
    """Tool to read all previous answers."""

    name: str = "read_answers"
    description: str = """
    Use this tool to retrieve all previously saved answers.

    Call this tool:
    - When the user asks to review their answers
    - **IMPORTANT: At the end of the questionnaire when all questions have been answered** to show a summary
    - To check which questions have been completed
    """
    args_schema: type[BaseModel] = ReadAnswersInput
    thread_meta: Dict[str, Any] = Field(default_factory=dict)

    def _run(self) -> Dict[str, Any]:
        """Read all answers."""
        answers = self.thread_meta.get('answers', {})
        total_questions = self.thread_meta.get('total_questions', len(answers))

        return {
            "type": "answers_list",
            "total_questions": total_questions,
            "answers_count": len(answers),
            "answers": answers,
            "message": f"Retrieved {len(answers)} answer(s)"
        }

    async def _arun(self) -> Dict[str, Any]:
        """Async version."""
        return self._run()


def create_collection_brief_tools(thread_meta: Dict[str, Any] = None) -> list:
    """Create the collection brief tools with thread context."""
    if thread_meta is None:
        thread_meta = {}

    # Create tools
    ask_question = AskQuestionTool()
    save_answer = SaveAnswerTool(thread_meta=thread_meta)
    read_answers = ReadAnswersTool(thread_meta=thread_meta)

    return [ask_question, save_answer, read_answers]
