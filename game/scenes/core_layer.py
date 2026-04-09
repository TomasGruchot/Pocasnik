from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math
import random

import pygame

from core.game_events import ENEMY_KILLED, GAME_WIN_CONDITION, PLAYER_HIT
from core.game_state import GameState
from entities.enemy import RootwormBoss, BitBug, PacketLeech
from entities.items.core_patch_item import CorePatchItem
from entities.items.system_pulse_item import SystemPulseItem
from scenes.base_layer_scene import GameplayScene


@dataclass
class AOEIndicator:
    x: float
    y: float
    radius: float
    duration_s: float
    elapsed_s: float = 0.0
    damaged_player: bool = False

    def update(self, dt: float) -> None:
        self.elapsed_s += dt

    def finished(self) -> bool:
        return self.elapsed_s >= self.duration_s


class CoreLayerScene(GameplayScene):
    """Level 3: Core Layer (ROOTWORM boss)."""

    def __init__(self, app: Any, game_state: GameState) -> None:
        super().__init__(app, game_state)
        self.boss: RootwormBoss | None = None
        self.aoes: list[AOEIndicator] = []

        self._minion_spawn_t: float = 0.0
        self._boss_attack_t: float = 0.0
        self._boss_aoe_t: float = 0.0

    def _on_layer_enter(self) -> None:
        self.aoes = []
        self.enemies = []
        self.player_projectiles = []
        self.enemy_projectiles = []

        self.game_state.access_keys = 0
        self.game_state.kernel_nodes_activated = 0

        # Spawn boss.
        w, h = self.app.settings.width, self.app.settings.height
        self.boss = RootwormBoss(
            x=w * 0.5 - 30,
            y=100,
            width=60,
            height=60,
            bounds_w=w,
            bounds_h=h,
            hp=24,
            touch_damage=3,
            touch_cooldown_s=0.55,
        )
        self.enemies.append(self.boss)

        # Loot items (real item polymorphism).
        self.items = [
            CorePatchItem(
                x=w * 0.22,
                y=h * 0.65,
                width=18,
                height=18,
            ),
            SystemPulseItem(
                x=w * 0.78,
                y=h * 0.65,
                width=18,
                height=18,
                event_manager=self.app.event_manager,
            ),
        ]

        self._minion_spawn_t = 1.0
        self._boss_attack_t = 0.3
        self._boss_aoe_t = 0.2

    def _spawn_enemies(self, dt: float) -> None:
        # Boss-driven spawn.
        if self.boss is None or not self.boss.alive:
            return

        self._minion_spawn_t -= dt
        if self._minion_spawn_t > 0.0:
            return

        self._minion_spawn_t = (
            2.5 if self.boss.phase == 1 else 1.9 if self.boss.phase == 2 else 1.4
        )

        # Spawn minions in phase 1/2.
        if self.boss.phase >= 1 and self.boss.phase <= 2:
            for _ in range(2 if self.boss.phase == 2 else 1):
                x = random.uniform(80, self.app.settings.width - 80)
                y = random.uniform(140, self.app.settings.height * 0.35)
                if random.random() < 0.6:
                    self.enemies.append(BitBug(x=x, y=y, width=22, height=22, hp=3))
                else:
                    self.enemies.append(PacketLeech(x=x, y=y, width=22, height=22, hp=4))

    def _update_layer(self, dt: float) -> None:
        if self.player is None:
            return

        player_rect = pygame.Rect(*self.player.rect())

        # Pickup items (polymorphic).
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

        # Update AOE indicators and apply damage once.
        px = float(self.player.x + self.player.width / 2)
        py = float(self.player.y + self.player.height / 2)
        for a in self.aoes[:]:
            a.update(dt)
            cx = float(a.x)
            cy = float(a.y)
            dist = math.hypot(px - cx, py - cy)
            if not a.damaged_player and dist <= a.radius:
                a.damaged_player = True
                self.app.event_manager.emit(
                    PLAYER_HIT,
                    {"damage": 2 + (1 if (self.boss is not None and self.boss.phase == 3) else 0), "source": self.boss},
                )
            if a.finished():
                self.aoes.remove(a)

        # Boss attacks.
        if self.boss is None or not self.boss.alive:
            return

        self._boss_attack_t -= dt
        if self._boss_attack_t > 0.0:
            return

        self._boss_attack_t = (
            0.9 if self.boss.phase == 1 else 0.7 if self.boss.phase == 2 else 0.55
        )

        dx = float(self.player.x - self.boss.x)
        dy = float(self.player.y - self.boss.y)
        dist = math.hypot(dx, dy) or 1.0
        speed = 120.0 if self.boss.phase == 1 else 140.0
        vx = (dx / dist) * speed
        vy = (dy / dist) * speed

        from entities.projectile import Projectile

        self.enemy_projectiles.append(
            Projectile(
                x=self.boss.x + self.boss.width / 2 - 4,
                y=self.boss.y + self.boss.height / 2 - 4,
                width=8,
                height=8,
                vx=vx,
                vy=vy,
                color=(255, 110, 120),
                damage=1 + (1 if self.boss.phase >= 2 else 0),
                from_player=False,
            )
        )

        # Phase 3: AOE pulses.
        if self.boss.phase >= 3:
            self._boss_aoe_t -= dt
            if self._boss_aoe_t <= 0.0:
                self._boss_aoe_t = 0.85
                ax = px + random.uniform(-120, 120)
                ay = py + random.uniform(-70, 70)
                self.aoes.append(AOEIndicator(x=ax, y=ay, radius=70.0, duration_s=0.35))

    def _check_end_conditions(self) -> None:
        if self.game_state.has_ended:
            return
        if self.boss is not None and not self.boss.alive:
            self.game_state.is_victory = True
            self.game_state.has_ended = True
            self.app.event_manager.emit(GAME_WIN_CONDITION)
            self.app.switch_scene("victory")

    def render_background(self, surface: "pygame.Surface") -> None:
        super().render_background(surface)

        # Yellow core pulses on top of base cyan grid.
        w, h = surface.get_width(), surface.get_height()
        from core.theme import NEON_YELLOW

        pulse = 0.5 + 0.5 * math.sin(self.game_state.elapsed_s * 2.4)
        tint = (int(NEON_YELLOW[0] * (0.6 + 0.4 * pulse)), NEON_YELLOW[1], NEON_YELLOW[2])

        step = 26
        for x in range(0, w, step):
            if x % (step * 2) == 0:
                pygame.draw.line(surface, tint, (x, 0), (x, h), 1)
        for y in range(0, h, step):
            if y % (step * 2) == 0:
                pygame.draw.line(surface, tint, (0, y), (w, y), 1)

        # Glitch noise blocks.
        for _ in range(20):
            if random.random() < 0.15:
                rx = random.randint(0, w - 10)
                ry = random.randint(0, h - 10)
                rw = random.randint(5, 22)
                rh = random.randint(1, 5)
                pygame.draw.rect(surface, NEON_YELLOW, pygame.Rect(rx, ry, rw, rh))

    def render_ui(self, surface: "pygame.Surface") -> None:
        super().render_ui(surface)

        font = pygame.font.SysFont(None, 20)
        boss_hp = self.boss.hp if (self.boss is not None) else 0
        surface.blit(font.render(f"ROOTWORM HP: {boss_hp}", True, (255, 230, 120)), (16, 40))

        # Draw AOE indicators.
        for a in self.aoes:
            alpha = int(110 * (1.0 - min(1.0, a.elapsed_s / a.duration_s)))
            pygame.draw.circle(surface, (255, 230, 90), (int(a.x), int(a.y)), int(a.radius), 2)
            if alpha > 0:
                pygame.draw.circle(surface, (255, 230, 90), (int(a.x), int(a.y)), int(a.radius * 0.25))

