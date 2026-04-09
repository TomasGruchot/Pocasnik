from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ItemBase:
    """Abstract base for loot items."""

    x: float
    y: float
    width: int = 16
    height: int = 16
    alive: bool = True

    # Optional dependencies (keeps SoundManager / EventManager responsibilities intact).
    event_manager: Optional[Any] = None

    # For placeholder neon rendering.
    color: tuple[int, int, int] = (0, 255, 255)

    def rect(self) -> tuple[int, int, int, int]:
        return (int(self.x), int(self.y), self.width, self.height)

    def apply(self, player: Any, game_state: Any) -> None:
        """Apply gameplay effect to the game_state (and optionally player)."""
        raise NotImplementedError

    def on_pickup_effect(self, effect_manager: Any) -> None:
        """Add a visual effect to the effect manager."""
        pass

    def on_pickup_sound(self, sound_manager: Any) -> None:
        """Play a sound via the sound manager."""
        pass

    def pickup(self, player: Any, game_state: Any, effect_manager: Any, sound_manager: Any) -> None:
        if not self.alive:
            return
        self.apply(player, game_state)
        self.on_pickup_effect(effect_manager)
        self.on_pickup_sound(sound_manager)
        self.alive = False

    def render(self, surface: Any) -> None:
        """Draw the item (placeholder neon outline)."""
        import pygame

        if not self.alive:
            return
        r = pygame.Rect(*self.rect())
        pygame.draw.rect(surface, self.color, r, 2, border_radius=6)

