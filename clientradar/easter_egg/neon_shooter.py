from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

import pygame


WIDTH, HEIGHT = 1280, 720
INTERNAL_W, INTERNAL_H = 320, 180
FPS = 60
LANE_X = [36, 92, 148, 204, 260]
DEFENSE_LINE_Y = INTERNAL_H - 34
LEVEL_TARGETS = [20, 32, 46]
MAX_BREACHES = 10

NEON_CYAN = (63, 255, 222)
NEON_MAGENTA = (255, 87, 214)
NEON_PURPLE = (123, 88, 255)
BG = (6, 7, 14)
GRID = (21, 30, 50)


@dataclass
class Player:
    x: float
    y: float
    speed: float = 190.0
    radius: int = 7
    cooldown: float = 0.0
    hp: int = 7


@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    life: float = 1.2
    radius: int = 2


@dataclass
class EnemyBullet:
    x: float
    y: float
    vx: float
    vy: float
    life: float = 2.2
    radius: int = 2


@dataclass
class Enemy:
    x: float
    y: float
    lane_x: float
    vx: float
    vy: float
    spin: float
    phase: float
    hp: int
    radius: int
    kind: str
    shoot_cd: float


@dataclass
class PowerUp:
    x: float
    y: float
    vy: float
    kind: str
    life: float = 8.0
    radius: int = 6


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]


@dataclass
class AfterImage:
    x: float
    y: float
    life: float


class Effects:
    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.after_images: list[AfterImage] = []
        self.shake = 0.0
        self.flash = 0.0

    def add_shake(self, amount: float, max_value: float = 1.0) -> None:
        # Clamp shake to avoid unreadable visuals on heavy action frames.
        self.shake = min(max_value, self.shake + amount)

    def burst(
        self,
        x: float,
        y: float,
        count: int,
        color: tuple[int, int, int],
        life_scale: float,
        spread_bias: float = 1.0,
    ) -> None:
        for _ in range(count):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(20, 95) * spread_bias
            vec = pygame.math.Vector2(1, 0).rotate_rad(angle)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=vec.x * speed,
                    vy=vec.y * speed,
                    life=random.uniform(0.08, life_scale),
                    color=color,
                )
            )

    def update(self, dt: float) -> None:
        alive: list[Particle] = []
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.98
            p.vy *= 0.98
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self.particles = alive[:700]

        trails: list[AfterImage] = []
        for after in self.after_images:
            after.life -= dt
            if after.life > 0:
                trails.append(after)
        self.after_images = trails
        self.shake = max(0.0, self.shake - dt * 1.35)
        self.flash = max(0.0, self.flash - dt * 1.9)

    def shake_offset(self) -> tuple[int, int]:
        if self.shake <= 0:
            return (0, 0)
        amp = int(4 + self.shake * 9)
        return (random.randint(-amp, amp), random.randint(-amp, amp))


class PlayerController:
    def __init__(self, player: Player, effects: Effects) -> None:
        self.player = player
        self.effects = effects
        self.trail_emit = 0.0
        self.tilt = 0.0

    def reset(self) -> None:
        self.player = Player(INTERNAL_W / 2, INTERNAL_H - 22)
        self.trail_emit = 0.0
        self.tilt = 0.0

    def update(self, dt: float, score: int, rapid_fire: bool) -> list[Bullet]:
        keys = pygame.key.get_pressed()
        dx = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        self.player.y = DEFENSE_LINE_Y

        if dx:
            self.player.x += dx * self.player.speed * dt
            self.trail_emit -= dt
            if self.trail_emit <= 0:
                self.effects.after_images.append(AfterImage(self.player.x, self.player.y, 0.22))
                self.trail_emit = 0.028

        target_tilt = dx * 18.0
        self.tilt += (target_tilt - self.tilt) * min(1.0, dt * 12.0)
        self.player.x = max(14, min(INTERNAL_W - 14, self.player.x))

        self.player.cooldown = max(0.0, self.player.cooldown - dt)
        shooting = keys[pygame.K_SPACE] or keys[pygame.K_RETURN]
        if not shooting or self.player.cooldown > 0.0:
            return []

        self.player.cooldown = 0.05 if rapid_fire else 0.095
        shots = [Bullet(self.player.x, self.player.y - 10, 0.0, -270.0)]
        spread = 0.05 if score < 350 else 0.11
        if score >= 600:
            shots.extend(
                [
                    Bullet(self.player.x - 5, self.player.y - 8, -22.0, -260.0),
                    Bullet(self.player.x + 5, self.player.y - 8, 22.0, -260.0),
                ]
            )
        elif score >= 350:
            shots.extend(
                [
                    Bullet(self.player.x - 4, self.player.y - 8, -8.0, -255.0),
                    Bullet(self.player.x + 4, self.player.y - 8, 8.0, -255.0),
                ]
            )
        self.effects.burst(self.player.x, self.player.y - 6, 4, NEON_CYAN, 0.2, spread)
        return shots


