from __future__ import annotations

from typing import Any, Optional

import math

from core.base_scene import BaseScene
from core.game_state import GameState


class MainMenuScene(BaseScene):
    def __init__(self, app: Any, game_state: GameState) -> None:
        super().__init__(app, game_state)

        # Lazy init because pygame.font isn't available until pygame is initialized.
        self._font: Optional[Any] = None
        self._big_font: Optional[Any] = None

        self._menu_time_s: float = 0.0
        self._start_rect: Optional[Any] = None
        self._quit_rect: Optional[Any] = None

    def enter(self, prev_scene: Optional[BaseScene]) -> None:
        super().enter(prev_scene)

    def handle_event(self, event: Any) -> None:
        import pygame

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.switch_scene("perimeter_layer")
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._start_rect is not None and self._start_rect.collidepoint(event.pos):
                self.app.switch_scene("perimeter_layer")
            elif self._quit_rect is not None and self._quit_rect.collidepoint(event.pos):
                import pygame

                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt: float) -> None:
        super().update(dt)
        self._menu_time_s += dt

    def render(self, screen: Any) -> None:
        import pygame

        # Animated background (fake parallax-ish effect).
        w = screen.get_width()
        h = screen.get_height()
        t = self._menu_time_s
        r = int(10 + 18 * (0.5 + 0.5 * math.sin(t * 1.2)))
        g = int(12 + 20 * (0.5 + 0.5 * math.sin(t * 1.0 + 1.7)))
        b = int(24 + 24 * (0.5 + 0.5 * math.sin(t * 0.9 + 3.1)))
        screen.fill((r, g, b))

        # A few drifting blobs.
        for i in range(5):
            cx = int(w * (0.15 + i * 0.17) + math.sin(t * (0.6 + i * 0.08)) * 40)
            cy = int(h * 0.2 + math.cos(t * (0.55 + i * 0.1)) * 26 + i * 18)
            pygame.draw.circle(screen, (50, 80, 140), (cx, cy), 18 + i * 2)

        if self._font is None:
            self._font = pygame.font.SysFont(None, 26)
            self._big_font = pygame.font.SysFont(None, 56)

        assert self._font is not None
        assert self._big_font is not None

        title = self._big_font.render("NEON BREACH", True, (220, 235, 255))
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 80))

        button_w, button_h = 320, 54
        start_x = screen.get_width() // 2 - button_w // 2
        start_y = screen.get_height() // 2 - button_h // 2 - 20
        quit_y = start_y + button_h + 18

        self._start_rect = pygame.Rect(start_x, start_y, button_w, button_h)
        self._quit_rect = pygame.Rect(start_x, quit_y, button_w, button_h)

        mouse = pygame.mouse.get_pos()
        start_hover = self._start_rect.collidepoint(mouse)
        quit_hover = self._quit_rect.collidepoint(mouse)

        def draw_button(rect: Any, label: str, hover: bool) -> None:
            base = (70, 120, 190)
            fg = (220, 235, 255)
            if hover:
                base = (110, 165, 235)
            pygame.draw.rect(screen, base, rect, border_radius=12)
            pygame.draw.rect(screen, (20, 35, 60), rect, width=2, border_radius=12)
            txt = self._font.render(label, True, fg)
            screen.blit(txt, (rect.x + rect.width // 2 - txt.get_width() // 2, rect.y + 12))

        draw_button(self._start_rect, "Start", start_hover)
        draw_button(self._quit_rect, "Quit", quit_hover)

        self._apply_fade_overlay(screen)

