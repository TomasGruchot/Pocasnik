from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.effect_manager import EffectManager
from core.effects.pickup_pulse import PickupPulseEffect
from core.effects.screen_flash import ScreenFlashEffect
from core.game_events import SYSTEM_PULSE_USED
from core.game_state import GameState
from core.theme import NEON_CYAN_SOFT, NEON_CYAN
from entities.items.item_base import ItemBase


@dataclass
class CorePatchItem(ItemBase):
    """Big heal (Core Patch)."""

    heal_amount: int = 50
    sound_name: str = "heal.wav"
    color: tuple[int, int, int] = NEON_CYAN_SOFT

    def apply(self, player: Any, game_state: GameState) -> None:
        game_state.lives = min(
            int(game_state.player_max_lives), int(game_state.lives + self.heal_amount)
        )

    def on_pickup_effect(self, effect_manager: EffectManager) -> None:
        effect_manager.add(
            PickupPulseEffect(
                duration_s=0.45, x=self.x, y=self.y, color=NEON_CYAN, radius=28.0
            )
        )
        effect_manager.add(
            ScreenFlashEffect(duration_s=0.10, color=NEON_CYAN, intensity=0.9)
        )

    def on_pickup_sound(self, sound_manager: Any) -> None:
        sound_manager.play_sound(self.sound_name)

