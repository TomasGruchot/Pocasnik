from __future__ import annotations

from typing import Any

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from .base_state import BaseState


class GameOverState(BaseState):
    """Game over state."""

    def handle_event(self, event: Any) -> None:
        if pygame is None:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game.set_state("menu")
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.game.request_quit = True

    def render(self, surface: Any) -> None:
        if pygame is None:
            return
        surface.fill((0, 0, 0))
        font_big = pygame.font.SysFont(None, 56)
        font_small = pygame.font.SysFont(None, 22)
        title = font_big.render("GAME OVER", True, (255, 190, 190))
        score = font_small.render(f"Score: {self.game.last_score}", True, (220, 235, 255))
        hint = font_small.render("ENTER = Menu   ESC = Quit", True, (160, 180, 210))
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 70))
        surface.blit(score, (surface.get_width() // 2 - score.get_width() // 2, 140))
        surface.blit(hint, (surface.get_width() // 2 - hint.get_width() // 2, 170))

