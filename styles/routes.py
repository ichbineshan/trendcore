"""
Style generation routes.
"""

from fastapi import APIRouter

from styles.views import (
    trigger_style_generation,
    get_style,
    get_styles_by_theme,
    webhook_callback,
    update_designer_review,
    update_showroom_review,
)

router = APIRouter(prefix="/styles")

router.add_api_route(
    path="/generate",
    endpoint=trigger_style_generation,
    methods=["POST"],
    description="Trigger style generation workflow",
)

router.add_api_route(
    path="/{style_id}",
    endpoint=get_style,
    methods=["GET"],
    description="Get style by ID",
)

router.add_api_route(
    path="/theme/{theme_id}",
    endpoint=get_styles_by_theme,
    methods=["GET"],
    description="Get all styles for a theme",
)

router.add_api_route(
    path="/{style_id}/designer-review",
    endpoint=update_designer_review,
    methods=["PATCH"],
    description="Update designer review status",
)

router.add_api_route(
    path="/{style_id}/showroom-review",
    endpoint=update_showroom_review,
    methods=["PATCH"],
    description="Update showroom review status",
)

# Webhook-only router for dedicated webhook server instances
webhook_router = APIRouter(prefix="/styles")

webhook_router.add_api_route(
    path="/webhook/{style_id}",
    endpoint=webhook_callback,
    methods=["POST"],
    description="Webhook endpoint for style generation results",
)
