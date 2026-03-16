"""
ResponseHandler: normalizes tool/stream events.
Handles ToolMessage in on_tool_end and produces JSON event payloads.
"""

import json
from typing import Optional

from langchain_core.messages import ToolMessage

from config.logging import get_logger
from .stream_factory import StreamHandlerFactory

logger = get_logger(__name__)


class ResponseHandler:
    def __init__(
        self,
        tools: dict = None,
        model_name: str = None,
        provider: str = None,
    ):
        self.tools = tools or {}
        self.stream_handler = StreamHandlerFactory.create_handler(
            model_name=model_name,
            provider=provider,
            name="collection_brief_agent",
        )
        self.run_id_tool_name_mapping = {}

    def _substitute_dict_values(self, obj, params: dict, content: str = None):
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = self._substitute_dict_values(value, params, content)
            return result
        elif isinstance(obj, list):
            return [self._substitute_dict_values(item, params, content) for item in obj]
        elif isinstance(obj, str):
            if content is not None and "$content" in obj:
                obj = obj.replace("$content", content)
            try:
                for key, value in params.items():
                    placeholder = f"${key}"
                    if placeholder in obj:
                        replacement = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                        obj = obj.replace(placeholder, replacement)
            except Exception:
                pass
            return obj
        return obj

    async def handle_response(self, event: dict, last_tool: str = ""):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            return self.stream_handler.handle_stream_event(event)

        if kind == "on_tool_start":
            registry = self.tools.get(event["name"])
            self.run_id_tool_name_mapping.update({event["run_id"]: event["name"]})

            if registry:
                response_format = registry.get("response_format", {}).copy()
                response_format["type"] = "toolStart"
                params = event.get("data", {}).get("input", {})
                response_format = self._substitute_dict_values(response_format, params)
                response_format["run_id"] = event.get("run_id")
                return json.dumps(response_format)

        if kind == "on_tool_end":
            output = event.get("data", {}).get("output")
            if output is not None and isinstance(output, ToolMessage):
                tool_name = self.run_id_tool_name_mapping.get(event["run_id"])
                registry = self.tools.get(tool_name)
                if registry:
                    response_format = registry.get("response_format", {}).copy()
                    response_format["type"] = "toolUsed"
                    params = event.get("data", {}).get("input", {})

                    content = None
                    if output and hasattr(output, "content"):
                        content = json.dumps(output.content) if isinstance(output.content, (dict, list)) else str(output.content)

                    response_format["call_id"] = output.tool_call_id
                    message = self._substitute_dict_values(response_format.get("message", {}), params)
                    try:
                        content_json = json.loads(content) if content else None
                    except Exception:
                        content_json = content
                    detail = self._substitute_dict_values(response_format.get("detail", {}), content_json or {}, content)
                    detail = self._substitute_dict_values(detail, params)

                    # Ensure form_schema is an object (substitution may have made it a JSON string)
                    if isinstance(detail.get("form_schema"), str):
                        try:
                            detail["form_schema"] = json.loads(detail["form_schema"])
                        except (json.JSONDecodeError, TypeError):
                            pass

                    response_format["message"] = message
                    response_format["detail"] = detail
                    response_format["run_id"] = event.get("run_id")
                    return json.dumps(response_format)
        return None
