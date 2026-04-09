from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.effect_manager import EffectManager
from core.effects.pickup_pulse import PickupPulseEffect
from core.effects.screen_flash import ScreenFlashEffect
from core.game_state import GameState
from core.theme import NEON_CYAN, NEON_CYAN_SOFT
from core.settings import Settings
from entities.items.item_base import ItemBase


@dataclass
class OverclockChipItem(ItemBase):
    """Speed boost (Overclock Chip)."""

    speed_multiplier: float = 1.6
    duration_s: float = 5.0
    sound_name: str = "boost.wav"
    color: tuple[int, int, int] = NEON_CYAN_SOFT

    def apply(self, player: Any, game_state: GameState) -> None:
        game_state.speed_boost_multiplier = float(self.speed_multiplier)
        game_state.speed_boost_timer_s = float(self.duration_s)

    def on_pickup_effect(self, effect_manager: EffectManager) -> None:
        # Small cyan pulse + tiny flash.
        effect_manager.add(
            PickupPulseEffect(
                duration_s=0.25, x=self.x, y=self.y, color=NEON_CYAN, radius=22.0
            )
        )
        effect_manager.add(
            ScreenFlashEffect(duration_s=0.10, color=(0, 255, 255), intensity=0.8)
        )

    def on_pickup_sound(self, sound_manager: Any) -> None:
        sound_manager.play_sound(self.sound_name)

