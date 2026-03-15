"""
Collection Brief Agent

AI agent for conducting the collection brief questionnaire interview using tools.
Built on LangGraph (create_react_agent), aligned with cortex: checkpointer is obtained
via get_async_postgres_saver_with_retry and passed in when running in streaming.
"""

from pathlib import Path

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from config.settings import loaded_config
from .system_prompt import collection_brief_prompt
from .tools import create_collection_brief_tools


def load_questionnaire_markdown() -> str:
    """Load questionnaire.md content."""
    md_path = Path(__file__).parent / "questionnaire.md"
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


# Load questionnaire content once at module level
QUESTIONNAIRE_CONTENT = load_questionnaire_markdown()


def _build_system_message(thread_meta: dict) -> SystemMessage:
    """Build system message with questionnaire content and current answers state."""
    answers = thread_meta.get("answers", {})

    if answers:
        answers_summary = []
        sorted_answers = sorted(
            answers.items(), key=lambda x: x[1].get("question_number", 999)
        )
        for q_id, answer_data in sorted_answers:
            q_num = answer_data.get("question_number", "?")
            q_title = answer_data.get("question_title", q_id)
            answer_text = answer_data.get("answer_text", "")
            answers_summary.append(
                f"{q_num}. {q_id} ({q_title}):\n   {answer_text}"
            )
        completed_answers_str = "\n\n".join(answers_summary)
    else:
        completed_answers_str = "none"

    return SystemMessage(
        content=collection_brief_prompt.format(
            questionnaire_content=QUESTIONNAIRE_CONTENT,
            answers_count=len(answers),
            completed_answers=completed_answers_str,
        )
    )


def create_collection_brief_agent(thread_meta: dict, checkpointer):
    """
    Create a collection brief agent (LangGraph create_react_agent) for the questionnaire.

    Args:
        thread_meta: Thread metadata (current_question, answers).
        checkpointer: AsyncPostgresSaver from get_async_postgres_saver_with_retry(conn_string).
    """
    if thread_meta is None:
        thread_meta = {}

    model = ChatOpenAI(
        model="gpt-5.4",
        api_key=loaded_config.openai_api_key,
        temperature=0.3,
        streaming=True,
    )
    tools = create_collection_brief_tools(thread_meta)
    system_message = _build_system_message(thread_meta)

    return create_react_agent(
        model=model,
        prompt=system_message,
        tools=tools,
        checkpointer=checkpointer,
    )
