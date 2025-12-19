"""Event system exports for MediaForge.

This module provides an async event bus for decoupled component communication.
"""

from src.events.bus import EventBus, EventPriority, event_bus
from src.events.types import (
    Event,
    MediaDiscoveredEvent,
    ScanStartedEvent,
    ScanProgressEvent,
    ScanCompletedEvent,
    MetadataExtractedEvent,
    ErrorEvent,
    TagAddedEvent,
    TagRemovedEvent,
    CollectionUpdatedEvent,
    FileChangedEvent,
    TaskProgressEvent,
    TaskCompletedEvent,
)

__all__ = [
    # Core
    "EventBus",
    "EventPriority",
    "event_bus",
    # Event types
    "Event",
    "MediaDiscoveredEvent",
    "ScanStartedEvent",
    "ScanProgressEvent",
    "ScanCompletedEvent",
    "MetadataExtractedEvent",
    "ErrorEvent",
    "TagAddedEvent",
    "TagRemovedEvent",
    "CollectionUpdatedEvent",
    "FileChangedEvent",
    "TaskProgressEvent",
    "TaskCompletedEvent",
]
