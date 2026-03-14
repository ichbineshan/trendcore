from fastapi import APIRouter

from collection.views import create_collection, get_collection_overview

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
