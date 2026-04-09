from __future__ import annotations

from typing import Any, Optional

from core.base_scene import BaseScene
from core.game_state import GameState


class SceneManager:
    """Handles scene switching + lifecycle callbacks."""

    def __init__(
        self,
        app: Any,
        game_state: GameState,
        scenes: dict[str, type[BaseScene]],
    ) -> None:
        self.app = app
        self.game_state = game_state
        self.scenes = scenes
        self.current: Optional[BaseScene] = None

    def switch_to(self, name: str) -> None:
        if name not in self.scenes:
            raise KeyError(f"Unknown scene: {name}")

        prev = self.current
        next_scene = self.scenes[name](self.app, self.game_state)
        self.current = next_scene

        if prev is not None:
            prev.on_exit()
        next_scene.on_enter(prev)

