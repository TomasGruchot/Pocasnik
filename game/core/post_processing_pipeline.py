from __future__ import annotations

from dataclasses import dataclass

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from core import post_processing


@dataclass
class PostProcessingPipeline:
    """Encapsulates post-processing steps (order matters)."""

    glitch_intensity: float = 1.0
    vignette_strength: float = 0.8
    scanlines_step: int = 3
    scanlines_alpha: int = 35

    def apply(self, surface: "pygame.Surface") -> "pygame.Surface":
        if pygame is None:  # pragma: no cover
            raise ModuleNotFoundError("pygame není nainstalované. pip install pygame")

        # Order: glitch -> vignette -> scanlines
        processed = surface
        processed = post_processing.apply_glitch(
            processed, intensity=self.glitch_intensity
        )
        processed = post_processing.apply_vignette(
            processed, strength=self.vignette_strength
        )
        processed = post_processing.apply_scanlines(
            processed, step=self.scanlines_step, alpha=self.scanlines_alpha
        )
        return processed

