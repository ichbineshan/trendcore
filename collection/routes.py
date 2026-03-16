from fastapi import APIRouter

from collection.views import create_collection, get_collection_overview, get_collections_by_brand

router = APIRouter(prefix="/collection", tags=["collection"])

router.add_api_route(
    path="/create",
    endpoint=create_collection,
    methods=["POST"],
    summary="Create a new collection",
    description="Start collection generation workflow. Generates overview and range details.",
)

router.add_api_route(
    path="/{collection_id}/overview",
    endpoint=get_collection_overview,
    methods=["GET"],
    summary="Get collection overview",
    description="Get collection overview including narrative, range overview, and target market.",
)

router.add_api_route(
    path="/brand/{brand_id}",
    endpoint=get_collections_by_brand,
    methods=["GET"],
    summary="Get collections by brand",
    description="Get all collections for a specific brand.",
)
