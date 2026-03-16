"""
Moodboard Image Generation Activities.

Activities for generating moodboard collage and element images
using Vertex AI with rate limiting and backoff.
"""

import asyncio
import logging
import random
from typing import Any
from uuid import UUID

from google.genai.errors import ClientError
from temporalio import activity

from collection.service import CollectionService
from moodboard.service import MoodboardService
from utils.nano_banana import VertexAIImageGenerator

logger = logging.getLogger(__name__)

# =============================================================================
# Rate Limiting Configuration
# =============================================================================

PROACTIVE_DELAY_SECONDS = 10
BACKOFF_INITIAL_DELAY = 60
BACKOFF_MULTIPLIER = 1.5
BACKOFF_MAX_RETRIES = 12
BACKOFF_MAX_DELAY = 180

# =============================================================================
# Model Configuration
# =============================================================================

PRIMARY_MODEL_ID = "gemini-3.1-flash-image-preview"
FALLBACK_MODEL_ID = "gemini-2.5-flash-image"

# =============================================================================
# Guardrail Prompt
# =============================================================================

COLLAGE_GUARDRAIL_PROMPT = (
    "Create a high-quality, professional moodboard collage. "
    "STRICTLY FOLLOW THIS DESCRIPTION: {prompt}. "
    "DO NOT deviate from the details provided. "
    "The output MUST be a moodboard collage, not a single standalone image or any other type of visualization. "
    "CRITICAL TEXT REQUIREMENTS: If any text is mentioned in the description, it MUST be generated with PERFECT accuracy. "
    "All text must be clear, legible, properly spelled, and exactly as specified in the description. "
    "ABSOLUTELY NO text distortion, warping, blurring, artifacts, or errors shall be entertained. "
    "Text must have clean edges, proper kerning, and be pixel-perfect. "
    "If you cannot generate text accurately, DO NOT include distorted text - omit it entirely."
)

COLLECTION_HERO_PROMPT = (
    "Create a high-quality, professional fashion collection hero/banner image. "
    "Collection Name: {collection_name}. "
    "Collection Description: {overview}. "
    "The image should visually represent the essence, mood, and aesthetic of this fashion collection. "
    "Create a visually striking, editorial-style image that captures the collection's theme, color palette, and target aesthetic. "
    "The image should be suitable for use as a hero banner on a fashion e-commerce or brand website. "
    "DO NOT include any text in the image. Focus purely on visual representation of the collection's mood and style."
)


# =============================================================================
# Helper Functions
# =============================================================================

async def generate_image_with_backoff(
    generator: VertexAIImageGenerator,
    prompt: str,
    aspect_ratio: str = "16:9",
    image_size: str = "1K",
) -> tuple[str | None, dict]:
    """
    Generate image with exponential backoff on rate limit errors.

    Handles Vertex AI rate limiting (10 images/min) by retrying with
    exponential backoff when 429 errors occur.

    Backoff configuration:
        - Initial delay: 60 seconds (full quota reset cycle)
        - Multiplier: 1.5x per retry
        - Max retries: 12
        - Max delay cap: 180 seconds
        - Jitter: 0-15 seconds random addition (spreads concurrent retries)

    Model fallback:
        - On 400 INVALID_ARGUMENT: Switch to fallback model
        - On 429: Retry with backoff using same model

    Args:
        generator: VertexAIImageGenerator instance.
        prompt: Image generation prompt.
        aspect_ratio: Aspect ratio for the image (default: "16:9").
        image_size: Resolution - "1K", "2K", or "4K" (default: "1K").

    Returns:
        Tuple of (cdn_url, usage_dict).

    Raises:
        ClientError: If all retries are exhausted or non-recoverable error occurs.
    """
    current_generator = generator

    for attempt in range(BACKOFF_MAX_RETRIES):
        try:
            cdn_url, usage = await current_generator.generate_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            )
            return cdn_url, usage

        except ClientError as e:
            if e.code == 400:
                # INVALID_ARGUMENT - likely model deprecated or unsupported params
                if current_generator.model_id != FALLBACK_MODEL_ID:
                    logger.warning(
                        f"Got 400 INVALID_ARGUMENT with model {current_generator.model_id}. "
                        f"Falling back to {FALLBACK_MODEL_ID}"
                    )
                    current_generator = VertexAIImageGenerator(model_id=FALLBACK_MODEL_ID)
                    continue
                else:
                    # Fallback model also failed with 400
                    logger.error(
                        f"Fallback model {FALLBACK_MODEL_ID} also returned 400. "
                        f"Prompt: {prompt[:100]}..."
                    )
                    raise

            if e.code != 429:
                raise

            if attempt == BACKOFF_MAX_RETRIES - 1:
                logger.error(
                    f"Max retries ({BACKOFF_MAX_RETRIES}) exhausted for image generation. "
                    f"Prompt: {prompt[:100]}..."
                )
                raise

            delay = min(
                BACKOFF_INITIAL_DELAY * (BACKOFF_MULTIPLIER ** attempt),
                BACKOFF_MAX_DELAY,
            )
            jitter = random.uniform(0, 15)
            total_delay = delay + jitter

            logger.warning(
                f"Rate limited (attempt {attempt + 1}/{BACKOFF_MAX_RETRIES}). "
                f"Retrying in {total_delay:.1f}s. Prompt: {prompt[:50]}..."
            )
            await asyncio.sleep(total_delay)

    return "", {}


