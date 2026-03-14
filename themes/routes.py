"""
Theme Routes for Collection DNA.

API routes for theme operations.
"""

from fastapi import APIRouter

from themes.views import get_theme_tiles, get_theme_detail

router = APIRouter(tags=["themes"])

# Theme tiles for a collection
router.add_api_route(
    path="/collection/{collection_id}/themes",
    endpoint=get_theme_tiles,
    methods=["GET"],
    summary="Get theme tiles for a collection",
    description="Get lightweight theme data for card/tile display including name, status, summary, and moodboard image.",
)

# Single theme detail
router.add_api_route(
    path="/themes/{theme_id}",
    endpoint=get_theme_detail,
    methods=["GET"],
    summary="Get theme details",
    description="Get complete theme details including color direction, materials, micro trends, and UI suggestions.",
)
