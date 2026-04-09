from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]


class PlayerSprite(pygame.sprite.Sprite):  # type: ignore[misc]
    """Player sprite with acceleration + friction movement."""

    def __init__(self, pos: "pygame.Vector2", image: "pygame.Surface") -> None:
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = pygame.Vector2(pos.x, pos.y)
        self.vel = pygame.Vector2(0, 0)

    def update(self, dt: float, input_dir: "pygame.Vector2", accel: float, max_speed: float, friction: float) -> None:
        # Acceleration
        if input_dir.length_squared() > 0:
            input_dir = input_dir.normalize()
            self.vel += input_dir * accel * dt
        # Friction
        self.vel -= self.vel * min(1.0, friction * dt)
        # Clamp speed
        if self.vel.length() > max_speed:
            self.vel.scale_to_length(max_speed)
        # Integrate
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

