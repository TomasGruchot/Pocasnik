from __future__ import annotations

from dataclasses import dataclass

from entities.entity_base import EntityBase


@dataclass
class Projectile(EntityBase):
    vx: float = 0.0
    vy: float = 0.0
    color: tuple[int, int, int] = (255, 255, 90)
    damage: int = 1
    from_player: bool = True

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        if not self.alive:
            return
        pygame.draw.rect(screen, self.color, pygame.Rect(*self.rect()))

