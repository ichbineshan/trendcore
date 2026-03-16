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
    ColorDirection,
    TrendNarrative,
    MicroTrends,
    MaterialAndSilhouetteDirection,
    UISuggestions,
    ColorPalette,
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

# Phase 1 Research MCP Tools
MCP_MACRO_MICRO_TREND_TOOL = [{
    "type": "mcp",
    "server_label": "macro_micro_trend_server",
    "server_url": "https://api.fexz0.de/service/nighteye/mcp",
    "allowed_tools": ["macro_micro_trend"],
    "require_approval": "never"
}]

MCP_WGSN_TOOL = [{
    "type": "mcp",
    "server_label": "Night_Eye_Trend_Analysis",
    "server_url": "https://api.fexz0.de/service/nighteye/mcp",
    "allowed_tools": ["wgsn_edited_trend_search"],
    "require_approval": "never"
}]

MCP_GOOGLE_TRENDS_TOOL = [{
    "type": "mcp",
    "server_label": "google_trends",
    "server_url": "https://api.fexz0.de/service/nighteye/mcp",
    "allowed_tools": ["get_related_trending_queries"],
    "require_approval": "never"
}]


# =============================================================================
# Phase 1 Research Output Schemas
# =============================================================================

class MacroTrendsOutput(BaseModel):
    """Output from macro/micro cultural trends research."""
    macro_trends: list[str] = Field(default_factory=list, description="Broad cultural/societal trends")
    micro_trends: list[str] = Field(default_factory=list, description="Niche/emerging trends")
    cultural_context: str = Field(default="", description="Cultural context summary")


class WGSNTrendsOutput(BaseModel):
    """Output from WGSN design direction research."""
    design_directions: list[str] = Field(default_factory=list, description="Key design directions")
    color_stories: list[str] = Field(default_factory=list, description="Color story themes")
    silhouettes: list[str] = Field(default_factory=list, description="Key silhouette trends")
    mood_references: list[str] = Field(default_factory=list, description="Mood/aesthetic references")
    raw_references: list[str] = Field(default_factory=list, description="Raw source references")


class ConsumerTrendsOutput(BaseModel):
    """Output from consumer/Google Trends research."""
    trending_queries: list[str] = Field(default_factory=list, description="Trending search queries")
    rising_terms: list[str] = Field(default_factory=list, description="Rising search terms")
    related_topics: list[str] = Field(default_factory=list, description="Related topic areas")


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

# =============================================================================
# Phase 1 Research Prompts
# =============================================================================

MACRO_TRENDS_PROMPT = """
You are a Cultural Trends Researcher identifying macro and micro trends for fashion collection planning.

YOUR TASK:
Use the `macro_micro_trend` MCP tool to research cultural and societal trends relevant to the brand and target market.

RESEARCH FOCUS:
1. Macro Trends: Broad cultural/societal shifts (sustainability, digital lifestyle, wellness, etc.)
2. Micro Trends: Emerging niche trends relevant to fashion (specific aesthetics, subcultures, etc.)
3. Cultural Context: How these trends connect to the target region and demographic

OUTPUT REQUIREMENTS:
- Extract 5-8 macro trends with brief descriptions
- Extract 5-8 micro trends with brief descriptions
- Provide a 2-3 sentence cultural context summary

Be specific and actionable. Focus on trends that can inform fashion design decisions.
"""

WGSN_TRENDS_PROMPT = """
You are a Fashion Trend Analyst researching WGSN design directions for collection planning.

YOUR TASK:
Use the `wgsn_edited_trend_search` MCP tool to research design trends relevant to the brand, season, and categories.

RESEARCH FOCUS:
1. Design Directions: Key aesthetic and design movements
2. Color Stories: Emerging color themes and palettes
3. Silhouettes: Key shape and proportion trends
4. Mood References: Aesthetic and emotional references

SEARCH STRATEGY:
- Search for the target season and year
- Search for relevant categories (menswear, womenswear, etc.)
- Search for brand-relevant aesthetic terms

OUTPUT REQUIREMENTS:
- Extract 5-8 design directions
- Extract 4-6 color story themes
- Extract 4-6 silhouette trends
- Extract 4-6 mood references
- Include raw references/sources for traceability

Be specific about WGSN insights. These will inform theme generation.
"""

