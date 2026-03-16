"""Constants for file upload Temporal workflows."""
from enum import Enum


class TemporalQueue(str, Enum):
    """Task queue names for file upload workflows."""
    PDF_PROCESSING = "pdf-processing-queue"
