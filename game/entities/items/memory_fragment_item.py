from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.effect_manager import EffectManager
from core.effects.pickup_pulse import PickupPulseEffect
from core.effects.screen_flash import ScreenFlashEffect
from core.game_state import GameState
from core.theme import NEON_MAGENTA, NEON_MAGENTA_SOFT
from entities.items.item_base import ItemBase


@dataclass
class MemoryFragmentItem(ItemBase):
    """Damage boost (Memory Fragment)."""

    damage_multiplier: float = 3.0
    duration_s: float = 6.0
    sound_name: str = "boost.wav"
    color: tuple[int, int, int] = NEON_MAGENTA_SOFT

    def apply(self, player: Any, game_state: GameState) -> None:
        game_state.damage_boost_multiplier = float(self.damage_multiplier)
        game_state.damage_boost_timer_s = float(self.duration_s)

    def on_pickup_effect(self, effect_manager: EffectManager) -> None:
        effect_manager.add(
            PickupPulseEffect(
                duration_s=0.25,
                x=self.x,
                y=self.y,
                color=NEON_MAGENTA,
                radius=22.0,
            )
        )
        effect_manager.add(
            ScreenFlashEffect(duration_s=0.10, color=(255, 60, 230), intensity=0.85)
        )

    def on_pickup_sound(self, sound_manager: Any) -> None:
        sound_manager.play_sound(self.sound_name)

