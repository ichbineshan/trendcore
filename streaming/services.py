import json
import uuid
from typing import AsyncGenerator

from config.logging import logger
from config.settings import loaded_config
from streaming.serializers import QuestionSchema, StreamEventType
from streaming.utils import format_stream_event
from threads.models import Task
from threads.services import ThreadService
from threads.dao import TaskDAO
from utils.connection_handler import ConnectionHandler


class StreamingService:
    """Service for handling streaming AI responses."""

    def __init__(self, connection_handler: ConnectionHandler):
        self.connection_handler = connection_handler
        self.thread_service = ThreadService(connection_handler)
        self.task_dao = TaskDAO(connection_handler.session)

    async def generate_streaming_response(
        self,
        question_schema: QuestionSchema,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming AI response."""
        thread_id = None
        user_message_id = None
        task_id = None

        try:
            logger.info("Starting streaming response", message=question_schema.message)

            # Step 1: Create or get thread
            if not question_schema.thread_id:
                thread = await self.thread_service.create_thread(
                    request=type('CreateThreadRequest', (), {
                        'title': question_schema.message[:50],
                        'meta': question_schema.metadata,
                    })(),
                    user_id="anonymous",
                    org_id="default",
                    user_email="anonymous@example.com",
                )
                thread_id = thread.id
                yield format_stream_event(
                    StreamEventType.THREAD_CREATED,
                    "Thread created",
                    thread_id=str(thread_id),
                )
            else:
                thread_id = question_schema.thread_id
                await self.thread_service.get_thread(thread_id)

            # Step 2: Create user message
            user_message = await self.thread_service.create_message(
                request=type('CreateMessageRequest', (), {
                    'role': 'user',
                    'content': {'text': question_schema.message},
                    'parent_message_id': question_schema.parent_message_id,
                    'prompt_details': {},
                    'images': question_schema.images or [],
                    'user_query': question_schema.message,
                    'metadata': question_schema.metadata or {},
                })(),
                thread_id=thread_id,
            )
            user_message_id = user_message.id

            yield format_stream_event(
                StreamEventType.USER_MESSAGE_CREATED,
                "User message created",
                message_id=str(user_message_id),
                thread_id=str(thread_id),
            )

            # Step 3: Create task
            task = Task(
                id=uuid.uuid4(),
                thread_id=thread_id,
                status="pending",
            )
            await self.task_dao.create_task(task)
            await self.connection_handler.session_commit()
            task_id = task.id

            yield format_stream_event(
                StreamEventType.STREAM_START,
                "Starting AI response",
                thread_id=str(thread_id),
            )

            # Step 4: Get thread metadata to check if it's a questionnaire
            thread = await self.thread_service.get_thread(thread_id)
            # Ensure thread.meta is initialized
            if thread.meta is None:
                thread.meta = {}

            is_questionnaire = thread.meta.get('type') == 'collection_brief'

            # Initialize collection brief metadata if this is a new questionnaire thread
            if is_questionnaire and 'current_question' not in thread.meta:
                thread.meta['current_question'] = 1
                thread.meta['answers'] = {}
                thread.meta['completed'] = False
                await self.thread_service.update_thread_meta(thread_id, thread.meta)

            # Select appropriate agent
            if is_questionnaire:
                from agents.collection_brief_agent import create_collection_brief_agent
                agent_executor = create_collection_brief_agent(thread.meta)

                # Stream agent execution with tool calls
                accumulated_content = ""
                async for event in agent_executor.astream_events(
                    {"input": question_schema.message},
                    version="v1",
                ):
                    event_type = event.get("event")

                    # Tool start - emit tool call with arguments
                    if event_type == "on_tool_start":
                        tool_name = event.get("name")
                        tool_input = event.get("data", {}).get("input", {})

                        yield format_stream_event(
                            StreamEventType.TOOL_CALL,
                            json.dumps({
                                "tool": tool_name,
                                "arguments": tool_input
                            }),
                            thread_id=str(thread_id),
                        )

                    # Tool end - handle save_answer to update thread
                    elif event_type == "on_tool_end":
                        tool_name = event.get("name")
                        tool_output = event.get("data", {}).get("output", {})

                        # If save_answer was called, update thread metadata
                        if tool_name == "save_answer" and isinstance(tool_output, dict):
                            thread = await self.thread_service.get_thread(thread_id)
                            # Ensure thread.meta is initialized
                            if thread.meta is None:
                                thread.meta = {}
                            current_num = thread.meta.get('current_question', 1)
                            answers = thread.meta.get('answers', {})

                            # Save the answer
                            question_id = tool_output.get('question_id')
                            question_number = tool_output.get('question_number')
                            answer_text = tool_output.get('answer_text')

                            if question_id:
                                from agents.questionnaire import get_question_by_id
                                question = get_question_by_id(question_id)

                                answers[question_id] = {
                                    'question_number': question_number,
                                    'question_title': question.get('title', '') if question else '',
                                    'answer_text': answer_text,
                                    'timestamp': str(user_message.created_at) if user_message.created_at else None
                                }

                                # Move to next question or mark complete
                                if question_number >= 10:
                                    thread.meta['completed'] = True
                                else:
                                    thread.meta['current_question'] = question_number + 1

                                thread.meta['answers'] = answers
                                await self.thread_service.update_thread_meta(thread_id, thread.meta)

                        yield format_stream_event(
                            StreamEventType.TOOL_RESULT,
                            json.dumps(tool_output),
                            thread_id=str(thread_id),
                        )

                    # Chat model stream - text chunks
                    elif event_type == "on_chat_model_stream":
                        chunk_data = event.get("data", {}).get("chunk")
                        if chunk_data:
                            content = getattr(chunk_data, 'content', '')
                            if content:
                                accumulated_content += content
                                yield format_stream_event(
                                    StreamEventType.CONTENT_CHUNK,
                                    content,
                                    thread_id=str(thread_id),
                                )

                # Create assistant message
                assistant_message = await self.thread_service.create_message(
                    request=type('CreateMessageRequest', (), {
                        'role': 'assistant',
                        'content': {'text': accumulated_content},
                        'parent_message_id': user_message_id,
                        'prompt_details': {},
                        'images': [],
                        'user_query': None,
                        'metadata': {},
                    })(),
                    thread_id=thread_id,
                )

            else:
                # Regular agent (non-questionnaire)
                from agents.registry import get_agent
                agent = get_agent("trend_analysis")

                accumulated_content = ""
                async for chunk in agent.astream({"input": question_schema.message}):
                    if isinstance(chunk, str):
                        accumulated_content += chunk
                        yield format_stream_event(
                            StreamEventType.CONTENT_CHUNK,
                            chunk,
                            thread_id=str(thread_id),
                        )
                    elif isinstance(chunk, dict) and "content" in chunk:
                        content_chunk = chunk["content"]
                        accumulated_content += content_chunk
                        yield format_stream_event(
                            StreamEventType.CONTENT_CHUNK,
                            content_chunk,
                            thread_id=str(thread_id),
                        )

                # Create assistant message
                assistant_message = await self.thread_service.create_message(
                    request=type('CreateMessageRequest', (), {
                        'role': 'assistant',
                        'content': {'text': accumulated_content},
                        'parent_message_id': user_message_id,
                        'prompt_details': {},
                        'images': [],
                        'user_query': None,
                        'metadata': {},
                    })(),
                    thread_id=thread_id,
                )

            # Update task status
            await self.task_dao.update_task_status(task_id, "completed")

            await self.connection_handler.session_commit()

            yield format_stream_event(
                StreamEventType.STREAM_COMPLETE,
                "Response complete",
                thread_id=str(thread_id),
                message_id=str(assistant_message.id),
            )

            logger.info("Streaming completed", thread_id=str(thread_id))

        except Exception as e:
            logger.error("Streaming error", error=str(e), thread_id=str(thread_id) if thread_id else None)

            if task_id:
                try:
                    await self.task_dao.update_task_status(task_id, "failed")
                    await self.connection_handler.session_commit()
                except:
                    pass

            error_event = {
                "type": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "content": "An error occurred during streaming",
            }
            yield f"{loaded_config.stream_token}: {json.dumps(error_event)}\n"

        finally:
            yield format_stream_event(StreamEventType.STREAM_END, "")
