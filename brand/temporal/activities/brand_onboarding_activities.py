"""
Brand Onboarding Activities with LiteLLM calls.

Each activity contains the actual LLM prompts and calls.
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
from brand.service import BrandService
from utils.token_tracking import track_litellm_usage

logger = logging.getLogger(__name__)

# ============================================================================
# Model Configuration
# ============================================================================

DEFAULT_MODEL = "gpt-5.2"
REASONING_HIGH = {"effort": "high", "summary": "auto"}
REASONING_MEDIUM = {"effort": "medium", "summary": "auto"}
REASONING_LOW = {"effort": "low", "summary": "auto"}

WEB_SEARCH_TOOL_HIGH = [{
    "type": "web_search_preview",
    "search_context_size": "high",
    "user_location": {"type": "approximate"}
}]

WEB_SEARCH_TOOL_MEDIUM = [{
    "type": "web_search_preview",
    "search_context_size": "medium",
    "user_location": {"type": "approximate"}
}]


# ============================================================================
# Pydantic Schemas for LLM Output
# ============================================================================

# --- Brand Category Schemas ---
class HeroCategoryItem(BaseModel):
    name: str
    description: str
    product_urls: list[str]
    price: str


class HeroCategoriesSchema(BaseModel):
    categories: list[HeroCategoryItem]


class ProductUrlItem(BaseModel):
    url: str
    category_name: str


class ProductUrlsSchema(BaseModel):
    urls: list[ProductUrlItem]


# --- Brand DNA Schemas ---
class BrandColorsGlobalPalette(BaseModel):
    overview: str
    master_palette: list[str]
    accessibility_notes: str


class VisualIdentitySchema(BaseModel):
    brand_colors_global_palette: BrandColorsGlobalPalette


class DesignGuardrailsSchema(BaseModel):
    brand_should_do: list[str]
    brand_should_not_do: list[str]


class BrandReferenceImageSchema(BaseModel):
    notes: str
    source: str
    image_id: str
    image_role: str
    image_type: str
    linked_topics: list[str]
    image_category: str


class VisualIdentityFullSchema(BaseModel):
    visual_identity: VisualIdentitySchema
    design_guardrails: DesignGuardrailsSchema
    source_references: list[str]
    brand_reference_images: list[BrandReferenceImageSchema]


class TargetAudienceSchema(BaseModel):
    genders: list[str]
    regions: list[str]
    age_range: str
    psychographics: str
    style_archetypes: list[str]
    demographic_summary: str


class GlobalPriceRangeSummarySchema(BaseModel):
    currency: str
    median_price: str
    maximum_price: str
    minimum_price: str


class MarketPositioningSchema(BaseModel):
    brand_tier: str
    target_audience: TargetAudienceSchema
    brand_descriptive_tags: list[str]
    global_price_range_summary: GlobalPriceRangeSummarySchema
    primary_product_categories: list[str]


class CulturalInfluencesSchema(BaseModel):
    cultural_references: list[str]
    language_or_script_usage: list[str]
    cultural_sensitivity_notes: str
    important_symbols_or_motifs: list[str]
    subculture_and_community_associations: list[str]
    festivals_or_occasions_influencing_design: list[str]


class CoreValuesAndVoiceSchema(BaseModel):
    voice_style: str
    heritage_background: str
    design_theme_summary: str
    brand_values_and_tones: str
    brand_story_and_ideology: str


class BrandDnaCoreSchema(BaseModel):
    market_positioning: MarketPositioningSchema
    cultural_influences: CulturalInfluencesSchema
    core_values_and_voice: CoreValuesAndVoiceSchema
    brand_name: str


# --- Brand Classification Schemas ---
class VelocitySchema(BaseModel):
    velocity: float


class DepthSchema(BaseModel):
    depth: float


class StrictnessSchema(BaseModel):
    strictness: float


class BrandNotesSchema(BaseModel):
    notes: str


class BrandClassifierSchema(BaseModel):
    brand_class: str
    reasoning: str


# ============================================================================
# System Prompts
# ============================================================================

HERO_CATEGORIES_PROMPT = """You are the Brand Category Extraction Agent.

Your task is to research a fashion brand online and extract all relevant information about the best selling and promoted categories.

Use web search to research the brand and get the best sellers or primary promoted product categories.

Extract at least 5 product detail URLs for each category.

Rules:
1. Search only brand website.
2. Accept the user input exactly as provided.

