from __future__ import annotations

from dataclasses import dataclass

from core.effect_base import BaseEffect


@dataclass
class MuzzleFlashEffect(BaseEffect):
    x: float = 0.0
    y: float = 0.0
    color: tuple[int, int, int] = (255, 220, 90)
    radius: float = 10.0

    def render(self, screen: object) -> None:
        import pygame

        if self.finished or self.duration_s <= 0:
            return

        remaining = max(0.0, 1.0 - (self.elapsed_s / self.duration_s))
        r = max(1, int(self.radius * (0.3 + 0.9 * remaining)))
        alpha = int(190 * remaining)

        flash = pygame.Surface(screen.get_size(), flags=pygame.SRCALPHA)
        flash_color = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(flash, flash_color, (int(self.x), int(self.y)), r)
        screen.blit(flash, (0, 0))

