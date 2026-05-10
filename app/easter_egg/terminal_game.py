"""Easter egg – terminálový minigame jako Toplevel okno.

Kód je v podstatě shodný s `terminal_game/__main__.py` (samostatná verze),
jen místo `tk.Tk` dědí z `tk.Toplevel`, aby se dal otevřít z hlavní
aplikace bez kolize s existujícím root oknem.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class GameState:
    authenticated: bool = False
    scanned: bool = False
    breached: bool = False
    purged: bool = False
    rebooted: bool = False
    history: list[str] = field(default_factory=list)


class TerminalGameWindow(tk.Toplevel):
    """Toplevel verze easter-egg hry pro spuštění z hlavní aplikace."""

    def __init__(self, master: tk.Misc | None = None) -> None:
        super().__init__(master=master)
        self.title("ClientRadar // OVERRIDE")
        self.geometry("900x560")
        self.minsize(720, 480)

        self._state = GameState()
        self._prompt = "OZ> "

        bg = "#050607"
        fg = "#7CFFB2"
        err = "#FF6B6B"
        dim = "#5EEAD4"

        self.configure(bg=bg)

        self._text = tk.Text(
            self,
            wrap="word",
            bg=bg,
            fg=fg,
            insertbackground=fg,
            highlightthickness=0,
            borderwidth=0,
            font=("Consolas", 12),
        )
        self._text.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self._text.tag_configure("err", foreground=err)
        self._text.tag_configure("dim", foreground=dim)
        self._text.tag_configure("sys", foreground="#A7F3D0")
        self._text.configure(state="disabled")

        frame = tk.Frame(self, bg=bg)
        frame.pack(fill="x", padx=10, pady=10)

        self._entry = tk.Entry(
            frame,
            bg="#0B1220",
            fg=fg,
            insertbackground=fg,
            highlightthickness=1,
            highlightbackground="#134E4A",
            highlightcolor="#34D399",
            borderwidth=0,
            font=("Consolas", 12),
        )
        self._entry.pack(side="left", fill="x", expand=True)
        self._entry.bind("<Return>", self._on_submit)
        self.after(100, self._entry.focus_set)

        self._banner()
        self._println("Zadej `help` pro příkazy.", tag="dim")

    def _banner(self) -> None:
        for line in (
            "OZ SECURITY SHELL v0.9 — read-only override channel",
            "Varování: neautorizovaná aktivita je logována.",
            "",
        ):
            self._println(line, tag="sys")

    def _println(self, line: str, tag: str | None = None) -> None:
        self._text.configure(state="normal")
        if tag:
            self._text.insert("end", line + "\n", tag)
        else:
            self._text.insert("end", line + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def _echo_cmd(self, raw: str) -> None:
        self._println(self._prompt + raw)

    def _on_submit(self, _event=None) -> None:
        raw = self._entry.get().strip()
        self._entry.delete(0, "end")
        if not raw:
            return
        self._echo_cmd(raw)
        self._handle_command(raw.lower())

    def _handle_command(self, cmd: str) -> None:
        parts = cmd.split()
        verb = parts[0] if parts else ""
        arg = " ".join(parts[1:]).strip()

        if verb in {"quit", "exit"}:
            self.destroy()
            return
        if verb == "help":
            self._help()
            return
        if verb == "clear":
            self._text.configure(state="normal")
            self._text.delete("1.0", "end")
            self._text.configure(state="disabled")
            self._banner()
            return
        if verb == "auth":
            self._cmd_auth(arg)
            return
        if verb == "scan":
            self._cmd_scan()
            return
        if verb == "breach":
            self._cmd_breach(arg)
            return
        if verb == "purge":
            self._cmd_purge(arg)
            return
        if verb == "reboot":
            self._cmd_reboot()
            return

        self._println(f"Neznámý příkaz: `{verb}`. Zadej `help`.", tag="err")

    def _help(self) -> None:
        for line in (
            "Příkazy:",
            "  auth <token>     — ověření (token: OZ-CORE)",
            "  scan             — mapování perimetru",
            "  breach <target>  — průnik (target: NEON)",
            "  purge <malware>  — odstranění (malware: ROOTWORM)",
            "  reboot           — restart jádra a ukončení přístupu",
            "  clear            — vyčistit obrazovku",
            "  exit             — zavřít",
        ):
            self._println(line, tag="dim")

    def _cmd_auth(self, token: str) -> None:
        if self._state.authenticated:
            self._println("Již autentizováno.", tag="dim")
            return
        if token.upper() != "OZ-CORE":
            self._println("AUTH FAILED: neplatný token.", tag="err")
            return
        self._state.authenticated = True
        self._println("AUTH OK — kanál OZ-CORE aktivní.", tag="sys")

    def _require_auth(self) -> bool:
        if self._state.authenticated:
            return True
        self._println("Nejprve: `auth OZ-CORE`.", tag="err")
        return False

    def _cmd_scan(self) -> None:
        if not self._require_auth():
            return
        if self._state.scanned:
            self._println("Scan už proběhl — výsledky jsou v bufferu.", tag="dim")
            return

        def done() -> None:
            self._state.scanned = True
            self._println("SCAN COMPLETE:", tag="sys")
            self._println("  - NEON perimeter: DETECTED", tag="dim")
            self._println("  - anomaly signature: ROOTWORM (latent)", tag="dim")

        self._sequence(
            [
                ("Inicializuji pasivní sondu…", 220),
                ("Snímám ARP/NDP artefakty…", 260),
                ("Koreluji šumové vzory…", 300),
            ],
            on_finish=done,
        )

    def _cmd_breach(self, target: str) -> None:
        if not self._require_auth():
            return
        if not self._state.scanned:
            self._println("Nejdřív `scan`, ať víš kam šaháš.", tag="err")
            return
        if target.upper() != "NEON":
            self._println("Neplatný cíl. Zkus `breach NEON`.", tag="err")
            return
        if self._state.breached:
            self._println("Perimeter už je otevřený.", tag="dim")
            return

        def done() -> None:
            self._state.breached = True
            self._println("BREACH OK — NEON perimeter compromised.", tag="sys")

        self._sequence(
            [
                ("Vyjednávám TLS downgrade (simulace)…", 240),
                ("Vkládám kanár token…", 220),
                ("Otevírám tunel do kernel vrstvy…", 280),
            ],
            on_finish=done,
        )

    def _cmd_purge(self, malware: str) -> None:
        if not self._require_auth():
            return
        if not self._state.breached:
            self._println("Nejdřív `breach NEON`.", tag="err")
            return
        if malware.upper() != "ROOTWORM":
            self._println("Neplatný malware. Zkus `purge ROOTWORM`.", tag="err")
            return
        if self._state.purged:
            self._println("ROOTWORM už není v paměti.", tag="dim")
            return

        def done() -> None:
            self._state.purged = True
            self._println("PURGE OK — ROOTWORM izolován a odstraněn.", tag="sys")

        self._sequence(
            [
                ("Izoluji infikované segmenty…", 240),
                ("Přepisuji kontrolní součty…", 260),
                ("Mažu latentní hooky…", 280),
            ],
            on_finish=done,
        )

    def _cmd_reboot(self) -> None:
        if not self._require_auth():
            return
        if not self._state.purged:
            self._println("Nejdřív `purge ROOTWORM`.", tag="err")
            return
        if self._state.rebooted:
            self._println("Systém už běží ve stabilním režimu.", tag="dim")
            return

        def done() -> None:
            self._state.rebooted = True
            self._println("REBOOT OK — jádro stabilní. Přístup se uzavírá…", tag="sys")
            self._println("Díky, že jsi to neudělal z kavárny.", tag="dim")
            self.after(900, self.destroy)

        self._sequence(
            [
                ("Flushuji cache policy…", 220),
                ("Rotuji klíče relace…", 240),
                ("Restartuji služby OZ…", 260),
            ],
            on_finish=done,
        )

    def _sequence(
        self, steps: list[tuple[str, int]], on_finish: Callable[[], None]
    ) -> None:
        if not steps:
            on_finish()
            return

        def run(idx: int) -> None:
            if idx >= len(steps):
                on_finish()
                return
            msg, delay = steps[idx]
            self._println(msg, tag="dim")
            self.after(delay, lambda: run(idx + 1))

        run(0)
