from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.effect_manager import EffectManager
from core.effects.pickup_pulse import PickupPulseEffect
from core.effects.screen_flash import ScreenFlashEffect
from core.game_state import GameState
from core.theme import NEON_CYAN, NEON_CYAN_SOFT
from entities.items.item_base import ItemBase


@dataclass
class AccessKeyItem(ItemBase):
    """Quest key to progress Layer 1."""

    sound_name: str = "key.wav"
    color: tuple[int, int, int] = NEON_CYAN_SOFT

    def apply(self, player: Any, game_state: GameState) -> None:
        game_state.access_keys += 1

    def on_pickup_effect(self, effect_manager: EffectManager) -> None:
        effect_manager.add(
            PickupPulseEffect(duration_s=0.35, x=self.x, y=self.y, color=NEON_CYAN, radius=24.0)
        )
        effect_manager.add(
            ScreenFlashEffect(duration_s=0.08, color=NEON_CYAN, intensity=0.7)
        )

    def on_pickup_sound(self, sound_manager: Any) -> None:
        sound_manager.play_sound(self.sound_name)

