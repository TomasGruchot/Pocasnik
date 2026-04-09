from __future__ import annotations

import time
from typing import Any, Optional

from core.asset_loader import AssetLoader
from core.game_events import (
    ENEMY_KILLED,
    GAME_OVER_CONDITION,
    GAME_WIN_CONDITION,
    LIVES_ZERO,
    PLAYER_HIT,
    PROJECTILE_FIRED,
    TIME_UP,
)
from core.settings import Settings

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]


class SoundManager:
    """Event-driven sound playback."""

    def __init__(self, settings: Settings, asset_loader: Optional[AssetLoader] = None) -> None:
        self.settings = settings
        self.asset_loader = asset_loader or AssetLoader(settings)

        self._event_to_sound = {
            PROJECTILE_FIRED: "shoot.wav",
            PLAYER_HIT: "hit.wav",
            ENEMY_KILLED: "explosion.wav",
            GAME_OVER_CONDITION: "thud.wav",
            LIVES_ZERO: "thud.wav",
            GAME_WIN_CONDITION: "fanfare.wav",
            TIME_UP: "fanfare.wav",
        }

        self._sounds_cache: dict[str, Any] = {}
        self._last_play: dict[str, float] = {}
        self._bound_tokens: list[tuple[str, Any]] = []
        self._mixer_initialized: bool = False

    def initialize(self) -> None:
        if pygame is None:
            return
        if self._mixer_initialized:
            return
        if pygame.mixer.get_init() is not None:
            self._mixer_initialized = True
            return

        # Frequency/format chosen to work out-of-box.
        try:
            pygame.mixer.init()
            self._mixer_initialized = True
        except Exception:
            # Keep game playable even if audio fails.
            self._mixer_initialized = False

    def bind(self, event_manager: Any) -> None:
        """Subscribes sound handlers once."""

        def make_handler(event_type: str):
            return lambda payload: self.play_event(event_type)

        for event_type in self._event_to_sound.keys():
            token = event_manager.subscribe(event_type, make_handler(event_type))
            self._bound_tokens.append(token)

    def unbind(self, event_manager: Any) -> None:
        for token in self._bound_tokens:
            event_manager.unsubscribe(token)
        self._bound_tokens.clear()

    def play_event(self, event_type: str) -> None:
        sound_name = self._event_to_sound.get(event_type)
        if not sound_name:
            return

        # Simple cooldown prevents rapid re-trigger spam.
        now = time.perf_counter()
        last = self._last_play.get(sound_name, 0.0)
        if now - last < 0.06:
            return

        self._last_play[sound_name] = now
        if pygame is None:
            return
        if not self._mixer_initialized:
            self.initialize()
        if pygame is None or not self._mixer_initialized:
            return

        snd = self._sounds_cache.get(sound_name)
        if snd is None:
            snd = self.asset_loader.load_sound(sound_name)
            self._sounds_cache[sound_name] = snd

        if snd is None:
            return

        try:
            snd.play()
        except Exception:
            # Ignore playback errors.
            return

    def play_sound(self, sound_name: str) -> None:
        """Play a specific sound file from assets (e.g. 'heal.wav')."""
        if pygame is None:
            return
        if not self._mixer_initialized:
            self.initialize()
        if pygame is None or not self._mixer_initialized:
            return

        snd = self._sounds_cache.get(sound_name)
        if snd is None:
            snd = self.asset_loader.load_sound(sound_name)
            self._sounds_cache[sound_name] = snd
        if snd is None:
            return
        try:
            snd.play()
        except Exception:
            return

