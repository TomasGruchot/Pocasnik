from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.effect_manager import EffectManager
from core.effects.explosion import ExplosionEffect
from core.effects.pickup_pulse import PickupPulseEffect
from core.effects.screen_flash import ScreenFlashEffect
from core.effects.screen_shake import ScreenShakeEffect
from core.game_events import SYSTEM_PULSE_USED
from core.game_state import GameState
from core.theme import NEON_YELLOW, NEON_YELLOW_SOFT
from entities.items.item_base import ItemBase


@dataclass
class SystemPulseItem(ItemBase):
    """AOE damage (System Pulse)."""

    radius: float = 90.0
    damage: int = 8
    sound_name: str = "pulse.wav"
    color: tuple[int, int, int] = NEON_YELLOW_SOFT

    pulse_x: float = 0.0
    pulse_y: float = 0.0

    def apply(self, player: Any, game_state: GameState) -> None:
        # Center the AOE on the player at pickup time.
        self.pulse_x = float(player.x + player.width / 2)
        self.pulse_y = float(player.y + player.height / 2)

        if self.event_manager is not None:
            self.event_manager.emit(
                SYSTEM_PULSE_USED,
                {
                    "x": self.pulse_x,
                    "y": self.pulse_y,
                    "radius": float(self.radius),
                    "damage": int(self.damage),
                },
            )

    def on_pickup_effect(self, effect_manager: EffectManager) -> None:
        effect_manager.add(
            ExplosionEffect(
                duration_s=0.45,
                x=self.pulse_x,
                y=self.pulse_y,
                count=14,
                rng_seed=123,
            )
        )
        effect_manager.add(
            ScreenShakeEffect(duration_s=0.25, amplitude_px=8.0, frequency_hz=35.0)
        )
        effect_manager.add(
            PickupPulseEffect(
                duration_s=0.40,
                x=self.pulse_x,
                y=self.pulse_y,
                color=NEON_YELLOW,
                radius=40.0,
            )
        )
        effect_manager.add(
            ScreenFlashEffect(duration_s=0.12, color=NEON_YELLOW, intensity=0.8)
        )

    def on_pickup_sound(self, sound_manager: Any) -> None:
        sound_manager.play_sound(self.sound_name)