class SpawnDirector:
    def __init__(self) -> None:
        self.spawn_timer = 1.0

    def reset(self) -> None:
        self.spawn_timer = 1.0

    def next_wave(self, score: int) -> int:
        return 1 + score // 250

    def update(self, dt: float, score: int, level: int) -> list[Enemy]:
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return []

        tension = min(1.35, 0.92 + score / 520.0 + (level - 1) * 0.14)
        self.spawn_timer = random.uniform(0.82, 1.3) / tension
        formations = [
            [0, 2, 4],
            [1, 3],
            [0, 1, 2, 3, 4],
            [0, 4],
            [2],
            [1, 2, 3],
            [0, 2],
            [2, 4],
        ]
        pattern = random.choice(formations)
        enemies: list[Enemy] = []
        for lane_idx in pattern:
            lane_x = LANE_X[lane_idx]
            kind = self._pick_kind(level, score)
            enemies.append(self._build_enemy(kind, lane_x, tension))
        return enemies

    def _pick_kind(self, level: int, score: int) -> str:
        roll = random.random()
        if level >= 3 and roll < 0.23:
            return "shooter"
        if level >= 2 and roll < 0.45:
            return "brute"
        if score > 200 and roll < 0.7:
            return "spinner"
        return "drone"

    def _build_enemy(self, kind: str, lane_x: float, tension: float) -> Enemy:
        phase = random.uniform(0, 6.283)
        common = {"lane_x": lane_x, "x": lane_x, "y": -12, "phase": phase, "kind": kind}
        if kind == "drone":
            return Enemy(
                **common,
                vx=0.0,
                vy=random.uniform(17, 25) * tension,
                spin=random.uniform(-70, 70),
                hp=1,
                radius=7,
                shoot_cd=0.0,
            )
        if kind == "spinner":
            return Enemy(
                **common,
                vx=0.0,
                vy=random.uniform(20, 30) * tension,
                spin=random.uniform(-180, 180),
                hp=2,
                radius=9,
                shoot_cd=0.0,
            )
        if kind == "brute":
            return Enemy(
                **common,
                vx=0.0,
                vy=random.uniform(14, 21) * tension,
                spin=random.uniform(-45, 45),
                hp=4,
                radius=12,
                shoot_cd=0.0,
            )
        return Enemy(
            **common,
            vx=0.0,
            vy=random.uniform(14, 19) * tension,
            spin=random.uniform(-80, 80),
            hp=2,
            radius=10,
            shoot_cd=random.uniform(1.3, 2.2),
        )


class CombatSystem:
    def __init__(self, effects: Effects) -> None:
        self.effects = effects
        self.combo = 0
        self.combo_decay = 0.0

    def reset(self) -> None:
        self.combo = 0
        self.combo_decay = 0.0

    def update_combo(self, dt: float) -> None:
        if self.combo <= 0:
            return
        self.combo_decay -= dt
        if self.combo_decay <= 0:
            self.combo = max(0, self.combo - 1)
            self.combo_decay = 0.4 if self.combo else 0.0

    def destroy_enemy(self, enemy: Enemy) -> int:
        base_points = {"drone": 10, "spinner": 16, "shooter": 24, "brute": 32}[enemy.kind]
        self.combo = min(9, self.combo + 1)
        self.combo_decay = 1.2
        self.effects.add_shake(0.12, max_value=0.75)
        self.effects.flash = min(1.0, self.effects.flash + 0.18)
        self.effects.burst(enemy.x, enemy.y, 20, NEON_PURPLE, 0.56)
        return int(base_points * (1.0 + self.combo * 0.08))

    @staticmethod
    def collides(ax: float, ay: float, ar: int, bx: float, by: float, br: int) -> bool:
        return (ax - bx) ** 2 + (ay - by) ** 2 < (ar + br) ** 2


