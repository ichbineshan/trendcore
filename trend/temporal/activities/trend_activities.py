"""
Trend Activities for Temporal Workflow.

Independent LiteLLM calls for category_trends and trend_spotting.
Does NOT depend on agent_workflows module.
"""

import json
import os
from typing import Any
from uuid import UUID

import litellm
from pydantic import BaseModel, Field
from temporalio import activity

from config.logging import logger
from config.settings import loaded_config
from utils.token_tracking import track_litellm_usage


# =============================================================================
# Model Configuration
# =============================================================================

DEFAULT_MODEL = "gpt-5.2"
REASONING_HIGH = {"effort": "high", "summary": "auto"}
REASONING_LOW = {"effort": "low", "summary": "auto"}


# =============================================================================
# MCP Tool Configurations
# =============================================================================

# Google Trends MCP
MCP_GOOGLE_TRENDS_TOOL = {
    "type": "mcp",
    "server_label": "google_trends",
    "server_url": "https://api.fexz0.de/service/nighteye/mcp",
    "allowed_tools": [
        "get_interest_by_region_based_on_query",
        "get_related_trending_queries",
        "get_interest_over_a_timeperiod"
    ],
    "require_approval": "never"
}

# Macro/Micro Trend MCP
MCP_MACRO_MICRO_TREND_TOOL = {
    "type": "mcp",
    "server_label": "macro_micro_trend_server",
    "server_url": "https://api.fexz0.de/service/nighteye/mcp",
    "allowed_tools": ["macro_micro_trend"],
    "require_approval": "never"
}

# Ahrefs MCP
MCP_AHREFS_TOOL = {
    "type": "mcp",
    "server_label": "ahrefs",
    "server_url": "https://api.fexz0.de/service/nighteye/mcp",
    "allowed_tools": [
        "keywords_explorer_overview",
        "keywords_explorer_related_terms",
        "keywords_explorer_volume_history"
    ],
    "require_approval": "never"
}

# Web search tool
WEB_SEARCH_TOOL = {
    "type": "web_search_preview",
    "search_context_size": "medium",
    "user_location": {"type": "approximate"}
}


# =============================================================================
# Pydantic Schemas for Category Trends
# =============================================================================

class CategoryDesignLanguage(BaseModel):
    trims: str
    fabric: str
    silhouette: str
    modesty_level: str
    print_and_graphics: str


class CategoryVisualIdentity(BaseModel):
    visual_notes: str
    accent_colors: list[str]
    dominant_colors: list[str]


class CategoryMicroTrendsStatic(BaseModel):
    styling: str
    placement: str


class CategoryStaticSpec(BaseModel):
    category_design_language: CategoryDesignLanguage
    category_visual_identity: CategoryVisualIdentity
    category_micro_trends_static: CategoryMicroTrendsStatic


class PrintOverview(BaseModel):
    print_style_tags: list[str]
    print_techniques: list[str]
    primary_print_families: list[str]
    secondary_print_families: list[str]


class MicroTrendTags(BaseModel):
    color_micro_trends: list[str]
    print_micro_trends: list[str]
    detail_micro_trends: list[str]
    placement_micro_trends: list[str]


class MotifVocabularyItem(BaseModel):
    scale: str
    density: str
    colorways: str
    motif_type: str
    edge_treatment: str
    spacing_pattern: str
    motif_description: str


class ColorStoryAnalysis(BaseModel):
    contrast_behaviors: list[str]
    colorblocking_notes: str
    common_print_colors: list[str]
    dominant_base_colors: list[str]


class TextAndLogoPatterns(BaseModel):
    logo_styles: list[str]
    typography_approaches: list[str]
    common_text_placements: list[str]


class ConstructionAndDetails(BaseModel):
    print_cutoff_patterns: str
    border_and_trim_patterns: list[str]
    feature_placement_strategies: list[str]


class PrintPlacementPatternsItem(BaseModel):
    side: str
    zone: str
    notes: str
    orientation: str
    coverage_description: str
    alignment_with_garment: str


class CategoryVisualAnalysis(BaseModel):
    print_overview: PrintOverview
    micro_trend_tags: MicroTrendTags
    motif_vocabulary: list[MotifVocabularyItem]
    color_story_analysis: ColorStoryAnalysis
    category_trend_summary: str
    text_and_logo_patterns: TextAndLogoPatterns
    construction_and_details: ConstructionAndDetails
    print_placement_patterns: list[PrintPlacementPatternsItem]


class CategoryItem(BaseModel):
    name: str
    theme_slug: str
    gender: str
    age_range: str
    category_static_spec: CategoryStaticSpec
    category_visual_analysis: CategoryVisualAnalysis


class CategoryTrendsOutput(BaseModel):
    categories: list[CategoryItem]


