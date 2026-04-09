from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]

from .base_state import BaseState


@dataclass
class _Fx:
    glitch_t: float = 0.0
    glitch_intensity: float = 0.0
    shake_t: float = 0.0
    shake_amp: float = 0.0


class PlayingState(BaseState):
    """Secret terminal easter egg (command-based hacking UI)."""

    def __init__(self, game: Any) -> None:
        super().__init__(game)
        self.lines: list[str] = []
        self.input_buffer: str = ""
        self.history: list[str] = []
        self.history_idx: int = -1

        self.stage: int = 0
        self.attempts: int = 0
        self._t: float = 0.0
        self._cursor_t: float = 0.0
        self.fx = _Fx()

    def on_enter(self, prev: Any) -> None:
        self.lines = []
        self.input_buffer = ""
        self.history = []
        self.history_idx = -1
        self.stage = 0
        self.attempts = 0
        self._t = 0.0
        self._cursor_t = 0.0
        self.fx = _Fx()

        self._boot()

    def _boot(self) -> None:
        self._print("OZ Core Security Terminal v3.7")
        self._print("WARNING: ROOTWORM intrusion detected.")
        self._print("Type 'help' for commands.")
        self._print("")
        self._print("Objective: authenticate -> scan -> isolate -> purge -> reboot")
        self._print("")

    def _print(self, text: str) -> None:
        self.lines.append(text)
        # Keep terminal readable.
        if len(self.lines) > 60:
            self.lines = self.lines[-60:]

    def handle_event(self, event: Any) -> None:
        if pygame is None:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.set_state("menu")
                return

            if event.key == pygame.K_RETURN:
                cmd = self.input_buffer.strip()
                self._print(f"> {cmd}")
                if cmd:
                    self.history.append(cmd)
                self.history_idx = -1
                self.input_buffer = ""
                self._execute(cmd)
                return

            if event.key == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
                return

            if event.key == pygame.K_UP:
                if self.history:
                    if self.history_idx == -1:
                        self.history_idx = len(self.history) - 1
                    else:
                        self.history_idx = max(0, self.history_idx - 1)
                    self.input_buffer = self.history[self.history_idx]
                return

            if event.key == pygame.K_DOWN:
                if self.history:
                    if self.history_idx == -1:
                        return
                    self.history_idx = min(len(self.history) - 1, self.history_idx + 1)
                    self.input_buffer = self.history[self.history_idx]
                return

            # Accept text input (printable).
            ch = event.unicode
            if ch and ch.isprintable() and ch not in ("\r", "\n"):
                # Keep buffer length sane.
                if len(self.input_buffer) < 64:
                    self.input_buffer += ch

    def _bad(self, msg: str) -> None:
        self.attempts += 1
        self._print(msg)
        self.fx.glitch_t = 0.20
        self.fx.glitch_intensity = min(1.0, 0.35 + self.attempts * 0.08)
        self.fx.shake_t = 0.12
        self.fx.shake_amp = min(6.0, 2.0 + self.attempts * 0.5)

    def _ok(self, msg: str) -> None:
        self._print(msg)
        self.fx.glitch_t = 0.06
        self.fx.glitch_intensity = 0.15

    def _execute(self, cmdline: str) -> None:
        cmdline = cmdline.strip()
        if not cmdline:
            return

        parts = cmdline.split()
        cmd = parts[0].lower()
        args = parts[1:]

        # Global commands
        if cmd in ("help", "?"):
            self._print("Commands:")
            self._print("  help                - show this help")
            self._print("  status              - show objective progress")
            self._print("  clear               - clear screen")
            self._print("  auth <pass>         - authenticate (try: OZ-CORE)")
            self._print("  scan                - scan perimeter")
            self._print("  isolate rootworm    - isolate malware")
            self._print("  purge rootworm      - purge malware")
            self._print("  reboot              - reboot system")
            self._print("  exit                - back to menu")
            return

        if cmd == "exit":
            self.game.set_state("menu")
            return

        if cmd == "clear":
            self.lines = []
            return

        if cmd == "status":
            steps = [
                ("AUTH", self.stage >= 1),
                ("SCAN", self.stage >= 2),
                ("ISOLATE", self.stage >= 3),
                ("PURGE", self.stage >= 4),
                ("REBOOT", self.stage >= 5),
            ]
            self._print("Progress:")
            for name, done in steps:
                self._print(f"  [{ 'X' if done else ' ' }] {name}")
            return

        # Stage commands
        if cmd == "auth":
            if self.stage >= 1:
                self._ok("Already authenticated.")
                return
            if not args:
                self._bad("Usage: auth <pass>")
                return
            pwd = " ".join(args).strip()
            if pwd.upper() == "OZ-CORE":
                self.stage = 1
                self._ok("AUTH OK. Welcome, DEFENSE MODULE.")
                self._print("Next: scan")
            else:
                self._bad("AUTH FAIL. Hint: OZ-CORE")
            return

        if cmd == "scan":
            if self.stage < 1:
                self._bad("Denied. Authenticate first (auth <pass>).")
                return
            if self.stage >= 2:
                self._ok("Scan already complete.")
                return
            self.stage = 2
            self._ok("SCAN OK. ROOTWORM signature found in KERNEL & CORE sectors.")
            self._print("Next: isolate rootworm")
            return

        if cmd == "isolate":
            if self.stage < 2:
                self._bad("Missing prerequisite. Run: scan")
                return
            if args and args[0].lower() == "rootworm":
                if self.stage >= 3:
                    self._ok("Isolation already active.")
                    return
                self.stage = 3
                self._ok("ISOLATE OK. Quarantine walls deployed.")
                self._print("Next: purge rootworm")
                return
            self._bad("Usage: isolate rootworm")
            return

        if cmd == "purge":
            if self.stage < 3:
                self._bad("Missing prerequisite. Run: isolate rootworm")
                return
            if args and args[0].lower() == "rootworm":
                if self.stage >= 4:
                    self._ok("Purge already executed.")
                    return
                self.stage = 4
                self._ok("PURGE OK. Malware processes terminated.")
                self._print("Next: reboot")
                return
            self._bad("Usage: purge rootworm")
            return

        if cmd == "reboot":
            if self.stage < 4:
                self._bad("Unsafe. Purge must be completed first.")
                return
            self.stage = 5
            self._print("REBOOTING OZ CORE...")
            self._print("Integrity check: OK")
            self._print("ROOT ACCESS: GRANTED")
            self._print("")
            self._print("PREMIUM MODE UNLOCKED.")
            # Persist easter-egg result:
            if hasattr(self.game, "unlock_premium"):
                self.game.unlock_premium()
            self.fx.glitch_t = 0.35
            self.fx.glitch_intensity = 0.25
            return

        self._bad(f"Unknown command: {cmd}. Try: help")

    def update(self, dt: float) -> None:
        self._t += dt
        self._cursor_t += dt
        if self.fx.glitch_t > 0:
            self.fx.glitch_t = max(0.0, self.fx.glitch_t - dt)
        if self.fx.shake_t > 0:
            self.fx.shake_t = max(0.0, self.fx.shake_t - dt)
            if self.fx.shake_t <= 0:
                self.fx.shake_amp = 0.0

    def render(self, surface: Any) -> None:
        if pygame is None:
            return

        s = self.game.settings
        surface.fill((0, 0, 0))

        # Optional glitch: horizontal strip offsets
        if self.fx.glitch_t > 0.0:
            w, h = surface.get_size()
            base = surface.copy()
            strips = 6
            dx_max = int(10 * self.fx.glitch_intensity)
            for _ in range(strips):
                y = random.randint(0, h - 1)
                sh = random.randint(1, 6)
                rect = pygame.Rect(0, y, w, min(sh, h - y))
                part = base.subsurface(rect).copy()
                dx = random.randint(-dx_max, dx_max)
                surface.blit(part, (dx, y))

        # Screen shake (small)
        if self.fx.shake_amp > 0.0:
            frame = surface.copy()
            dx = random.randint(-int(self.fx.shake_amp), int(self.fx.shake_amp))
            dy = random.randint(-int(self.fx.shake_amp), int(self.fx.shake_amp))
            surface.blit(frame, (dx, dy))

        # Terminal frame
        w, h = surface.get_size()
        pygame.draw.rect(surface, (0, 255, 255), pygame.Rect(6, 6, w - 12, h - 12), 1)
        pygame.draw.rect(surface, (255, 60, 230), pygame.Rect(8, 8, w - 16, h - 16), 1)

        font = pygame.font.SysFont("consolas", 16) or pygame.font.SysFont(None, 16)
        small = pygame.font.SysFont("consolas", 14) or pygame.font.SysFont(None, 14)

        # Header
        hdr = small.render("OZ CORE :: SECURITY SHELL", True, (220, 235, 255))
        surface.blit(hdr, (14, 10))
        status = "PREMIUM=UNLOCKED" if getattr(self.game, "premium_unlocked", False) else "PREMIUM=LOCKED"
        st = small.render(status, True, (190, 255, 190) if "UNLOCKED" in status else (255, 190, 190))
        surface.blit(st, (w - st.get_width() - 14, 10))

        # Body text
        top = 32
        max_lines = (h - top - 28) // 18
        view = self.lines[-max_lines:]
        y = top
        for line in view:
            txt = font.render(line, True, (160, 255, 245))
            surface.blit(txt, (14, y))
            y += 18

        # Input line with blinking cursor
        cursor_on = int(self._cursor_t * 2) % 2 == 0
        prompt = "> " + self.input_buffer + ("_" if cursor_on else " ")
        prompt_surf = font.render(prompt, True, (220, 235, 255))
        surface.blit(prompt_surf, (14, h - 24))

        # Scanlines overlay
        overlay = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        for yy in range(0, h, 3):
            overlay.fill((160, 255, 245, 18), rect=pygame.Rect(0, yy, w, 1))
        surface.blit(overlay, (0, 0))

