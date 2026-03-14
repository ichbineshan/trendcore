"""
Theme Generation Temporal Worker.
"""

import sys

from temporalio.client import Client
from temporalio.worker import Worker

from themes.temporal.constants import TemporalQueue
from themes.temporal.workflow import ThemeGenerationWorkflow
from themes.temporal.activities import (
    generate_theme_briefs_activity,
    generate_single_theme_activity,
    generate_themes_activity,
    update_themes_completed_activity,
    update_themes_failed_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker


@register_worker("theme_generation_worker")
async def theme_generation_worker():
    """Run the theme generation Temporal worker."""
    try:
        print("THEME_WORKER: Starting worker function...", file=sys.stderr, flush=True)

        print(f"THEME_WORKER: Connecting to Temporal at {loaded_config.temporal_host}...", file=sys.stderr, flush=True)
        client = await Client.connect(loaded_config.temporal_host)
        print("THEME_WORKER: Connected to Temporal.", file=sys.stderr, flush=True)

        print("THEME_WORKER: Creating Worker...", file=sys.stderr, flush=True)
        worker = Worker(
            client,
            task_queue=TemporalQueue.THEME_GENERATION.value,
            workflows=[ThemeGenerationWorkflow],
            activities=[
                generate_theme_briefs_activity,
                generate_single_theme_activity,
                generate_themes_activity,
                update_themes_completed_activity,
                update_themes_failed_activity,
            ],
        )
        print("THEME_WORKER: Worker created.", file=sys.stderr, flush=True)

        print(f"THEME_WORKER: Listening on queue: {TemporalQueue.THEME_GENERATION.value}", file=sys.stderr, flush=True)
        await worker.run()
    except Exception as e:
        import traceback
        print(f"THEME_WORKER: ERROR - {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print("THEME_WORKER: Full traceback:", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise
