"""
Agent Registry

Centralized registry for all agents in the trend analysis system.
"""

from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from config.settings import loaded_config
from config.logging import logger


class AgentRegistry:
    """Registry for managing agents."""

    _agents: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, agent: Any):
        """Register an agent."""
        cls._agents[name] = agent
        logger.info(f"Agent registered: {name}")

    @classmethod
    def get(cls, name: str) -> Any:
        """Get an agent by name."""
        if name not in cls._agents:
            raise ValueError(f"Agent '{name}' not found in registry")
        return cls._agents[name]

    @classmethod
    def list_agents(cls) -> list:
        """List all registered agents."""
        return list(cls._agents.keys())


def create_trend_analysis_agent():
    """
    Create a basic trend analysis agent using OpenAI GPT.

    This is a simple single-agent implementation that can be enhanced later.
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    # Create the LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=loaded_config.openai_api_key,
        temperature=0.7,
        streaming=True,
    )

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful trend analysis assistant.
You help users analyze trends, patterns, and insights from data.
Provide clear, actionable insights and recommendations."""),
        ("human", "{input}"),
    ])

    # Create the chain
    chain = prompt | llm | StrOutputParser()

    return chain


def initialize_agents():
    """Initialize and register all agents."""
    logger.info("Initializing agents...")

    # Register trend analysis agent
    trend_agent = create_trend_analysis_agent()
    AgentRegistry.register("trend_analysis", trend_agent)

    logger.info(f"Agents initialized: {AgentRegistry.list_agents()}")


def get_agent(name: str = "trend_analysis"):
    """
    Get an agent by name.

    Args:
        name: Name of the agent to retrieve

    Returns:
        The requested agent
    """
    return AgentRegistry.get(name)


# Initialize agents on module import
initialize_agents()
