"""
Collection Brief Router
"""

from fastapi import APIRouter
from agents import views

router = APIRouter(prefix="/collection-brief", tags=["Collection Brief"])

# Start collection brief
router.add_api_route(
    "/start",
    views.start_collection_brief,
    methods=["POST"],
    summary="Start Collection Brief Questionnaire"
)

# Get questionnaire status
router.add_api_route(
    "/{thread_id}/status",
    views.get_questionnaire_status,
    methods=["GET"],
    summary="Get Questionnaire Status"
)
