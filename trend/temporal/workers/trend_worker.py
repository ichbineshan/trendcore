"""
Theme Trend Temporal Worker.
"""

import sys

from temporalio.client import Client
from temporalio.worker import Worker

from trend.temporal.constants import TemporalQueue
from trend.temporal.workflow import ThemeTrendWorkflow
from trend.temporal.activities.trend_activities import (
    create_theme_trend_record_activity,
    run_category_trends_activity,
    run_trend_spotting_activity,
    mark_trend_failed_activity,
)
from config.settings import loaded_config
from utils.temporal.worker_registry import register_worker


@register_worker("theme_trend_worker")
async def theme_trend_worker():
    """Run the theme trend Temporal worker."""
    try:
        print("TREND_WORKER: Starting worker function...", file=sys.stderr, flush=True)

        print(f"TREND_WORKER: Connecting to Temporal at {loaded_config.temporal_host}...", file=sys.stderr, flush=True)
        client = await Client.connect(loaded_config.temporal_host)
        print("TREND_WORKER: Connected to Temporal.", file=sys.stderr, flush=True)

        print("TREND_WORKER: Creating Worker...", file=sys.stderr, flush=True)
        worker = Worker(
            client,
            task_queue=TemporalQueue.THEME_TREND.value,
            workflows=[ThemeTrendWorkflow],
            activities=[
                create_theme_trend_record_activity,
                run_category_trends_activity,
                run_trend_spotting_activity,
                mark_trend_failed_activity,
            ],
        )
        print("TREND_WORKER: Worker created.", file=sys.stderr, flush=True)

        print(f"TREND_WORKER: Listening on queue: {TemporalQueue.THEME_TREND.value}", file=sys.stderr, flush=True)
        await worker.run()
    except Exception as e:
        import traceback
        print(f"TREND_WORKER: ERROR - {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print("TREND_WORKER: Full traceback:", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise
