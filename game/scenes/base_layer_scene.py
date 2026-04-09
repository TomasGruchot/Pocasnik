from __future__ import annotations

from typing import Any, Optional

import random

from core.base_scene import BaseScene
from core.collision_system import CollisionSystem
from core.effect_manager import EffectManager
from core.game_events import (
    ENEMY_KILLED,
    GAME_OVER_CONDITION,
    LIVES_ZERO,
    PLAYER_HIT,
    PROJECTILE_FIRED,
    SYSTEM_PULSE_USED,
)
from core.game_state import GameState
from core.game_events import TIMER_TICK
from core.effects.explosion import ExplosionEffect
from core.effects.muzzle_flash import MuzzleFlashEffect
from core.effects.screen_flash import ScreenFlashEffect
from entities.items.item_base import ItemBase
from entities.enemy import EnemyBase
from entities.player import Player
from entities.projectile import Projectile


class BaseLayerScene(BaseScene):
    """Shared gameplay for all three layers (movement + shooting + collisions)."""

    def __init__(self, app: Any, game_state: GameState) -> None:
        super().__init__(app, game_state)

        self.player: Player | None = None
        self.enemies: list[EnemyBase] = []
        self.player_projectiles: list[Projectile] = []
        self.enemy_projectiles: list[Projectile] = []

        self._spawn_delay_s: float = 0.0
        self._shot_cooldown_s: float = 0.0
        self.bullet_damage: int = 1
        self.items: list[ItemBase] = []
        self._event_tokens: list[tuple[str, Any]] = []

        self.effect_manager = EffectManager()

        # Event listeners for decoupled logic (lives/score + juice).
        self._event_tokens.append(
            self.app.event_manager.subscribe(PLAYER_HIT, self._on_player_hit)
        )
        self._event_tokens.append(
            self.app.event_manager.subscribe(ENEMY_KILLED, self._on_enemy_killed)
        )
        self._event_tokens.append(
            self.app.event_manager.subscribe(
                PROJECTILE_FIRED, self._on_projectile_fired
            )
        )
        # Used only for HUD timing; we still emit TIMER_TICK from update().
        self._event_tokens.append(
            self.app.event_manager.subscribe(TIMER_TICK, self._on_timer_tick)
        )

        self._event_tokens.append(
            self.app.event_manager.subscribe(
                GAME_OVER_CONDITION, self._on_game_over
            )
        )
        self._event_tokens.append(
            self.app.event_manager.subscribe(LIVES_ZERO, self._on_game_over)
        )

        # AOE intents from items.
        self._event_tokens.append(
            self.app.event_manager.subscribe(
                SYSTEM_PULSE_USED, self._on_system_pulse_used
            )
        )

    def enter(self, prev_scene: Optional[BaseScene]) -> None:
        super().enter(prev_scene)

        self.game_state.score = 0
        self.game_state.is_victory = False
        self.game_state.has_ended = False
        self.game_state.shield = 0
        self.game_state.elapsed_s = 0.0
        self.game_state.player_max_lives = int(self.app.settings.player_max_lives)
        self.game_state.speed_boost_timer_s = 0.0
        self.game_state.speed_boost_multiplier = 1.0
        self.game_state.damage_boost_timer_s = 0.0
        self.game_state.damage_boost_multiplier = 1.0
        self.game_state.has_firewall_key = False

        self.enemies = []
        self.player_projectiles = []
        self.enemy_projectiles = []
        self.items = []

        w, h = self.app.settings.width, self.app.settings.height
        self.player = Player(x=w * 0.5, y=h * 0.75, width=26, height=26)

        self._shot_cooldown_s = 0.0
        self._spawn_delay_s = 0.5
        self.bullet_damage = 1

        self._on_layer_enter()

        # Cache base stats after layer-specific setup.
        self._base_player_speed = self.player.speed if self.player is not None else 0.0
        self._base_bullet_damage = int(self.bullet_damage)

    def exit(self) -> None:
        for token in self._event_tokens:
            self.app.event_manager.unsubscribe(token)
        self._event_tokens.clear()

    # Hooks for concrete layers.
    def _on_layer_enter(self) -> None:
        pass

    def _spawn_enemies(self, dt: float) -> None:
        # Override in subclasses.
        pass

    def _update_layer(self, dt: float) -> None:
        # Override in subclasses (items, nodes, boss logic, etc.).
        pass

    def _check_end_conditions(self) -> None:
        # Override in subclasses.
        pass

    def handle_event(self, event: Any) -> None:
        # Most layers use E interaction; subclasses should override if needed.
        pass

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.game_state.has_ended:
            return
        if self.player is None:
            return

        # Apply temporary buffs from game_state.
        if self.game_state.speed_boost_timer_s > 0.0:
            self.game_state.speed_boost_timer_s = max(
                0.0, self.game_state.speed_boost_timer_s - dt
            )
            if self.game_state.speed_boost_timer_s <= 0.0:
                self.player.speed = self._base_player_speed
                self.game_state.speed_boost_multiplier = 1.0
            else:
                self.player.speed = self._base_player_speed * float(
                    self.game_state.speed_boost_multiplier
                )
        else:
            self.player.speed = self._base_player_speed

        if self.game_state.damage_boost_timer_s > 0.0:
            self.game_state.damage_boost_timer_s = max(
                0.0, self.game_state.damage_boost_timer_s - dt
            )
            if self.game_state.damage_boost_timer_s <= 0.0:
                self.bullet_damage = self._base_bullet_damage
                self.game_state.damage_boost_multiplier = 1.0
            else:
                self.bullet_damage = int(
                    round(
                        self._base_bullet_damage
                        * float(self.game_state.damage_boost_multiplier)
                    )
                )
        else:
            self.bullet_damage = self._base_bullet_damage

        # Global systems
        self._shot_cooldown_s = max(0.0, self._shot_cooldown_s - dt)
        self.app.event_manager.emit(TIMER_TICK, {"dt": dt})

        import pygame

        # Shooting (SPACE) -> emits PROJECTILE_FIRED for decoupling.
        if self._shot_cooldown_s <= 0.0 and pygame.key.get_pressed()[pygame.K_SPACE]:
            self._shot_cooldown_s = 0.22
            x = self.player.x + self.player.width / 2 - 4
            y = self.player.y
            self.app.event_manager.emit(
                PROJECTILE_FIRED,
                {"x": x, "y": y, "vx": 0.0, "vy": -260.0, "damage": self.bullet_damage},
            )

        # Subclass update (spawns, items, boss logic).
        self._update_layer(dt)
        self._spawn_enemies(dt)

        # Update entities.
        for e in self.enemies:
            if e.alive:
                e.target = self.player
                e.tick_touch_cd(dt)
                e.update(dt)

        for p in self.player_projectiles:
            p.update(dt)
        for p in self.enemy_projectiles:
            p.update(dt)

        # Cull projectiles off-screen.
        h = self.app.settings.height
        for p in self.player_projectiles:
            if p.alive and (p.y + p.height < 0 or p.y > h + 100):
                p.alive = False
        for p in self.enemy_projectiles:
            if p.alive and (p.y + p.height < -100 or p.y > h + 100):
                p.alive = False

        # Collisions:
        # 1) player bullets -> enemies
        for p in self.player_projectiles:
            if not p.alive:
                continue
            for e in self.enemies:
                if not e.alive:
                    continue
                if CollisionSystem.intersects(p, e):
                    p.alive = False
                    died = e.take_damage(p.damage)
                    if died:
                        self.app.event_manager.emit(
                            ENEMY_KILLED, {"enemy": e, "points": e.points}
                        )
                    break

        # 2) enemy bullets -> player
        for p in self.enemy_projectiles:
            if not p.alive or self.player is None:
                continue
            if CollisionSystem.intersects(p, self.player):
                p.alive = False
                self.app.event_manager.emit(
                    PLAYER_HIT, {"damage": p.damage, "source": p}
                )

        # 3) enemy touch -> player
        for e in self.enemies:
            if not e.alive or self.player is None:
                continue
            if CollisionSystem.intersects(e, self.player) and e.try_deal_touch():
                self.app.event_manager.emit(
                    PLAYER_HIT, {"damage": e.touch_damage, "source": e}
                )

        self._check_end_conditions()

    # --- Rendering (split for post-processing pipeline) ---
    def render_background(self, surface: "pygame.Surface") -> None:
        """Scrolling neon grid background (parallax)."""
        import pygame
        from core.theme import BG_BLACK, NEON_CYAN, NEON_CYAN_SOFT

        surface.fill(BG_BLACK)

        w, h = surface.get_size()
        t = self.game_state.elapsed_s

        # Two layers of grid to mimic parallax.
        layers = [
            {"step": 22, "speed": 18.0, "color": NEON_CYAN_SOFT, "alpha": 70},
            {"step": 44, "speed": 9.0, "color": NEON_CYAN, "alpha": 120},
        ]

        for layer in layers:
            step = layer["step"]
            speed = layer["speed"]
            color = layer["color"]
            alpha = layer["alpha"]

            offset_x = int((t * speed) % step)
            offset_y = int((t * speed * 0.75) % step)

            overlay = pygame.Surface((w, h), flags=pygame.SRCALPHA)

            for x in range(-step + offset_x, w + step, step):
                pygame.draw.line(overlay, (*color, alpha), (x, 0), (x, h), 1)
            for y in range(-step + offset_y, h + step, step):
                pygame.draw.line(overlay, (*color, alpha), (0, y), (w, y), 1)

            surface.blit(overlay, (0, 0))

    def render_entities(self, surface: "pygame.Surface") -> None:
        # Entities.
        if self.player is not None:
            self.player.render(surface)
        for e in self.enemies:
            if e.alive:
                e.render(surface)
        for p in self.player_projectiles:
            if p.alive:
                p.render(surface)
        for p in self.enemy_projectiles:
            if p.alive:
                p.render(surface)

        # Items (loot).
        for it in self.items:
            if it.alive:
                it.render(surface)

    def render_effects(self, surface: "pygame.Surface") -> None:
        self.effect_manager.render(surface)

    def render_ui(self, surface: "pygame.Surface") -> None:
        import pygame

        font = pygame.font.SysFont(None, 22)
        hud = font.render(
            f"Score: {self.game_state.score}   Lives: {self.game_state.lives}   Shield: {self.game_state.shield}   Time: {self.game_state.elapsed_s:.1f}s",
            True,
            (220, 235, 255),
        )
        surface.blit(hud, (16, 14))

    def render(self, screen: "pygame.Surface") -> None:
        # BaseLayerScene is rendered to internal surface; GameApp will upscale + post-process.
        self.render_background(screen)
        self.render_entities(screen)
        self.render_effects(screen)
        self.render_ui(screen)
        self._apply_fade_overlay(screen)


