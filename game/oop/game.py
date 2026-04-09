from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from .assets import AssetManager
from .config import Settings
from .states.base_state import BaseState
from .states.menu_state import MenuState
from .states.playing_state import PlayingState
from .states.game_over_state import GameOverState


class Game:
    """Top-level game class (loop + init + state switching)."""

    def __init__(self, settings: Optional[Settings] = None, *, host_surface: Any = None) -> None:
        if pygame is None:
            raise ModuleNotFoundError("pygame není nainstalované. pip install pygame")

        self.settings = settings or Settings()
        self.assets = AssetManager()

        self.request_quit: bool = False
        self.last_score: int = 0
        self.premium_unlocked: bool = False

        self._config_path = Path(__file__).resolve().parents[2] / "config.json"
        self._load_config()

        # Internal render target (for easy embedding/postfx later).
        self.internal_surface = pygame.Surface(
            (self.settings.internal_width, self.settings.internal_height)
        )

        self._window: Any = host_surface
        self._clock = pygame.time.Clock()

        self._states: dict[str, type[BaseState]] = {
            "menu": MenuState,
            "playing": PlayingState,
            "game_over": GameOverState,
        }
        self._state: BaseState = self._states["menu"](self)

    def _load_config(self) -> None:
        try:
            if self._config_path.exists():
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                self.premium_unlocked = bool(data.get("premium_unlocked", False))
        except Exception:
            self.premium_unlocked = False

    def _save_config(self) -> None:
        try:
            self._config_path.write_text(
                json.dumps({"premium_unlocked": bool(self.premium_unlocked)}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def unlock_premium(self) -> None:
        self.premium_unlocked = True
        self._save_config()

    def set_state(self, name: str) -> None:
        if name not in self._states:
            raise KeyError(f"Unknown state: {name}")
        prev = self._state
        next_state = self._states[name](self)
        prev.on_exit(next_state)
        next_state.on_enter(prev)
        self._state = next_state

    def run(self) -> None:
        pygame.init()
        pygame.display.set_caption(self.settings.window_title)

        if self._window is None:
            self._window = pygame.display.set_mode(
                (self.settings.window_width, self.settings.window_height)
            )

        self._state.on_enter(None)

        last = time.perf_counter()
        running = True
        while running and not self.request_quit:
            dt = time.perf_counter() - last
            last = time.perf_counter()
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self._state.handle_event(event)

            self._state.update(dt)
            self._state.render(self.internal_surface)

            # Upscale internal -> window.
            scaled = pygame.transform.smoothscale(
                self.internal_surface,
                (self.settings.window_width, self.settings.window_height),
            )
            self._window.blit(scaled, (0, 0))
            pygame.display.flip()
            self._clock.tick(self.settings.fps)

        pygame.quit()


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()

