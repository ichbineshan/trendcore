"""
Collection Brief Tools

Tools for the collection brief agent to interact with the questionnaire.
Uses langchain_core.tools @tool decorator.
"""

from typing import Any, Dict, Union

from langchain_core.tools import tool

from .models import FormConfig


@tool("ask_question")
def ask_question_tool(
    question_number: int,
    question_id: str,
    question_data: Union[FormConfig, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Show a structured form to the user for a topic that benefits from structured input
    (chip-selects, tag-inputs, many options, nested selections).
    ASK QUESTIONS VIA FORM.

    DO NOT use this for every question. Most topics can be asked conversationally in
    plain chat text. Only call this when typing the answer would be tedious or when
    the topic has predefined options the user should pick from.

    Parameters:
    - question_number: Sequential step number (e.g. 1, 2, 3…)
    - question_id: Topic id from the data source (e.g. 'range-architecture')
    - question_data: FormConfig JSON — id, title, description, submitLabel, fields[]
        Use this tool to ask the next question in the collection brief questionnaire:
      {
        "id": "form-id",
        "title": "Question title",
        "description": "Optional description",
        "submitLabel": "Continue",
        "fields": [
          {
            "id": "field_id",
            "type": "chip-select|text|number|select|checkbox|textarea|radio|tag-input|nested-chip-select",
            "label": "Field label",
            "required": true,
            "placeholder": "Optional placeholder",
            "multiSelect": false,
            "options": [{"label": "Option", "value": "value"}], "nestedOptions": [...] (for nested-chip-select)
          }
        ]
      }
    The tool will format and return the question for display.
    """
    config = (
        FormConfig.model_validate(question_data)
        if isinstance(question_data, dict)
        else question_data
    )
    return {
        "type": "form",
        "question_number": question_number,
        "question_id": question_id,
        "form_schema": config.model_dump(mode="json"),
    }


@tool("review_and_finish_questionnaire")
def review_and_finish_questionnaire_tool(
    question_data: Union[FormConfig, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Use this tool to show the final review screen when the questionnaire is complete.

    Call this when all questions have been answered and the user is ready to review
    and finish. Presents all answers in a read-only, well-formatted summary with
    a "Create Design" button.

    You must provide question_data using the same form config structure as ask_question:
    - id: e.g. "review-and-finish"
    - title: e.g. "Review your answers"
    - submitLabel: "Create Design"
    - fields: One FormField per completed question. For each, use:
      id: question_id, type: "text", label: question label (e.g. "Collection Snapshot"),
      defaultValue: the user's answer (displayed read-only).
    """
    config = (
        FormConfig.model_validate(question_data)
        if isinstance(question_data, dict)
        else question_data
    )
    form_schema = config.model_dump(mode="json")
    # Signal to frontend: render this form read-only and show field.defaultValue in each field
    form_schema["readOnly"] = True
    return {
        "type": "review_and_finish",
        "form_type": "review_and_finish",
        "form_schema": form_schema,
        "submit_label": "Create Design",
        "read_only": True,
    }


def create_collection_brief_tools(thread_meta: Dict[str, Any] = None) -> list:
    """Create the collection brief tools with thread context."""
    if thread_meta is None:
        thread_meta = {}

    @tool("save_answer")
    def save_answer_tool(
        question_id: str,
        question_number: int,
        answer_text: str,
    ) -> Dict[str, Any]:
        """
        Save the user's answer for a topic. THIS IS MANDATORY for every answer — whether
        the user replied in chat or submitted a form. If one message covers multiple
        topics, call this once per topic.

        Parameters:
        - question_id: Topic id (e.g. 'collection-snapshot', 'customer-persona')
        - question_number: The topic's step number
        - answer_text: The user's answer content
        """
        return {
            "type": "answer_saved",
            "question_id": question_id,
            "question_number": question_number,
            "answer_text": answer_text,
            "message": f"Answer to question {question_number} saved successfully",
        }

    @tool("read_answers")
    def read_answers_tool() -> Dict[str, Any]:
        """
        Use this tool to retrieve all previously saved answers.

        Call this tool:
        - When the user asks to review their answers
        - To check which questions have been completed
        """
        answers = thread_meta.get("answers", {})
        total_questions = thread_meta.get("total_questions", len(answers))
        return {
            "type": "answers_list",
            "total_questions": total_questions,
            "answers_count": len(answers),
            "answers": answers,
            "message": f"Retrieved {len(answers)} answer(s)",
        }

    return [
        ask_question_tool,
        save_answer_tool,
        read_answers_tool,
        review_and_finish_questionnaire_tool,
    ]
