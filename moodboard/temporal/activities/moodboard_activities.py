"""
Moodboard Generation Activities with LiteLLM.

Activities for generating moodboard collage prompts and element prompts.
Uses web search for reference image discovery.
"""

import json
import os
from typing import Any
from uuid import UUID

import litellm
from temporalio import activity

from config.logging import logger
from config.settings import loaded_config
from collection_dna.moodboard.service import MoodboardService
from collection_dna.moodboard.schemas import MoodboardCollageOutput, MoodboardElementsOutput
from utils.token_tracking import track_litellm_usage


# =============================================================================
# Model Configuration
# =============================================================================

DEFAULT_MODEL = "gpt-5.2"
REASONING_LOW = {"effort": "low", "summary": "auto"}

WEB_SEARCH_TOOL = {
    "type": "web_search_preview",
    "search_context_size": "medium",
    "user_location": {"type": "approximate"}
}


# =============================================================================
# System Prompts
# =============================================================================

MOODBOARD_COLLAGE_PROMPT = """You are part of a larger Trend Report Agent.

Trend Report Agent creates personalised trend reports with launch strategies for any fashion brand.

Your task is to create the descriptions of moodboards for the theme, stories and categories mentioned in the user prompt.

Look at the of the brand dna and brand categories details which will provide the boundaries of inspiration. Look at the predicted upcoming trends in the trend prediction to understand upcoming themes, motifs, silhouettes, color palettes, trims, print directions etc. Use these information to search for inspirational images from both brand website, wgsn websites, instagram, pinterest etc to make a moodboard description. Make sure to bring all the image links for each moodboard and save as reference visuals.

A fashion mood board is a collage. A visual summary of inspirational images, objects, material swatches, trims, or product examples that explain the concept and feeling of your brand, collection, or customer. It is basically a brain dump of whatever you are inspired by. The inspiration can be a theme, a place, a color scheme, a material story, or entirely functional, based on the activity of your customer.

To indicate the importance of the pics you can work with size. The more essential pics can be bigger in size and the less important ones a bit smaller. Add colors, fonts, materials swatches to create a balance. It should feel comfortable to the eye and remember, we see things from top left, to the right, then down left towards right. Another way is to focus from the center of the board, outward. You can also group related pictures for a stronger impact.

How to create a Fashion Moodboard?
1. Colour palette
Colour choices need to be clearly identified through the use of swatches or images. These can be in the form of fabrics, paint shade cards.
2. Fabric and texture
Fabrics that you've chosen during the research period should be displayed on your board.
Include, trimmings, prints and any other embellishments also.
3. Theme reference research
Ground the moodboards based on the themes mentioned in the trend research report. Stay true to it. Do not deviate or modify any elements of the theme. Make sure to stay true to the brand's identity and core values.

Create a detailed description of 1 moodboard for the theme mentioned in the user prompt. Make sure to describe each element and their placement in detail. Make sure that the moodboard description is in great detail. Each element of the moodboard and placement of the element must be described in detail.

Explain the layout of the moodboard first, then for each item in the moodboard explain its position and the element itself. Add so much detail so that nothing can be left for imagination.

Generate moodboard_slug from the generated moodboard content.
Get the theme_slug from the Theme data in the input.
"""


MOODBOARD_ELEMENTS_PROMPT = """You are a Fashion Moodboard Image Generator Agent.

You get an input that is a description of moodboard for a fashion brand. Each moodboard consists of multiple elements.

Your task is to take the description of the moodboard, given as an input, and split it into 10 or less image descriptions of each element. Do not add any extra information or extra elements. Stick to the description of the moodboard.

Convert the moodboard description into a list of descriptions of single elements of moodboard.

Each element description should be detailed enough to generate a standalone image that represents that specific part of the moodboard.

Make sure that moodboard slug that is part of the moodboard description is maintained as it is in the output."""


# =============================================================================
# Activities
# =============================================================================

@activity.defn
async def create_moodboard_record_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Create a ThemeMoodboard record in the database.

    Args:
        params: {"theme_id": str}

    Returns:
        {"success": True, "moodboard_id": str}
    """
    theme_id = UUID(params["theme_id"])

    try:
        moodboard_id = await MoodboardService.create_moodboard(theme_id)

        logger.info(
            f"Created moodboard record: {moodboard_id}",
            extra={"theme_id": str(theme_id)},
        )

        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
        }

    except Exception as e:
        logger.error(
            f"Failed to create moodboard record: {e}",
            extra={"theme_id": str(theme_id)},
        )
        raise


@activity.defn
async def generate_collage_prompt_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Generate moodboard collage description using LiteLLM with web search.

    Args:
        params: {
            "moodboard_id": str,
            "theme_id": str,
            "theme_data": dict,
            "brand_dna": dict,
            "brand_special_requests": str,
            "target_categories": list,
            "brand_category_details": dict,
            "competitors_string": str,
        }

    Returns:
        {"success": True, "moodboard_slug": str, "collage_prompt": str}
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    moodboard_id = UUID(params["moodboard_id"])
    theme_id = params["theme_id"]
    theme_data = params.get("theme_data", {})
    brand_dna = params.get("brand_dna", {})

    try:
        # Build generation prompt
        input_prompt = f"""Brand DNA:
{json.dumps(brand_dna, indent=2)}

