"""
Collection Brief Agent

AI agent for conducting the collection brief questionnaire interview using tools.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor

from config.settings import loaded_config
from agents.collection_brief_tools import create_collection_brief_tools


SYSTEM_PROMPT = """You are a helpful AI assistant conducting a collection brief questionnaire interview.

You have access to three tools:
1. **ask_question** - Use this to ask the next question in the questionnaire
2. **save_answer** - Use this immediately after the user provides an answer
3. **read_answers** - Use this when the user wants to review their previous answers

Your workflow:
1. When starting (first message) or after saving an answer, call ask_question with the current question number
2. When the user provides an answer, call save_answer with the question_id, question_number, and their answer_text
3. After saving, immediately call ask_question for the next question
4. If the user asks to see their answers, call read_answers

Important rules:
- Always use the tools to ask questions and save answers
- Do NOT generate questions yourself - use the ask_question tool
- Do NOT skip questions or change the order
- Be brief and friendly in your responses between tool calls
- After saving an answer, immediately ask the next question

Current state:
- Current question number: {current_question}
- Questions completed: {answers_count}
- Total questions: 10
"""


def create_collection_brief_agent(thread_meta: dict = None):
    """
    Create a collection brief agent that uses tools to conduct the questionnaire.

    Args:
        thread_meta: Thread metadata containing current_question and answers

    Returns:
        AgentExecutor
    """
    if thread_meta is None:
        thread_meta = {}

    current_question = thread_meta.get('current_question', 1)
    answers = thread_meta.get('answers', {})

    # Create LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=loaded_config.openai_api_key,
        temperature=0.3,
        streaming=True,
    )

    # Create tools with thread context
    tools = create_collection_brief_tools(thread_meta)

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Partial with current state
    prompt = prompt.partial(
        current_question=current_question,
        answers_count=len(answers)
    )

    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Create executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    return agent_executor
