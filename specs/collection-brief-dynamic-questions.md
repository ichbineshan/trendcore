# Collection Brief Dynamic Question Generation - Specification

## Overview
Feed the `questionnaire.md` content directly to the LLM agent's system prompt, enabling dynamic question generation without parsing logic.

## Current State
- **questionnaire.py**: Hardcoded list of 10 questions with static content
- **forms.py**: Hardcoded form schemas for each question ID
- **Agent**: Asks questions by number (1-10) using hardcoded prompts
- **Limitation**: Any question changes require code modifications

## Proposed State
- **questionnaire.md**: Single source of truth loaded into agent's system prompt
- **Agent**: LLM reads markdown and generates questions dynamically
- **No parser needed**: LLM understands markdown natively
- **Benefit**: Update questions by editing markdown, no code changes needed

## Architecture

### Simple Flow
```
questionnaire.md → Read file → Include in agent system prompt → LLM generates questions
```

### Agent System Prompt Structure
```
You are conducting a collection brief questionnaire.

# Questionnaire Questions

[FULL CONTENT OF questionnaire.md]

# Instructions
- Ask questions in order (1-10)
- Use the prompts and guidance from the questionnaire above
- Adapt your phrasing based on the context
- Include examples when helpful
- Track which question we're on
```

## Implementation

### Step 1: Load Markdown
**File**: `collection_brief/agent.py`

```python
from pathlib import Path

def load_questionnaire_markdown() -> str:
    """Load questionnaire.md content"""
    md_path = Path(__file__).parent / "questionnaire.md"
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

QUESTIONNAIRE_CONTENT = load_questionnaire_markdown()
```

### Step 2: Update System Prompt
**File**: `collection_brief/agent.py`

```python
SYSTEM_PROMPT = """You are a helpful AI assistant conducting a collection brief questionnaire interview.

# Questionnaire Content

{questionnaire_content}

# Your Task

You have access to three tools:
1. **ask_question** - Use this to ask the next question in the questionnaire
2. **save_answer** - Use this immediately after the user provides an answer
3. **read_answers** - Use this when the user wants to review their previous answers

# Workflow
1. When starting or after saving an answer, call ask_question with the current question number
2. Generate the question based on the questionnaire content above for that number
3. When the user provides an answer, call save_answer with the question_id, question_number, and their answer_text
4. After saving, immediately call ask_question for the next question

# Important Rules
- Always use the tools to ask questions and save answers
- Generate questions based on the questionnaire content above
- Do NOT skip questions or change the order
- Be brief and friendly in your responses between tool calls
- After saving an answer, immediately ask the next question

Current state:
- Current question number: {current_question}
- Questions completed: {answers_count}
- Total questions: 10
"""
```

### Step 3: Inject Content into Prompt
**File**: `collection_brief/agent.py`

```python
def create_collection_brief_agent(thread_meta: dict = None):
    # ... existing code ...

    # Partial with current state AND questionnaire content
    prompt = prompt.partial(
        current_question=current_question,
        answers_count=len(answers),
        questionnaire_content=QUESTIONNAIRE_CONTENT
    )
```

## Benefits

1. **Zero Parsing Logic**: No regex, no string manipulation, no bugs
2. **LLM Native**: The LLM can understand markdown perfectly
3. **Dynamic Adaptation**: LLM can rephrase questions contextually
4. **Easy Updates**: Edit markdown file, restart server
5. **Flexible**: LLM can handle conditional sections naturally
6. **Simple**: Minimal code changes

## Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Parser + Code** | Predictable, structured, typed | Complex, brittle, code changes needed |
| **Markdown to LLM** | Simple, flexible, maintainable | Slightly less predictable, token cost |

We choose **Markdown to LLM** for maintainability and simplicity.

## Migration Steps

1. ✅ Create specs folder
2. ✅ Move spec to specs/
3. ✅ Load questionnaire.md in agent.py
4. ✅ Update SYSTEM_PROMPT to include markdown content
5. ✅ Inject content when creating agent
6. ✅ Remove sequential question enforcement
7. ⏳ Test that questions are asked correctly
8. ⏳ Verify agent behavior matches current implementation

## Backward Compatibility

- Forms still exist (forms.py unchanged for now)
- Tools unchanged
- API unchanged
- Frontend unchanged
- Only the agent's internal prompt changes

## Future Enhancements

- Remove forms.py entirely, let LLM describe fields
- Dynamic question count (not fixed to 10)
- Conditional question flows
- Multi-language support (different markdown files)

## Success Criteria

- [ ] Questionnaire markdown loaded into agent prompt
- [ ] Agent asks questions based on markdown content
- [ ] Questions match the markdown content
- [ ] Agent continues to work without modifications to tools
- [ ] Frontend continues to work without modifications
- [ ] Can update question text by editing markdown only