# =============================================================================
# Pydantic Schemas for Trend Spotting
# =============================================================================

class MetricItem(BaseModel):
    label: str
    value: int | float | str | None
    formatted: str
    description: str | None = None


class TopSearchItem(BaseModel):
    term: str
    searches: str
    trend: str
    buyer_intent: str


class CommercialSummary(BaseModel):
    market_size: str
    market_size_value: str
    growth_trend: str
    commercial_potential: str
    confidence: str


class CommercialMetrics(BaseModel):
    monthly_searches: MetricItem
    audience_reach: MetricItem
    buyer_intent: MetricItem
    ad_value: MetricItem


class CommercialValidation(BaseModel):
    summary: CommercialSummary
    metrics: CommercialMetrics
    top_searches: list[TopSearchItem]
    data_date: str | None = None
    error: str | None = None


class TrendItem(BaseModel):
    trend_name: str
    concept: str
    focus_items: list[str]
    key_takeaways: list[str]
    market_validation: list[str]
    mood: str


class EnrichedTrendItem(BaseModel):
    trend_name: str
    concept: str
    focus_items: list[str]
    key_takeaways: list[str]
    market_validation: list[str]
    commercial_validation: CommercialValidation
    mood: str


class TrendSpottingOutput(BaseModel):
    season: str
    trends: list[TrendItem]


class EnrichedTrendSpottingOutput(BaseModel):
    season: str
    trends: list[EnrichedTrendItem]


# =============================================================================
# System Prompts
# =============================================================================

CATEGORY_TRENDS_PROMPT = """You are a trend analysing agent. Your role is to create category level design inspirations based on:
1. Brand Identity
2. Target Categories or Brand Categories
3. Provided Theme and design directions (silhouette, print, colour etc)

Make sure you strictly adhere to the provided details while generating design inspirations for the categories mentioned in the user prompt.

If there are no target categories mentioned, use the brand's categories information mentioned in input. Extract 1 or more categories. Not more than 5 top categories.

Make sure that category specific design inspirations are different from each other while adhering to Brand's Core Design Values and adhering to the core theme.

Play around with the attributes of the clothing item like:
- Silhouettes
- Colors
- Prints and Patterns and their placement
- Lengths of different parts - sleeves, legs etc
- Necklines, cuts, visible stitching methods etc
- Fabric and techniques.

Pay attention to brand guidelines - what the brand should do and shouldn't do.

OUTPUT: Generate category-level design specifications with:
- category_static_spec: Design language, visual identity, micro trends
- category_visual_analysis: Print overview, motif vocabulary, color story, placement patterns
"""


TREND_SPOTTING_PROMPT = """You are a Trend Analysis agent.
Your task is to use the provided `google_trends` MCP tools and the `macro_micro_trend` MCP tool to understand the upcoming trends for the brand and target categories.

RETRIEVAL MECHANICS:
1. Use `macro_micro_trend` tool to fetch trend hierarchy data.
2. Use `google_trends` tools to validate keywords with real search data.

OUTPUT FORMAT:
Return structured JSON with:
{
  "season": "Spring-Summer 2026 (India)",
  "trends": [
    {
      "trend_name": "Trend Name",
      "concept": "Description of the trend concept...",
      "focus_items": ["item1", "item2", "item3"],
      "mood": "Mood description...",
      "market_validation": ["Google Trends data point 1...", "Data point 2..."],
      "key_takeaways": ["Takeaway 1", "Takeaway 2"]
    }
  ]
}

RULES:
1. Include specific numbers from Google Trends in market_validation.
2. Set region as worldwide for Google Trends.
3. Report trends honestly (rising, stable, or declining).
"""


AHREFS_ENRICHMENT_PROMPT = """You are a Commercial Data Enrichment agent.
Your task is to add commercial validation data from Ahrefs to trend analysis.

For each trend, use Ahrefs tools to get:
- volume: Monthly search volume
- traffic_potential: Estimated traffic
- cpc: Cost per click (commercial value indicator)

OUTPUT FORMAT - Add commercial_validation to each trend:
{
  "summary": {
    "market_size": "Medium",  // High (>50K), Medium (10K-50K), Low (1K-10K), Niche (<1K)
    "market_size_value": "15.4K",
    "growth_trend": "Rising",  // Rising, Stable, Declining
    "commercial_potential": "High",  // Based on CPC
    "confidence": "Strong"  // Strong (3+ keywords), Moderate (1-2), Limited (no data)
  },
  "metrics": {
    "monthly_searches": {"label": "Monthly Searches", "value": 15400, "formatted": "15.4K", "description": "..."},
    "audience_reach": {"label": "Potential Audience", "value": 22000, "formatted": "22K", "description": "..."},
    "buyer_intent": {"label": "Buyer Intent", "value": "Commercial", "formatted": "Commercial", "description": "..."},
    "ad_value": {"label": "Advertising Value", "value": 1.85, "formatted": "$1.85/click", "description": "..."}
  },
  "top_searches": [
    {"term": "keyword", "searches": "8.5K/mo", "trend": "↑", "buyer_intent": "High"}
  ],
  "data_date": "March 2026"
}

RULES:
1. DO NOT modify existing fields (trend_name, concept, etc.)
2. ONLY ADD the commercial_validation field
3. Format numbers with K for thousands
"""


