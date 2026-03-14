"""
Theme Generation Activities with LiteLLM and MCP calls.

Generates themes using:
1. Brand DNA data
2. WGSN trends via MCP (color_pantone_trend_search)
3. User requirements and prompts
"""

import json
import logging
import os
from typing import Any, Dict
from uuid import UUID

import litellm
from pydantic import BaseModel, Field
from temporalio import activity

from config.settings import loaded_config
from themes.service import ThemeService
from themes.schemas import (
    ThemeGenerationOutput,
    ThemesGenerationOutput,
    ThemeBriefsOutput,
)
from utils.token_tracking import track_litellm_usage

logger = logging.getLogger(__name__)


# =============================================================================
# Model Configuration
# =============================================================================

DEFAULT_MODEL = "gpt-5.2"
REASONING_HIGH = {"effort": "high", "summary": "auto"}
REASONING_MEDIUM = {"effort": "medium", "summary": "auto"}
REASONING_LOW = {"effort": "low", "summary": "auto"}


# =============================================================================
# MCP Tool Configurations
# =============================================================================

MCP_TREND_ANALYSIS_TOOL = [{
    "type": "mcp",
    "server_label": "Night_Eye_Trend_Analysis",
    "server_url": "https://api.fexz0.de/service/nighteye/mcp",
    "allowed_tools": [
        "wgsn_edited_trend_search",
        "fashion_books_similarity_search",
        "color_pantone_trend_search"
    ],
    "require_approval": "never"
}]


# =============================================================================
# System Prompts
# =============================================================================

THEME_BRIEFS_PROMPT = """
You are a Fashion Theme Strategist creating DISTINCT theme directions for a collection.

YOUR TASK:
Generate theme briefs that are conceptually DIFFERENT from each other.

DISTINCTIVENESS RULES (CRITICAL):
1. Each theme MUST have a different mood (e.g., one energetic, one calm, one dramatic)
2. Each theme MUST have a different color family (e.g., one warm, one cool, one neutral)
3. Each theme MUST have a different aesthetic direction (e.g., one minimal, one maximal, one heritage)
4. NO two themes should feel like variations of the same idea

FOR EACH THEME BRIEF, PROVIDE:
- theme_name: Creative, evocative name (2-4 words)
- theme_slug: kebab-case identifier
- core_concept: 50-100 words describing the theme's essence
- key_differentiator: One sentence on what makes THIS theme unique from the others
- color_direction_hint: General color family direction (NOT specific codes)
- mood_keywords: 3-5 mood descriptors
- material_direction_hint: General fabric/texture direction
- reasoning: Your thought process on why this theme is distinct

Use the user's theme prompts as starting points, but ensure the final briefs are clearly differentiated.
"""

SINGLE_THEME_GENERATION_PROMPT = """
You are a Fashion Theme Designer expanding a theme brief into complete details.

YOU ARE GIVEN:
1. A theme brief with: name, concept, differentiator, color hints, mood keywords
2. Brand DNA and identity information
3. User requirements (season, categories, region)

YOUR TASK:
Expand the brief into a complete theme with all details. Stay TRUE to the brief's direction.

RETRIEVAL MECHANICS:
1. Use `color_pantone_trend_search` MCP tool to fetch Pantone/Coloro codes.
   - Search for colors aligned with the brief's color_direction_hint
   - Extract actual pantone_codes and coloro_codes from the response

2. Use `wgsn_edited_trend_search` for trend reports matching the theme's mood and direction.

3. Use `fashion_books_similarity_search` for silhouette and fabric references.

GENERATION RULES:
- CRITICAL: Do NOT deviate from the brief's core_concept and key_differentiator
- Use MCP tools to fetch ACTUAL Pantone TCX codes (e.g., "18-1140 TCX")
- Align all details (colors, materials, silhouettes) with the brief's mood_keywords

OUTPUT SECTIONS:
1. Basic Info: theme_name, theme_slug, season_title, main_concept (150-200 words), one_line_summary, mood_tags, design_keywords, aesthetic_labels, is_aligned_to_brand_dna

2. Color Direction: primary_colors, accent_colors, neutral_colors, palette_notes, palette

3. Color Palette (from MCP): pantone_codes (actual TCX codes), coloro_codes, palette_description

4. Material & Silhouette: fabric_notes, trim_keywords, print_keywords, important_fabrics, important_silhouettes, key_silhouettes, key_trend_fabrics, print_usage_guidelines

5. Micro Trends: print_placement_trends, wash_and_finish_trends, graphic_and_icon_trends, typography_micro_trends, fit_and_proportion_trends, construction_detail_trends, accessory_and_styling_trends, other_micro_trend_signals

6. UI Suggestions: fabric_suggestions (4-6 items), trim_suggestions (4-6 items), artwork_suggestions (4-6 items)

THEME ALIGNMENT RULES:
- Themes with high brandDna weight (>50%) should be is_aligned_to_brand_dna = true
- Themes with low brandDna weight (<40%) can be is_aligned_to_brand_dna = false (experimental)
"""

