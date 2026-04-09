from __future__ import annotations

import random
from typing import Tuple

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from core.theme import VIGNETTE_COLOR, NEON_SCANLINE


def apply_vignette(surface: pygame.Surface, strength: float = 0.75) -> pygame.Surface:
    """Darken corners while keeping the center brighter."""
    if pygame is None:  # pragma: no cover
        raise ModuleNotFoundError("pygame není nainstalované (pip install pygame)")

    w, h = surface.get_size()
    output = surface.copy()

    # Radial gradient-like overlay via concentric circles (cheap).
    cx, cy = w // 2, h // 2
    max_r = max(cx, cy)
    overlay = pygame.Surface((w, h), flags=pygame.SRCALPHA)
    for i in range(0, 8):
        t = i / 7.0
        r = int(max_r * t)
        # Higher alpha near corners.
        a = int(180 * (t ** 2) * strength)
        pygame.draw.circle(overlay, (*VIGNETTE_COLOR, a), (cx, cy), r)
    output.blit(overlay, (0, 0))
    return output


def apply_scanlines(surface: pygame.Surface, step: int = 3, alpha: int = 35) -> pygame.Surface:
    """Add subtle horizontal scanlines."""
    if pygame is None:  # pragma: no cover
        raise ModuleNotFoundError("pygame není nainstalované (pip install pygame)")

    w, h = surface.get_size()
    output = surface.copy()
    overlay = pygame.Surface((w, h), flags=pygame.SRCALPHA)

    # Draw every `step` pixels.
    for y in range(0, h, step):
        pygame.draw.line(overlay, (*NEON_SCANLINE, alpha), (0, y), (w, y), 1)
    output.blit(overlay, (0, 0))
    return output


def apply_glitch(surface: pygame.Surface, intensity: float = 1.0) -> pygame.Surface:
    """Lightweight glitch: shift random horizontal strips."""
    if pygame is None:  # pragma: no cover
        raise ModuleNotFoundError("pygame není nainstalované (pip install pygame)")

    w, h = surface.get_size()
    output = surface.copy()

    # Fewer strips when intensity is low.
    strips = int(6 * intensity)
    strips = max(2, min(12, strips))
    dx_max = int(10 * intensity)

    for _ in range(strips):
        y = random.randint(0, h - 1)
        strip_h = random.randint(1, 6)
        y2 = min(h, y + strip_h)
        dx = random.randint(-dx_max, dx_max)

        rect = pygame.Rect(0, y, w, y2 - y)
        part = surface.subsurface(rect).copy()

        # Clamp horizontal position.
        x = max(0, min(w - 1, dx))
        output.blit(part, (x, y))

    return output