# =============================================================================
# Helper Functions
# =============================================================================

def create_empty_commercial_validation(error_message: str = None) -> dict:
    """Create an empty commercial validation object for fallback scenarios."""
    return {
        "summary": {
            "market_size": "Unknown",
            "market_size_value": "N/A",
            "growth_trend": "Unknown",
            "commercial_potential": "Unknown",
            "confidence": "Limited"
        },
        "metrics": {
            "monthly_searches": {
                "label": "Monthly Searches",
                "value": 0,
                "formatted": "N/A",
                "description": "How often people search for related terms"
            },
            "audience_reach": {
                "label": "Potential Audience",
                "value": 0,
                "formatted": "N/A",
                "description": "Estimated monthly visitors if ranking well"
            },
            "buyer_intent": {
                "label": "Buyer Intent",
                "value": "Unknown",
                "formatted": "Unknown",
                "description": "Search intent classification"
            },
            "ad_value": {
                "label": "Advertising Value",
                "value": 0,
                "formatted": "N/A",
                "description": "What advertisers pay - indicates commercial interest"
            }
        },
        "top_searches": [],
        "data_date": None,
        "error": error_message
    }


# =============================================================================
# Activities
# =============================================================================

@activity.defn
async def create_theme_trend_record_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Create a ThemeTrend record in the database.

    Args:
        params: {"theme_id": str}

    Returns:
        {"success": True, "theme_trend_id": str}
    """
    from trend.service import ThemeTrendService

    theme_id = UUID(params["theme_id"])

    try:
        theme_trend_id = await ThemeTrendService.create_theme_trend(theme_id)

        logger.info(
            f"Created theme trend record: {theme_trend_id}",
            extra={"theme_id": str(theme_id)},
        )

        return {
            "success": True,
            "theme_trend_id": str(theme_trend_id),
        }

    except Exception as e:
        logger.error(
            f"Failed to create theme trend record: {e}",
            extra={"theme_id": str(theme_id)},
        )
        raise


@activity.defn
async def run_category_trends_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Run category trends generation using LiteLLM.

    Args:
        params: {
            "theme_id": str,
            "theme_data": dict,
            "brand_dna": dict,
            "brand_special_requests": str,
            "target_categories": list,
            "brand_category_details": dict,
            "target_region": str,
            "target_age": str,
            "target_gender": str,
            "brand_classification": dict,
        }

    Returns:
        {"success": True, "categories": list}
    """
    from trend.service import ThemeTrendService

    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    theme_id = UUID(params["theme_id"])
    theme_data = params.get("theme_data", {})
    brand_dna = params.get("brand_dna", {})

    try:
        # Build prompt for category trends
        prompt = f"""Brand Requirements:

Brand's Special Requests:
{params.get("brand_special_requests", "")}

Target Categories:
{json.dumps(params.get("target_categories", []), indent=2)}

Brand's Available Categories Information:
{json.dumps(params.get("brand_category_details", {}), indent=2)}

Region: {params.get("target_region", "")}
Age: {params.get("target_age", "")}
Gender: {params.get("target_gender", "")}

Brand Class: {params.get("brand_classification", {}).get("brand_class", "A1")}

Brand DNA:
{json.dumps(brand_dna, indent=2)}

Theme Details:
{json.dumps(theme_data, indent=2)}

Generate category-level design specifications for this theme."""

        # Call LiteLLM
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=prompt,
            instructions=CATEGORY_TRENDS_PROMPT,
            text_format=CategoryTrendsOutput,
            reasoning=REASONING_HIGH,
            store=True,
        )

        if response.error:
            raise RuntimeError(f"LLM API error: {response.error}")

        result = CategoryTrendsOutput.model_validate_json(response.output_text)
        category_data = {"categories": [cat.model_dump() for cat in result.categories]}

        # Track token usage
        state = {}
        track_litellm_usage(state, "category_trends", response, DEFAULT_MODEL)

        # Save to database
        await ThemeTrendService.update_category_trends(theme_id, category_data)

        logger.info(
            f"Category trends completed for theme: {theme_id}",
            extra={
                "theme_id": str(theme_id),
                "category_count": len(category_data["categories"]),
            },
        )

        return {
            "success": True,
            "categories": category_data["categories"],
        }

    except Exception as e:
        logger.error(
            f"Category trends failed: {e}",
            extra={"theme_id": str(theme_id)},
        )
        raise