# Legacy prompt for reference/fallback
THEME_GENERATION_PROMPT_LEGACY = """
You are a Fashion Theme Generation Agent for a collection planning system.

Your task is to generate detailed design themes based on:
1. Brand DNA and identity
2. User requirements (season, categories, region, competitors)
3. Theme generation weights (brandDna %, wgsn %, competitor %)
4. WGSN trend data from MCP tools

RETRIEVAL MECHANICS:
1. Use `color_pantone_trend_search` MCP tool to fetch Pantone/Coloro color codes from WGSN.
   - This is your PRIMARY source for specific color codes.
   - Extract coloro and pantone arrays from the response.

2. Use `wgsn_edited_trend_search` to fetch trend reports relevant to the season and categories.

3. Use `fashion_books_similarity_search` for silhouette and fabric references.

THEME GENERATION RULES:
- Generate themes that are distinct from each other while adhering to brand core values.
- Use the weight percentages (brandDna, wgsn, competitor) to balance influences.
- CRITICAL: Extract and include actual Pantone TCX codes (e.g., "18-1140 TCX") and Coloro codes from MCP results.

For each theme, generate:

1. **Basic Info:**
   - theme_name: Creative, evocative name (e.g., "Urban Nomad", "Coastal Drift")
   - theme_slug: kebab-case identifier (e.g., "urban-nomad")
   - season_title: Season with year (e.g., "Summer Spring 2026")
   - main_concept: Core concept paragraph (150-200 words)
   - one_line_summary: Single sentence summary
   - mood_tags: Comma-separated mood adjectives
   - design_keywords: List of design intent keywords
   - aesthetic_labels: Short aesthetic flavor labels
   - is_aligned_to_brand_dna: boolean based on alignment rules

2. **Color Direction:**
   - primary_colors: Core colors that appear most frequently
   - accent_colors: Highlight colors for pops
   - neutral_colors: Balancing tones
   - palette_notes: Usage intent notes
   - palette: Short 100-char palette sentence

3. **Color Palette (from MCP):**
   - pantone_codes: MUST use actual TCX codes from color_pantone_trend_search (e.g., ["18-1140 TCX", "19-3940 TCX"])
   - coloro_codes: MUST use actual codes from MCP (e.g., ["098-59-30"])
   - palette_description: Short description

4. **Material & Silhouette:**
   - fabric_notes, trim_keywords, print_keywords
   - important_fabrics, important_silhouettes
   - key_silhouettes, key_trend_fabrics (comma-separated, max 200 chars)
   - print_usage_guidelines

5. **Micro Trends:**
   - print_placement_trends, wash_and_finish_trends
   - graphic_and_icon_trends, typography_micro_trends
   - fit_and_proportion_trends, construction_detail_trends
   - accessory_and_styling_trends, other_micro_trend_signals

6. **UI Suggestions (Simple lists for frontend display):**
   - fabric_suggestions: 4-6 simple fabric names (e.g., ["Organic Cotton Twill", "Tencel Lyocell Jersey"])
   - trim_suggestions: 4-6 simple trim names (e.g., ["Wooden Buttons", "Handwoven Tassels"])
   - artwork_suggestions: 4-6 simple artwork names (e.g., ["Block Print Motif", "Shibori Tie-Dye"])

THEME ALIGNMENT RULES:
- Themes with high brandDna weight (>50%) should be is_aligned_to_brand_dna = true
- Themes with low brandDna weight (<40%) can be is_aligned_to_brand_dna = false (experimental)
"""


