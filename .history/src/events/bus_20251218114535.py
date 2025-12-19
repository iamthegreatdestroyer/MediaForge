"""Async event bus for MediaForge.

Provides a lightweight, async-native publish/subscribe event system
with typed events, priority handling, and error isolation.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Type, TypeVar

from src.events.types import Event

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Handler execution priority (lower value = higher priority)."""
    CRITICAL = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    BACKGROUND = 100


# Type variables for generic event handling
E = TypeVar("E", bound=Event)
EventHandler = Callable[[E], Coroutine[Any, Any, None]]


@dataclass
class HandlerRegistration:
    """Tracks a registered event handler.
    
    Attributes:
        handler: The async handler function
        priority: Execution priority
        once: If True, handler auto-unsubscribes after first call
    """
    handler: EventHandler
    priority: EventPriority
    once: bool = False


class EventBus:
    """Async event bus with typed events and priority handling.
    
    Features:
    - Type-safe event handling with generics
    - Priority-based handler execution
    - One-time handlers (fire once, auto-unsubscribe)
    - Async/await native
    - Error isolation (one handler failure doesn't break others)
    - Singleton pattern for global access
    
    Example:
        >>> bus = EventBus.get_instance()
        >>> 
        >>> @bus.subscribe(MediaDiscoveredEvent)
        >>> async def on_media_discovered(event: MediaDiscoveredEvent):
        ...     print(f"New media: {event.file_path}")
        >>> 
        >>> await bus.emit(MediaDiscoveredEvent(file_path="/media/video.mp4"))
    """
    
    _instance: "EventBus | None" = None
    
    def __init__(self) -> None:
        """Initialize the event bus."""
        self._handlers: Dict[Type[Event], List[HandlerRegistration]] = {}
        self._lock = asyncio.Lock()
        self._emit_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._background_task: asyncio.Task | None = None
    
    @classmethod
    def get_instance(cls) -> "EventBus":
        """Get the singleton instance of the event bus.
        
        Returns:
            The global EventBus instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        if cls._instance is not None:
            cls._instance.clear()
        cls._instance = None
    
    def subscribe(
        self,
        event_type: Type[E],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False
    ) -> Callable[[EventHandler[E]], EventHandler[E]]:
        """Decorator to subscribe a handler to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            priority: Execution priority (lower = earlier)
            once: If True, handler auto-unsubscribes after first call
            
        Returns:
            Decorator function
            
        Example:
            >>> @bus.subscribe(ScanCompletedEvent, priority=EventPriority.HIGH)
            >>> async def handle_scan_complete(event: ScanCompletedEvent):
            ...     print(f"Scan complete: {event.new_files} new files")
        """
        def decorator(handler: EventHandler[E]) -> EventHandler[E]:
            self.add_handler(event_type, handler, priority, once)
            return handler
        return decorator
    
    def add_handler(
        self,
        event_type: Type[E],
        handler: EventHandler[E],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False
    ) -> None:
        """Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async handler function
            priority: Execution priority
            once: If True, auto-unsubscribe after first call
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        registration = HandlerRegistration(
            handler=handler,
            priority=priority,
            once=once
        )
        self._handlers[event_type].append(registration)
        
        # Sort handlers by priority (lower value = higher priority)
        self._handlers[event_type].sort(key=lambda r: r.priority.value)
        
        logger.debug(
            f"Registered handler for {event_type.__name__}: "
            f"{handler.__name__} (priority={priority.name})"
        )
    
    def unsubscribe(
        self,
        event_type: Type[E],
        handler: EventHandler[E]
    ) -> bool:
        """Remove a handler.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
            
        Returns:
            True if handler was found and removed
        """
        if event_type not in self._handlers:
            return False
        
        original_len = len(self._handlers[event_type])
        self._handlers[event_type] = [
            r for r in self._handlers[event_type]
            if r.handler != handler
        ]
        
        removed = len(self._handlers[event_type]) < original_len
        if removed:
            logger.debug(
                f"Unsubscribed handler from {event_type.__name__}: "
                f"{handler.__name__}"
            )
        
        return removed
    
    async def emit(self, event: Event) -> int:
        """Emit an event to all subscribed handlers.
        
        Handlers are called in priority order. Errors in handlers are
        logged but don't prevent other handlers from running.
        
        Args:
            event: Event to emit
            
        Returns:
            Number of handlers that were called
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for {event_type.__name__}")
            return 0
        
        # Also include handlers subscribed to base Event class
        base_handlers = self._handlers.get(Event, [])
        all_handlers = sorted(
            handlers + base_handlers,
            key=lambda r: r.priority.value
        )
        
        to_remove: List[tuple[Type[Event], HandlerRegistration]] = []
        called_count = 0
        
        for registration in all_handlers:
            try:
                await registration.handler(event)
                called_count += 1
                
                if registration.once:
                    to_remove.append((event_type, registration))
                    
            except Exception as e:
                logger.error(
                    f"Handler {registration.handler.__name__} failed for "
                    f"{event_type.__name__}: {e}",
                    exc_info=True
                )
        
        # Remove one-time handlers
        for evt_type, registration in to_remove:
            if evt_type in self._handlers:
                self._handlers[evt_type] = [
                    r for r in self._handlers[evt_type]
                    if r != registration
                ]
        
        logger.debug(
            f"Emitted {event_type.__name__} to {called_count} handlers"
        )
        
        return called_count
    
    def emit_sync(self, event: Event) -> None:
        """Queue an event for emission (for use in sync contexts).
        
        Events queued this way are processed by the background processor.
        
        Args:
            event: Event to queue
        """
        self._emit_queue.put_nowait(event)
    
    async def start_background_processor(self) -> None:
        """Start background task to process queued events.
        
        This enables emit_sync() to work from synchronous code.
        """
        if self._running:
            return
            
        self._running = True
        self._background_task = asyncio.create_task(
            self._process_queue()
        )
        logger.info("Event bus background processor started")
    
    async def stop_background_processor(self) -> None:
        """Stop the background processor."""
        self._running = False
        
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None
            
        logger.info("Event bus background processor stopped")
    
    async def _process_queue(self) -> None:
        """Process queued events from emit_sync()."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._emit_queue.get(),
                    timeout=0.1
                )
                await self.emit(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    def clear(self) -> None:
        """Remove all handlers (useful for testing)."""
        self._handlers.clear()
        logger.debug("Event bus cleared")
    
    def handler_count(self, event_type: Type[Event] | None = None) -> int:
        """Get the number of registered handlers.
        
        Args:
            event_type: Specific event type, or None for all handlers
            
        Returns:
            Number of handlers
        """
        if event_type is not None:
            return len(self._handlers.get(event_type, []))
        
        return sum(len(handlers) for handlers in self._handlers.values())
    
    def get_subscribed_events(self) -> List[str]:
        """Get list of event types with registered handlers.
        
        Returns:
            List of event type names
        """
        return [evt_type.__name__ for evt_type in self._handlers.keys()]


# Global event bus instance
event_bus = EventBus.get_instance()
