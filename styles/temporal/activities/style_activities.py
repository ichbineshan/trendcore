"""
Style generation activities.
"""

from typing import Dict, Any
from uuid import UUID

from temporalio import activity

from styles.service import StyleGenerationService


@activity.defn
async def trigger_style_generation_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trigger style generation via Naruto API.

    Args:
        params: Dictionary containing 'theme_id'

    Returns:
        Dictionary with style_id and success status
    """
    theme_id = params.get("theme_id")
    theme_uuid = UUID(theme_id)

    activity.logger.info(f"Triggering style generation for theme: {theme_id}")

    try:
        style = await StyleGenerationService.trigger_style_workflow(theme_uuid)

        activity.logger.info(
            f"Style generation triggered: theme_id={theme_id}, "
            f"style_id={str(style.id)}, status={style.status}"
        )

        return {
            "style_id": str(style.id),
            "theme_id": theme_id,
            "success": True,
        }

    except Exception as e:
        activity.logger.error(
            f"Failed to trigger style generation for theme {theme_id}: {str(e)}",
            exc_info=True,
        )
        raise


@activity.defn
async def mark_style_failed_activity(params: Dict[str, Any]) -> None:
    """
    Mark style generation as failed.

    Args:
        params: Dictionary containing 'style_id' and 'error'
    """
    style_id = params.get("style_id")
    error = params.get("error", "Unknown error")

    activity.logger.error(
        f"Marking style generation as failed: style_id={style_id}, error={error}"
    )

    if style_id:
        try:
            style_uuid = UUID(style_id)
            await StyleGenerationService.mark_style_failed(style_uuid, error)
        except Exception as e:
            activity.logger.error(
                f"Failed to mark style as failed: style_id={style_id}, error={str(e)}"
            )
