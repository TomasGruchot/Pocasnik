from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # Window
    # Internal (render target) size; all scenes draw here.
    width: int = 480
    height: int = 270
    # Actual window size (upscaled from internal).
    window_width: int = 1280
    window_height: int = 720
    fps: int = 60
    window_title: str = "NEON BREACH"

    # Transitions / animations
    fade_in_seconds: float = 0.35

    # Gameplay MVP rules
    initial_lives: int = 3
    player_max_lives: int = 30
    survival_seconds_to_win: float = 15.0
    kills_to_win: int = 3

    # Asset roots (keep them relative so the project is portable).
    repo_root: Path = Path(__file__).resolve().parents[2]
    assets_root: Path = repo_root / "game" / "assets"
    images_root: Path = assets_root / "images"
    sounds_root: Path = assets_root / "sounds"
    fonts_root: Path = assets_root / "fonts"

