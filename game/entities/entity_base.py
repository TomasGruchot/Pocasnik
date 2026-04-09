from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover
    import pygame


@dataclass
class EntityBase:
    """Base entity with position + simple update/render hooks."""

    x: float
    y: float
    width: int = 24
    height: int = 24
    alive: bool = True

    def rect(self) -> tuple[int, int, int, int]:
        return (int(self.x), int(self.y), self.width, self.height)

    def update(self, dt: float) -> None:
        # Override in subclasses.
        pass

    def render(self, screen: "pygame.Surface") -> None:
        # Override in subclasses.
        pass

    def intersects(self, other: "EntityBase") -> bool:
        ax, ay, aw, ah = self.rect()
        bx, by, bw, bh = other.rect()
        return (ax < bx + bw) and (ax + aw > bx) and (ay < by + bh) and (ay + ah > by)

