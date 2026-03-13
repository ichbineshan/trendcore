"""
Trend Analysis Agent

Single agent implementation for trend analysis using LangChain.
"""

from typing import AsyncGenerator, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from config.settings import loaded_config
from config.logging import logger


class TrendAnalysisAgent:
    """
    Trend Analysis Agent using LangChain.

    This agent specializes in analyzing trends and providing insights.
    """

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=loaded_config.anthropic_api_key,
            temperature=0.7,
            streaming=True,
        )

        self.system_prompt = """You are an expert trend analysis assistant.

Your capabilities include:
- Analyzing data trends and patterns
- Providing actionable insights
- Making data-driven recommendations
- Explaining complex trends in simple terms

Always be clear, concise, and helpful in your responses."""

    async def astream(self, message: HumanMessage) -> AsyncGenerator[Dict[str, str], None]:
        """
        Stream responses from the agent.

        Args:
            message: The human message to process

        Yields:
            Dict containing content chunks
        """
        logger.info(f"Trend agent processing message")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message.content},
        ]

        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield {"content": chunk.content}

    def invoke(self, message: str) -> str:
        """
        Synchronously invoke the agent.

        Args:
            message: The message to process

        Returns:
            The agent's response
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message},
        ]

        response = self.llm.invoke(messages)
        return response.content
