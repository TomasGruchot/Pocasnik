from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from core.base_scene import BaseScene
from core.sound_manager import SoundManager
from core.asset_loader import AssetLoader
from core.scene_manager import SceneManager
from core.event_manager import EventManager
from core.game_state import GameState
from core.settings import Settings
from core.post_processing_pipeline import PostProcessingPipeline
from core.theme import BG_BLACK
from scenes.core_layer import CoreLayerScene
from scenes.kernel_layer import KernelLayerScene
from scenes.game_over import GameOverScene
from scenes.main_menu import MainMenuScene
from scenes.perimeter_layer import PerimeterLayerScene
from scenes.victory import VictoryScene


@dataclass
class SceneDef:
    name: str
    scene: BaseScene


class GameApp:
    """Main application entrypoint (scene loop)."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()
        self.event_manager = EventManager()
        self.game_state = GameState()
        self.asset_loader = AssetLoader(self.settings)
        self.sound_manager = SoundManager(self.settings, self.asset_loader)
        self.sound_manager.bind(self.event_manager)

        self._scenes: dict[str, type[BaseScene]] = {
            "main_menu": MainMenuScene,
            "perimeter_layer": PerimeterLayerScene,
            "kernel_layer": KernelLayerScene,
            "core_layer": CoreLayerScene,
            "victory": VictoryScene,
            "game_over": GameOverScene,
        }
        self.scene_manager = SceneManager(
            app=self,
            game_state=self.game_state,
            scenes=self._scenes,
        )

        # Post-processing pipeline for the internal render surface.
        self.postfx = PostProcessingPipeline()

        self._config_path: Path = self.settings.repo_root / "config.json"
        self._config: dict[str, Any] = self._load_config()
        self.premium_unlocked: bool = bool(self._config.get("premium_unlocked", False))

    def _load_config(self) -> dict[str, Any]:
        try:
            if self._config_path.exists():
                return json.loads(self._config_path.read_text(encoding="utf-8"))
        except Exception:
            # If config is corrupted, fall back to defaults.
            pass
        return {"premium_unlocked": False}

    def _save_config(self) -> None:
        try:
            self._config_path.write_text(
                json.dumps(self._config, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # Best-effort persistence; the game can still run.
            pass

    def on_game_won(self) -> dict[str, bool]:
        """Callback from `VictoryScene` (premium unlock)."""
        self.premium_unlocked = True
        self.game_state.is_victory = True
        self._config["premium_unlocked"] = True
        self._save_config()
        return {"premium_unlocked": True}

    def switch_scene(self, name: str) -> None:
        self.scene_manager.switch_to(name)

    def run(self) -> None:
        if pygame is None:  # pragma: no cover
            raise ModuleNotFoundError(
                "Chybí závislost 'pygame'. Nainstaluj ji např. přes: pip install pygame"
            )

        pygame.init()
        self.sound_manager.initialize()
        pygame.display.set_caption(self.settings.window_title)
        window_screen = pygame.display.set_mode(
            (self.settings.window_width, self.settings.window_height)
        )
        internal_surface = pygame.Surface((self.settings.width, self.settings.height))
        clock = pygame.time.Clock()

        self.switch_scene("main_menu")

        last = time.perf_counter()
        accumulator = 0.0

        # Fixed timestep for steadier animations.
        fixed_dt = 1.0 / float(self.settings.fps)
        running = True

        while running:
            dt = time.perf_counter() - last
            last = time.perf_counter()
            accumulator = min(accumulator + dt, 0.25)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

                if self.scene_manager.current is not None:
                    self.scene_manager.current.on_event(event)

            # Update with fixed timestep.
            while accumulator >= fixed_dt:
                if self.scene_manager.current is not None:
                    self.scene_manager.current.on_update(fixed_dt)
                accumulator -= fixed_dt

            if self.scene_manager.current is not None:
                internal_surface.fill(BG_BLACK)
                self.scene_manager.current.on_render(internal_surface)

            # Post-processing on the internal render surface.
            processed = self.postfx.apply(internal_surface)

            scaled = pygame.transform.smoothscale(
                processed, (self.settings.window_width, self.settings.window_height)
            )
            window_screen.blit(scaled, (0, 0))

            pygame.display.flip()
            clock.tick(self.settings.fps)

        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    # New OOP engine entrypoint (Sprite-based).
    from oop.game import Game

    Game().run()

