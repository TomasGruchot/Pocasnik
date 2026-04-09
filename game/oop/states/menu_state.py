from __future__ import annotations

from typing import Any

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from .base_state import BaseState


class MenuState(BaseState):
    """Main menu state."""

    def handle_event(self, event: Any) -> None:
        if pygame is None:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game.set_state("playing")
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.game.request_quit = True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click anywhere to start (MVP).
            self.game.set_state("playing")

    def render(self, surface: Any) -> None:
        if pygame is None:
            return
        surface.fill((0, 0, 0))
        font_big = pygame.font.SysFont(None, 56)
        font_small = pygame.font.SysFont(None, 22)
        title = font_big.render("NEON BREACH", True, (220, 235, 255))
        howto = font_small.render("ENTER/SPACE = Start Terminal   ESC/Q = Quit", True, (160, 180, 210))
        howto2 = font_small.render("Type commands. Try: help", True, (160, 180, 210))
        premium = font_small.render(
            f"PREMIUM: {'UNLOCKED' if getattr(self.game, 'premium_unlocked', False) else 'LOCKED'}",
            True,
            (190, 255, 190) if getattr(self.game, "premium_unlocked", False) else (255, 190, 190),
        )
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 70))
        surface.blit(howto, (surface.get_width() // 2 - howto.get_width() // 2, 150))
        surface.blit(howto2, (surface.get_width() // 2 - howto2.get_width() // 2, 176))
        surface.blit(premium, (surface.get_width() // 2 - premium.get_width() // 2, 210))