# =============================================================================
# Activities
# =============================================================================

@activity.defn
async def fetch_moodboard_data_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch moodboard data and update status to generating.

    Args:
        params: {"moodboard_id": str}

    Returns:
        {
            "success": True,
            "moodboard_id": str,
            "collage_prompt": str,
            "element_prompts": list[str],
        }
    """
    moodboard_id = UUID(params["moodboard_id"])

    try:
        moodboard = await MoodboardService.get_by_id(moodboard_id)
        if not moodboard:
            raise ValueError(f"Moodboard not found: {moodboard_id}")

        # Update status to generating
        await MoodboardService.update_status(moodboard_id, "generating")

        activity.logger.info(
            f"Fetched moodboard data: {moodboard_id}, "
            f"elements: {len(moodboard.element_prompts or [])}"
        )

        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
            "collage_prompt": moodboard.collage_prompt or "",
            "element_prompts": moodboard.element_prompts or [],
        }

    except Exception as e:
        logger.error(
            f"Failed to fetch moodboard data: {e}",
            extra={"moodboard_id": str(moodboard_id)},
        )
        raise


@activity.defn
async def generate_collage_image_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Generate collage image for moodboard.

    Args:
        params: {
            "moodboard_id": str,
            "collage_prompt": str,
        }

    Returns:
        {"success": True, "collage_image_url": str}
    """
    moodboard_id = UUID(params["moodboard_id"])
    collage_prompt = params["collage_prompt"]

    if not collage_prompt:
        activity.logger.warning(f"No collage prompt for moodboard: {moodboard_id}")
        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
            "collage_image_url": None,
        }

    try:
        generator = VertexAIImageGenerator(model_id=PRIMARY_MODEL_ID)

        # Apply guardrail prompt
        guardrailed_prompt = COLLAGE_GUARDRAIL_PROMPT.format(prompt=collage_prompt)

        activity.logger.info(f"Generating collage image for moodboard: {moodboard_id}")

        cdn_url, usage = await generate_image_with_backoff(
            generator=generator,
            prompt=guardrailed_prompt,
            aspect_ratio="16:9",
            image_size="2K",
        )

        activity.logger.info(f"Generated collage image: {cdn_url}")

        # Save to database
        await MoodboardService.update_collage_image_url(moodboard_id, cdn_url)

        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
            "collage_image_url": cdn_url,
            "usage": usage,
        }

    except Exception as e:
        logger.error(
            f"Failed to generate collage image: {e}",
            extra={"moodboard_id": str(moodboard_id)},
        )
        raise


@activity.defn
async def generate_element_images_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Generate element images for moodboard sequentially.

    Args:
        params: {
            "moodboard_id": str,
            "element_prompts": list[str],
        }

    Returns:
        {"success": True, "element_image_urls": list[str], "generated_count": int}
    """
    moodboard_id = UUID(params["moodboard_id"])
    element_prompts = params.get("element_prompts", [])

    if not element_prompts:
        activity.logger.warning(f"No element prompts for moodboard: {moodboard_id}")
        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
            "element_image_urls": [],
            "generated_count": 0,
        }

    try:
        generator = VertexAIImageGenerator(model_id=PRIMARY_MODEL_ID)
        element_image_urls = []
        total_usage = []

        for i, element_prompt in enumerate(element_prompts):
            activity.logger.info(
                f"Generating element {i + 1}/{len(element_prompts)} for moodboard: {moodboard_id}"
            )

            # Proactive delay between images (except first)
            if i > 0:
                activity.logger.info(f"Waiting {PROACTIVE_DELAY_SECONDS}s before next image...")
                await asyncio.sleep(PROACTIVE_DELAY_SECONDS)

            cdn_url, usage = await generate_image_with_backoff(
                generator=generator,
                prompt=element_prompt,
                aspect_ratio="16:9",
                image_size="1K",
            )

            activity.logger.info(f"Generated element image {i + 1}: {cdn_url}")

            if cdn_url:
                element_image_urls.append(cdn_url)
                total_usage.append(usage)

        # Save all element URLs to database
        await MoodboardService.update_element_image_urls(moodboard_id, element_image_urls)

        activity.logger.info(
            f"Generated {len(element_image_urls)} element images for moodboard: {moodboard_id}"
        )

        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
            "element_image_urls": element_image_urls,
            "generated_count": len(element_image_urls),
        }

    except Exception as e:
        logger.error(
            f"Failed to generate element images: {e}",
            extra={"moodboard_id": str(moodboard_id)},
        )
        raise


@activity.defn
async def mark_images_completed_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Mark moodboard image generation as completed.

    Args:
        params: {"moodboard_id": str}

    Returns:
        {"success": True}
    """
    moodboard_id = UUID(params["moodboard_id"])

    try:
        await MoodboardService.update_status(moodboard_id, "completed")

        activity.logger.info(f"Marked moodboard images as completed: {moodboard_id}")

        return {"success": True}

    except Exception as e:
        logger.error(
            f"Failed to mark moodboard as completed: {e}",
            extra={"moodboard_id": str(moodboard_id)},
        )
        raise


