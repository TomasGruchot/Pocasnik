from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import math
import random

from core.game_state import GameState
from core.effects.pickup_pulse import PickupPulseEffect
from core.theme import NEON_CYAN, NEON_CYAN_SOFT, NEON_SCANLINE
from entities.enemy import BitBug, PacketLeech, EnemyBase
from entities.items.access_key_item import AccessKeyItem
from entities.items.data_shard_item import DataShardItem
from entities.items.overclock_chip_item import OverclockChipItem
from scenes.base_layer_scene import GameplayScene

import pygame


@dataclass
class HackGate:
    x: float
    y: float
    width: int = 90
    height: int = 40
    hack_time_s: float = 1.5
    progress_s: float = 0.0
    completed: bool = False

    def rect(self) -> tuple[int, int, int, int]:
        return (int(self.x), int(self.y), self.width, self.height)


class PerimeterLayerScene(GameplayScene):
    """Level 1: Perimeter Layer (Access Keys + HACK GATE)."""

    def __init__(self, app: Any, game_state: GameState) -> None:
        super().__init__(app, game_state)
        self.gate = HackGate(x=430, y=330)
        self._keys_required = 3

    def _on_layer_enter(self) -> None:
        self.game_state.access_keys = 0
        self.game_state.kernel_nodes_activated = 0
        self.game_state.has_firewall_key = False

        self.gate = HackGate(
            x=self.app.settings.width * 0.48 - 45,
            y=self.app.settings.height * 0.62,
        )

        # Build loot as real items (polymorphism, no kind strings).
        self.items = []

        # 3 access keys.
        for _ in range(self._keys_required):
            self.items.append(
                AccessKeyItem(
                    x=random.uniform(70, self.app.settings.width - 70),
                    y=random.uniform(100, self.app.settings.height - 140),
                    width=18,
                    height=18,
                )
            )

        # A few heals/boosts.
        for _ in range(5):
            if random.random() < 0.55:
                item = DataShardItem(
                    x=random.uniform(50, self.app.settings.width - 50),
                    y=random.uniform(110, self.app.settings.height - 160),
                    width=16,
                    height=16,
                )
            else:
                item = OverclockChipItem(
                    x=random.uniform(50, self.app.settings.width - 50),
                    y=random.uniform(110, self.app.settings.height - 160),
                    width=16,
                    height=16,
                )
            self.items.append(item)

    def _spawn_enemies(self, dt: float) -> None:
        self._spawn_delay_s -= dt
        if self._spawn_delay_s > 0.0:
            return

        # Spawn Bit Bugs & Packet Leeches.
        spawn_x = random.uniform(30, self.app.settings.width - 30)
        spawn_y = random.uniform(60, self.app.settings.height * 0.35)

        if random.random() < 0.65:
            e: EnemyBase = BitBug(x=spawn_x, y=spawn_y, width=22, height=22)
        else:
            e = PacketLeech(x=spawn_x, y=spawn_y, width=22, height=22)
        self.enemies.append(e)

        # Pace increases slightly with elapsed time.
        pace = 0.95 + min(0.25, self.game_state.elapsed_s / 600.0)
        self._spawn_delay_s = random.uniform(0.55, 1.05) * pace

    def _update_layer(self, dt: float) -> None:
        if self.player is None:
            return

        player_rect = pygame.Rect(*self.player.rect())

        # Pickup items.
        for it in self.items:
            if not it.alive:
                continue
            if pygame.Rect(*it.rect()).colliderect(player_rect):
                it.pickup(
                    self.player,
                    self.game_state,
                    self.effect_manager,
                    self.app.sound_manager,
                )

        # Gate hacking (only after keys collected).
        if self.game_state.access_keys >= self._keys_required and not self.gate.completed:
            on_gate = pygame.Rect(*self.gate.rect()).colliderect(player_rect)
            e_pressed = pygame.key.get_pressed()[pygame.K_e]
            if on_gate and e_pressed:
                self.gate.progress_s = min(
                    self.gate.hack_time_s, self.gate.progress_s + dt
                )
                if self.gate.progress_s >= self.gate.hack_time_s:
                    self.gate.completed = True
                    self.game_state.has_ended = True
                    self.app.switch_scene("kernel_layer")
            elif not e_pressed:
                self.gate.progress_s = max(0.0, self.gate.progress_s - dt * 1.3)

    def render_background(self, surface: "pygame.Surface") -> None:
        super().render_background(surface)

        # Cyan glitch scanlines overlay (extra).
        w, h = surface.get_width(), surface.get_height()
        t = self.game_state.elapsed_s
        for i in range(10):
            y = int((t * 60 + i * 37) % h)
            off = int(6 * math.sin(t * 3 + i))
            pygame.draw.rect(
                surface,
                NEON_SCANLINE,
                pygame.Rect(off, y, w - abs(off), 3),
            )

    def render_ui(self, surface: "pygame.Surface") -> None:
        super().render_ui(surface)
        font = pygame.font.SysFont(None, 20)

        keys_text = font.render(
            f"Access Keys: {self.game_state.access_keys}/{self._keys_required}",
            True,
            NEON_CYAN,
        )
        surface.blit(keys_text, (16, 40))

        # Gate UI.
        if self.game_state.access_keys >= self._keys_required and not self.gate.completed:
            r = pygame.Rect(*self.gate.rect())
            pygame.draw.rect(surface, NEON_CYAN_SOFT, r, 2, border_radius=8)
            progress = (
                self.gate.progress_s / self.gate.hack_time_s
                if self.gate.hack_time_s > 0
                else 0.0
            )
            bar_w = int((r.width - 10) * progress)
            pygame.draw.rect(
                surface,
                NEON_CYAN_SOFT,
                pygame.Rect(r.x + 5, r.y + r.height - 8, bar_w, 4),
            )
            label = font.render("HACK GATE (hold E)", True, NEON_CYAN)
            surface.blit(label, (r.x - 6, r.y - 26))

