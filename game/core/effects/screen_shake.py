from __future__ import annotations

import random
from dataclasses import dataclass

from core.effect_base import BaseEffect


@dataclass
class ScreenShakeEffect(BaseEffect):
    amplitude_px: float = 6.0
    frequency_hz: float = 25.0

    def render(self, screen: object) -> None:
        # Camera shake is implemented as a blit-offset of the current frame.
        import pygame

        if self.finished or self.duration_s <= 0:
            return

        w, h = screen.get_size()
        t = self.elapsed_s
        # Fade amplitude over time.
        remaining = max(0.0, 1.0 - (t / self.duration_s))
        amp = int(self.amplitude_px * remaining)
        if amp <= 0:
            return

        # Copy current frame.
        frame = screen.copy()

        # Jitter offsets.
        dx = random.randint(-amp, amp)
        dy = random.randint(-amp, amp)

        # Blit shifted.
        screen.blit(frame, (dx, dy), area=pygame.Rect(0, 0, w, h))