CONSUMER_TRENDS_PROMPT = """
You are a Consumer Insights Researcher validating fashion trends with search data.

YOUR TASK:
Use the `get_related_trending_queries` MCP tool to research what consumers are actively searching for.

RESEARCH FOCUS:
1. Trending Queries: What fashion-related terms are trending
2. Rising Terms: What terms are gaining momentum
3. Related Topics: What broader topics connect to fashion trends

SEARCH STRATEGY:
- Search for fashion-related terms from the macro/micro trends
- Search for brand-relevant style terms
- Search for seasonal and category-specific queries

OUTPUT REQUIREMENTS:
- Extract 5-10 trending queries related to fashion
- Extract 5-10 rising terms showing momentum
- Extract 5-8 related topic areas

Focus on consumer-validated trends that confirm or add to the research.
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
# Status Update Activities
# =============================================================================

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
# Phase 1A Activity: Gather Macro/Micro Cultural Trends
# =============================================================================

@activity.defn
async def gather_macro_trends_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1A: Gather macro/micro cultural trends using macro_micro_trend MCP tool.

    Input state:
        - collection_id: UUID of the collection
        - user_req: User request payload with theme_count
        - brand_dna: Brand DNA data

    Output state (mutated):
        - macro_trends_data: MacroTrendsOutput data
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    collection_id = state["collection_id"]
    user_req = state["user_req"]
    brand_dna = state.get("brand_dna", {})

    activity.logger.info(f"Phase 1A: Gathering macro/micro trends for collection_id={collection_id}")

    # Build season info
    season = user_req.get("season", "").replace("-", " ").title()
    target_year = user_req.get("target_year", "")
    season_title = f"{season} {target_year}".strip()

    research_prompt = f"""
Research macro and micro cultural trends for:

Brand: {user_req.get('brand_name', 'Unknown')}
Season: {season_title}
Region: {user_req.get('region', '')}
Country: {user_req.get('country', '')}
Target Age: {user_req.get('target_age', '')}
Target Gender: {user_req.get('target_gender', '')}

Categories:
{json.dumps(user_req.get('categories', []), indent=2)}

Brand Special Requests:
{user_req.get('brand_special_requests', 'None')}

Use the macro_micro_trend tool to research relevant cultural and societal trends.
"""

    try:
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=research_prompt,
            instructions=MACRO_TRENDS_PROMPT,
            tools=MCP_MACRO_MICRO_TREND_TOOL,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "MacroTrendsOutput",
                    "strict": False,
                    "schema": MacroTrendsOutput.model_json_schema()
                }
            },
            reasoning=REASONING_LOW,
            store=True,
        )

        if response.error:
            activity.logger.warning(f"Macro trends MCP error: {response.error}")
            # Continue with empty data
            state["macro_trends_data"] = MacroTrendsOutput().model_dump()
        else:
            result = MacroTrendsOutput.model_validate_json(response.output_text)
            track_litellm_usage(state, "gather_macro_trends", response, DEFAULT_MODEL)
            state["macro_trends_data"] = result.model_dump()
            activity.logger.info(
                f"Phase 1A completed: {len(result.macro_trends)} macro, "
                f"{len(result.micro_trends)} micro trends"
            )

    except Exception as e:
        activity.logger.warning(f"Phase 1A failed (continuing with empty data): {e}")
        state["macro_trends_data"] = MacroTrendsOutput().model_dump()

    return state


# =============================================================================
# Phase 1B Activity: Gather WGSN Design Trends
# =============================================================================

@activity.defn
async def gather_wgsn_trends_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1B: Gather WGSN design directions using wgsn_edited_trend_search MCP tool.

    Input state:
        - collection_id: UUID of the collection
        - user_req: User request payload
        - brand_dna: Brand DNA data
        - macro_trends_data: From Phase 1A (optional)

    Output state (mutated):
        - wgsn_trends_data: WGSNTrendsOutput data
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    collection_id = state["collection_id"]
    user_req = state["user_req"]
    brand_dna = state.get("brand_dna", {})
    macro_trends = state.get("macro_trends_data", {})

    activity.logger.info(f"Phase 1B: Gathering WGSN trends for collection_id={collection_id}")

    # Build season info
    season = user_req.get("season", "").replace("-", " ").title()
    target_year = user_req.get("target_year", "")
    season_title = f"{season} {target_year}".strip()

    # Include macro trends for context if available
    macro_context = ""
    if macro_trends.get("macro_trends"):
        macro_context = f"\nRelevant macro trends to consider:\n{', '.join(macro_trends.get('macro_trends', []))}"

    research_prompt = f"""
Research WGSN design directions for:

Brand: {user_req.get('brand_name', 'Unknown')}
Season: {season_title}
Region: {user_req.get('region', '')}
Country: {user_req.get('country', '')}

Categories:
{json.dumps(user_req.get('categories', []), indent=2)}

Brand Aesthetic (from DNA):
{json.dumps(brand_dna.get('core_values_and_voice', {}), indent=2) if brand_dna else "Not available"}
{macro_context}

