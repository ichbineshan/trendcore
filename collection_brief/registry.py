"""
Tool registry for collection brief agent.

Maps tool names to display metadata and response_format for streaming/handlers
(same pattern as ai-genetic file_generator_agent).
"""

tools_registry = {
    "ask_question": {
        "name": "Ask Question",
        "description": "Presents a questionnaire question to the user with a form schema.",
        "response_format": {
            "type": "toolStart",
            "message": {
                "action": "Asking question",
                "param": "$question_id",
            },
            "detail": {
                "question_number": "$question_number",
                "question_id": "$question_id",
                "form_schema": "$form_schema",
            },
        },
    },
    "save_answer": {
        "name": "Save Answer",
        "description": "Saves the user's answer to a question.",
        "response_format": {
            "type": "toolUsed",
            "message": {
                "action": "Answer saved",
                "param": "$question_id",
            },
            "detail": {
                "question_id": "$question_id",
                "question_number": "$question_number",
                "answer_text": "$answer_text",
            },
        },
    },
    "read_answers": {
        "name": "Read Answers",
        "description": "Retrieves all previously saved answers.",
        "response_format": {
            "type": "toolUsed",
            "message": {
                "action": "Retrieved answers",
                "param": "",
            },
            "detail": {
                "answers_count": "$answers_count",
                "answers": "$answers",
            },
        },
    },
    "review_and_finish_questionnaire": {
        "name": "Review and Finish Questionnaire",
        "description": "Shows the final review screen with all answers (read-only) and a Create Design button.",
        "response_format": {
            "type": "toolStart",
            "message": {
                "action": "Review and finish",
                "param": "",
            },
            "detail": {
                "form_type": "$form_type",
                "form_schema": "$form_schema",
                "submit_label": "$submit_label",
                "read_only": "$read_only",
            },
        },
    },
}
