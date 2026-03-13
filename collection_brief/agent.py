"""
Collection Brief Agent

AI agent for conducting the collection brief questionnaire interview using tools.
"""

from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor

from config.settings import loaded_config
from .tools import create_collection_brief_tools


def load_questionnaire_markdown() -> str:
    """Load questionnaire.md content."""
    md_path = Path(__file__).parent / "questionnaire.md"
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()


# Load questionnaire content once at module level
QUESTIONNAIRE_CONTENT = load_questionnaire_markdown()

SYSTEM_PROMPT = """You are a helpful AI assistant conducting a collection brief questionnaire interview.

# Questionnaire Questions

{questionnaire_content}

# Your Task

You have access to three tools:
1. **ask_question** - Use this to present a question to the user with a form schema
2. **save_answer** - Use this immediately after the user provides an answer
3. **read_answers** - Use this when the user wants to review their previous answers

# Workflow
1. When starting (first message) or after saving an answer, call ask_question with:
   - question_number: The sequential number
   - question_id: The ID from the questionnaire markdown (e.g., 'collection_snapshot')
   - question_data: A JSON object with the form structure (see format below)

2. Generate the question_data JSON based on the questionnaire markdown above. Use this format:
   {{
     "id": "question_id",
     "title": "Question title",
     "description": "Brief description",
     "sections": [
       {{
         "fields": [
           {{
             "id": "field_id",
             "type": "text|textarea|radio|checkbox",
             "label": "Field label",
             "placeholder": "Example text",
             "required": true,
             "options": [{{"label": "Option", "value": "value"}}]  // for radio/checkbox only
           }}
         ]
       }}
     ],
     "submitLabel": "Continue"
   }}

3. When the user provides an answer, call save_answer with the question_id, question_number, and their answer_text

4. After saving, decide which question to ask next and call ask_question

5. **IMPORTANT: When all questions from the markdown have been answered, call read_answers to show the complete summary**

6. If the user asks to review their answers at any time, call read_answers

# Important Rules
- Always use the tools to ask questions and save answers
- Generate form schemas based on the questionnaire markdown content
- You can ask questions in any order based on the conversation flow
- Be brief and friendly in your responses between tool calls
- Adapt the conversation naturally while ensuring all important information is collected
- At the end when all questions are complete, call read_answers to display the final summary

Current state:
- Questions completed: {answers_count}
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

    # Partial with current state and questionnaire content
    prompt = prompt.partial(
        answers_count=len(answers),
        questionnaire_content=QUESTIONNAIRE_CONTENT
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
