"""
Collection Brief Tools

Tools for the collection brief agent to interact with the questionnaire.
"""

from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .questionnaire import COLLECTION_BRIEF_QUESTIONS, get_question_by_number, get_total_questions
from .forms import get_form_schema


class AskQuestionInput(BaseModel):
    """Input for asking a question."""
    question_number: int = Field(description="The question number to ask (1-10)")


class AskQuestionTool(BaseTool):
    """Tool to ask a questionnaire question."""

    name: str = "ask_question"
    description: str = """
    Use this tool to ask the next question in the collection brief questionnaire.
    The tool returns the complete question with all metadata including:
    - Question number and title
    - The prompt to ask
    - What to include in the answer
    - An example answer

    This should be called when you need to ask the user a question.
    """
    args_schema: type[BaseModel] = AskQuestionInput

    def _run(self, question_number: int) -> Dict[str, Any]:
        """Ask a question by number."""
        question = get_question_by_number(question_number)
        if not question:
            return {
                "error": f"Question {question_number} not found",
                "type": "error"
            }

        # Get the form schema for this question
        form_schema = get_form_schema(question["id"])

        if not form_schema:
            # Fallback to simple question format if no form schema exists
            return {
                "type": "question",
                "question_number": question["number"],
                "question_id": question["id"],
                "title": question["title"],
                "prompt": question["prompt"],
                "what_to_include": question["what_to_include"],
                "example": question.get("example", ""),
                "total_questions": get_total_questions()
            }

        # Return the form schema with additional metadata
        return {
            "type": "form",
            "question_number": question["number"],
            "question_id": question["id"],
            "total_questions": get_total_questions(),
            "form_schema": form_schema
        }

    async def _arun(self, question_number: int) -> Dict[str, Any]:
        """Async version."""
        return self._run(question_number)


class SaveAnswerInput(BaseModel):
    """Input for saving an answer."""
    question_id: str = Field(description="The ID of the question being answered")
    question_number: int = Field(description="The question number (1-10)")
    answer_text: str = Field(description="The user's answer text")


class SaveAnswerTool(BaseTool):
    """Tool to save a questionnaire answer."""

    name: str = "save_answer"
    description: str = """
    Use this tool to save the user's answer to a question.
    Call this immediately after the user provides an answer.

    You must provide:
    - question_id: The ID of the question (e.g., 'collection_snapshot')
    - question_number: The question number (1-10)
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
    This is useful when the user asks to review their answers or wants to see what they've already provided.
    """
    args_schema: type[BaseModel] = ReadAnswersInput
    thread_meta: Dict[str, Any] = Field(default_factory=dict)

    def _run(self) -> Dict[str, Any]:
        """Read all answers."""
        answers = self.thread_meta.get('answers', {})
        current_question = self.thread_meta.get('current_question', 1)

        return {
            "type": "answers_list",
            "current_question": current_question,
            "total_questions": get_total_questions(),
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
