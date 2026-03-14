"""
Collection Generation Activities with LiteLLM calls.
"""

import json
import logging
import os
from typing import Any, Dict
from uuid import UUID

import litellm
from pydantic import BaseModel
from temporalio import activity

from config.settings import loaded_config
from collection.service import CollectionService
from utils.token_tracking import track_litellm_usage

logger = logging.getLogger(__name__)

# ============================================================================
# Model Configuration
# ============================================================================

DEFAULT_MODEL = "gpt-5.2"
REASONING_MEDIUM = {"effort": "medium", "summary": "auto"}


# ============================================================================
# Pydantic Schemas for LLM Output
# ============================================================================

class RangeOverviewStats(BaseModel):
    categories: int
    styles: int
    themes: int


class RangeOverviewItem(BaseModel):
    category: str
    brick: str
    style_fit: str
    num_styles: int
    price_range: str


class RangeOverview(BaseModel):
    stats: RangeOverviewStats
    items: list[RangeOverviewItem]


class CollectionOverviewSchema(BaseModel):
    collection_name: str
    overview: str
    range_overview: RangeOverview


# ============================================================================
# System Prompt
# ============================================================================

GENERATE_OVERVIEW_PROMPT = """You are a fashion collection strategist and creative director.

Given the collection details below, generate:

1. **collection_name**: A creative, evocative name for the collection (e.g., "Breezy Resortwear", "Urban Nomad", "Coastal Drift"). Should reflect the season, target market, and overall aesthetic.

2. **overview**: A compelling narrative paragraph (150-200 words) describing the collection. Include:
   - The inspiration and mood of the collection
   - Target customer persona
   - Key design elements and aesthetic direction
   - How it bridges occasion and everyday wear
   - Positioning against competitors

3. **range_overview**: A structured breakdown with:
   - **stats**: Count of categories, estimated total styles, and number of themes
   - **items**: For each category/brick combination, provide:
     - category: The segment name (e.g., "Womenswear", "Menswear")
     - brick: The specific product type (e.g., "Kurtas & Kurtis", "Co-ord Sets")
     - style_fit: Recommended silhouettes and fits (e.g., "Straight Cut · A-Line · High-Low")
     - num_styles: Estimated number of styles for this brick
     - price_range: Format as "₹{{startPrice}}-₹{{endPrice}}"

Use the categories, themes, season, target year, and brand information from the input to inform your response.

INPUT:
{user_req}
"""


# ============================================================================
# Activities
# ============================================================================

@activity.defn
async def generate_overview_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate collection overview using LiteLLM.

    Input: state["user_req"]
    Output: state["collection_name"], state["overview"], state["range_overview"]
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    user_req = state["user_req"]
    user_req_str = json.dumps(user_req, indent=2)

    activity.logger.info(f"Starting generate_overview_activity for collection_id={state.get('collection_id')}")

    response = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=GENERATE_OVERVIEW_PROMPT.format(user_req=user_req_str),
        text_format=CollectionOverviewSchema,
        reasoning=REASONING_MEDIUM,
    )

    if response.error:
        raise RuntimeError(f"LLM API error: {response.error}")

    result = CollectionOverviewSchema.model_validate_json(response.output_text)

    state["collection_name"] = result.collection_name
    state["overview"] = result.overview
    state["range_overview"] = result.range_overview.model_dump()

    track_litellm_usage(state, "generate_overview", response, DEFAULT_MODEL)

    activity.logger.info(f"generate_overview_activity completed for collection_id={state.get('collection_id')}")

    return state


@activity.defn
async def update_collection_completed_activity(state: Dict[str, Any]) -> None:
    """Update collection record with generated data and set status to completed."""
    collection_id = UUID(state.get("collection_id"))

    # Update overview fields
    await CollectionService.update_collection_overview(
        collection_id=collection_id,
        collection_name=state.get("collection_name"),
        overview=state.get("overview"),
        range_overview=state.get("range_overview"),
    )

    # Update status to completed
    await CollectionService.update_collection_status(
        collection_id=collection_id,
        status="completed",
    )

    activity.logger.info(f"Collection updated to completed: {collection_id}")


@activity.defn
async def update_collection_failed_activity(state: Dict[str, Any]) -> None:
    """Update collection status to failed."""
    collection_id = UUID(state.get("collection_id"))

    await CollectionService.update_collection_status(
        collection_id=collection_id,
        status="failed",
    )

    activity.logger.info(f"Collection updated to failed: {collection_id}")