# =============================================================================
# Activities
# =============================================================================

@activity.defn
async def generate_themes_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate themes using LiteLLM with MCP tools.

    Input state:
        - collection_id: UUID of the collection
        - user_req: User request payload with themes requirements
        - brand_dna: Brand DNA data (fetched from brand service)
        - theme_ids: List of placeholder theme IDs

    Output state:
        - themes_data: Generated themes data
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    collection_id = state["collection_id"]
    user_req = state["user_req"]
    brand_dna = state.get("brand_dna", {})
    theme_requirements = user_req.get("themes", [])
    theme_ids = state.get("theme_ids", [])

    activity.logger.info(f"Starting theme generation for collection_id={collection_id}")

    # Build generation prompt
    num_themes = len(theme_requirements)

    theme_guidance = "\n".join([
        f"Theme {i+1} Requirements:\n"
        f"  - Focus/Prompt: {theme.get('prompt', 'General theme exploration')}\n"
        f"  - Brand DNA Weight: {theme.get('brandDna', 40)}% (How much to align with brand identity)\n"
        f"  - WGSN Trends Weight: {theme.get('wgsn', 40)}% (How much to consider WGSN trend reports)\n"
        f"  - Competitor Weight: {theme.get('competitor', 20)}% (How much to consider competitor analysis)\n"
        for i, theme in enumerate(theme_requirements)
    ])

    # Build season title
    season = user_req.get("season", "").replace("-", " ").title()
    target_year = user_req.get("target_year", "")
    season_title = f"{season} {target_year}".strip()

    generation_prompt = f"""
Brand Information:
- Brand Name: {user_req.get('brand_name', 'Unknown')}
- Brand Type: {user_req.get('brand_type', 'regular')}
- Brand Website: {user_req.get('brand_website', '')}

Target Market:
- Season: {season_title}
- Country: {user_req.get('country', '')}
- Region: {user_req.get('region', '')}

Categories:
{json.dumps(user_req.get('categories', []), indent=2)}

Competitors:
{json.dumps(user_req.get('competitors', []), indent=2)}

Brand DNA:
{json.dumps(brand_dna, indent=2) if brand_dna else "Not available"}

Number of Themes to Generate: {num_themes}

Theme Requirements:
{theme_guidance}

Generate {num_themes} distinct themes following the requirements above.
Use the MCP tools to fetch actual Pantone/Coloro codes and trend data.
"""

    try:
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=generation_prompt,
            instructions=THEME_GENERATION_PROMPT_LEGACY,
            tools=MCP_TREND_ANALYSIS_TOOL,
            text_format=ThemesGenerationOutput,
            reasoning=REASONING_HIGH,
            store=True,
        )

        if response.error:
            raise RuntimeError(f"LLM API error: {response.error}")

        result = ThemesGenerationOutput.model_validate_json(response.output_text)

        # Track token usage
        track_litellm_usage(state, "generate_themes", response, DEFAULT_MODEL)

        # Store each theme
        for idx, theme_data in enumerate(result.themes):
            if idx < len(theme_ids):
                theme_id = UUID(theme_ids[idx]) if isinstance(theme_ids[idx], str) else theme_ids[idx]
                await ThemeService.update_theme_with_generated_data(
                    theme_id=theme_id,
                    generated_data=theme_data,
                )

        # Update references for all themes
        if result.references:
            for theme_id in theme_ids:
                tid = UUID(theme_id) if isinstance(theme_id, str) else theme_id
                await ThemeService.update_references(tid, result.references)

        state["themes_data"] = [t.model_dump() for t in result.themes]
        state["references"] = result.references

        activity.logger.info(f"Theme generation completed for collection_id={collection_id}")

    except Exception as e:
        activity.logger.error(f"Theme generation failed: {e}")
        raise

    return state


