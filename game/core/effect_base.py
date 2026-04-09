from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BaseEffect:
    """Base class for temporary visual/audio effects."""

    duration_s: float
    elapsed_s: float = 0.0
    finished: bool = False

    def update(self, dt: float) -> None:
        self.elapsed_s += dt
        if self.elapsed_s >= self.duration_s:
            self.finished = True

    def render(self, screen: object) -> None:
        # Override in subclasses.
        pass