class SpriteFactory:
    @staticmethod
    def build_player_sprite() -> pygame.Surface:
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        hull = [(16, 3), (26, 24), (16, 19), (6, 24)]
        core = [(16, 6), (22, 20), (16, 15), (10, 20)]
        wing_l = [(10, 15), (3, 24), (10, 22), (13, 16)]
        wing_r = [(22, 15), (29, 24), (22, 22), (19, 16)]
        cockpit = [(16, 9), (18, 13), (16, 12), (14, 13)]
        pygame.draw.polygon(surf, (160, 255, 240, 235), hull)
        pygame.draw.polygon(surf, (40, 218, 208, 255), core)
        pygame.draw.polygon(surf, (100, 235, 220, 238), wing_l)
        pygame.draw.polygon(surf, (100, 235, 220, 238), wing_r)
        pygame.draw.polygon(surf, (255, 255, 255, 175), cockpit)
        pygame.draw.line(surf, (130, 255, 240, 160), (16, 19), (16, 28), 2)
        return surf

    @staticmethod
    def build_enemy_sprite(kind: str) -> pygame.Surface:
        if kind == "drone":
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 120, 210, 220), (12, 12), 9, 2)
            pygame.draw.circle(surf, (255, 75, 165, 255), (12, 12), 5)
            pygame.draw.circle(surf, (255, 240, 250, 150), (12, 12), 1)
            return surf
        if kind == "spinner":
            surf = pygame.Surface((28, 28), pygame.SRCALPHA)
            pts = [(14, 2), (19, 9), (26, 14), (19, 19), (14, 26), (9, 19), (2, 14), (9, 9)]
            pygame.draw.polygon(surf, (255, 130, 220, 230), pts)
            pygame.draw.polygon(surf, (255, 85, 180, 255), [(14, 6), (20, 14), (14, 22), (8, 14)])
            return surf
        if kind == "brute":
            surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 125, 205, 220), (18, 18), 15, 3)
            pygame.draw.circle(surf, (255, 85, 165, 255), (18, 18), 10)
            for i in range(6):
                ang = i * (math.pi / 3)
                x1 = 18 + int(math.cos(ang) * 9)
                y1 = 18 + int(math.sin(ang) * 9)
                x2 = 18 + int(math.cos(ang) * 14)
                y2 = 18 + int(math.sin(ang) * 14)
                pygame.draw.line(surf, (255, 210, 245, 170), (x1, y1), (x2, y2), 2)
            return surf
        surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 110, 205, 230), (7, 7, 16, 16), border_radius=4)
        pygame.draw.rect(surf, (255, 70, 160, 255), (10, 10, 10, 10), border_radius=3)
        pygame.draw.line(surf, (255, 220, 245, 170), (15, 0), (15, 7), 2)
        pygame.draw.line(surf, (255, 220, 245, 170), (15, 23), (15, 30), 2)
        return surf


