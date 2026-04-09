from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from core.effect_base import BaseEffect


@dataclass
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    size: int
    hue: float


@dataclass
class ExplosionEffect(BaseEffect):
    x: float = 0.0
    y: float = 0.0
    count: int = 10
    base_color: tuple[int, int, int] = (255, 210, 90)
    rng_seed: int | None = None
    particles: list[_Particle] = field(default_factory=list)

    def __post_init__(self) -> None:
        rng = random.Random(self.rng_seed)
        self.particles = []
        for _ in range(self.count):
            angle = rng.random() * math.tau
            speed = rng.uniform(80.0, 260.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = rng.randint(2, 4)
            hue = rng.random()
            self.particles.append(
                _Particle(
                    x=self.x,
                    y=self.y,
                    vx=vx,
                    vy=vy,
                    size=size,
                    hue=hue,
                )
            )

    def render(self, screen: object) -> None:
        import pygame

        if self.finished or self.duration_s <= 0:
            return

        remaining = max(0.0, 1.0 - (self.elapsed_s / self.duration_s))
        if remaining <= 0:
            return

        # Draw simple pixel particles.
        for p in self.particles:
            t = min(self.elapsed_s, self.duration_s)
            px = p.x + p.vx * t
            py = p.y + p.vy * t

            # Fade-out guaranteed without relying on alpha blending:
            # shrink the particle size as time runs out.
            size = max(1, int(p.size * (0.25 + 1.0 * remaining)))
            brightness = 0.35 + 0.65 * remaining
            color = (
                int(self.base_color[0] * brightness),
                int(self.base_color[1] * brightness),
                int(self.base_color[2] * brightness),
            )
            pygame.draw.circle(screen, color, (int(px), int(py)), size)

