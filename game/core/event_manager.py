from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class EventManager:
    """Simple in-process event bus."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(
        self, event_type: str, handler: Callable[[Any], None]
    ) -> tuple[str, Callable[[Any], None]]:
        """Subscribe to an event. Returns a token that can be used for unsubscribe."""
        self._listeners[event_type].append(handler)
        return (event_type, handler)

    def unsubscribe(self, token: tuple[str, Callable[[Any], None]]) -> None:
        event_type, handler = token
        listeners = self._listeners.get(event_type)
        if not listeners:
            return
        try:
            listeners.remove(handler)
        except ValueError:
            return

    def emit(self, event_type: str, payload: Any = None) -> None:
        for handler in list(self._listeners.get(event_type, [])):
            handler(payload)

