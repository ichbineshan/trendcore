"""
Style generation views.
"""

from uuid import UUID

from styles.schemas import (
    TriggerStyleRequest,
    StyleWebhookPayload,
    UpdateReviewRequest,
)
from styles.service import StyleGenerationService
from styles.temporal.temporal_client import StyleTemporalClient
from styles.types import MCPResponse


def _style_to_dict(style) -> dict:
    """Convert ThemeStyle model to response dict."""
    return {
        "style_id": str(style.id),
        "theme_id": str(style.theme_id),
        "external_job_id": style.external_job_id,
        "external_style_id": style.external_style_id,
        "status": style.status,
        "designer_review": style.designer_review,
        "showroom_review": style.showroom_review,
        "error_message": style.error_message,
        "gsm": style.gsm,
        "cost": style.cost,
        "colors": style.colors,
        "fabric": style.fabric,
        "segment": style.segment,
        "garment_type": style.garment_type,
        "key_details": style.key_details,
        "category_name": style.category_name,
        "category_slug": style.category_slug,
        "fabric_composition": style.fabric_composition,
        "sheet_image": style.sheet_image,
        "swatch_image": style.swatch_image,
        "artwork_image": style.artwork_image,
        "garment_image": style.garment_image,
        "theme_name": style.theme_name,
        "theme_slug": style.theme_slug,
        "created_at": style.created_at,
        "updated_at": style.updated_at,
    }


async def trigger_style_generation(request: TriggerStyleRequest):
    """Trigger style generation for a theme via Temporal workflow."""
    try:
        # Validate theme_id format
        theme_uuid = UUID(request.theme_id)

        # Start Temporal workflow
        temporal_client = StyleTemporalClient()
        workflow_id = await temporal_client.start_style_generation_workflow(
            theme_id=str(theme_uuid),
        )

        return MCPResponse(
            success=True,
            message="Style generation workflow triggered successfully",
            data={
                "theme_id": str(theme_uuid),
                "workflow_id": workflow_id,
                "status": "pending",
            },
            error=None,
        ).model_dump()

    except ValueError as e:
        return MCPResponse(
            success=False,
            message="Invalid request",
            data=None,
            error=str(e),
        ).model_dump()
    except Exception as e:
        return MCPResponse(
            success=False,
            message="Failed to trigger style generation",
            data=None,
            error=str(e),
        ).model_dump()


async def get_style(style_id: UUID):
    """Get style by ID."""
    try:
        style = await StyleGenerationService.get_style_by_id(style_id)

        if not style:
            return MCPResponse(
                success=False,
                message="Style not found",
                data=None,
                error=f"No style found with ID: {str(style_id)}",
            ).model_dump()

        return MCPResponse(
            success=True,
            message="Style retrieved successfully",
            data=_style_to_dict(style),
            error=None,
        ).model_dump()

    except Exception as e:
        return MCPResponse(
            success=False,
            message="Failed to retrieve style",
            data=None,
            error=str(e),
        ).model_dump()


async def get_styles_by_theme(theme_id: UUID):
    """Get all styles for a theme."""
    try:
        styles = await StyleGenerationService.get_styles_by_theme_id(theme_id)

        return MCPResponse(
            success=True,
            message=f"Retrieved {len(styles)} styles",
            data={
                "theme_id": str(theme_id),
                "styles": [_style_to_dict(style) for style in styles],
                "count": len(styles),
            },
            error=None,
        ).model_dump()

    except Exception as e:
        return MCPResponse(
            success=False,
            message="Failed to retrieve styles",
            data=None,
            error=str(e),
        ).model_dump()


async def webhook_callback(style_id: str, payload: StyleWebhookPayload):
    """Webhook endpoint for style generation results from Naruto API."""
    try:
        styles = await StyleGenerationService.process_webhook_callback(style_id, payload)

        return MCPResponse(
            success=True,
            message="Webhook processed successfully",
            data={
                "placeholder_style_id": style_id,
                "styles_created": len(styles),
                "style_ids": [str(s.id) for s in styles],
            },
            error=None,
        ).model_dump()

    except Exception as e:
        return MCPResponse(
            success=False,
            message="Failed to process webhook",
            data=None,
            error=str(e),
        ).model_dump()


async def update_designer_review(style_id: UUID, request: UpdateReviewRequest):
    """Update designer review status for a style."""
    try:
        style = await StyleGenerationService.update_designer_review(
            style_id=style_id,
            review_status=request.status,
        )

        if not style:
            return MCPResponse(
                success=False,
                message="Style not found",
                data=None,
                error=f"No style found with ID: {str(style_id)}",
            ).model_dump()

        return MCPResponse(
            success=True,
            message="Designer review updated successfully",
            data=_style_to_dict(style),
            error=None,
        ).model_dump()

    except Exception as e:
        return MCPResponse(
            success=False,
            message="Failed to update designer review",
            data=None,
            error=str(e),
        ).model_dump()


async def update_showroom_review(style_id: UUID, request: UpdateReviewRequest):
    """Update showroom review status for a style."""
    try:
        style = await StyleGenerationService.update_showroom_review(
            style_id=style_id,
            review_status=request.status,
        )

        if not style:
            return MCPResponse(
                success=False,
                message="Style not found",
                data=None,
                error=f"No style found with ID: {str(style_id)}",
            ).model_dump()

        return MCPResponse(
            success=True,
            message="Showroom review updated successfully",
            data=_style_to_dict(style),
            error=None,
        ).model_dump()

    except Exception as e:
        return MCPResponse(
            success=False,
            message="Failed to update showroom review",
            data=None,
            error=str(e),
        ).model_dump()
