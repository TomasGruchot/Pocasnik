from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]


@dataclass
class AssetManager:
    """Loads and caches images/sounds; falls back to generated Surfaces."""

    images: dict[str, Any] = field(default_factory=dict)
    sounds: dict[str, Any] = field(default_factory=dict)

    def image(self, key: str, size: tuple[int, int], color: tuple[int, int, int]) -> Any:
        if pygame is None:
            raise ModuleNotFoundError("pygame není nainstalované. pip install pygame")
        if key in self.images:
            return self.images[key]
        surf = pygame.Surface(size, flags=pygame.SRCALPHA)
        surf.fill((*color, 255))
        self.images[key] = surf
        return surf

    def sound(self, key: str) -> Optional[Any]:
        # Placeholder: you can wire this to real file loading later.
        return self.sounds.get(key)