@activity.defn
async def mark_images_failed_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Mark moodboard image generation as failed.

    Args:
        params: {"moodboard_id": str}

    Returns:
        {"success": True}
    """
    moodboard_id = UUID(params["moodboard_id"])

    try:
        await MoodboardService.update_status(moodboard_id, "failed")

        activity.logger.warning(f"Marked moodboard images as failed: {moodboard_id}")

        return {"success": True}

    except Exception as e:
        logger.error(
            f"Failed to mark moodboard as failed: {e}",
            extra={"moodboard_id": str(moodboard_id)},
        )
        raise


# =============================================================================
# Collection Image Activities
# =============================================================================

@activity.defn
async def fetch_collection_data_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch collection data for image generation.

    Args:
        params: {"collection_id": str}

    Returns:
        {
            "success": True,
            "collection_id": str,
            "collection_name": str,
            "overview": str,
        }
    """
    collection_id = UUID(params["collection_id"])

    try:
        collection = await CollectionService.get_collection_by_id(collection_id)
        if not collection:
            raise ValueError(f"Collection not found: {collection_id}")

        activity.logger.info(
            f"Fetched collection data: {collection_id}, "
            f"name: {collection.collection_name}"
        )

        return {
            "success": True,
            "collection_id": str(collection_id),
            "collection_name": collection.collection_name or "",
            "overview": collection.overview or "",
        }

    except Exception as e:
        logger.error(
            f"Failed to fetch collection data: {e}",
            extra={"collection_id": str(collection_id)},
        )
        raise


@activity.defn
async def generate_collection_image_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Generate hero/banner image for collection.

    Args:
        params: {
            "collection_id": str,
            "collection_name": str,
            "overview": str,
        }

    Returns:
        {"success": True, "image_url": str}
    """
    collection_id = UUID(params["collection_id"])
    collection_name = params.get("collection_name", "")
    overview = params.get("overview", "")

    if not collection_name and not overview:
        activity.logger.warning(f"No collection data for image generation: {collection_id}")
        return {
            "success": True,
            "collection_id": str(collection_id),
            "image_url": None,
        }

    try:
        generator = VertexAIImageGenerator(model_id=PRIMARY_MODEL_ID)

        # Build prompt using collection data
        prompt = COLLECTION_HERO_PROMPT.format(
            collection_name=collection_name,
            overview=overview,
        )

        activity.logger.info(f"Generating hero image for collection: {collection_id}")

        cdn_url, usage = await generate_image_with_backoff(
            generator=generator,
            prompt=prompt,
            aspect_ratio="16:9",
            image_size="1K",
        )

        activity.logger.info(f"Generated collection hero image: {cdn_url}")

        return {
            "success": True,
            "collection_id": str(collection_id),
            "image_url": cdn_url,
            "usage": usage,
        }

    except Exception as e:
        logger.error(
            f"Failed to generate collection image: {e}",
            extra={"collection_id": str(collection_id)},
        )
        raise


@activity.defn
async def save_collection_image_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Save generated image URL to collection.

    Args:
        params: {"collection_id": str, "image_url": str}

    Returns:
        {"success": True}
    """
    collection_id = UUID(params["collection_id"])
    image_url = params.get("image_url")

    if not image_url:
        activity.logger.warning(f"No image URL to save for collection: {collection_id}")
        return {"success": True}

    try:
        await CollectionService.update_collection_image_url(collection_id, image_url)

        activity.logger.info(f"Saved image URL for collection: {collection_id}")

        return {"success": True}

    except Exception as e:
        logger.error(
            f"Failed to save collection image URL: {e}",
            extra={"collection_id": str(collection_id)},
        )
        raise
