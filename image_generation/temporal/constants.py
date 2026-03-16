"""
Temporal constants for Image Generation.
"""

from enum import Enum


class TemporalQueue(str, Enum):
    """Temporal task queue names for image generation."""

    MOODBOARD_IMAGE_GENERATION = "moodboard-image-generation-queue"
    COLLECTION_IMAGE_GENERATION = "collection-image-generation-queue"
