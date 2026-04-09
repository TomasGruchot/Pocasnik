from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from entities.entity_base import EntityBase


@dataclass
class Enemy(EntityBase):
    speed_x: float = 60.0
    color: tuple[int, int, int] = (255, 90, 90)
    bounds_w: int = 960

    def update(self, dt: float) -> None:
        # Simple left-right patrol (placeholder).
        self.x += self.speed_x * dt
        if self.x < 0:
            self.x = 0
            self.speed_x *= -1
        if self.x + self.width > self.bounds_w:
            self.x = float(self.bounds_w - self.width)
            self.speed_x *= -1

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        pygame.draw.rect(screen, self.color, pygame.Rect(*self.rect()))


if TYPE_CHECKING:  # pragma: no cover
    from entities.player import Player
    from entities.projectile import Projectile


@dataclass
class EnemyBase(EntityBase):
    """Common enemy logic (hp + touch damage + optional targeting)."""

    hp: int = 1
    points: int = 1
    touch_damage: int = 1
    touch_cooldown_s: float = 0.6
    _touch_cd: float = 0.0
    target: Optional["Player"] = None

    def take_damage(self, dmg: int) -> bool:
        if not self.alive:
            return False
        self.hp -= int(dmg)
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def tick_touch_cd(self, dt: float) -> None:
        self._touch_cd = max(0.0, self._touch_cd - dt)

    def try_deal_touch(self) -> bool:
        if self._touch_cd > 0.0:
            return False
        self._touch_cd = self.touch_cooldown_s
        return True


@dataclass
class BitBug(EnemyBase):
    speed: float = 55.0
    color: tuple[int, int, int] = (120, 255, 255)
    hp: int = 2
    points: int = 1
    touch_damage: int = 1

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        if self.target is None:
            return
        dx = float(self.target.x - self.x)
        dy = float(self.target.y - self.y)
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        pygame.draw.rect(screen, self.color, pygame.Rect(*self.rect()), border_radius=6)


@dataclass
class PacketLeech(EnemyBase):
    speed: float = 35.0
    color: tuple[int, int, int] = (80, 180, 255)
    hp: int = 3
    points: int = 2
    touch_damage: int = 1
    touch_cooldown_s: float = 0.35

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        if self.target is None:
            return
        dx = float(self.target.x - self.x)
        dy = float(self.target.y - self.y)
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        pygame.draw.circle(screen, self.color, (int(self.x + self.width / 2), int(self.y + self.height / 2)), self.width // 2)


@dataclass
class KernelSpider(EnemyBase):
    speed: float = 80.0
    color: tuple[int, int, int] = (255, 160, 255)
    hp: int = 6
    points: int = 4
    touch_damage: int = 2
    touch_cooldown_s: float = 0.45

    def update(self, dt: float) -> None:
        if not self.alive or self.target is None:
            return
        dx = float(self.target.x - self.x)
        dy = float(self.target.y - self.y)
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            # A bit more "jump-like": bias movement towards target.
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        # Draw a "spider-ish" shape (triangle + outline).
        cx = int(self.x + self.width / 2)
        cy = int(self.y + self.height / 2)
        size = self.width
        pts = [(cx, cy - size // 2), (cx - size // 2, cy + size // 2), (cx + size // 2, cy + size // 2)]
        pygame.draw.polygon(screen, self.color, pts)


@dataclass
class FirewallDrone(EnemyBase):
    speed_x: float = 45.0
    color: tuple[int, int, int] = (255, 70, 170)
    hp: int = 5
    points: int = 3
    touch_damage: int = 1
    bounds_w: int = 960

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        # Slow horizontal patrol.
        self.x += self.speed_x * dt
        if self.x < 0:
            self.x = 0
            self.speed_x *= -1
        if self.x + self.width > self.bounds_w:
            self.x = float(self.bounds_w - self.width)
            self.speed_x *= -1

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        pygame.draw.rect(screen, self.color, pygame.Rect(*self.rect()), border_radius=10)


@dataclass
class RootwormBoss(EnemyBase):
    color: tuple[int, int, int] = (255, 230, 120)
    hp: int = 18
    points: int = 10
    touch_damage: int = 2
    touch_cooldown_s: float = 0.5
    phase: int = 1
    bounds_w: int = 960
    bounds_h: int = 540
    _attack_t: float = 0.0
    _teleport_t: float = 0.0

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        # Phase depends on current hp.
        max_hp = 18
        if self.hp <= max_hp * 0.33:
            self.phase = 3
        elif self.hp <= max_hp * 0.66:
            self.phase = 2
        else:
            self.phase = 1

        self._attack_t += dt
        self._teleport_t += dt

        # In phase 3, occasionally "glitch teleport".
        if self.phase >= 3 and self._teleport_t >= 1.2:
            self._teleport_t = 0.0
            self.x = random.uniform(40, self.bounds_w - 40 - self.width)
            self.y = random.uniform(80, self.bounds_h - 80 - self.height)

    def render(self, screen: "pygame.Surface") -> None:
        import pygame

        # Boss as a big rounded rectangle with neon outline-like layers.
        r = pygame.Rect(*self.rect())
        pygame.draw.rect(screen, self.color, r, border_radius=18)
        pygame.draw.rect(screen, (40, 30, 10), r, width=3, border_radius=18)

