from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import math
import random

import pygame

from core.game_state import GameState
from core.theme import NEON_MAGENTA, NEON_MAGENTA_SOFT, NEON_YELLOW, NEON_YELLOW_SOFT
from entities.enemy import FirewallDrone, KernelSpider, EnemyBase
from entities.items.firewall_key_item import FirewallKeyItem
from entities.items.memory_fragment_item import MemoryFragmentItem
from entities.items.shield_item import ShieldItem
from scenes.base_layer_scene import GameplayScene


@dataclass
class KernelNode:
    x: float
    y: float
    width: int = 46
    height: int = 46
    activated: bool = False
    hack_time_s: float = 1.2
    progress_s: float = 0.0

    def rect(self) -> tuple[int, int, int, int]:
        return (int(self.x), int(self.y), self.width, self.height)


@dataclass
class HackGate:
    x: float
    y: float
    width: int = 95
    height: int = 44
    hack_time_s: float = 1.0
    progress_s: float = 0.0
    completed: bool = False

    def rect(self) -> tuple[int, int, int, int]:
        return (int(self.x), int(self.y), self.width, self.height)


class KernelLayerScene(GameplayScene):
    """Level 2: Kernel Layer (activate nodes + hack gate)."""

    def __init__(self, app: Any, game_state: GameState) -> None:
        super().__init__(app, game_state)

        self.nodes: list[KernelNode] = [
            KernelNode(x=180, y=260),
            KernelNode(x=560, y=260),
        ]
        self.gate = HackGate(x=430, y=340)
        self._firewall_key_spawned: bool = False

    def _on_layer_enter(self) -> None:
        self.game_state.kernel_nodes_activated = 0
        self.game_state.has_firewall_key = False
        self._firewall_key_spawned = False

        w = self.app.settings.width
        h = self.app.settings.height
        self.nodes = [
            KernelNode(x=w * 0.22, y=260),
            KernelNode(x=w * 0.62, y=260),
        ]
        self.gate = HackGate(x=w * 0.48 - 47, y=h * 0.62)

        # Items.
        self.items = []
        for _ in range(5):
            if random.random() < 0.5:
                self.items.append(
                    ShieldItem(
                        x=random.uniform(70, w - 70),
                        y=random.uniform(120, h - 160),
                        width=16,
                        height=16,
                    )
                )
            else:
                self.items.append(
                    MemoryFragmentItem(
                        x=random.uniform(70, w - 70),
                        y=random.uniform(120, h - 160),
                        width=16,
                        height=16,
                    )
                )

        self._spawn_delay_s = 0.5

    def _spawn_enemies(self, dt: float) -> None:
        self._spawn_delay_s -= dt
        if self._spawn_delay_s > 0.0:
            return

        spawn_x = random.uniform(30, self.app.settings.width - 30)
        spawn_y = random.uniform(80, self.app.settings.height * 0.35)

        if random.random() < 0.6:
            e: EnemyBase = FirewallDrone(
                x=spawn_x, y=spawn_y, width=24, height=24, bounds_w=self.app.settings.width
            )
        else:
            e = KernelSpider(x=spawn_x, y=spawn_y, width=26, height=26)

        # Occasional "spike" when nodes aren't activated yet.
        if self.game_state.kernel_nodes_activated == 0 and random.random() < 0.15:
            e.hp += 4
            e.touch_damage = max(1, e.touch_damage + 1)
            e.points += 2

        self.enemies.append(e)
        self._spawn_delay_s = random.uniform(0.65, 1.1)

    def _update_layer(self, dt: float) -> None:
        if self.player is None:
            return

        player_rect = pygame.Rect(*self.player.rect())

        # Spawn firewall key after both nodes are ready.
        if (
            self.game_state.kernel_nodes_activated >= 2
            and not self._firewall_key_spawned
        ):
            self._firewall_key_spawned = True
            self.items.append(
                FirewallKeyItem(
                    x=self.app.settings.width * 0.5 - 9,
                    y=self.app.settings.height * 0.42,
                    width=18,
                    height=18,
                )
            )

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

        # Hack nodes (hold E).
        for n in self.nodes:
            if n.activated:
                continue
            on_node = pygame.Rect(*n.rect()).colliderect(player_rect)
            if on_node and pygame.key.get_pressed()[pygame.K_e]:
                n.progress_s = min(n.hack_time_s, n.progress_s + dt)
                if n.progress_s >= n.hack_time_s:
                    n.activated = True
                    self.game_state.kernel_nodes_activated += 1
            else:
                n.progress_s = max(0.0, n.progress_s - dt * 1.2)

        # Hack gate after firewall key.
        gate_ready = (
            self.game_state.kernel_nodes_activated >= 2 and self.game_state.has_firewall_key
        )
        if gate_ready and not self.gate.completed:
            on_gate = pygame.Rect(*self.gate.rect()).colliderect(player_rect)
            e_pressed = pygame.key.get_pressed()[pygame.K_e]
            if on_gate and e_pressed:
                self.gate.progress_s = min(
                    self.gate.hack_time_s, self.gate.progress_s + dt
                )
                if self.gate.progress_s >= self.gate.hack_time_s:
                    self.gate.completed = True
                    self.game_state.has_ended = True
                    self.app.switch_scene("core_layer")
            elif not e_pressed:
                self.gate.progress_s = max(0.0, self.gate.progress_s - dt * 1.1)

        # Enemy drone shooting (simple MVP).
        self._shoot_enemy_drones(dt)

    def _shoot_enemy_drones(self, dt: float) -> None:
        if self.player is None:
            return

        # Fire only from Firewall Drones.
        for e in self.enemies:
            if not e.alive or not isinstance(e, FirewallDrone):
                continue

            if not hasattr(e, "_shot_t"):
                setattr(e, "_shot_t", random.uniform(0.0, 0.6))

            e._shot_t -= dt  # type: ignore[attr-defined]
            if e._shot_t > 0.0:
                continue

            e._shot_t = random.uniform(0.45, 1.0)  # type: ignore[attr-defined]

            dx = float(self.player.x - e.x)
            dy = float(self.player.y - e.y)
            dist = math.hypot(dx, dy) or 1.0
            speed = 130.0
            vx = (dx / dist) * speed
            vy = (dy / dist) * speed

            from entities.projectile import Projectile

            self.enemy_projectiles.append(
                Projectile(
                    x=e.x + e.width / 2 - 4,
                    y=e.y + e.height / 2 - 4,
                    width=8,
                    height=8,
                    vx=vx,
                    vy=vy,
                    color=(255, 110, 230),
                    damage=1,
                    from_player=False,
                )
            )

    def render_background(self, surface: "pygame.Surface") -> None:
        super().render_background(surface)

        # Occasional magenta laser lines.
        w, h = surface.get_width(), surface.get_height()
        t = self.game_state.elapsed_s
        if int(t * 2) % 4 == 0:
            yy = int((t * 120) % h)
            pygame.draw.rect(surface, NEON_MAGENTA, pygame.Rect(0, yy, w, 3))

    def render_ui(self, surface: "pygame.Surface") -> None:
        super().render_ui(surface)

        font = pygame.font.SysFont(None, 20)
        nodes_text = font.render(
            f"Kernel Nodes: {self.game_state.kernel_nodes_activated}/2",
            True,
            NEON_MAGENTA_SOFT,
        )
        surface.blit(nodes_text, (16, 40))

        key_text = font.render(
            f"Firewall Key: {'READY' if self.game_state.has_firewall_key else 'LOCKED'}",
            True,
            NEON_YELLOW_SOFT,
        )
        surface.blit(key_text, (16, 62))

        # Nodes.
        for n in self.nodes:
            r = pygame.Rect(*n.rect())
            color = NEON_MAGENTA if not n.activated else (120, 255, 210)
            pygame.draw.rect(surface, color, r, 2, border_radius=8)
            if not n.activated:
                progress = n.progress_s / n.hack_time_s if n.hack_time_s > 0 else 0.0
                pygame.draw.rect(
                    surface,
                    color,
                    pygame.Rect(
                        r.x + 4,
                        r.y + r.height - 7,
                        int((r.width - 8) * progress),
                        3,
                    ),
                )

        # Gate UI.
        if self.gate is not None and not self.gate.completed:
            r = pygame.Rect(*self.gate.rect())
            pygame.draw.rect(surface, NEON_MAGENTA, r, 2, border_radius=10)
            if self.game_state.kernel_nodes_activated >= 2 and self.game_state.has_firewall_key:
                progress = (
                    self.gate.progress_s / self.gate.hack_time_s
                    if self.gate.hack_time_s > 0
                    else 0.0
                )
                pygame.draw.rect(
                    surface,
                    NEON_MAGENTA,
                    pygame.Rect(
                        r.x + 5,
                        r.y + r.height - 8,
                        int((r.width - 10) * progress),
                        4,
                    ),
                )

            label = font.render(
                "ACTIVATE 2 NODES + HACK GATE (hold E)", True, (235, 210, 255)
            )
            surface.blit(label, (20, 55))