@activity.defn
async def update_themes_completed_activity(state: Dict[str, Any]) -> None:
    """Mark all themes as completed."""
    collection_id = UUID(state.get("collection_id"))
    theme_ids = state.get("theme_ids", [])

    for theme_id in theme_ids:
        tid = UUID(theme_id) if isinstance(theme_id, str) else theme_id
        await ThemeService.update_theme_status(tid, "completed")

    activity.logger.info(f"Themes marked as completed for collection: {collection_id}")


@activity.defn
async def update_themes_failed_activity(state: Dict[str, Any]) -> None:
    """Mark all themes as failed."""
    collection_id = UUID(state.get("collection_id"))

    await ThemeService.mark_themes_failed(collection_id)

    activity.logger.info(f"Themes marked as failed for collection: {collection_id}")


# =============================================================================
# Phase 1 Activity: Generate Theme Briefs
# =============================================================================

@activity.defn
async def generate_theme_briefs_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1: Generate distinct theme briefs.

    Single LLM call to create N distinct briefs with explicit differentiation.
    No MCP calls here - save those for Phase 2.

    Input state:
        - collection_id: UUID of the collection
        - user_req: User request payload with themes requirements
        - brand_dna: Brand DNA data
        - theme_ids: List of placeholder theme IDs

    Output state:
        - briefs: List of ThemeBrief data (one per theme)
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    collection_id = state["collection_id"]
    user_req = state["user_req"]
    brand_dna = state.get("brand_dna", {})
    theme_requirements = user_req.get("themes", [])
    theme_ids = state.get("theme_ids", [])

    activity.logger.info(
        f"Phase 1: Generating theme briefs for collection_id={collection_id}, "
        f"num_themes={len(theme_requirements)}"
    )

    num_themes = len(theme_requirements)

    # Build theme requirements guidance
    theme_guidance = "\n".join([
        f"Theme {i+1}:\n"
        f"  - User Prompt: {theme.get('prompt', 'General theme exploration')}\n"
        f"  - Brand DNA Weight: {theme.get('brandDna', 40)}%\n"
        f"  - WGSN Trends Weight: {theme.get('wgsn', 40)}%\n"
        f"  - Competitor Weight: {theme.get('competitor', 20)}%\n"
        for i, theme in enumerate(theme_requirements)
    ])

    # Build season title
    season = user_req.get("season", "").replace("-", " ").title()
    target_year = user_req.get("target_year", "")
    season_title = f"{season} {target_year}".strip()

    generation_prompt = f"""
Brand: {user_req.get('brand_name', 'Unknown')}
Season: {season_title}
Country: {user_req.get('country', '')}
Region: {user_req.get('region', '')}

Brand DNA Summary:
{json.dumps(brand_dna.get('core_values_and_voice', {}), indent=2) if brand_dna else "Not available"}

Number of Themes to Generate: {num_themes}

Theme Requirements from User:
{theme_guidance}

Generate {num_themes} DISTINCT theme briefs. Each brief must be clearly different from the others.
Explain in distinctiveness_rationale how each theme differs.
"""

    try:
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=generation_prompt,
            instructions=THEME_BRIEFS_PROMPT,
            text_format=ThemeBriefsOutput,
            reasoning=REASONING_MEDIUM,
            store=True,
        )

        if response.error:
            raise RuntimeError(f"LLM API error: {response.error}")

        result = ThemeBriefsOutput.model_validate_json(response.output_text)

        # Track token usage
        track_litellm_usage(state, "generate_theme_briefs", response, DEFAULT_MODEL)

        # Map briefs to theme_ids
        briefs_with_ids = []
        for idx, brief in enumerate(result.briefs):
            if idx < len(theme_ids):
                briefs_with_ids.append({
                    "theme_id": theme_ids[idx],
                    "brief": brief.model_dump(),
                })

        state["briefs"] = briefs_with_ids
        state["distinctiveness_rationale"] = result.distinctiveness_rationale

        activity.logger.info(
            f"Phase 1 completed: Generated {len(briefs_with_ids)} distinct briefs "
            f"for collection_id={collection_id}"
        )

    except Exception as e:
        activity.logger.error(f"Phase 1 failed: {e}")
        raise

    return state


