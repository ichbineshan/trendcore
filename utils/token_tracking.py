"""
Token Usage Tracking Utilities.

Provides helpers for extracting and accumulating token usage from
OpenAI Agents SDK Runner results.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class AgentTokenUsage:
    """Token usage for a single agent run."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __add__(self, other: "AgentTokenUsage") -> "AgentTokenUsage":
        """Add two AgentTokenUsage objects together (for retries)."""
        return AgentTokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            requests=self.requests + other.requests,
            model=self.model or other.model  # Preserve model from either instance
        )


def extract_usage_from_litellm(response: Any, model: str = None) -> AgentTokenUsage:
    """
    Extract token usage from a LiteLLM response.

    Supports both:
    - acompletion() format: prompt_tokens, completion_tokens
    - aresponses() format: input_tokens, output_tokens

    Args:
        response: The response from litellm.acompletion() or litellm.aresponses()
        model: Model name (optional, extracted from response if not provided)

    Returns:
        AgentTokenUsage with extracted values
    """
    try:
        usage = response.usage

        # aresponses format uses input_tokens/output_tokens
        # acompletion format uses prompt_tokens/completion_tokens
        input_tokens = (
            getattr(usage, 'input_tokens', None) or
            getattr(usage, 'prompt_tokens', None) or 0
        )
        output_tokens = (
            getattr(usage, 'output_tokens', None) or
            getattr(usage, 'completion_tokens', None) or 0
        )
        total_tokens = getattr(usage, 'total_tokens', None) or (input_tokens + output_tokens)

        return AgentTokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            requests=1,
            model=model or getattr(response, 'model', None)
        )
    except (AttributeError, TypeError):
        return AgentTokenUsage()


def track_litellm_usage(
    state: Dict[str, Any],
    agent_name: str,
    response: Any,
    model: str = None,
    accumulate: bool = True
) -> AgentTokenUsage:
    """
    Track token usage for a LiteLLM call and store it in state.

    Args:
        state: Workflow state dict
        agent_name: Name of the agent/call
        response: The response from litellm.acompletion()
        model: Model name (optional)
        accumulate: If True, add to existing usage; if False, replace

    Returns:
        The AgentTokenUsage that was recorded
    """
    if "_token_usage" not in state:
        state["_token_usage"] = {}

    usage = extract_usage_from_litellm(response, model)

    if accumulate and agent_name in state["_token_usage"]:
        existing = AgentTokenUsage(**state["_token_usage"][agent_name])
        usage = existing + usage

    state["_token_usage"][agent_name] = usage.to_dict()
    return usage


def extract_usage_from_result(result: Any) -> AgentTokenUsage:
    """
    Extract token usage from a Runner.run() result.

    Args:
        result: The result from Runner.run()

    Returns:
        AgentTokenUsage with extracted values including model name
    """
    try:
        usage = result.context_wrapper.usage


        model = None
        if hasattr(result, 'last_agent'):
            try:
                agent = result.last_agent
                model = getattr(agent, 'model', None)
            except Exception:
                pass

        return AgentTokenUsage(
            input_tokens=getattr(usage, 'input_tokens', 0) or 0,
            output_tokens=getattr(usage, 'output_tokens', 0) or 0,
            total_tokens=getattr(usage, 'total_tokens', 0) or 0,
            requests=getattr(usage, 'requests', 0) or 0,
            model=model
        )
    except (AttributeError, TypeError):
        return AgentTokenUsage()


def track_agent_usage(
    state: Dict[str, Any],
    agent_name: str,
    result: Any,
    accumulate: bool = True
) -> AgentTokenUsage:
    """
    Track token usage for an agent and store it in state.

    Args:
        state: Workflow state dict
        agent_name: Name of the agent (e.g., 'brand_dna_visual_identity')
        result: The result from Runner.run()
        accumulate: If True, add to existing usage (for retries); if False, replace

    Returns:
        The AgentTokenUsage that was recorded
    """

    if "_token_usage" not in state:
        state["_token_usage"] = {}

    usage = extract_usage_from_result(result)

    if accumulate and agent_name in state["_token_usage"]:

        existing = AgentTokenUsage(**state["_token_usage"][agent_name])
        usage = existing + usage

    state["_token_usage"][agent_name] = usage.to_dict()
    return usage


def get_activity_token_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of token usage for the current activity.

    Args:
        state: Workflow state dict

    Returns:
        Dict with per-agent usage and totals
    """
    token_usage = state.get("_token_usage", {})

    total_input = sum(u.get("input_tokens", 0) for u in token_usage.values())
    total_output = sum(u.get("output_tokens", 0) for u in token_usage.values())
    total_tokens = sum(u.get("total_tokens", 0) for u in token_usage.values())
    total_requests = sum(u.get("requests", 0) for u in token_usage.values())

    return {
        "agents": token_usage,
        "totals": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_tokens,
            "requests": total_requests
        }
    }


def merge_token_usage(
    existing: Optional[Dict[str, Any]],
    new_usage: Dict[str, Any],
    activity_name: str
) -> Dict[str, Any]:
    """
    Merge new token usage into existing meta_data token_usage structure.

    Args:
        existing: Existing token_usage from meta_data (or None)
        new_usage: New usage dict from get_activity_token_summary()
        activity_name: Name of the activity to store under

    Returns:
        Merged token_usage dict ready to save to meta_data
    """
    if existing is None:
        existing = {"activities": {}, "totals": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}}


    existing["activities"][activity_name] = new_usage

    existing["totals"]["input_tokens"] += new_usage["totals"]["input_tokens"]
    existing["totals"]["output_tokens"] += new_usage["totals"]["output_tokens"]
    existing["totals"]["total_tokens"] += new_usage["totals"]["total_tokens"]
    existing["totals"]["requests"] += new_usage["totals"]["requests"]

    return existing


def get_model_aggregated_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate token usage by model name.

    Args:
        state: Workflow state dict

    Returns:
        Dict with per-model totals and grand totals
        {
            "by_model": {
                "gpt-5.2": {
                    "input_tokens": 5000,
                    "output_tokens": 2000,
                    "total_tokens": 7000,
                    "requests": 10
                },
                "gpt-4o": {...}
            },
            "totals": {
                "input_tokens": 7000,
                "output_tokens": 2500,
                "total_tokens": 9500,
                "requests": 13
            }
        }
    """
    token_usage = state.get("_token_usage", {})
    by_model = {}

    for agent_name, usage in token_usage.items():
        model = usage.get("model", "unknown")

        if model not in by_model:
            by_model[model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "requests": 0
            }

        by_model[model]["input_tokens"] += usage.get("input_tokens", 0)
        by_model[model]["output_tokens"] += usage.get("output_tokens", 0)
        by_model[model]["total_tokens"] += usage.get("total_tokens", 0)
        by_model[model]["requests"] += usage.get("requests", 0)


    totals = {
        "input_tokens": sum(m["input_tokens"] for m in by_model.values()),
        "output_tokens": sum(m["output_tokens"] for m in by_model.values()),
        "total_tokens": sum(m["total_tokens"] for m in by_model.values()),
        "requests": sum(m["requests"] for m in by_model.values())
    }

    return {
        "by_model": by_model,
        "totals": totals
    }
