import inspect
import uuid
import time
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
import logging
from structlog import contextvars
from structlog.stdlib import BoundLogger

from config.settings import loaded_config
from pytz import timezone


UTC_TIME_ZONE = "UTC"


def get_current_time(time_zone: str = UTC_TIME_ZONE):
    return datetime.now(timezone(time_zone))


def add_timestamp(_, __, event_dict):
    """Add current datetime to log event."""
    event_dict["timestamp"] = get_current_time().isoformat()
    return event_dict


def add_service_context(_, __, event_dict):
    """Add service context to log event."""
    event_dict.setdefault("service", "trend-analysis")
    event_dict.setdefault("environment", loaded_config.env)
    return event_dict


def get_logger(*args, **kwargs) -> BoundLogger:
    """Create structlog logger for logging."""

    is_local = loaded_config.env == "local"

    processors = [
        add_timestamp,
        add_service_context,
        contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        (
            structlog.dev.ConsoleRenderer()
            if is_local
            else structlog.processors.JSONRenderer()
        ),
    ]

    structlog.configure(
        processors=processors,
        cache_logger_on_first_use=True,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )
    return structlog.get_logger(**kwargs)


# Default logger instance
logger = get_logger()
