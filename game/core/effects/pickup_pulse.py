from __future__ import annotations

from dataclasses import dataclass

from core.effect_base import BaseEffect


@dataclass
class PickupPulseEffect(BaseEffect):
    x: float = 0.0
    y: float = 0.0
    color: tuple[int, int, int] = (0, 255, 255)
    radius: float = 18.0

    def render(self, screen: object) -> None:
        import pygame

        if self.finished or self.duration_s <= 0:
            return

        remaining = max(0.0, 1.0 - (self.elapsed_s / self.duration_s))
        r = max(1, int(self.radius * (0.2 + 0.9 * remaining)))
        alpha = int(160 * remaining)

        # Draw a neon-ish ring with 2 passes.
        ring = pygame.Surface(screen.get_size(), flags=pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self.color, alpha), (int(self.x), int(self.y)), r, width=2)
        pygame.draw.circle(
            ring, (*self.color, max(0, alpha - 70)), (int(self.x), int(self.y)), max(1, r - 4), width=1
        )
        screen.blit(ring, (0, 0))

