from __future__ import annotations

from typing import Any, Optional


class BaseState:
    """Base class for a state in the state machine."""

    def __init__(self, game: Any) -> None:
        self.game = game

    def on_enter(self, prev: Optional["BaseState"]) -> None:
        pass

    def on_exit(self, next_state: Optional["BaseState"]) -> None:
        pass

    def handle_event(self, event: Any) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: Any) -> None:
        raise NotImplementedError

