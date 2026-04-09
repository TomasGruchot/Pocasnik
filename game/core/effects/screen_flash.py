from __future__ import annotations

from dataclasses import dataclass

from core.effect_base import BaseEffect


@dataclass
class ScreenFlashEffect(BaseEffect):
    color: tuple[int, int, int] = (255, 60, 60)
    intensity: float = 1.0

    def render(self, screen: object) -> None:
        import pygame

        if self.finished or self.duration_s <= 0:
            return

        # Fade out quickly.
        remaining = max(0.0, 1.0 - (self.elapsed_s / self.duration_s))
        alpha = int(255 * remaining * self.intensity)
        if alpha <= 0:
            return

        overlay = pygame.Surface(screen.get_size(), flags=pygame.SRCALPHA)
        r, g, b = self.color
        overlay.fill((r, g, b, alpha))
        screen.blit(overlay, (0, 0))

