import logging
from typing import Any
from uuid import UUID

from collection.schemas import (
    CollectionCreateRequest,
    CollectionCreateResponse,
    CollectionOverviewResponse,
    CollectionOverviewData,
    NarrativeSection,
    TargetMarketSection,
    RangeOverview,
    RangeOverviewStats,
    RangeOverviewItem,
    CollectionSummary,
    BrandCollectionsResponse,
)
from collection.service import CollectionService
from collection.temporal.temporal_client import CollectionTemporalClient
from brand.service import BrandService
from themes.temporal.temporal_client import ThemeTemporalClient

logger = logging.getLogger(__name__)


async def create_collection(
    request: CollectionCreateRequest,
) -> dict[str, Any]:
    """
    Create a new collection.

    1. Extract brand_id from payload
    2. Store entire payload in user_req (includes theme_count)
    3. Fetch brand DNA for theme generation
    4. Trigger Collection workflow (fire & forget)
    5. Trigger Theme generation workflow (fire & forget)
       - Theme rows are created dynamically during workflow based on theme_count
    6. Return collection_id with pending status
    """
    try:
        user_req = request.model_dump()
        brand_id = UUID(request.brand_id)

        # 1. Create collection record
        collection_id = await CollectionService.create_collection(
            brand_id=brand_id,
            user_req=user_req,
        )

        # 2. Fetch brand DNA for theme generation
        brand_dna = {}
        brand = await BrandService.get_brand_by_id(brand_id)
        if brand:
            brand_dna = {
                "brand_name": brand.brand_name,
                "visual_identity": brand.visual_identity,
                "design_guardrails": brand.design_guardrails,
                "market_positioning": brand.market_positioning,
                "cultural_influences": brand.cultural_influences,
                "core_values_and_voice": brand.core_values_and_voice,
                "source_references": brand.source_references,
                "brand_class": brand.brand_class,
                "velocity": brand.velocity,
                "depth": brand.depth,
                "strictness": brand.strictness,
            }
        else:
            logger.error(
                f"Brand not found for theme generation",
                extra={"brand_id": str(brand_id), "collection_id": str(collection_id)}
            )

        # 3. Fire Collection Generation Workflow (fire & forget)
        collection_client = CollectionTemporalClient()
        collection_workflow_id = await collection_client.start_collection_generation_workflow(
            collection_id=str(collection_id),
            user_req=user_req,
        )

        # 4. Fire Theme Generation Workflow (fire & forget)
        # Always trigger - theme rows are created dynamically based on theme_count in user_req
        theme_client = ThemeTemporalClient()
        theme_workflow_id = await theme_client.start_theme_generation_workflow(
            collection_id=str(collection_id),
            user_req=user_req,
            brand_dna=brand_dna,
        )

        theme_count = user_req.get("theme_count", 3)
        logger.info(
            f"Collection creation started",
            extra={
                "collection_id": str(collection_id),
                "collection_workflow_id": collection_workflow_id,
                "theme_workflow_id": theme_workflow_id,
                "theme_count": theme_count,
            }
        )

        return CollectionCreateResponse(
            success=True,
            message="Collection creation started",
            data={
                "collection_id": str(collection_id),
                "status": "pending",
                "workflow_id": collection_workflow_id,
            },
        ).model_dump()

    except Exception as e:
        logger.exception(f"Failed to create collection: {e}")
        return CollectionCreateResponse(
            success=False,
            message="Failed to create collection",
            error=str(e),
        ).model_dump()


async def get_collection_overview(
    collection_id: str,
) -> dict[str, Any]:
    """
    Get collection overview by ID.

    Returns:
    - Narrative: collection_name, season, overview
    - Range Overview: stats + items table
    - Target & Market: season_year, market, occasion, gender, design_mood, design_details
    """
    try:
        collection = await CollectionService.get_collection_by_id(UUID(collection_id))

        if not collection:
            return CollectionOverviewResponse(
                success=False,
                message="Collection not found",
                error=f"No collection found with id: {collection_id}",
            ).model_dump()

        user_req = collection.user_req or {}

        # Build season string (e.g., "Summer 2026")
        season = user_req.get("season", "")
        target_year = user_req.get("target_year", "")
        season_display = f"{season.replace('-', ' ').title()} {target_year}".strip()

        # Build Narrative section
        narrative = NarrativeSection(
            collection_name=collection.collection_name,
            season=season_display if season_display else None,
            overview=collection.overview,
        )

        # Build Range Overview section
        range_overview = None
        if collection.range_overview:
            ro = collection.range_overview
            stats = RangeOverviewStats(
                categories=ro.get("stats", {}).get("categories", 0),
                styles=ro.get("stats", {}).get("styles", 0),
                themes=ro.get("stats", {}).get("themes", 0),
            )
            items = [
                RangeOverviewItem(
                    category=item.get("category", ""),
                    brick=item.get("brick", ""),
                    style_fit=item.get("style_fit", ""),
                    num_styles=item.get("num_styles", 0),
                    price_range=item.get("price_range", ""),
                )
                for item in ro.get("items", [])
            ]
            range_overview = RangeOverview(stats=stats, items=items)

        # Build Target & Market section (derived from user_req)
        target_market = TargetMarketSection(
            season_year=season_display if season_display else None,
            market=user_req.get("country"),
            occasion=None,  # Can be added later or LLM-generated
            gender=None,  # Can be derived from categories if needed
            design_mood=None,  # Can be added later or LLM-generated
            design_details=None,  # Can be added later or LLM-generated
        )

        # Build response data
        data = CollectionOverviewData(
            collection_id=str(collection.id),
            status=collection.status,
            image_url=collection.image_url,
            narrative=narrative,
            range_overview=range_overview,
            target_market=target_market,
        )

        return CollectionOverviewResponse(
            success=True,
            message="Collection overview retrieved successfully",
            data=data,
        ).model_dump()

    except Exception as e:
        logger.exception(f"Failed to get collection overview: {e}")
        return CollectionOverviewResponse(
            success=False,
            message="Failed to get collection overview",
            error=str(e),
        ).model_dump()


async def get_collections_by_brand(brand_id: str) -> dict[str, Any]:
    """Get all collections for a brand."""
    try:
        collections = await CollectionService.get_collections_by_brand_id(UUID(brand_id))

        data = [
            CollectionSummary(
                collection_id=str(c.id),
                collection_name=c.collection_name,
                status=c.status,
                created_at=c.created_at,
                image_url=c.image_url
            )
            for c in collections
        ]

        return BrandCollectionsResponse(
            success=True,
            message=f"Found {len(data)} collections",
            data=data,
        ).model_dump()

    except Exception as e:
        logger.exception(f"Failed to get collections for brand: {e}")
        return BrandCollectionsResponse(
            success=False,
            message="Failed to get collections",
            error=str(e),
        ).model_dump()