# Compatibility alias for the requested architecture wording.
class GameplayScene(BaseLayerScene):
    """Gameplay base (movement/combat) with separated render phases."""


    # --- Event handlers ---
    def _on_timer_tick(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        self.game_state.elapsed_s += float(payload.get("dt", 0.0))

    def _on_player_hit(self, payload: Any) -> None:
        if self.game_state.has_ended:
            return
        if not isinstance(payload, dict):
            damage = 1
        else:
            damage = int(payload.get("damage", 1))

        # Juice feedback
        self.effect_manager.add(ScreenFlashEffect(duration_s=0.15))

        shield = int(self.game_state.shield)
        if shield > 0:
            absorbed = min(shield, damage)
            self.game_state.shield = shield - absorbed
            remaining = damage - absorbed
        else:
            remaining = damage

        self.game_state.lives -= max(0, remaining)
        if self.game_state.lives <= 0:
            self.app.event_manager.emit(GAME_OVER_CONDITION)
            self.app.event_manager.emit(LIVES_ZERO)

    def _on_enemy_killed(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        points = int(payload.get("points", 1))
        self.game_state.score += max(0, points)

        enemy = payload.get("enemy")
        if enemy is not None:
            ex = float(getattr(enemy, "x", 0.0)) + getattr(enemy, "width", 0) / 2
            ey = float(getattr(enemy, "y", 0.0)) + getattr(enemy, "height", 0) / 2
            self.effect_manager.add(
                ExplosionEffect(duration_s=0.45, x=ex, y=ey, count=12, rng_seed=random.randint(0, 1_000_000))
            )

    def _on_projectile_fired(self, payload: Any) -> None:
        if not isinstance(payload, dict) or self.player is None:
            return

        x = float(payload.get("x", 0.0))
        y = float(payload.get("y", 0.0))
        vx = float(payload.get("vx", 0.0))
        vy = float(payload.get("vy", -260.0))
        damage = int(payload.get("damage", 1))

        self.effect_manager.add(
            MuzzleFlashEffect(duration_s=0.05, x=x + 4, y=y, radius=12.0)
        )

        self.player_projectiles.append(
            Projectile(
                x=x,
                y=y,
                width=8,
                height=16,
                vx=vx,
                vy=vy,
                damage=damage,
                from_player=True,
            )
        )

    def _on_system_pulse_used(self, payload: Any) -> None:
        """Damages enemies within radius (collision system lives in BaseLayerScene)."""
        if not isinstance(payload, dict):
            return
        if self.game_state.has_ended:
            return

        x = float(payload.get("x", 0.0))
        y = float(payload.get("y", 0.0))
        radius = float(payload.get("radius", 90.0))
        damage = int(payload.get("damage", 8))

        for e in self.enemies[:]:
            if not getattr(e, "alive", True):
                continue
            ex = float(getattr(e, "x", 0.0)) + getattr(e, "width", 0) / 2
            ey = float(getattr(e, "y", 0.0)) + getattr(e, "height", 0) / 2
            if ((ex - x) ** 2 + (ey - y) ** 2) <= radius * radius:
                died = e.take_damage(damage)
                if died:
                    self.app.event_manager.emit(
                        ENEMY_KILLED, {"enemy": e, "points": e.points}
                    )

    def _on_game_over(self, payload: Any = None) -> None:
        self.game_state.is_victory = False
        if self.game_state.has_ended:
            return
        self.game_state.has_ended = True
        self.app.switch_scene("game_over")

