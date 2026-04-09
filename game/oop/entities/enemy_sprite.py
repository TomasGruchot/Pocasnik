from __future__ import annotations

from typing import Any

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]


class EnemySprite(pygame.sprite.Sprite):  # type: ignore[misc]
    """Simple seeker enemy (placeholder AI)."""

    def __init__(self, pos: "pygame.Vector2", image: "pygame.Surface", speed: float = 60.0) -> None:
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = pygame.Vector2(pos.x, pos.y)
        self.speed = float(speed)

    def update(self, dt: float, target: "pygame.Vector2") -> None:
        delta = target - self.pos
        if delta.length_squared() > 0:
            delta = delta.normalize()
            self.pos += delta * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