# =============================================================================
# Phase 2 Activity: Generate Single Theme Details
# =============================================================================

@activity.defn
async def generate_single_theme_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 2: Generate full theme details from a brief.

    One activity per theme, runs in parallel with other themes.
    Uses MCP tools for this specific theme's color/trend research.

    Input params:
        - theme_id: UUID of the theme
        - brief: ThemeBrief data
        - user_req: User request payload
        - brand_dna: Brand DNA data
        - collection_id: For logging

    Output:
        - success: bool
        - theme_id: str
        - error: str (if failed)
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    theme_id = params["theme_id"]
    brief = params["brief"]
    user_req = params["user_req"]
    brand_dna = params.get("brand_dna", {})
    collection_id = params.get("collection_id", "unknown")

    activity.logger.info(
        f"Phase 2: Generating details for theme_id={theme_id}, "
        f"theme_name={brief.get('theme_name', 'unknown')}"
    )

    # Build season title
    season = user_req.get("season", "").replace("-", " ").title()
    target_year = user_req.get("target_year", "")
    season_title = f"{season} {target_year}".strip()

    generation_prompt = f"""
THEME BRIEF TO EXPAND:
- Theme Name: {brief.get('theme_name')}
- Core Concept: {brief.get('core_concept')}
- Key Differentiator: {brief.get('key_differentiator')}
- Color Direction: {brief.get('color_direction_hint')}
- Mood Keywords: {', '.join(brief.get('mood_keywords', []))}
- Material Direction: {brief.get('material_direction_hint')}

BRAND INFORMATION:
- Brand Name: {user_req.get('brand_name', 'Unknown')}
- Brand Type: {user_req.get('brand_type', 'regular')}

TARGET MARKET:
- Season: {season_title}
- Country: {user_req.get('country', '')}
- Region: {user_req.get('region', '')}

CATEGORIES:
{json.dumps(user_req.get('categories', []), indent=2)}

BRAND DNA:
{json.dumps(brand_dna, indent=2) if brand_dna else "Not available"}

Expand this brief into a complete theme. Use MCP tools to fetch actual Pantone/Coloro codes
that align with the color direction hint: "{brief.get('color_direction_hint')}".

Stay true to the brief's core concept and key differentiator.
"""

    try:
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=generation_prompt,
            instructions=SINGLE_THEME_GENERATION_PROMPT,
            tools=MCP_TREND_ANALYSIS_TOOL,
            text_format=ThemeGenerationOutput,
            reasoning=REASONING_HIGH,
            store=True,
        )

        if response.error:
            raise RuntimeError(f"LLM API error: {response.error}")

        result = ThemeGenerationOutput.model_validate_json(response.output_text)

        # Track token usage
        track_litellm_usage(params, "generate_single_theme", response, DEFAULT_MODEL)

        # Save to database
        theme_uuid = UUID(theme_id) if isinstance(theme_id, str) else theme_id
        await ThemeService.update_theme_with_generated_data(
            theme_id=theme_uuid,
            generated_data=result,
        )

        activity.logger.info(
            f"Phase 2 completed: theme_id={theme_id}, theme_name={result.theme_name}"
        )

        return {
            "success": True,
            "theme_id": str(theme_id),
            "theme_name": result.theme_name,
        }

    except Exception as e:
        activity.logger.error(f"Phase 2 failed for theme_id={theme_id}: {e}")

        # Update theme status to failed
        try:
            theme_uuid = UUID(theme_id) if isinstance(theme_id, str) else theme_id
            await ThemeService.update_theme_status(theme_uuid, "failed")
        except Exception as db_error:
            activity.logger.error(f"Failed to update theme status: {db_error}")

        return {
            "success": False,
            "theme_id": str(theme_id),
            "error": str(e),
        }
