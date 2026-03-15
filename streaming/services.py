import json
import uuid
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage

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

    async def _apply_tool_meta(self, thread_id, tool_name: str, data: dict, user_message) -> None:
        """Update thread meta from tool output (ask_question / save_answer)."""
        if not isinstance(data, dict):
            return
        if tool_name == "ask_question":
            thread = await self.thread_service.get_thread(thread_id)
            if thread.meta is None:
                thread.meta = {}
            form_schema = data.get("form_schema", data) if isinstance(data.get("form_schema"), dict) else {}
            thread.meta["current_question"] = {
                "question_id": data.get("question_id"),
                "question_number": data.get("question_number"),
                "question_title": form_schema.get("title", data.get("question_id", "")),
            }
            await self.thread_service.update_thread_meta(thread_id, thread.meta)
        elif tool_name == "save_answer":
            thread = await self.thread_service.get_thread(thread_id)
            if thread.meta is None:
                thread.meta = {}
            answers = thread.meta.get("answers", {})
            question_id = data.get("question_id")
            if question_id:
                current_question = thread.meta.get("current_question", {})
                question_title = current_question.get("question_title", question_id) if current_question.get("question_id") == question_id else question_id
                answers[question_id] = {
                    "question_number": data.get("question_number"),
                    "question_title": question_title,
                    "answer_text": data.get("answer_text", ""),
                    "timestamp": str(user_message.created_at) if getattr(user_message, "created_at", None) else None,
                }
                thread.meta["answers"] = answers
                await self.thread_service.update_thread_meta(thread_id, thread.meta)

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
            if is_questionnaire and 'answers' not in thread.meta:
                thread.meta['answers'] = {}
                await self.thread_service.update_thread_meta(thread_id, thread.meta)

            # Select appropriate agent; use Postgres checkpointer per request (same as cortex)
            if is_questionnaire:
                from collection_brief import create_collection_brief_agent
                from collection_brief.registry import tools_registry
                from agent_utils import ResponseHandler
                from streaming.retry_utils import get_async_postgres_saver_with_retry

                async with get_async_postgres_saver_with_retry(loaded_config.postgres_url) as checkpointer:
                    await checkpointer.setup()
                    agent = create_collection_brief_agent(thread.meta, checkpointer=checkpointer)
                    messages = [HumanMessage(content=question_schema.message)]
                    response_handler = ResponseHandler(
                        tools=tools_registry,
                        model_name="gpt-4o",
                    )
                    stream_config = {"configurable": {"thread_id": str(thread_id)}}

                    accumulated_content = ""
                    last_tool = ""
                    async for event in agent.astream_events(
                        {"messages": messages},
                        config=stream_config,
                        version="v1",
                    ):
                        if event.get("event") == "on_tool_start":
                            last_tool = event.get("name", "")
                        response = await response_handler.handle_response(event, last_tool)

                        if response is None:
                            continue

                        try:
                            parsed = json.loads(response)
                        except json.JSONDecodeError:
                            accumulated_content += response
                            yield format_stream_event(StreamEventType.CONTENT_CHUNK, response, thread_id=str(thread_id))
                            continue

                        event_type = parsed.get("type")
                        if event_type == "toolStart":
                            yield format_stream_event(
                                StreamEventType.TOOL_CALL,
                                json.dumps({
                                    "tool": event.get("name"),
                                    "arguments": event.get("data", {}).get("input", {}),
                                }),
                                thread_id=str(thread_id),
                            )
                        elif event_type == "toolUsed":
                            detail = parsed.get("detail", {})
                            await self._apply_tool_meta(thread_id, last_tool, detail, user_message)
                            yield format_stream_event(
                                StreamEventType.TOOL_RESULT,
                                response,
                                thread_id=str(thread_id),
                            )
                        elif event_type in ("supervisor_streaming", "streaming"):
                            content = parsed.get("content", "")
                            if content:
                                accumulated_content += content
                                yield format_stream_event(StreamEventType.CONTENT_CHUNK, content, thread_id=str(thread_id))

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
                # For non-questionnaire threads, raise an error or handle differently
                raise ValueError("Only collection_brief type threads are supported")

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
