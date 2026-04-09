from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from entities.entity_base import EntityBase


if TYPE_CHECKING:  # pragma: no cover
    import pygame


@dataclass
class Player(EntityBase):
    speed: float = 160.0
    color: tuple[int, int, int] = (90, 200, 255)

    def handle_input(self, dt: float) -> None:
        # Lazy pygame usage (called from scenes only).
        import pygame

        keys = pygame.key.get_pressed()
        vx = 0.0
        vy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            vy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            vy += 1.0

        self.x += vx * self.speed * dt
        self.y += vy * self.speed * dt

    def update(self, dt: float) -> None:
        self.handle_input(dt)

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        pygame.draw.rect(screen, self.color, pygame.Rect(*self.rect()))

