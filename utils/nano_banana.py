"""Vertex AI Image Generator using Gemini with Vertex AI.

This module provides a reusable class for generating images using Gemini
with Vertex AI support and saving them to local storage.
"""

import logging
import uuid

import google
import google.auth.transport.requests
from google import genai
from google.api_core.exceptions import ResourceExhausted
from google.genai.types import GenerateContentConfig, ImageConfig

from config.settings import loaded_config
from file_upload.gcs_file_upload_connector import GCSFileConnector
from mcp_tools.types import AspectRatio, ImageSize

logger = logging.getLogger(__name__)


class VertexAIImageGenerator:
    """
    This class provides a simple interface to generate images from text prompts
    using Gemini with Vertex AI support.

    Attributes:
        client: The Gemini client instance.
        location: GCP region for Vertex AI.
        model_id: Model ID to use for generation.

    Example:
        >>> generator = VertexAIImageGenerator()
        >>> image_path = generator.generate_image(
        ...     prompt="A beautiful sunset over mountains",
        ...     output_filename="sunset"
        ... )
        >>> print(f"Image saved to: {image_path}")
    """

    def __init__(
        self, location: str = "global", model_id: str = "gemini-2.5-flash-image"
    ):
        """Initialize the Vertex AI Image Generator.

        Args:
            location: GCP region for Vertex AI. Defaults to "us-central1".
            model_id: The Gemini model ID to use for image generation.
                Defaults to "gemini-2.0-flash-exp".
        """
        self.location = location

        self.model_id = model_id
        self.file_upload = GCSFileConnector()
        self.project_id = loaded_config.cloud_storage_util.project_id
        self.credentials = loaded_config.cloud_storage_util.credentials

        try:

            if not self.credentials.valid:
                self.credentials.refresh(google.auth.transport.requests.Request())

            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location,
                credentials=self.credentials,
            )
            logger.info(
                f"Initialized VertexAIImageGenerator with model: {self.model_id}, "
                f"project: {self.project_id}, location: {self.location}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    async def generate_image(
        self, prompt: str, aspect_ratio: AspectRatio = "16:9", image_size: ImageSize = "1K"
    ) -> tuple[str | None, dict]:
        """Generate an image from a text prompt and save it locally.

        Args:
            prompt: The text prompt describing the image to generate.
            aspect_ratio: Aspect ratio for the image to be generated.
                Options: "16:9" (widescreen landscape), "9:16" (portrait),
                "4:3" (standard landscape), "1:1" (square).
                Defaults to "16:9".
            image_size: The resolution for the generated image.
                Options: "1K", "2K", "4K".
                Defaults to "1K".

        Returns:
            A tuple of (cdn_url, usage_dict) where:
            - cdn_url: The CDN URL of the uploaded image, or None if failed
            - usage_dict: Token usage information with keys:
                - prompt_tokens: Number of input tokens (text tokens to understand prompt)
                - image_output_tokens: Number of output tokens (tokens representing the image)
                - total_tokens: Total tokens used
                - image_count: Number of images generated
                - image_size: Resolution of generated image
                - model_id: Model used for generation

        Example:
            >>> generator = VertexAIImageGenerator()
            >>> cdn_url, usage = generator.generate_image(
            ...     prompt="A cat wearing a hat",
            ... )
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        logger.info(f"Generating image with prompt: '{prompt}'")


        usage = {
            "prompt_tokens": 0,
            "image_output_tokens": 0,
            "total_tokens": 0,
            "image_count": 0,
            "image_size": image_size,
            "model_id": self.model_id,
            "aspect_ratio": aspect_ratio
        }

        try:
            async with self.client.aio as genai_async_client:
                response = await genai_async_client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        candidate_count=loaded_config.number_of_candidate_images,
                        image_config=ImageConfig(
                            aspect_ratio=aspect_ratio,
                            image_size=image_size
                        ),
                    ),
                )

                logger.info(
                    f"Image generation response - "
                    f"candidates: {len(response.candidates)}, "
                    f"finish_reason: {response.candidates[0].finish_reason}"
                )


                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage["prompt_tokens"] = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                    usage["image_output_tokens"] = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0
                    usage["total_tokens"] = getattr(response.usage_metadata, 'total_token_count', 0) or 0
                    logger.info(
                        f"Image generation usage - prompt_tokens: {usage['prompt_tokens']}, "
                        f"image_output_tokens: {usage['image_output_tokens']}, total_tokens: {usage['total_tokens']}"
                    )

            for part in response.candidates[0].content.parts:
                if part.text:
                    logger.info(f"Generated text: {part.text}")

                elif part.inline_data:
                    image_data = part.inline_data.data
                    unique_id = uuid.uuid4().hex
                    cdn_image_link = await self.file_upload.upload(
                        bytearray(image_data),
                        f"{unique_id}_image.png",
                        "image/png",
                        "inline",
                    )
                    usage["image_count"] = 1
                    return cdn_image_link, usage

            return None, usage

        except ResourceExhausted as e:
            logger.error(
                f"RATE LIMITED: Image generation hit rate limit (429). "
                f"Details: {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            raise
