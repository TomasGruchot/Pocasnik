from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional


if TYPE_CHECKING:  # pragma: no cover
    import pygame

    from core.game_state import GameState
    from game_app import GameApp


class BaseScene:
    """Common scene interface with optional fade-in animation support."""

    def __init__(self, app: GameApp, game_state: GameState) -> None:
        self.app = app
        self.game_state = game_state
        self._fade_alpha: int = 255
        self._fade_t: float = 0.0
        self._fade_done: bool = False

    def enter(self, prev_scene: Optional["BaseScene"]) -> None:
        # Reset fade-in at each scene switch.
        self._fade_alpha = 255
        self._fade_t = 0.0
        self._fade_done = False

    # --- Lifecycle aliases (milestones call them on_enter/on_exit) ---
    def on_enter(self, prev_scene: Optional["BaseScene"]) -> None:
        self.enter(prev_scene)

    def exit(self) -> None:
        pass

    def on_exit(self) -> None:
        self.exit()

    def handle_event(self, event: Any) -> None:
        pass

    def on_event(self, event: Any) -> None:
        self.handle_event(event)

    def update(self, dt: float) -> None:
        self._tick_fade_in(dt)

    def on_update(self, dt: float) -> None:
        self.update(dt)

    def render(self, screen: "pygame.Surface") -> None:
        raise NotImplementedError

    def on_render(self, screen: "pygame.Surface") -> None:
        self.render(screen)

    def _tick_fade_in(self, dt: float) -> None:
        if self._fade_done:
            return

        self._fade_t += dt
        duration = max(0.0001, float(self.app.settings.fade_in_seconds))
        progress = min(1.0, self._fade_t / duration)
        self._fade_alpha = int(255 * (1.0 - progress))
        self._fade_done = progress >= 1.0

    def _apply_fade_overlay(self, screen: "pygame.Surface") -> None:
        """Draw a fade overlay on top of the scene."""
        if self._fade_alpha <= 0:
            return

        import pygame

        overlay = pygame.Surface(screen.get_size(), flags=pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self._fade_alpha)))
        screen.blit(overlay, (0, 0))