Use the wgsn_edited_trend_search tool to research design directions, color stories, and silhouette trends.
"""

    try:
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=research_prompt,
            instructions=WGSN_TRENDS_PROMPT,
            tools=MCP_WGSN_TOOL,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "WGSNTrendsOutput",
                    "strict": False,
                    "schema": WGSNTrendsOutput.model_json_schema()
                }
            },
            reasoning=REASONING_LOW,
            store=True,
        )

        if response.error:
            activity.logger.warning(f"WGSN trends MCP error: {response.error}")
            state["wgsn_trends_data"] = WGSNTrendsOutput().model_dump()
        else:
            result = WGSNTrendsOutput.model_validate_json(response.output_text)
            track_litellm_usage(state, "gather_wgsn_trends", response, DEFAULT_MODEL)
            state["wgsn_trends_data"] = result.model_dump()
            activity.logger.info(
                f"Phase 1B completed: {len(result.design_directions)} directions, "
                f"{len(result.color_stories)} color stories"
            )

    except Exception as e:
        activity.logger.warning(f"Phase 1B failed (continuing with empty data): {e}")
        state["wgsn_trends_data"] = WGSNTrendsOutput().model_dump()

    return state


# =============================================================================
# Phase 1C Activity: Gather Consumer/Google Trends
# =============================================================================

@activity.defn
async def gather_consumer_trends_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1C: Validate trends with get_related_trending_queries MCP tool.

    Input state:
        - collection_id: UUID of the collection
        - user_req: User request payload
        - brand_dna: Brand DNA data
        - macro_trends_data: From Phase 1A (optional)
        - wgsn_trends_data: From Phase 1B (optional)

    Output state (mutated):
        - consumer_trends_data: ConsumerTrendsOutput data
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    collection_id = state["collection_id"]
    user_req = state["user_req"]
    macro_trends = state.get("macro_trends_data", {})
    wgsn_trends = state.get("wgsn_trends_data", {})

    activity.logger.info(f"Phase 1C: Gathering consumer trends for collection_id={collection_id}")

    # Build context from previous activities
    search_context = []
    if macro_trends.get("micro_trends"):
        search_context.extend(macro_trends.get("micro_trends", [])[:3])
    if wgsn_trends.get("design_directions"):
        search_context.extend(wgsn_trends.get("design_directions", [])[:3])

    research_prompt = f"""
Research consumer search trends for:

Brand: {user_req.get('brand_name', 'Unknown')}
Region: {user_req.get('region', '')}
Country: {user_req.get('country', '')}

Categories:
{json.dumps(user_req.get('categories', []), indent=2)}

Trend terms to validate (from prior research):
{', '.join(search_context) if search_context else 'General fashion trends'}

Use the get_related_trending_queries tool to find what consumers are searching for.
"""

    try:
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=research_prompt,
            instructions=CONSUMER_TRENDS_PROMPT,
            tools=MCP_GOOGLE_TRENDS_TOOL,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ConsumerTrendsOutput",
                    "strict": False,
                    "schema": ConsumerTrendsOutput.model_json_schema()
                }
            },
            reasoning=REASONING_LOW,
            store=True,
        )

        if response.error:
            activity.logger.warning(f"Consumer trends MCP error: {response.error}")
            state["consumer_trends_data"] = ConsumerTrendsOutput().model_dump()
        else:
            result = ConsumerTrendsOutput.model_validate_json(response.output_text)
            track_litellm_usage(state, "gather_consumer_trends", response, DEFAULT_MODEL)
            state["consumer_trends_data"] = result.model_dump()
            activity.logger.info(
                f"Phase 1C completed: {len(result.trending_queries)} queries, "
                f"{len(result.rising_terms)} rising terms"
            )

    except Exception as e:
        activity.logger.warning(f"Phase 1C failed (continuing with empty data): {e}")
        state["consumer_trends_data"] = ConsumerTrendsOutput().model_dump()

    return state


# =============================================================================
# Phase 1D Activity: Generate Theme Briefs + Create DB Rows
# =============================================================================

@activity.defn
async def generate_theme_briefs_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1D: Generate distinct theme briefs and create DB rows.

    Uses research data from prior activities to generate theme briefs.
    Creates theme DB rows after generating briefs.

    Input state:
        - collection_id: UUID of the collection
        - user_req: User request payload with theme_count
        - brand_dna: Brand DNA data
        - macro_trends_data: From Phase 1A (optional)
        - wgsn_trends_data: From Phase 1B (optional)
        - consumer_trends_data: From Phase 1C (optional)

    Output state:
        - briefs: List of ThemeBrief data with theme_ids
        - theme_ids: List of created theme IDs
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    collection_id = state["collection_id"]
    user_req = state["user_req"]
    brand_dna = state.get("brand_dna", {})

    # Get research data from prior activities
    macro_trends = state.get("macro_trends_data", {})
    wgsn_trends = state.get("wgsn_trends_data", {})
    consumer_trends = state.get("consumer_trends_data", {})

    # Get theme_count from user_req (new approach - no detailed theme requirements)
    num_themes = user_req.get("theme_count", 3)

    activity.logger.info(
        f"Phase 1D: Generating {num_themes} theme briefs for collection_id={collection_id}"
    )

    # Build season title
    season = user_req.get("season", "").replace("-", " ").title()
    target_year = user_req.get("target_year", "")
    season_title = f"{season} {target_year}".strip()

    # Build research context from prior activities
    research_context = ""
    if macro_trends.get("macro_trends") or macro_trends.get("micro_trends"):
        research_context += f"""