USER REQUEST:
{user_request}
"""

PRODUCT_EXTRACTOR_PROMPT = """From the given brand category details, extract the product detail pages' URL as a list.
Do not list more than 5. Only pick the best sellers or highlighted ones.

Brand Categories:
{categories}
"""

VISUAL_IDENTITY_PROMPT = """You are a Brand Visual Identity Analyser Agent.

Analyse the products and categories to generate the visual identity schema for the brand.

Extract:
- brand_colors_global_palette (overview, master_palette, accessibility_notes)
- design_guardrails (brand_should_do, brand_should_not_do)
- source_references (URLs consulted)
- brand_reference_images (image metadata)

Rules:
1. Use web search to find the brand's official website.
2. Include ALL URLs visited in source_references.

USER REQUEST:
{user_request}

CATEGORY DETAILS:
{category_details}
"""

BRAND_DNA_CORE_PROMPT = """You are an expert Fashion Designer Agent.

Search the web (brand website, social media, fashion blogs) and extract:
- market_positioning (brand_tier, target_audience, price_range, categories)
- cultural_influences (references, symbols, festivals, sensitivity notes)
- core_values_and_voice (voice_style, heritage, story, values)
- brand_name

Rules:
1. Search brand website, social media, and fashion blogs.
2. Include source URLs in relevant fields.

USER REQUEST:
{user_request}
"""

VELOCITY_PROMPT = """Analyse the brand DNA and category details to calculate VELOCITY (1-5 scale).

Velocity measures how fast the brand adopts trends.
- 1 = Very slow, classic brand that rarely changes
- 5 = Very fast, trend-driven brand that changes frequently

Brand DNA:
{brand_dna}

Category Details:
{category_details}

Return only the velocity score as a float.
"""

DEPTH_PROMPT = """Analyse the brand DNA and category details to calculate DEPTH (1-5 scale).

Depth measures how deeply trends change the brand's products.
- 1 = Surface-level changes only (colors, prints)
- 5 = Deep changes (silhouettes, construction, materials)

Brand DNA:
{brand_dna}

Category Details:
{category_details}

Return only the depth score as a float.
"""

STRICTNESS_PROMPT = """Analyse the brand DNA and category details to calculate STRICTNESS (1-5 scale).

Strictness measures how tightly trends are bound by the brand's DNA.
- 1 = Very loose, brand adopts any trend
- 5 = Very strict, only trends aligned with brand DNA

Brand DNA:
{brand_dna}

Category Details:
{category_details}

Return only the strictness score as a float.
"""

BRAND_NOTES_PROMPT = """Based on the brand DNA, create a short descriptive note about the brand's trend adoption characteristics.

Brand DNA:
{brand_dna}

Write 1-2 sentences describing how this brand approaches trends.
"""

BRAND_CLASSIFIER_PROMPT = """Classify the brand into one of these classes based on velocity, depth, and strictness:

- A0: Classicist - Very low velocity, minimal trend adoption
- A1: Heritage Adapter - Low velocity, selective trend adoption
- A2: Balanced Follower - Moderate velocity and depth
- A3: Trend Conscious - Higher velocity, moderate depth
- A4: Trend Forward - High velocity and depth
- A5: Trend Setter - Highest velocity and depth, leads trends

Velocity: {velocity}
Depth: {depth}
Strictness: {strictness}

Brand DNA:
{brand_dna}

