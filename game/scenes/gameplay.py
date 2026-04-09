from __future__ import annotations

from typing import Any

import random

from core.base_scene import BaseScene
from core.collision_system import CollisionSystem
from core.effect_manager import EffectManager
from core.game_events import (
    ENEMY_KILLED,
    GAME_OVER_CONDITION,
    GAME_WIN_CONDITION,
    LIVES_ZERO,
    PLAYER_HIT,
    PROJECTILE_FIRED,
    TIME_UP,
    TIMER_TICK,
)
from core.game_state import GameState
from core.effects.explosion import ExplosionEffect
from core.effects.muzzle_flash import MuzzleFlashEffect
from core.effects.screen_flash import ScreenFlashEffect
from entities.enemy import Enemy
from entities.player import Player
from entities.projectile import Projectile


class GameplayScene(BaseScene):
    def __init__(self, app: Any, game_state: GameState) -> None:
        super().__init__(app, game_state)
        self.player: Player | None = None
        self.enemy: Enemy | None = None
        self.projectiles: list[Projectile] = []

        self._spawn_delay_s: float = 0.0
        self._shot_cooldown_s: float = 0.0
        self._event_tokens: list[tuple[str, Any]] = []
        self.effect_manager = EffectManager()

        # Subscribe to gameplay events to decouple logic.
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
        self._event_tokens.append(
            self.app.event_manager.subscribe(TIMER_TICK, self._on_timer_tick)
        )
        self._event_tokens.append(
            self.app.event_manager.subscribe(GAME_WIN_CONDITION, self._on_win)
        )
        self._event_tokens.append(
            self.app.event_manager.subscribe(GAME_OVER_CONDITION, self._on_game_over)
        )
        self._event_tokens.append(
            self.app.event_manager.subscribe(LIVES_ZERO, self._on_game_over)
        )
        self._event_tokens.append(
            self.app.event_manager.subscribe(TIME_UP, self._on_win)
        )

    def enter(self, prev_scene: BaseScene | None) -> None:
        super().enter(prev_scene)
        self.game_state.score = 0
        self.game_state.is_victory = False
        self.game_state.lives = int(self.app.settings.initial_lives)
        self.game_state.elapsed_s = 0.0
        self.game_state.has_ended = False

        w, h = self.app.settings.width, self.app.settings.height
        self.player = Player(x=w * 0.5, y=h * 0.75, width=26, height=26)
        self.enemy = Enemy(x=w * 0.5, y=h * 0.15, width=28, height=28, bounds_w=w)
        self.projectiles = []

        self._spawn_delay_s = 0.0
        self._shot_cooldown_s = 0.0
        self.effect_manager = EffectManager()

    def exit(self) -> None:
        # Unsubscribe so switching scenes doesn't duplicate handlers.
        for token in self._event_tokens:
            self.app.event_manager.unsubscribe(token)
        self._event_tokens.clear()

    def handle_event(self, event: Any) -> None:
        # Gameplay works primarily through polling in update().
        pass

    def _try_end(self, end_scene: str) -> None:
        if self.game_state.has_ended:
            return
        self.game_state.has_ended = True
        self.app.switch_scene(end_scene)

    # --- Event handlers ---
    def _on_player_hit(self, payload: Any) -> None:
        # payload example: {"damage": 1, "source": enemy, ...}
        if self.game_state.has_ended:
            return
        damage = int(payload.get("damage", 1)) if isinstance(payload, dict) else 1
        self.game_state.lives -= max(0, damage)

        # Juice: red flash on hit.
        self.effect_manager.add(ScreenFlashEffect(duration_s=0.15))

        if self.game_state.lives <= 0:
            self.app.event_manager.emit(GAME_OVER_CONDITION)
            self.app.event_manager.emit(LIVES_ZERO)

    def _on_enemy_killed(self, payload: Any) -> None:
        # payload example: {"enemy": enemy, "points": 1}
        if self.game_state.has_ended:
            return
        points = 1
        if isinstance(payload, dict):
            points = int(payload.get("points", 1))

        # Juice: explosion at enemy position.
        enemy = payload.get("enemy") if isinstance(payload, dict) else None
        if enemy is not None:
            self.effect_manager.add(
                ExplosionEffect(
                    duration_s=0.45,
                    x=float(getattr(enemy, "x", 0.0)) + getattr(enemy, "width", 0) / 2,
                    y=float(getattr(enemy, "y", 0.0)) + getattr(enemy, "height", 0) / 2,
                    count=12,
                    rng_seed=int(self.game_state.score + 1),
                )
            )
        self.game_state.score += max(0, points)

        if self.game_state.score >= int(self.app.settings.kills_to_win):
            self.app.event_manager.emit(GAME_WIN_CONDITION)

        # Schedule enemy respawn (keeps collision logic simple).
        self._spawn_delay_s = 0.6
        self.enemy = None

    def _on_projectile_fired(self, payload: Any) -> None:
        # payload example: {"x": ..., "y": ..., "vx": ..., "vy": ...}
        if self.player is None:
            return
        if not isinstance(payload, dict):
            return
        x = float(payload.get("x", 0.0))
        y = float(payload.get("y", 0.0))
        vx = float(payload.get("vx", 0.0))
        vy = float(payload.get("vy", -260.0))

        # Juice: muzzle flash near player.
        self.effect_manager.add(
            MuzzleFlashEffect(
                duration_s=0.05,
                x=float(self.player.x) + self.player.width / 2,
                y=float(self.player.y),
                radius=12.0,
            )
        )

        self.projectiles.append(Projectile(x=x, y=y, width=8, height=16, vx=vx, vy=vy))

    def _on_timer_tick(self, payload: Any) -> None:
        # payload example: {"dt": dt}
        if self.game_state.has_ended:
            return
        dt = float(payload.get("dt", 0.0)) if isinstance(payload, dict) else 0.0
        self.game_state.elapsed_s += dt

        if self.game_state.elapsed_s >= float(self.app.settings.survival_seconds_to_win):
            self.app.event_manager.emit(TIME_UP)

    def _on_win(self, payload: Any = None) -> None:
        self.game_state.is_victory = True
        self._try_end("victory")

    def _on_game_over(self, payload: Any = None) -> None:
        self.game_state.is_victory = False
        self._try_end("game_over")

    def update(self, dt: float) -> None:
        super().update(dt)

        import pygame

        if self.player is None:
            return

        self._shot_cooldown_s = max(0.0, self._shot_cooldown_s - dt)
        self.app.event_manager.emit(TIMER_TICK, {"dt": dt})
        self.effect_manager.update(dt)

        # Shoot with SPACE.
        if self._shot_cooldown_s <= 0.0 and pygame.key.get_pressed()[pygame.K_SPACE]:
            self._shot_cooldown_s = 0.22
            px = self.player.x + self.player.width / 2 - 4
            py = self.player.y
            self.app.event_manager.emit(
                PROJECTILE_FIRED,
                {"x": px, "y": py, "vx": 0.0, "vy": -260.0},
            )

        self.player.update(dt)
        if self.enemy is not None:
            self.enemy.update(dt)

        for p in self.projectiles:
            p.update(dt)

        # Cull projectiles off-screen.
        h = self.app.settings.height
        for p in self.projectiles:
            if p.alive and (p.y + p.height < 0 or p.y > h + 100):
                p.alive = False

        # Collisions: projectile -> enemy.
        for p in self.projectiles:
            if not p.alive:
                continue
            if self.enemy is not None and CollisionSystem.intersects(p, self.enemy):
                p.alive = False
                self.enemy.alive = False
                self.app.event_manager.emit(
                    ENEMY_KILLED,
                    {"enemy": self.enemy, "points": 1},
                )
                break

        # Respawn enemy.
        if self.enemy is None and self._spawn_delay_s > 0:
            self._spawn_delay_s = max(0.0, self._spawn_delay_s - dt)
            if self._spawn_delay_s <= 0.0:
                w = self.app.settings.width
                h = self.app.settings.height
                self.enemy = Enemy(
                    x=random.uniform(80, w - 80),
                    y=h * 0.15,
                    width=28,
                    height=28,
                    bounds_w=w,
                    speed_x=random.choice([-80.0, 80.0]),
                )

        # Collision: enemy -> player.
        if (
            self.enemy is not None
            and self.enemy.alive
            and CollisionSystem.intersects(self.player, self.enemy)
        ):
            # Apply damage as an event to decouple gameplay logic.
            self.app.event_manager.emit(
                PLAYER_HIT,
                {"damage": 1, "enemy": self.enemy},
            )

    def render(self, screen: Any) -> None:
        import pygame

        screen.fill((8, 12, 20))

        # Simple HUD.
        font = pygame.font.SysFont(None, 22)
        hud = font.render(
            f"Score: {self.game_state.score}   Lives: {self.game_state.lives}   Time: {self.game_state.elapsed_s:.1f}s",
            True,
            (220, 235, 255),
        )
        screen.blit(hud, (16, 14))

        if self.player is not None:
            self.player.render(screen)
        if self.enemy is not None and self.enemy.alive:
            self.enemy.render(screen)
        for p in self.projectiles:
            if p.alive:
                p.render(screen)

        self.effect_manager.render(screen)
        self._apply_fade_overlay(screen)