Brand Special Request:
{params.get("brand_special_requests", "")}

Target Categories:
{json.dumps(params.get("target_categories", []), indent=2)}

Available Brand Categories:
{json.dumps(params.get("brand_category_details", {}), indent=2)}

Theme for Moodboard:
{json.dumps(theme_data, indent=2)}

Competitor Details:
{params.get("competitors_string", "")}

Generate a detailed moodboard description for this theme.
Make sure to add moodboard_slug and theme_slug values properly in the response."""

        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=input_prompt,
            instructions=MOODBOARD_COLLAGE_PROMPT,
            tools=[WEB_SEARCH_TOOL],
            text_format=MoodboardCollageOutput,
            reasoning=REASONING_LOW,
            store=True,
        )

        if response.error:
            raise RuntimeError(f"LLM API error: {response.error}")

        result = MoodboardCollageOutput.model_validate_json(response.output_text)

        # Track token usage
        state = {}
        track_litellm_usage(state, "moodboard_collage", response, DEFAULT_MODEL)

        # Parse reference images (comma-separated string to list)
        reference_images = [
            img.strip()
            for img in result.reference_images.split(",")
            if img.strip()
        ]

        # Update database
        await MoodboardService.update_collage_data(
            moodboard_id=moodboard_id,
            moodboard_slug=result.moodboard_slug,
            collage_prompt=result.moodboard,
            collage_reference_images=reference_images,
        )

        logger.info(
            f"Generated collage prompt for moodboard: {moodboard_id}",
            extra={
                "theme_id": theme_id,
                "moodboard_slug": result.moodboard_slug,
                "reference_images_count": len(reference_images),
            },
        )

        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
            "moodboard_slug": result.moodboard_slug,
            "collage_prompt": result.moodboard,
        }

    except Exception as e:
        logger.error(
            f"Failed to generate collage prompt: {e}",
            extra={"moodboard_id": str(moodboard_id), "theme_id": theme_id},
        )
        raise


@activity.defn
async def split_into_elements_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Split moodboard collage description into individual element prompts.

    Args:
        params: {
            "moodboard_id": str,
            "moodboard_slug": str,
            "collage_prompt": str,
        }

    Returns:
        {"success": True, "element_count": int}
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    moodboard_id = UUID(params["moodboard_id"])
    moodboard_slug = params["moodboard_slug"]
    collage_prompt = params["collage_prompt"]

    try:
        input_prompt = f"""Mood Board Description:
{collage_prompt}

Moodboard Slug: {moodboard_slug}

Split this moodboard description into individual element descriptions (up to 10 elements)."""

        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=input_prompt,
            instructions=MOODBOARD_ELEMENTS_PROMPT,
            text_format=MoodboardElementsOutput,
            reasoning=REASONING_LOW,
            store=True,
        )

        if response.error:
            raise RuntimeError(f"LLM API error: {response.error}")

        result = MoodboardElementsOutput.model_validate_json(response.output_text)

        # Track token usage
        state = {}
        track_litellm_usage(state, "moodboard_elements", response, DEFAULT_MODEL)

        # Update database
        await MoodboardService.update_element_prompts(
            moodboard_id=moodboard_id,
            element_prompts=result.elements,
        )

        logger.info(
            f"Split moodboard into {len(result.elements)} elements",
            extra={
                "moodboard_id": str(moodboard_id),
                "element_count": len(result.elements),
            },
        )

        return {
            "success": True,
            "moodboard_id": str(moodboard_id),
            "element_count": len(result.elements),
        }

    except Exception as e:
        logger.error(
            f"Failed to split into elements: {e}",
            extra={"moodboard_id": str(moodboard_id)},
        )
        raise


@activity.defn
async def mark_moodboard_completed_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Mark a moodboard as completed.

    Args:
        params: {"moodboard_id": str}

    Returns:
        {"success": True}
    """
    moodboard_id = UUID(params["moodboard_id"])

    try:
        await MoodboardService.mark_completed(moodboard_id)

        logger.info(
            f"Marked moodboard as completed: {moodboard_id}",
            extra={"moodboard_id": str(moodboard_id)},
        )

        return {"success": True}

    except Exception as e:
        logger.error(
            f"Failed to mark moodboard as completed: {e}",
            extra={"moodboard_id": str(moodboard_id)},
        )
        raise


@activity.defn
async def mark_moodboard_failed_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Mark a moodboard as failed.

    Args:
        params: {"moodboard_id": str} or {"theme_id": str}

    Returns:
        {"success": True}
    """
    moodboard_id = params.get("moodboard_id")
    theme_id = params.get("theme_id")

    try:
        if moodboard_id:
            await MoodboardService.mark_failed(UUID(moodboard_id))
            logger.warning(
                f"Marked moodboard as failed: {moodboard_id}",
                extra={"moodboard_id": moodboard_id},
            )
        elif theme_id:
            await MoodboardService.mark_failed_by_theme_id(UUID(theme_id))
            logger.warning(
                f"Marked moodboard as failed for theme: {theme_id}",
                extra={"theme_id": theme_id},
            )

        return {"success": True}

    except Exception as e:
        logger.error(
            f"Failed to mark moodboard as failed: {e}",
            extra={"moodboard_id": moodboard_id, "theme_id": theme_id},
        )
        raise