Return brand_class (A0-A5) and reasoning.
"""


# ============================================================================
# Activities
# ============================================================================

@activity.defn
async def brand_category_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract brand categories using LiteLLM.

    Input: state["user_request"]
    Output: state["brand_category_details"], state["target_brand_categories"]
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    user_request = state["user_request"]
    user_request_str = json.dumps(user_request, indent=2)

    activity.logger.info(f"Starting brand_category_activity for brand_id={state.get('brand_id')}")

    # Step 1: Extract hero categories
    response_hero = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=HERO_CATEGORIES_PROMPT.format(user_request=user_request_str),
        tools=WEB_SEARCH_TOOL_HIGH,
        text_format=HeroCategoriesSchema,
        reasoning=REASONING_HIGH,
    )

    if response_hero.error:
        raise RuntimeError(f"LLM API error: {response_hero.error}")

    hero_result = HeroCategoriesSchema.model_validate_json(response_hero.output_text)
    state["target_brand_categories"] = hero_result.model_dump()["categories"]

    track_litellm_usage(state, "brand_category_hero", response_hero, DEFAULT_MODEL)

    # Step 2: Extract product URLs
    response_urls = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=PRODUCT_EXTRACTOR_PROMPT.format(categories=hero_result.model_dump_json()),
        text_format=ProductUrlsSchema,
        reasoning=REASONING_LOW,
    )

    if response_urls.error:
        raise RuntimeError(f"LLM API error: {response_urls.error}")

    urls_result = ProductUrlsSchema.model_validate_json(response_urls.output_text)
    state["brand_product_reference_links"] = urls_result.model_dump()["urls"]
    state["brand_category_details"] = hero_result.model_dump_json()

    track_litellm_usage(state, "brand_category_urls", response_urls, DEFAULT_MODEL)

    activity.logger.info(f"brand_category_activity completed for brand_id={state.get('brand_id')}")

    return state


@activity.defn
async def brand_dna_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract brand DNA using LiteLLM.

    Input: state["user_request"], state["brand_category_details"]
    Output: state["brand_dna"]
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    user_request = state["user_request"]
    user_request_str = json.dumps(user_request, indent=2)
    category_details = state.get("brand_category_details", "")

    activity.logger.info(f"Starting brand_dna_activity for brand_id={state.get('brand_id')}")

    state["brand_dna"] = {}

    # Step 1: Visual Identity Analysis
    response_visual = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=VISUAL_IDENTITY_PROMPT.format(
            user_request=user_request_str,
            category_details=category_details
        ),
        tools=WEB_SEARCH_TOOL_HIGH,
        text_format=VisualIdentityFullSchema,
        reasoning=REASONING_LOW,
    )

    if response_visual.error:
        raise RuntimeError(f"LLM API error: {response_visual.error}")

    visual_result = VisualIdentityFullSchema.model_validate_json(response_visual.output_text)
    visual_parsed = visual_result.model_dump()

    state["brand_dna"]["visual_identity"] = visual_parsed["visual_identity"]
    state["brand_dna"]["design_guardrails"] = visual_parsed["design_guardrails"]
    state["brand_dna"]["source_references"] = visual_parsed["source_references"]
    state["brand_dna"]["brand_reference_images"] = visual_parsed["brand_reference_images"]

    track_litellm_usage(state, "brand_dna_visual", response_visual, DEFAULT_MODEL)

    # Step 2: Brand DNA Core
    response_core = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=BRAND_DNA_CORE_PROMPT.format(user_request=user_request_str),
        tools=WEB_SEARCH_TOOL_HIGH,
        text_format=BrandDnaCoreSchema,
        reasoning=REASONING_MEDIUM,
    )

    if response_core.error:
        raise RuntimeError(f"LLM API error: {response_core.error}")

    core_result = BrandDnaCoreSchema.model_validate_json(response_core.output_text)
    core_parsed = core_result.model_dump()

    state["brand_dna"]["market_positioning"] = core_parsed["market_positioning"]
    state["brand_dna"]["cultural_influences"] = core_parsed["cultural_influences"]
    state["brand_dna"]["core_values_and_voice"] = core_parsed["core_values_and_voice"]

    track_litellm_usage(state, "brand_dna_core", response_core, DEFAULT_MODEL)

    activity.logger.info(f"brand_dna_activity completed for brand_id={state.get('brand_id')}")

    return state


@activity.defn
async def brand_classification_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify brand using LiteLLM.

    Input: state["brand_dna"], state["brand_category_details"]
    Output: state["brand_classification"]
    """
    os.environ.setdefault("OPENAI_API_KEY", loaded_config.openai_gpt4_key)

    brand_dna = json.dumps(state.get("brand_dna", {}), indent=2)
    category_details = state.get("brand_category_details", "")

    activity.logger.info(f"Starting brand_classification_activity for brand_id={state.get('brand_id')}")

    state["brand_classification"] = {}

    # Step 1: Calculate Velocity
    response_velocity = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=VELOCITY_PROMPT.format(brand_dna=brand_dna, category_details=category_details),
        text_format=VelocitySchema,
        reasoning=REASONING_HIGH,
    )

    if response_velocity.error:
        raise RuntimeError(f"LLM API error: {response_velocity.error}")

    velocity_result = VelocitySchema.model_validate_json(response_velocity.output_text)
    state["brand_classification"]["velocity"] = velocity_result.velocity

    track_litellm_usage(state, "classification_velocity", response_velocity, DEFAULT_MODEL)

    # Step 2: Calculate Depth
    response_depth = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=DEPTH_PROMPT.format(brand_dna=brand_dna, category_details=category_details),
        text_format=DepthSchema,
        reasoning=REASONING_HIGH,
    )

    if response_depth.error:
        raise RuntimeError(f"LLM API error: {response_depth.error}")

    depth_result = DepthSchema.model_validate_json(response_depth.output_text)
    state["brand_classification"]["depth"] = depth_result.depth

    track_litellm_usage(state, "classification_depth", response_depth, DEFAULT_MODEL)

    # Step 3: Calculate Strictness
    response_strictness = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=STRICTNESS_PROMPT.format(brand_dna=brand_dna, category_details=category_details),
        text_format=StrictnessSchema,
        reasoning=REASONING_HIGH,
    )

    if response_strictness.error:
        raise RuntimeError(f"LLM API error: {response_strictness.error}")

    strictness_result = StrictnessSchema.model_validate_json(response_strictness.output_text)
    state["brand_classification"]["strictness"] = strictness_result.strictness

    track_litellm_usage(state, "classification_strictness", response_strictness, DEFAULT_MODEL)

    # Step 4: Brand Notes
    response_notes = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=BRAND_NOTES_PROMPT.format(brand_dna=brand_dna),
        text_format=BrandNotesSchema,
        reasoning=REASONING_LOW,
    )

    if response_notes.error:
        raise RuntimeError(f"LLM API error: {response_notes.error}")

    notes_result = BrandNotesSchema.model_validate_json(response_notes.output_text)
    state["brand_classification"]["notes"] = notes_result.notes

    track_litellm_usage(state, "classification_notes", response_notes, DEFAULT_MODEL)

    # Step 5: Brand Classifier
    response_classifier = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=BRAND_CLASSIFIER_PROMPT.format(
            velocity=state["brand_classification"]["velocity"],
            depth=state["brand_classification"]["depth"],
            strictness=state["brand_classification"]["strictness"],
            brand_dna=brand_dna,
        ),
        text_format=BrandClassifierSchema,
        reasoning=REASONING_MEDIUM,
    )

    if response_classifier.error:
        raise RuntimeError(f"LLM API error: {response_classifier.error}")

    classifier_result = BrandClassifierSchema.model_validate_json(response_classifier.output_text)
    state["brand_classification"]["brand_class"] = classifier_result.brand_class
    state["brand_classification"]["reasoning"] = classifier_result.reasoning

    track_litellm_usage(state, "classification_classifier", response_classifier, DEFAULT_MODEL)

    activity.logger.info(f"brand_classification_activity completed for brand_id={state.get('brand_id')}")

    return state


