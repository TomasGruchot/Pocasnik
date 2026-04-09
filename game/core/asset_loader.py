from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from core.settings import Settings


class AssetLoader:
    """Loads assets from `game/assets/*`. Missing assets fall back gracefully."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _resolve(self, root: Path, relative: str) -> Path:
        return root / relative

    def load_image(self, relative_path: str, *, colorkey: Optional[Any] = None) -> Any:
        img_path = self._resolve(self.settings.images_root, relative_path)
        try:
            image = pygame.image.load(str(img_path)).convert_alpha()
            if colorkey is not None:
                image.set_colorkey(colorkey)
            return image
        except Exception:
            # Placeholder: solid block.
            if pygame is None:
                raise ModuleNotFoundError(
                    "pygame není nainstalované. Nainstaluj ho např.: pip install pygame"
                )
            surf = pygame.Surface((64, 64), flags=pygame.SRCALPHA)
            surf.fill((80, 120, 200, 220))
            return surf

    def load_font(self, relative_path: str, size: int) -> Any:
        font_path = self._resolve(self.settings.fonts_root, relative_path)
        try:
            return pygame.font.Font(str(font_path), size)
        except Exception:
            # Fallback to system font.
            return pygame.font.SysFont(None, size)

    def load_sound(self, relative_path: str) -> Optional[Any]:
        snd_path = self._resolve(self.settings.sounds_root, relative_path)
        try:
            return pygame.mixer.Sound(str(snd_path))
        except Exception:
            return None

