from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Central game configuration (portable, easter-egg friendly)."""

    # Internal resolution
    internal_width: int = 480
    internal_height: int = 270

    # Window size
    window_width: int = 1280
    window_height: int = 720

    fps: int = 60
    window_title: str = "NEON BREACH"

    # Theme
    bg: tuple[int, int, int] = (0, 0, 0)
    neon_cyan: tuple[int, int, int] = (0, 255, 255)
    neon_magenta: tuple[int, int, int] = (255, 60, 230)
    neon_yellow: tuple[int, int, int] = (255, 230, 90)
    ui_text: tuple[int, int, int] = (220, 235, 255)

    # Player feel
    player_accel: float = 1200.0
    player_max_speed: float = 165.0
    player_friction: float = 10.0

    # Combat
    projectile_speed: float = 260.0
    fire_cooldown_s: float = 0.22

    # Feedback
    shake_on_hit: float = 5.0
    shake_on_kill: float = 3.0

