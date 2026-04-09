from __future__ import annotations

from typing import Any, Optional

from core.base_scene import BaseScene
from core.game_state import GameState


class VictoryScene(BaseScene):
    def __init__(self, app: Any, game_state: GameState) -> None:
        super().__init__(app, game_state)

        self._font_small: Any = None
        self._font_big: Any = None

    def enter(self, prev_scene: Optional[BaseScene]) -> None:
        super().enter(prev_scene)
        # Premium unlock callback (store result in config via GameApp).
        result = self.app.on_game_won()
        self.game_state.is_victory = bool(result.get("premium_unlocked", False))

    def handle_event(self, event: Any) -> None:
        import pygame

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.switch_scene("main_menu")

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, screen: Any) -> None:
        import pygame

        screen.fill((18, 30, 20))

        if self._font_small is None:
            self._font_small = pygame.font.SysFont(None, 26)
            self._font_big = pygame.font.SysFont(None, 62)

        big = self._font_big.render("Victory!", True, (190, 255, 190))
        small = self._font_small.render(
            f"Score: {self.game_state.score}  -  Back: ENTER / SPACE",
            True,
            (190, 220, 190),
        )

        screen.blit(big, (screen.get_width() // 2 - big.get_width() // 2, 150))
        screen.blit(
            small,
            (screen.get_width() // 2 - small.get_width() // 2, screen.get_height() // 2 + 60),
        )

        self._apply_fade_overlay(screen)

