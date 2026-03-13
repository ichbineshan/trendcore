"""
Collection Brief Questionnaire API
"""

from uuid import UUID
from fastapi import Depends

from threads.services import ThreadService
from utils.common import ResponseData, handle_exceptions
from utils.connection_handler import ConnectionHandler, get_connection_handler_for_app_dependency


@handle_exceptions("Failed to start collection brief", [])
async def start_collection_brief(
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app_dependency),
):
    """
    Start a new collection brief questionnaire.

    Creates a thread with questionnaire metadata. Use the streaming chat API
    to conduct the interview - the agent will guide through all 10 questions.
    """
    thread_service = ThreadService(connection_handler)

    # Create thread with collection brief metadata
    thread = await thread_service.create_thread(
        request=type('CreateThreadRequest', (), {
            'title': 'Collection Brief Questionnaire',
            'meta': {
                'type': 'collection_brief',
                'current_question': 1,
                'answers': {},
                'completed': False
            },
        })(),
        user_id="anonymous",
        org_id="default",
        user_email="anonymous@example.com",
    )

    return ResponseData.model_construct(
        success=True,
        data={
            "thread_id": str(thread.id),
            "message": "Collection brief questionnaire started. Use the streaming chat API with this thread_id to begin.",
            "instructions": "Send your first message to start the interview. The agent will guide you through 10 questions."
        }
    )


@handle_exceptions("Failed to get questionnaire status", [])
async def get_questionnaire_status(
    thread_id: UUID,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app_dependency),
):
    """Get the current status of a collection brief questionnaire."""
    thread_service = ThreadService(connection_handler)
    thread = await thread_service.get_thread(thread_id)

    if not thread or not thread.meta or thread.meta.get('type') != 'collection_brief':
        raise ValueError("Invalid collection brief thread")

    return ResponseData.model_construct(
        success=True,
        data={
            "thread_id": str(thread_id),
            "current_question": thread.meta.get('current_question', 1),
            "total_questions": 10,
            "completed": thread.meta.get('completed', False),
            "answers_count": len(thread.meta.get('answers', {})),
            "answers": thread.meta.get('answers', {})
        }
    )
