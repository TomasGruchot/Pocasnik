from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GameState:
    """Mutable runtime state shared across scenes."""

    score: int = 0
    is_victory: bool = False

    # Gameplay pacing
    lives: int = 3
    shield: int = 0
    elapsed_s: float = 0.0

    # Guard to prevent multiple end transitions.
    has_ended: bool = False

    # Layer progression
    access_keys: int = 0
    kernel_nodes_activated: int = 0

    # Buff timers / multipliers (applied by BaseLayerScene).
    player_max_lives: int = 30
    speed_boost_timer_s: float = 0.0
    speed_boost_multiplier: float = 1.0
    damage_boost_timer_s: float = 0.0
    damage_boost_multiplier: float = 1.0

    # Quest / gate progression.
    has_firewall_key: bool = False