class PostProcessor:
    def __init__(self) -> None:
        self.scanline_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.vignette_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._build_post_overlays()

    def process(self, base: pygame.Surface, shake: float, flash: float) -> pygame.Surface:
        bloomed = self._apply_bloom(base)
        out = bloomed.copy()
        cyan_layer = bloomed.copy()
        cyan_layer.fill((40, 255, 220), special_flags=pygame.BLEND_MULT)
        magenta_layer = bloomed.copy()
        magenta_layer.fill((255, 40, 175), special_flags=pygame.BLEND_MULT)
        shift = 2 + int(shake * 10)
        # Fake chromatic aberration: separate cyan/magenta channels with tiny offset.
        out.blit(cyan_layer, (-shift, 0), special_flags=pygame.BLEND_ADD)
        out.blit(magenta_layer, (shift, 0), special_flags=pygame.BLEND_ADD)
        out.blit(self.scanline_overlay, (0, 0))
        if random.random() < 0.24:
            # Copy random horizontal strips to create retro glitch artifacts.
            for _ in range(random.randint(2, 7)):
                y = random.randint(0, HEIGHT - 28)
                h = random.randint(2, 11)
                dx = random.randint(-24, 24)
                segment = out.subsurface((0, y, WIDTH, h)).copy()
                out.blit(segment, (dx, y))
        if flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            strength = int(70 * flash)
            overlay.fill((180, 245, 255, strength))
            out.blit(overlay, (0, 0), special_flags=pygame.BLEND_ADD)
        out.blit(self.vignette_overlay, (0, 0))
        return out

    @staticmethod
    def _apply_bloom(base: pygame.Surface) -> pygame.Surface:
        small = pygame.transform.smoothscale(base, (WIDTH // 5, HEIGHT // 5))
        blur1 = pygame.transform.smoothscale(small, (WIDTH, HEIGHT))
        tiny = pygame.transform.smoothscale(base, (WIDTH // 8, HEIGHT // 8))
        blur2 = pygame.transform.smoothscale(tiny, (WIDTH, HEIGHT))
        out = base.copy()
        blur1.set_alpha(68)
        blur2.set_alpha(34)
        out.blit(blur1, (0, 0))
        out.blit(blur2, (0, 0))
        return out

    def _build_post_overlays(self) -> None:
        self.scanline_overlay.fill((0, 0, 0, 0))
        for y in range(0, HEIGHT, 3):
            pygame.draw.line(self.scanline_overlay, (0, 0, 0, 34), (0, y), (WIDTH, y), 1)
        self.vignette_overlay.fill((0, 0, 0, 0))
        center_x = WIDTH / 2
        center_y = HEIGHT / 2
        max_dist = (center_x**2 + center_y**2) ** 0.5
        for y in range(HEIGHT):
            for x in range(WIDTH):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5 / max_dist
                alpha = int(max(0, min(170, (dist**1.85) * 182)))
                if alpha:
                    self.vignette_overlay.set_at((x, y), (0, 0, 0, alpha))


class SceneRenderer:
    def __init__(self) -> None:
        # The game is rendered in a low internal resolution and then upscaled.
        # Why: pixel-art-like sharp gameplay and cheaper effects processing.
        self.internal = pygame.Surface((INTERNAL_W, INTERNAL_H)).convert()
        self.overlay = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        self.glow_layer = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        self.nebula_overlay = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        self.font = pygame.font.SysFont("consolas", 13)
        self.big_font = pygame.font.SysFont("consolas", 24, bold=True)
        self.hud_font = pygame.font.SysFont("consolas", 28, bold=True)
        self.hud_small = pygame.font.SysFont("consolas", 20, bold=True)
        self.hud_title = pygame.font.SysFont("consolas", 78, bold=True)
        self.player_sprite = SpriteFactory.build_player_sprite()
        self.enemy_sprites = {
            "drone": SpriteFactory.build_enemy_sprite("drone"),
            "spinner": SpriteFactory.build_enemy_sprite("spinner"),
            "brute": SpriteFactory.build_enemy_sprite("brute"),
            "shooter": SpriteFactory.build_enemy_sprite("shooter"),
        }
        self.stars = [
            (random.randint(0, INTERNAL_W - 1), random.randint(0, INTERNAL_H - 1), random.random())
            for _ in range(62)
        ]
        self._build_nebula_overlay()

    def render(
        self,
        screen: pygame.Surface,
        time_s: float,
        player: Player,
        player_tilt: float,
        bullets: Iterable[Bullet],
        enemy_bullets: Iterable[EnemyBullet],
        enemies: Iterable[Enemy],
        powerups: Iterable[PowerUp],
        effects: Effects,
        score: int,
        wave: int,
        level: int,
        level_progress: int,
        level_target: int,
        breaches: int,
        max_breaches: int,
        combo: int,
        rapid_fire_timer: float,
        game_over: bool,
        victory: bool,
        paused: bool,
        post: PostProcessor,
    ) -> None:
        self.internal.fill(BG)
        self.glow_layer.fill((0, 0, 0, 0))
        self._draw_grid(time_s)
        self._draw_after_images(effects.after_images, player.radius)
        self._draw_entities(time_s, player, player_tilt, bullets, enemy_bullets, enemies)
        self._draw_powerups(time_s, powerups)
        self._draw_particles(effects.particles)
        self._draw_glitch_overlay()

        # We draw glow separately and add it at the end so entities keep clear edges,
        # while still getting bright neon halos.
        self.internal.blit(self.glow_layer, (0, 0), special_flags=pygame.BLEND_ADD)
        scaled = pygame.transform.scale(self.internal, (WIDTH, HEIGHT))
        final_surface = post.process(scaled, effects.shake, effects.flash)
        screen.blit(final_surface, effects.shake_offset())
        self._draw_hud(
            score,
            wave,
            level,
            level_progress,
            level_target,
            breaches,
            max_breaches,
            combo,
            player.hp,
            rapid_fire_timer,
            game_over,
            victory,
            paused,
            screen,
        )

    def _draw_grid(self, time_s: float) -> None:
        pulse = 0.5 + 0.5 * math.sin(time_s * 1.4)
        y_shift = int((time_s * 22) % 16)
        x_shift = int((time_s * 14) % 16)
        self.internal.blit(self.nebula_overlay, (0, int(math.sin(time_s * 0.4) * 2)))
        for x, y, size in self.stars:
            radius = 1 if size < 0.65 else 2
            col = (
                80 + int(65 * pulse * size),
                110 + int(80 * pulse * size),
                140 + int(90 * pulse * size),
            )
            sy = (y + int(time_s * (4 + size * 10))) % INTERNAL_H
            pygame.draw.circle(self.internal, col, (x, sy), radius)
        for y in range(-16, INTERNAL_H + 16, 16):
            pygame.draw.line(self.internal, GRID, (0, y + y_shift), (INTERNAL_W, y + y_shift), 1)
        for x in range(-16, INTERNAL_W + 16, 16):
            pygame.draw.line(self.internal, GRID, (x + x_shift, 0), (x + x_shift, INTERNAL_H), 1)
        pygame.draw.line(
            self.internal,
            (110, 210, 255),
            (0, DEFENSE_LINE_Y + 8),
            (INTERNAL_W, DEFENSE_LINE_Y + 8),
            2,
        )

    def _draw_after_images(self, after_images: Iterable[AfterImage], player_radius: int) -> None:
        for after in after_images:
            alpha = int(max(0, min(255, (after.life / 0.22) * 140)))
            if alpha <= 0:
                continue
            pos = (int(after.x), int(after.y))
            ghost = self.player_sprite.copy()
            ghost.fill((80, 255, 220, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            self.internal.blit(ghost, ghost.get_rect(center=pos))
            pygame.draw.circle(self.glow_layer, (80, 255, 220, min(120, alpha)), pos, player_radius + 5)

    def _draw_entities(
        self,
        time_s: float,
        player: Player,
        player_tilt: float,
        bullets: Iterable[Bullet],
        enemy_bullets: Iterable[EnemyBullet],
        enemies: Iterable[Enemy],
    ) -> None:
        player_pos = (int(player.x), int(player.y))
        ship_angle = player_tilt + math.sin(time_s * 5.8) * 2.6
        ship = pygame.transform.rotozoom(self.player_sprite, ship_angle, 1.0)
        pygame.draw.circle(self.glow_layer, (52, 255, 220, 82), player_pos, player.radius + 7)
        self.internal.blit(ship, ship.get_rect(center=player_pos))
        thr_alpha = 130 + int(60 * abs(math.sin(time_s * 18)))
        thruster_pos = (
            int(player.x - math.sin(math.radians(ship_angle)) * 7),
            int(player.y + math.cos(math.radians(ship_angle)) * 8),
        )
        pygame.draw.circle(self.glow_layer, (80, 240, 255, min(110, thr_alpha)), thruster_pos, 3)

        for bullet in bullets:
            bpos = (int(bullet.x), int(bullet.y))
            pygame.draw.circle(self.glow_layer, (130, 255, 240, 70), bpos, bullet.radius + 3)
            pygame.draw.circle(self.internal, (240, 255, 255), bpos, bullet.radius + 1)
            pygame.draw.circle(self.internal, NEON_CYAN, bpos, bullet.radius)

        for bullet in enemy_bullets:
            bpos = (int(bullet.x), int(bullet.y))
            pygame.draw.circle(self.glow_layer, (255, 140, 210, 70), bpos, bullet.radius + 3)
            pygame.draw.circle(self.internal, (255, 210, 235), bpos, bullet.radius + 1)
            pygame.draw.circle(self.internal, (255, 100, 190), bpos, bullet.radius)

        for enemy in enemies:
            epos = (int(enemy.x), int(enemy.y))
            sprite = self.enemy_sprites[enemy.kind]
            angle = (time_s * enemy.spin) % 360
            scale = 1.03 + 0.04 * math.sin(time_s * 4 + enemy.phase)
            rot = pygame.transform.rotozoom(sprite, angle, scale)
            glow_alpha = 82 if enemy.kind != "brute" else 102
            glow_size = enemy.radius + (8 if enemy.kind == "brute" else 6)
            pygame.draw.circle(self.glow_layer, (255, 110, 200, glow_alpha), epos, glow_size)
            self.internal.blit(rot, rot.get_rect(center=epos))

    def _draw_particles(self, particles: Iterable[Particle]) -> None:
        self.overlay.fill((0, 0, 0, 0))
        for p in particles:
            alpha = max(12, min(155, int((p.life * 3.4) * 150)))
            px, py = int(p.x), int(p.y)
            if px < 0 or py < 0 or px >= INTERNAL_W or py >= INTERNAL_H:
                continue
            pygame.draw.circle(self.overlay, (*p.color, alpha), (px, py), 1)
            pygame.draw.circle(self.glow_layer, (*p.color, max(20, alpha // 3)), (px, py), 1)
        self.internal.blit(self.overlay, (0, 0))

    def _draw_powerups(self, time_s: float, powerups: Iterable[PowerUp]) -> None:
        for power in powerups:
            pos = (int(power.x), int(power.y))
            pulse = 0.75 + 0.25 * math.sin(time_s * 8.0 + power.x * 0.1)
            if power.kind == "heal":
                core = (120, 255, 170)
                glow = (90, 255, 150, int(120 * pulse))
            else:
                core = (130, 225, 255)
                glow = (90, 210, 255, int(120 * pulse))
            pygame.draw.circle(self.glow_layer, glow, pos, power.radius + 7)
            pygame.draw.circle(self.internal, (245, 255, 255), pos, power.radius + 1)
            pygame.draw.circle(self.internal, core, pos, power.radius)
            pygame.draw.line(self.internal, (30, 70, 90), (pos[0] - 2, pos[1]), (pos[0] + 2, pos[1]), 1)
            pygame.draw.line(self.internal, (30, 70, 90), (pos[0], pos[1] - 2), (pos[0], pos[1] + 2), 1)

    def _draw_hud(
        self,
        score: int,
        wave: int,
        level: int,
        level_progress: int,
        level_target: int,
        breaches: int,
        max_breaches: int,
        combo: int,
        hp: int,
        rapid_fire_timer: float,
        game_over: bool,
        victory: bool,
        paused: bool,
        screen: pygame.Surface,
    ) -> None:
        x = 22
        y = 14
        lines = [
            (f"SCORE: {score:05d}", NEON_CYAN),
            (f"INTEGRITY: {max(0, hp)}", NEON_MAGENTA),
            (f"WAVE: {wave}", (180, 210, 255)),
            (f"LEVEL: {level}/3", (190, 255, 210)),
            (f"TARGET: {level_progress}/{level_target}", (255, 220, 170)),
            (f"BREACHES: {breaches}/{max_breaches}", (255, 180, 180)),
            (f"COMBO x{1 + combo}", (255, 190, 235)),
            (
                f"RAPID: {rapid_fire_timer:0.1f}s" if rapid_fire_timer > 0 else "RAPID: OFF",
                (180, 255, 220) if rapid_fire_timer > 0 else (120, 165, 155),
            ),
        ]
        for text, color in lines:
            shadow = self.hud_font.render(text, True, (10, 18, 26))
            label = self.hud_font.render(text, True, color)
            screen.blit(shadow, (x + 2, y + 2))
            screen.blit(label, (x, y))
            y += 34

        hint = self.hud_small.render(
            "DEFEND LINE | MOVE: WASD/ARROWS   SHOOT: SPACE   PAUSE: P",
            True,
            (170, 235, 220),
        )
        hint_shadow = self.hud_small.render(
            "DEFEND LINE | MOVE: WASD/ARROWS   SHOOT: SPACE   PAUSE: P", True, (8, 16, 24)
        )
        screen.blit(hint_shadow, (21, HEIGHT - 42))
        screen.blit(hint, (19, HEIGHT - 44))

        if game_over:
            title = self.hud_title.render("SYSTEM BREACHED", True, (255, 125, 140))
            title_shadow = self.hud_title.render("SYSTEM BREACHED", True, (42, 10, 20))
            retry = self.hud_small.render("Press R to retry or ESC to exit", True, (255, 210, 220))
            retry_shadow = self.hud_small.render("Press R to retry or ESC to exit", True, (40, 12, 20))
            rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35))
            screen.blit(title_shadow, (rect.x + 3, rect.y + 3))
            screen.blit(title, rect)
            rrect = retry.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35))
            screen.blit(retry_shadow, (rrect.x + 2, rrect.y + 2))
            screen.blit(retry, rrect)
        elif victory:
            title = self.hud_title.render("AREA SECURED", True, (165, 255, 205))
            title_shadow = self.hud_title.render("AREA SECURED", True, (15, 45, 28))
            msg = self.hud_small.render("All 3 levels completed. ESC to exit.", True, (215, 255, 225))
            msg_shadow = self.hud_small.render(
                "All 3 levels completed. ESC to exit.",
                True,
                (10, 24, 15),
            )
            rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35))
            screen.blit(title_shadow, (rect.x + 3, rect.y + 3))
            screen.blit(title, rect)
            mrect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35))
            screen.blit(msg_shadow, (mrect.x + 2, mrect.y + 2))
            screen.blit(msg, mrect)
        elif paused:
            title = self.hud_title.render("PAUSED", True, (180, 240, 255))
            title_shadow = self.hud_title.render("PAUSED", True, (15, 30, 45))
            hint = self.hud_small.render("Press P to resume", True, (200, 240, 255))
            hint_shadow = self.hud_small.render("Press P to resume", True, (10, 20, 30))
            rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35))
            screen.blit(title_shadow, (rect.x + 3, rect.y + 3))
            screen.blit(title, rect)
            hrect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35))
            screen.blit(hint_shadow, (hrect.x + 2, hrect.y + 2))
            screen.blit(hint, hrect)

    def _draw_glitch_overlay(self) -> None:
        if random.random() < 0.2:
            y = random.randint(0, INTERNAL_H - 4)
            h = random.randint(1, 3)
            color = (random.randint(20, 60), random.randint(90, 155), random.randint(120, 185))
            pygame.draw.rect(self.internal, color, (0, y, INTERNAL_W, h))

    def _build_nebula_overlay(self) -> None:
        self.nebula_overlay.fill((0, 0, 0, 0))
        for _ in range(14):
            x = random.randint(0, INTERNAL_W)
            y = random.randint(0, INTERNAL_H)
            radius = random.randint(20, 55)
            color = random.choice(
                [(70, 40, 120, 24), (40, 80, 145, 18), (80, 30, 80, 20), (20, 110, 120, 14)]
            )
            pygame.draw.circle(self.nebula_overlay, color, (x, y), radius)


