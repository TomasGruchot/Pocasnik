from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]


@dataclass
class EntityManager:
    """Owns sprite groups; updates and renders them in order."""

    all_sprites: Any = field(default_factory=lambda: pygame.sprite.LayeredUpdates())  # type: ignore[misc]
    enemies: Any = field(default_factory=lambda: pygame.sprite.Group())  # type: ignore[misc]
    projectiles: Any = field(default_factory=lambda: pygame.sprite.Group())  # type: ignore[misc]
    particles: Any = field(default_factory=lambda: pygame.sprite.Group())  # type: ignore[misc]

    def add(self, sprite: Any, *, group: str = "all") -> None:
        self.all_sprites.add(sprite)
        if group == "enemy":
            self.enemies.add(sprite)
        elif group == "projectile":
            self.projectiles.add(sprite)
        elif group == "particle":
            self.particles.add(sprite)

    def update(self, *args: Any, **kwargs: Any) -> None:
        self.all_sprites.update(*args, **kwargs)

    def draw(self, surface: Any, camera_offset: Any = None) -> None:
        # MVP: ignore camera offset (screen shake is handled separately).
        self.all_sprites.draw(surface)