@activity.defn
async def run_trend_spotting_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Run trend spotting using LiteLLM with Google Trends + Ahrefs.

    Two-stage pipeline:
    1. Google Trends + WGSN for market validation
    2. Ahrefs for commercial validation

    Args:
        params: {
            "theme_id": str,
            "themes_string": str,
            "brand_dna": dict,
            "target_categories": list,
        }

    Returns:
        {"success": True, "trend_spotting": dict}
    """
    from trend.service import ThemeTrendService

    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    theme_id = UUID(params["theme_id"])
    themes_string = params.get("themes_string", "")
    brand_dna = params.get("brand_dna", {})
    target_categories = params.get("target_categories", [])

    try:
        # Stage 1: Google Trends + WGSN
        stage1_prompt = f"""Target Categories:
{json.dumps(target_categories, indent=2)}

Predicted Trends:
{themes_string}

Brand DNA:
{json.dumps(brand_dna, indent=2)}

Analyze trends using Google Trends and macro/micro trend data."""

        trendspotting_tools = [WEB_SEARCH_TOOL, MCP_GOOGLE_TRENDS_TOOL, MCP_MACRO_MICRO_TREND_TOOL]

        response_stage1 = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=stage1_prompt,
            instructions=TREND_SPOTTING_PROMPT,
            tools=trendspotting_tools,
            text_format=TrendSpottingOutput,
            reasoning=REASONING_LOW,
            store=True,
        )

        if response_stage1.error:
            raise RuntimeError(f"Stage 1 LLM API error: {response_stage1.error}")

        stage1_result = TrendSpottingOutput.model_validate_json(response_stage1.output_text)

        # Track token usage
        state = {}
        track_litellm_usage(state, "trend_spotting_stage1", response_stage1, DEFAULT_MODEL)

        # Stage 2: Ahrefs enrichment
        try:
            stage2_prompt = f"""Enrich the following trend analysis with commercial data from Ahrefs.

Stage 1 Output (Google Trends validated):
{json.dumps(stage1_result.model_dump(), indent=2)}

Target Country: worldwide (use "us" for Ahrefs queries as default)

Use the Ahrefs tools to get commercial metrics for each trend's focus_items.
Return the complete enriched trend data with commercial_validation added."""

            response_stage2 = await litellm.aresponses(
                model=DEFAULT_MODEL,
                input=stage2_prompt,
                instructions=AHREFS_ENRICHMENT_PROMPT,
                tools=[MCP_AHREFS_TOOL],
                text_format=EnrichedTrendSpottingOutput,
                reasoning=REASONING_LOW,
                store=True,
            )

            if response_stage2.error:
                raise RuntimeError(f"Stage 2 LLM API error: {response_stage2.error}")

            enriched_result = EnrichedTrendSpottingOutput.model_validate_json(
                response_stage2.output_text
            )
            trend_spotting_data = enriched_result.model_dump()

            track_litellm_usage(state, "trend_spotting_stage2", response_stage2, DEFAULT_MODEL)

        except Exception as e:
            logger.warning(f"Stage 2 (Ahrefs) failed: {e}, using Stage 1 output")
            # Fallback: Use Stage 1 output with empty commercial_validation
            enriched_trends = []
            for trend in stage1_result.trends:
                enriched_trend = {
                    **trend.model_dump(),
                    "commercial_validation": create_empty_commercial_validation(
                        f"Ahrefs enrichment failed: {str(e)}"
                    )
                }
                enriched_trends.append(enriched_trend)

            trend_spotting_data = {
                "season": stage1_result.season,
                "trends": enriched_trends
            }

        # Save to database
        await ThemeTrendService.update_trend_spotting(theme_id, trend_spotting_data)

        logger.info(
            f"Trend spotting completed for theme: {theme_id}",
            extra={"theme_id": str(theme_id)},
        )

        return {
            "success": True,
            "trend_spotting": trend_spotting_data,
        }

    except Exception as e:
        logger.error(
            f"Trend spotting failed: {e}",
            extra={"theme_id": str(theme_id)},
        )
        raise


@activity.defn
async def mark_trend_failed_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Mark a theme trend record as failed.

    Args:
        params: {"theme_id": str}

    Returns:
        {"success": True}
    """
    from trend.service import ThemeTrendService

    theme_id = UUID(params["theme_id"])

    try:
        await ThemeTrendService.mark_failed(theme_id)

        logger.warning(
            f"Marked theme trend as failed: {theme_id}",
            extra={"theme_id": str(theme_id)},
        )

        return {"success": True}

    except Exception as e:
        logger.error(
            f"Failed to mark theme trend as failed: {e}",
            extra={"theme_id": str(theme_id)},
        )
        raise
