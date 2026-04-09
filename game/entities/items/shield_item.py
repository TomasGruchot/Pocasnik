from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.effect_manager import EffectManager
from core.effects.pickup_pulse import PickupPulseEffect
from core.effects.screen_flash import ScreenFlashEffect
from core.game_state import GameState
from core.theme import NEON_YELLOW_SOFT, NEON_YELLOW
from entities.items.item_base import ItemBase


@dataclass
class ShieldItem(ItemBase):
    """Shield (absorbs hits)."""

    shield_amount: int = 12
    sound_name: str = "shield.wav"
    color: tuple[int, int, int] = NEON_YELLOW_SOFT

    def apply(self, player: Any, game_state: GameState) -> None:
        game_state.shield += int(self.shield_amount)

    def on_pickup_effect(self, effect_manager: EffectManager) -> None:
        effect_manager.add(
            PickupPulseEffect(duration_s=0.30, x=self.x, y=self.y, color=NEON_YELLOW, radius=26.0)
        )
        effect_manager.add(
            ScreenFlashEffect(duration_s=0.10, color=(255, 230, 90), intensity=0.6)
        )

    def on_pickup_sound(self, sound_manager: Any) -> None:
        sound_manager.play_sound(self.sound_name)