@activity.defn
async def update_brand_completed_activity(state: Dict[str, Any]) -> None:
    """Update brand record with extracted data and set status to completed."""
    brand_id = UUID(state.get("brand_id"))
    brand_dna = state.get("brand_dna", {})
    brand_classification = state.get("brand_classification", {})

    # Update brand DNA fields
    await BrandService.update_brand_dna(
        brand_id=brand_id,
        visual_identity=brand_dna.get("visual_identity"),
        design_guardrails=brand_dna.get("design_guardrails"),
        market_positioning=brand_dna.get("market_positioning"),
        cultural_influences=brand_dna.get("cultural_influences"),
        core_values_and_voice=brand_dna.get("core_values_and_voice"),
        source_references=brand_dna.get("source_references"),
        brand_reference_images=brand_dna.get("brand_reference_images"),
    )

    # Update brand classification fields
    await BrandService.update_brand_classification(
        brand_id=brand_id,
        velocity=brand_classification.get("velocity"),
        depth=brand_classification.get("depth"),
        strictness=brand_classification.get("strictness"),
        classification_notes=brand_classification.get("notes"),
        brand_class=brand_classification.get("brand_class"),
        classification_reasoning=brand_classification.get("reasoning"),
    )

    # Update status to completed
    await BrandService.update_brand_status(brand_id=brand_id, status="completed")

    activity.logger.info(f"Brand updated to completed: {brand_id}")


@activity.defn
async def update_brand_failed_activity(state: Dict[str, Any]) -> None:
    """Update brand status to failed."""
    brand_id = UUID(state.get("brand_id"))
    await BrandService.update_brand_status(brand_id=brand_id, status="failed")

    activity.logger.info(f"Brand updated to failed: {brand_id}")
