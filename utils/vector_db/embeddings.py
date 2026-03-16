"""Embedding generation utilities using OpenAI API for vector database operations."""
import traceback

from openai import AsyncOpenAI

from config.logging import logger
from config.settings import loaded_config


class EmbeddingGenerator:
    """Generates text embeddings using OpenAI API for vector database storage and retrieval."""

    def __init__(self, api_key: str):
        """Initializes the embedding generator with an OpenAI API key.

        Args:
            api_key (str): The OpenAI API key for authentication.
        """

        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_embedding(self, text: str):
        """Generates an embedding vector for the provided text using the OpenAI API.

        Args:
            text (str): The input text to embed.

        Returns:
            List[float]: The embedding vector.

        Raises:
            SearchError: If the OpenAI API call fails.
        """

        try:
            logger.info("Embedding started")
            response = await self.client.embeddings.create(
                input=[text], model=loaded_config.embedding_model, timeout=30
            )

            # Add null checks for response validation
            if response is None:
                raise Exception("Failed to generate embedding: No response from OpenAI API")

            if response.data is None or len(response.data) == 0:
                raise Exception("Failed to generate embedding: No data in response")

            return response.data[0].embedding  # Access as an attribute, not as a dictionary

        except Exception as e:
            # Convert exception to string to avoid logging concatenation issues
            error_msg = str(e)
            logger.error(f"Error in openai embedding: {error_msg}")
            raise Exception(f"Failed to generate embedding: {error_msg}") from e
