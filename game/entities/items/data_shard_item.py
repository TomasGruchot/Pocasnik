from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.effect_manager import EffectManager
from entities.items.item_base import ItemBase
from core.game_state import GameState
from core.effects.screen_flash import ScreenFlashEffect


@dataclass
class DataShardItem(ItemBase):
    """Heal +10 HP (Level 1 loot)."""

    heal_amount: int = 10
    sound_name: str = "heal.wav"
    color: tuple[int, int, int] = (80, 255, 140)

    def apply(self, player: Any, game_state: GameState) -> None:
        game_state.lives = min(int(game_state.player_max_lives), int(game_state.lives + self.heal_amount))

    def on_pickup_effect(self, effect_manager: EffectManager) -> None:
        effect_manager.add(ScreenFlashEffect(duration_s=0.12, color=self.color))

    def on_pickup_sound(self, sound_manager: Any) -> None:
        sound_manager.play_sound(self.sound_name)