MACRO/MICRO TRENDS (from cultural research):
- Macro Trends: {', '.join(macro_trends.get('macro_trends', []))}
- Micro Trends: {', '.join(macro_trends.get('micro_trends', []))}
- Cultural Context: {macro_trends.get('cultural_context', 'N/A')}
"""

    if wgsn_trends.get("design_directions") or wgsn_trends.get("color_stories"):
        research_context += f"""
WGSN DESIGN DIRECTIONS (from industry research):
- Design Directions: {', '.join(wgsn_trends.get('design_directions', []))}
- Color Stories: {', '.join(wgsn_trends.get('color_stories', []))}
- Silhouettes: {', '.join(wgsn_trends.get('silhouettes', []))}
- Mood References: {', '.join(wgsn_trends.get('mood_references', []))}
"""

    if consumer_trends.get("trending_queries") or consumer_trends.get("rising_terms"):
        research_context += f"""
CONSUMER TRENDS (from search data):
- Trending Queries: {', '.join(consumer_trends.get('trending_queries', []))}
- Rising Terms: {', '.join(consumer_trends.get('rising_terms', []))}
- Related Topics: {', '.join(consumer_trends.get('related_topics', []))}
"""

    generation_prompt = f"""
Brand: {user_req.get('brand_name', 'Unknown')}
Season: {season_title}
Country: {user_req.get('country', '')}
Region: {user_req.get('region', '')}
Target Age: {user_req.get('target_age', '')}
Target Gender: {user_req.get('target_gender', '')}

Categories:
{json.dumps(user_req.get('categories', []), indent=2)}

Brand DNA Summary:
{json.dumps(brand_dna.get('core_values_and_voice', {}), indent=2) if brand_dna else "Not available"}

Brand Special Requests:
{user_req.get('brand_special_requests', 'None')}
{research_context}
Number of Themes to Generate: {num_themes}

Using the research data above, generate {num_themes} DISTINCT theme briefs.
Each theme must be clearly different from the others and leverage the trend research.
Explain in distinctiveness_rationale how each theme differs.
"""

    try:
        response = await litellm.aresponses(
            model=DEFAULT_MODEL,
            input=generation_prompt,
            instructions=THEME_BRIEFS_PROMPT,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ThemeBriefsOutput",
                    "strict": False,
                    "schema": ThemeBriefsOutput.model_json_schema()
                }
            },
            reasoning=REASONING_MEDIUM,
            store=True,
        )

        if response.error:
            raise RuntimeError(f"LLM API error: {response.error}")

        result = ThemeBriefsOutput.model_validate_json(response.output_text)

        # Track token usage
        track_litellm_usage(state, "generate_theme_briefs", response, DEFAULT_MODEL)

        # Create DB rows for each brief and collect theme_ids
        briefs_with_ids = []
        theme_ids = []
        collection_uuid = UUID(collection_id) if isinstance(collection_id, str) else collection_id

        for brief in result.briefs:
            # Create theme row in database
            theme_id = await ThemeService.create_theme(
                collection_id=collection_uuid,
                theme_name=brief.theme_name,
                theme_slug=brief.theme_slug,
                generation_input={"brief": brief.model_dump()},
            )

            theme_ids.append(str(theme_id))
            briefs_with_ids.append({
                "theme_id": str(theme_id),
                "brief": brief.model_dump(),
            })

        state["briefs"] = briefs_with_ids
        state["theme_ids"] = theme_ids
        state["distinctiveness_rationale"] = result.distinctiveness_rationale

        activity.logger.info(
            f"Phase 1D completed: Generated {len(briefs_with_ids)} briefs, "
            f"created {len(theme_ids)} theme rows for collection_id={collection_id}"
        )

    except Exception as e:
        activity.logger.error(f"Phase 1D failed: {e}")
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
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ThemeGenerationOutput",
                    "strict": False,
                    "schema": ThemeGenerationOutput.model_json_schema()
                }
            },
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
