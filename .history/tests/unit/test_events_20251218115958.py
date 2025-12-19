"""Tests for the Event Bus system."""

import pytest
import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from src.events.bus import EventBus, EventPriority
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


class TestEvent:
    """Tests for base Event class."""
    
    def test_event_creation(self):
        """Test basic event creation."""
        event = Event(source="test")
        
        assert event.source == "test"
        assert isinstance(event.timestamp, datetime)
        assert event.event_type == "Event"
    
    def test_event_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated."""
        before = datetime.now(UTC)
        event = Event()
        after = datetime.now(UTC)
        
        assert before <= event.timestamp <= after
    
    def test_event_type_property(self):
        """Test event_type returns class name."""
        event = MediaDiscoveredEvent()
        assert event.event_type == "MediaDiscoveredEvent"


class TestMediaEvents:
    """Tests for media-related events."""
    
    def test_media_discovered_event(self):
        """Test MediaDiscoveredEvent creation."""
        event = MediaDiscoveredEvent(
            file_path="/media/video.mp4",
            file_hash="abc123",
            media_type="video",
            file_size=1024,
            source="scanner"
        )
        
        assert event.file_path == "/media/video.mp4"
        assert event.file_hash == "abc123"
        assert event.media_type == "video"
        assert event.file_size == 1024
        assert event.media_id is None
    
    def test_scan_started_event(self):
        """Test ScanStartedEvent."""
        event = ScanStartedEvent(
            scan_path="/media",
            recursive=True,
            incremental=False
        )
        
        assert event.scan_path == "/media"
        assert event.recursive is True
        assert event.incremental is False
    
    def test_scan_progress_event_percentage(self):
        """Test ScanProgressEvent percentage calculation."""
        event = ScanProgressEvent(processed=50, total=100)
        assert event.percentage == 50.0
        
        # Edge case: zero total
        event_zero = ScanProgressEvent(processed=10, total=0)
        assert event_zero.percentage == 0.0
    
    def test_scan_completed_event(self):
        """Test ScanCompletedEvent."""
        event = ScanCompletedEvent(
            new_files=10,
            updated_files=5,
            skipped_files=100,
            errors=2,
            duration_seconds=45.5
        )
        
        assert event.new_files == 10
        assert event.updated_files == 5
        assert event.skipped_files == 100
        assert event.errors == 2
        assert event.duration_seconds == 45.5


class TestTagEvents:
    """Tests for tag-related events."""
    
    def test_tag_added_event(self):
        """Test TagAddedEvent."""
        event = TagAddedEvent(
            media_id="123",
            tag_id="456",
            tag_name="vacation",
            auto_generated=True
        )
        
        assert event.media_id == "123"
        assert event.tag_name == "vacation"
        assert event.auto_generated is True
    
    def test_tag_removed_event(self):
        """Test TagRemovedEvent."""
        event = TagRemovedEvent(
            media_id="123",
            tag_id="456",
            tag_name="vacation"
        )
        
        assert event.media_id == "123"
        assert event.tag_name == "vacation"


class TestErrorEvent:
    """Tests for ErrorEvent."""
    
    def test_error_event_creation(self):
        """Test ErrorEvent with all fields."""
        event = ErrorEvent(
            error_type="FileNotFoundError",
            message="File does not exist",
            file_path="/missing/file.mp4",
            recoverable=False,
            details={"errno": 2}
        )
        
        assert event.error_type == "FileNotFoundError"
        assert event.message == "File does not exist"
        assert event.file_path == "/missing/file.mp4"
        assert event.recoverable is False
        assert event.details == {"errno": 2}


class TestEventBus:
    """Tests for EventBus class."""
    
    @pytest.fixture
    def event_bus(self):
        """Create a fresh EventBus for each test."""
        bus = EventBus()
        yield bus
        bus.clear()
    
    @pytest.mark.asyncio
    async def test_subscribe_and_emit(self, event_bus):
        """Test basic subscribe and emit."""
        received = []
        
        async def handler(event: MediaDiscoveredEvent):
            received.append(event)
        
        event_bus.add_handler(MediaDiscoveredEvent, handler)
        
        event = MediaDiscoveredEvent(file_path="/test.mp4")
        count = await event_bus.emit(event)
        
        assert count == 1
        assert len(received) == 1
        assert received[0].file_path == "/test.mp4"
    
    @pytest.mark.asyncio
    async def test_subscribe_decorator(self, event_bus):
        """Test subscribe decorator."""
        received = []
        
        @event_bus.subscribe(ScanStartedEvent)
        async def handler(event: ScanStartedEvent):
            received.append(event)
        
        event = ScanStartedEvent(scan_path="/media")
        await event_bus.emit(event)
        
        assert len(received) == 1
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, event_bus):
        """Test handlers are called in priority order."""
        call_order = []
        
        async def low_handler(event):
            call_order.append("low")
        
        async def high_handler(event):
            call_order.append("high")
        
        async def normal_handler(event):
            call_order.append("normal")
        
        event_bus.add_handler(Event, low_handler, EventPriority.LOW)
        event_bus.add_handler(Event, high_handler, EventPriority.HIGH)
        event_bus.add_handler(Event, normal_handler, EventPriority.NORMAL)
        
        await event_bus.emit(Event())
        
        assert call_order == ["high", "normal", "low"]
    
    @pytest.mark.asyncio
    async def test_once_handler(self, event_bus):
        """Test one-time handlers auto-unsubscribe."""
        call_count = 0
        
        async def once_handler(event):
            nonlocal call_count
            call_count += 1
        
        event_bus.add_handler(Event, once_handler, once=True)
        
        await event_bus.emit(Event())
        await event_bus.emit(Event())
        
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """Test unsubscribing a handler."""
        received = []
        
        async def handler(event):
            received.append(event)
        
        event_bus.add_handler(Event, handler)
        await event_bus.emit(Event())
        
        removed = event_bus.unsubscribe(Event, handler)
        assert removed is True
        
        await event_bus.emit(Event())
        assert len(received) == 1  # Only first event
    
    @pytest.mark.asyncio
    async def test_error_isolation(self, event_bus):
        """Test that handler errors don't break other handlers."""
        received = []
        
        async def failing_handler(event):
            raise ValueError("Test error")
        
        async def working_handler(event):
            received.append(event)
        
        event_bus.add_handler(Event, failing_handler, EventPriority.HIGH)
        event_bus.add_handler(Event, working_handler, EventPriority.LOW)
        
        count = await event_bus.emit(Event())
        
        # Both were called, even though first failed
        assert count == 1  # Only successful calls counted
        assert len(received) == 1
    
    @pytest.mark.asyncio
    async def test_emit_no_handlers(self, event_bus):
        """Test emitting with no handlers."""
        count = await event_bus.emit(Event())
        assert count == 0
    
    def test_handler_count(self, event_bus):
        """Test handler_count method."""
        async def handler(event):
            pass
        
        assert event_bus.handler_count() == 0
        
        event_bus.add_handler(Event, handler)
        assert event_bus.handler_count() == 1
        assert event_bus.handler_count(Event) == 1
        assert event_bus.handler_count(MediaDiscoveredEvent) == 0
    
    def test_get_subscribed_events(self, event_bus):
        """Test get_subscribed_events method."""
        async def handler(event):
            pass
        
        event_bus.add_handler(Event, handler)
        event_bus.add_handler(MediaDiscoveredEvent, handler)
        
        events = event_bus.get_subscribed_events()
        assert "Event" in events
        assert "MediaDiscoveredEvent" in events
    
    def test_clear(self, event_bus):
        """Test clear method."""
        async def handler(event):
            pass
        
        event_bus.add_handler(Event, handler)
        event_bus.add_handler(MediaDiscoveredEvent, handler)
        
        event_bus.clear()
        
        assert event_bus.handler_count() == 0


class TestEventBusSingleton:
    """Tests for EventBus singleton pattern."""
    
    def test_get_instance_returns_same_instance(self):
        """Test singleton pattern."""
        EventBus.reset_instance()
        
        instance1 = EventBus.get_instance()
        instance2 = EventBus.get_instance()
        
        assert instance1 is instance2
        
        EventBus.reset_instance()
    
    def test_reset_instance(self):
        """Test reset_instance clears singleton."""
        instance1 = EventBus.get_instance()
        EventBus.reset_instance()
        instance2 = EventBus.get_instance()
        
        assert instance1 is not instance2
        
        EventBus.reset_instance()