class NeonShooter:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("ClientRadar // Neon Breach")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.time = 0.0
        self.game_over = False
        self.victory = False
        self.paused = False
        self.score = 0
        self.wave = 1
        self.level = 1
        self.level_progress = 0
        self.breaches = 0
        self.rapid_fire_timer = 0.0

        self.effects = Effects()
        self.player_controller = PlayerController(Player(INTERNAL_W / 2, INTERNAL_H - 22), self.effects)
        self.spawn_director = SpawnDirector()
        self.combat = CombatSystem(self.effects)
        self.renderer = SceneRenderer()
        self.post = PostProcessor()

        self.bullets: list[Bullet] = []
        self.enemy_bullets: list[EnemyBullet] = []
        self.enemies: list[Enemy] = []
        self.powerups: list[PowerUp] = []

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.033)
            self.time += dt
            self._events()
            if not self.game_over:
                self._update(dt)
            self._render()
            pygame.display.flip()
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_p and not self.game_over and not self.victory:
                    self.paused = not self.paused
                elif self.game_over and event.key == pygame.K_r:
                    self._reset()

    def _reset(self) -> None:
        self.player_controller.reset()
        self.spawn_director.reset()
        self.combat.reset()
        self.effects = Effects()
        self.player_controller.effects = self.effects
        self.combat.effects = self.effects
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()
        self.score = 0
        self.wave = 1
        self.level = 1
        self.level_progress = 0
        self.breaches = 0
        self.game_over = False
        self.victory = False
        self.paused = False
        self.rapid_fire_timer = 0.0
        self.powerups.clear()

    def _update(self, dt: float) -> None:
        if self.paused or self.victory:
            return
        self.wave = self.spawn_director.next_wave(self.score)
        self.rapid_fire_timer = max(0.0, self.rapid_fire_timer - dt)
        self.bullets.extend(
            self.player_controller.update(dt, self.score, rapid_fire=self.rapid_fire_timer > 0)
        )
        self.enemies.extend(self.spawn_director.update(dt, self.score, self.level))
        self._update_bullets(dt)
        self._update_enemy_bullets(dt)
        self._update_powerups(dt)
        self._update_enemies(dt)
        # Effects/combo are updated last so they reflect everything that happened
        # during this frame (hits, kills, pickups, breaches).
        self.effects.update(dt)
        self.combat.update_combo(dt)

    def _update_bullets(self, dt: float) -> None:
        alive: list[Bullet] = []
        for bullet in self.bullets:
            bullet.x += bullet.vx * dt
            bullet.y += bullet.vy * dt
            bullet.life -= dt
            if bullet.life > 0 and bullet.y >= -8:
                alive.append(bullet)
        self.bullets = alive

    def _update_enemy_bullets(self, dt: float) -> None:
        alive: list[EnemyBullet] = []
        player = self.player_controller.player
        for bullet in self.enemy_bullets:
            bullet.x += bullet.vx * dt
            bullet.y += bullet.vy * dt
            bullet.life -= dt
            if self.combat.collides(bullet.x, bullet.y, bullet.radius, player.x, player.y, player.radius):
                player.hp -= 1
                self.effects.add_shake(0.18, max_value=0.9)
                self.effects.burst(bullet.x, bullet.y, 14, (255, 120, 120), 0.55)
                if player.hp <= 0:
                    self.game_over = True
                continue
            if bullet.life > 0 and bullet.y <= INTERNAL_H + 10:
                alive.append(bullet)
        self.enemy_bullets = alive

    def _update_enemies(self, dt: float) -> None:
        alive: list[Enemy] = []
        player = self.player_controller.player

        for enemy in self.enemies:
            self._move_enemy(enemy, dt)
            self._maybe_enemy_shoot(enemy, dt)
            destroyed = False

            # Bullet collisions are resolved before player/breach checks, so kills can
            # still happen in the same frame where enemies are near the defense line.
            for bullet in self.bullets:
                if bullet.life <= 0:
                    continue
                if not self.combat.collides(enemy.x, enemy.y, enemy.radius, bullet.x, bullet.y, bullet.radius):
                    continue
                enemy.hp -= 1
                bullet.life = -1
                self.effects.add_shake(0.07, max_value=0.35)
                self.effects.burst(enemy.x, enemy.y, 8, NEON_MAGENTA, 0.35)
                if enemy.hp <= 0:
                    self.score += self.combat.destroy_enemy(enemy)
                    self.level_progress += 1
                    self._maybe_drop_powerup(enemy)
                    self._check_level_progress()
                    destroyed = True
                break

            if destroyed:
                continue

            # Direct body collision is a stronger penalty than being shot because
            # the player failed to keep distance from an active threat.
            if self.combat.collides(enemy.x, enemy.y, enemy.radius, player.x, player.y, player.radius):
                player.hp -= 1
                self.effects.add_shake(0.22, max_value=1.0)
                self.effects.burst(enemy.x, enemy.y, 24, (255, 120, 120), 0.65)
                if player.hp <= 0:
                    self.game_over = True
                continue

            if enemy.y > DEFENSE_LINE_Y + 10:
                self.breaches += 1
                player.hp -= 1
                # A breach breaks momentum to make defense mistakes clearly visible.
                self.combat.combo = 0
                self.combat.combo_decay = 0.0
                self.effects.burst(enemy.x, DEFENSE_LINE_Y + 6, 16, (255, 150, 150), 0.48)
                self.effects.add_shake(0.2, max_value=0.9)
                if player.hp <= 0 or self.breaches >= MAX_BREACHES:
                    self.game_over = True
                continue
            alive.append(enemy)

        self.enemies = alive

    def _update_powerups(self, dt: float) -> None:
        alive: list[PowerUp] = []
        player = self.player_controller.player
        for power in self.powerups:
            power.y += power.vy * dt
            power.life -= dt
            if self.combat.collides(power.x, power.y, power.radius, player.x, player.y, player.radius):
                if power.kind == "heal":
                    player.hp = min(10, player.hp + 2)
                else:
                    self.rapid_fire_timer = max(self.rapid_fire_timer, 7.0)
                self.effects.flash = min(1.0, self.effects.flash + 0.45)
                self.effects.burst(power.x, power.y, 20, (160, 255, 220), 0.62)
                continue
            if power.life > 0 and power.y < INTERNAL_H + 12:
                alive.append(power)
        self.powerups = alive

    def _maybe_drop_powerup(self, enemy: Enemy) -> None:
        chance = 0.1 if enemy.kind in {"drone", "spinner"} else 0.16
        if random.random() > chance:
            return
        kind = "rapid" if random.random() < 0.65 else "heal"
        self.powerups.append(PowerUp(enemy.x, enemy.y, random.uniform(20, 36), kind))

    def _check_level_progress(self) -> None:
        target = LEVEL_TARGETS[self.level - 1]
        if self.level_progress < target:
            return
        if self.level >= 3:
            self.victory = True
            self.enemies.clear()
            self.enemy_bullets.clear()
            return
        # Level transitions intentionally clear active threats to create a short reset
        # window before higher difficulty starts.
        self.level += 1
        self.level_progress = 0
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.powerups.clear()
        self.effects.flash = 0.65
        self.effects.burst(INTERNAL_W / 2, DEFENSE_LINE_Y - 18, 32, (130, 255, 210), 0.7)

    def _move_enemy(self, enemy: Enemy, dt: float) -> None:
        # Each enemy type gets a distinct movement profile:
        # - spinner: high horizontal sway, harder to track
        # - brute: heavy/slow drift, high durability pressure
        # - shooter: moderate sway, keeps line of fire
        # - drone: simple baseline behavior
        # Why: this creates readable roles without complex AI state machines.
        if enemy.kind == "spinner":
            enemy.x += (enemy.lane_x - enemy.x) * min(1.0, dt * 6.0)
            enemy.x += math.sin(self.time * 4.0 + enemy.phase) * 10.0 * dt
            enemy.y += enemy.vy * dt
        elif enemy.kind == "brute":
            enemy.x += (enemy.lane_x - enemy.x) * min(1.0, dt * 4.0)
            enemy.x += math.sin(self.time * 1.2 + enemy.phase) * 2.2 * dt
            enemy.y += enemy.vy * dt
        elif enemy.kind == "shooter":
            enemy.x += (enemy.lane_x - enemy.x) * min(1.0, dt * 5.0)
            enemy.x += math.sin(self.time * 1.8 + enemy.phase) * 4.5 * dt
            enemy.y += enemy.vy * dt
        else:
            enemy.x += (enemy.lane_x - enemy.x) * min(1.0, dt * 5.0)
            enemy.x += math.sin(self.time * 1.6 + enemy.phase) * 3.2 * dt
            enemy.y += enemy.vy * dt
        enemy.x = max(10, min(INTERNAL_W - 10, enemy.x))

    def _maybe_enemy_shoot(self, enemy: Enemy, dt: float) -> None:
        if enemy.kind != "shooter":
            return
        enemy.shoot_cd -= dt
        if enemy.shoot_cd > 0 or enemy.y < 18:
            return
        enemy.shoot_cd = random.uniform(0.9, 1.7)
        player = self.player_controller.player
        dir_x = player.x - enemy.x
        dir_y = max(8.0, player.y - enemy.y)
        length = max((dir_x * dir_x + dir_y * dir_y) ** 0.5, 1.0)
        # Normalize direction vector so speed is consistent regardless of distance.
        # Without normalization, close targets would create slower bullets and far
        # targets faster bullets, which feels unfair/inconsistent.
        speed = 72.0 + min(30.0, self.wave * 3)
        self.enemy_bullets.append(
            EnemyBullet(enemy.x, enemy.y + 4, (dir_x / length) * speed, (dir_y / length) * speed)
        )
        self.effects.burst(enemy.x, enemy.y + 3, 4, (255, 115, 205), 0.24)

    def _render(self) -> None:
        self.renderer.render(
            screen=self.screen,
            time_s=self.time,
            player=self.player_controller.player,
            player_tilt=self.player_controller.tilt,
            bullets=self.bullets,
            enemy_bullets=self.enemy_bullets,
            enemies=self.enemies,
            powerups=self.powerups,
            effects=self.effects,
            score=self.score,
            wave=self.wave,
            level=self.level,
            level_progress=self.level_progress,
            level_target=LEVEL_TARGETS[self.level - 1],
            breaches=self.breaches,
            max_breaches=MAX_BREACHES,
            combo=self.combat.combo,
            rapid_fire_timer=self.rapid_fire_timer,
            game_over=self.game_over,
            victory=self.victory,
            paused=self.paused,
            post=self.post,
        )


def run() -> None:
    NeonShooter().run()

