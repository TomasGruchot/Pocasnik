from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


TextTag = str | None


@dataclass
class Message:
    """Jedna textova zprava pro vystup terminalu."""
    # text = co se vypise
    # tag = barva/styl textu v Tkinter Text widgetu
    text: str
    tag: TextTag = None


@dataclass
class SequenceStep:
    """Krok animovane sekvence: text + zpozdeni pred dalsim krokem."""
    # delay_ms je v milisekundach (1000 ms = 1 sekunda)
    text: str
    delay_ms: int
    tag: TextTag = "dim"


@dataclass
class CommandResponse:
    """Jednotna odpoved enginu, kterou UI jen vykresli."""
    # messages: okamzite vypisovane radky
    # sequence: kroky, ktere se vypisuji postupne s delay
    # on_sequence_complete: funkce, ktera vrati dalsi vystup po dokonceni sekvence
    # clear_screen/should_exit/close_delay_ms: pokyny pro GUI vrstvu
    messages: list[Message] = field(default_factory=list)
    sequence: list[SequenceStep] = field(default_factory=list)
    on_sequence_complete: Callable[[], "CommandResponse"] | None = None
    clear_screen: bool = False
    should_exit: bool = False
    close_delay_ms: int | None = None


@dataclass
class GameState:
    """Stav mise oddeleny od UI."""
    # Tento objekt drzi jen data o postupu hry.
    # Vyhoda: pravidla hry muzeme testovat i bez GUI.
    authenticated: bool = False
    scanned: bool = False
    breached: bool = False
    purged: bool = False
    rebooted: bool = False
    command_count: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    history: list[str] = field(default_factory=list)


class SecurityGameEngine:
    """Cista herni logika: validuje prikazy a meni stav hry."""
    # Konstanty drzi "spravne" hodnoty, ktere hrac musi zadat.
    TOKEN = "OZ-CORE"
    TARGET = "NEON"
    MALWARE = "ROOTWORM"

    def __init__(self) -> None:
        # Engine si vytvori vlastni stav hry.
        self._state = GameState()

    def banner(self) -> list[Message]:
        # Uvodni obrazovka po startu (nebo po clear).
        return [
            Message("OZ SECURITY SHELL v1.1 - override channel", "sys"),
            Message("Varovani: neautorizovana aktivita je logovana.", "sys"),
            Message(""),
            Message("Zadej 'help' pro prikazy.", "dim"),
        ]

    def execute(self, raw: str) -> CommandResponse:
        # Jediny vstupni bod pro prikazy; vraci data pro vykresleni.
        clean_raw = raw.strip()
        # Pocitame statistiku a historii, at lze zobrazit status/history.
        self._state.command_count += 1
        self._state.history.append(clean_raw)

        parts = clean_raw.split()
        verb = parts[0].lower() if parts else ""
        arg = " ".join(parts[1:]).strip()
        # verb = nazev prikazu, arg = zbytek za prikazem.

        if verb in {"quit", "exit"}:
            return CommandResponse(should_exit=True)
        if verb in {"help", "h", "?"}:
            return self._help()
        if verb == "clear":
            return CommandResponse(clear_screen=True)
        if verb == "status":
            return self._status()
        if verb == "hint":
            return self._hint()
        if verb == "history":
            return self._history(arg)
        if verb == "auth":
            return self._auth(arg)
        if verb == "scan":
            return self._scan()
        if verb == "breach":
            return self._breach(arg)
        if verb == "purge":
            return self._purge(arg)
        if verb == "reboot":
            return self._reboot()

        return CommandResponse(
            messages=[Message(f"Neznamy prikaz: '{verb}'. Zadej 'help'.", "err")]
        )

    def _help(self) -> CommandResponse:
        # Vypis vsech podporovanych prikazu.
        return CommandResponse(
            messages=[
                Message("Prikazy:", "dim"),
                Message("  auth <token>      - overeni (token: OZ-CORE)", "dim"),
                Message("  scan              - mapovani perimetru", "dim"),
                Message("  breach <target>   - prunik (target: NEON)", "dim"),
                Message("  purge <malware>   - odstraneni (malware: ROOTWORM)", "dim"),
                Message("  reboot            - restart jadra a uzavreni pristupu", "dim"),
                Message("  status            - vypis stavu mise", "dim"),
                Message("  hint              - napoveda dalsiho kroku", "dim"),
                Message("  history [n]       - posledni prikazy", "dim"),
                Message("  clear             - vycistit obrazovku", "dim"),
                Message("  exit              - zavrit", "dim"),
            ]
        )

    def _status(self) -> CommandResponse:
        # Uptime pocitame od startu hry.
        elapsed = int((datetime.now() - self._state.started_at).total_seconds())
        checks = [
            ("auth", self._state.authenticated),
            ("scan", self._state.scanned),
            ("breach", self._state.breached),
            ("purge", self._state.purged),
            ("reboot", self._state.rebooted),
        ]
        messages = [
            Message("STATUS", "sys"),
            Message(f"  uptime: {elapsed}s", "dim"),
            Message(f"  commands: {self._state.command_count}", "dim"),
        ]
        for name, done in checks:
            # OK = splneno, .. = jeste ne.
            mark = "OK" if done else ".."
            messages.append(Message(f"  {name:<6} [{mark}]", "dim"))
        return CommandResponse(messages=messages)

    def _hint(self) -> CommandResponse:
        # Napovi nejblizsi korektni krok podle aktualniho stavu mise.
        if not self._state.authenticated:
            return CommandResponse(messages=[Message("Napoveda: auth OZ-CORE", "dim")])
        if not self._state.scanned:
            return CommandResponse(messages=[Message("Napoveda: scan", "dim")])
        if not self._state.breached:
            return CommandResponse(messages=[Message("Napoveda: breach NEON", "dim")])
        if not self._state.purged:
            return CommandResponse(messages=[Message("Napoveda: purge ROOTWORM", "dim")])
        if not self._state.rebooted:
            return CommandResponse(messages=[Message("Napoveda: reboot", "dim")])
        return CommandResponse(messages=[Message("Mise dokoncena. Zadej exit.", "sys")])

    def _history(self, arg: str) -> CommandResponse:
        # Volitelny argument omezuje pocet radku historie.
        limit = 8
        if arg:
            try:
                limit = max(1, min(30, int(arg)))
            except ValueError:
                return CommandResponse(messages=[Message("Pouziti: history [n]", "err")])

        rows = self._state.history[-limit:]
        if not rows:
            return CommandResponse(messages=[Message("Historie je prazdna.", "dim")])

        messages = [Message("Historie prikazu:", "dim")]
        for idx, cmd in enumerate(rows, start=len(self._state.history) - len(rows) + 1):
            messages.append(Message(f"  {idx:02d}: {cmd}", "dim"))
        return CommandResponse(messages=messages)

    def _require_auth(self) -> CommandResponse | None:
        # Sdilena podminka pro prikazy, ktere vyzaduji prihlaseni.
        if self._state.authenticated:
            return None
        return CommandResponse(messages=[Message("Nejprve: auth OZ-CORE", "err")])

    def _auth(self, token: str) -> CommandResponse:
        # Kontrola tokenu je case-insensitive: upper() srovna velikost pismen.
        if self._state.authenticated:
            return CommandResponse(messages=[Message("Jiz autentizovano.", "dim")])
        if token.upper() != self.TOKEN:
            return CommandResponse(messages=[Message("AUTH FAILED: neplatny token.", "err")])
        self._state.authenticated = True
        return CommandResponse(messages=[Message("AUTH OK - kanal OZ-CORE aktivni.", "sys")])

    def _scan(self) -> CommandResponse:
        # Prikazy ve hre jsou zamerne linearni: auth -> scan -> breach -> purge -> reboot.
        auth_required = self._require_auth()
        if auth_required:
            return auth_required
        if self._state.scanned:
            return CommandResponse(
                messages=[Message("Scan uz probehl - vysledky jsou v bufferu.", "dim")]
            )

        def complete() -> CommandResponse:
            # Tohle se zavola az po animovane sekvenci kroku.
            self._state.scanned = True
            return CommandResponse(
                messages=[
                    Message("SCAN COMPLETE:", "sys"),
                    Message("  - NEON perimeter: DETECTED", "dim"),
                    Message("  - anomaly signature: ROOTWORM (latent)", "dim"),
                ]
            )

        return CommandResponse(
            sequence=[
                SequenceStep("Inicializuji pasivni sondu...", 220),
                SequenceStep("Snimam ARP/NDP artefakty...", 260),
                SequenceStep("Koreluji sumove vzory...", 300),
            ],
            on_sequence_complete=complete,
        )

    def _breach(self, target: str) -> CommandResponse:
        auth_required = self._require_auth()
        if auth_required:
            return auth_required
        if not self._state.scanned:
            return CommandResponse(messages=[Message("Nejdriv scan.", "err")])
        if target.upper() != self.TARGET:
            return CommandResponse(messages=[Message("Neplatny cil. Zkus breach NEON.", "err")])
        if self._state.breached:
            return CommandResponse(messages=[Message("Perimeter uz je otevreny.", "dim")])

        def complete() -> CommandResponse:
            self._state.breached = True
            return CommandResponse(
                messages=[Message("BREACH OK - NEON perimeter compromised.", "sys")]
            )

        return CommandResponse(
            sequence=[
                SequenceStep("Vyjednavam TLS downgrade (simulace)...", 240),
                SequenceStep("Vkladam kanar token...", 220),
                SequenceStep("Oteviram tunel do kernel vrstvy...", 280),
            ],
            on_sequence_complete=complete,
        )

    def _purge(self, malware: str) -> CommandResponse:
        auth_required = self._require_auth()
        if auth_required:
            return auth_required
        if not self._state.breached:
            return CommandResponse(messages=[Message("Nejdriv breach NEON.", "err")])
        if malware.upper() != self.MALWARE:
            return CommandResponse(
                messages=[Message("Neplatny malware. Zkus purge ROOTWORM.", "err")]
            )
        if self._state.purged:
            return CommandResponse(messages=[Message("ROOTWORM uz neni v pameti.", "dim")])

        def complete() -> CommandResponse:
            self._state.purged = True
            return CommandResponse(
                messages=[Message("PURGE OK - ROOTWORM izolovan a odstranen.", "sys")]
            )

        return CommandResponse(
            sequence=[
                SequenceStep("Izoluji infikovane segmenty...", 240),
                SequenceStep("Prepisuji kontrolni soucty...", 260),
                SequenceStep("Mazu latentni hooky...", 280),
            ],
            on_sequence_complete=complete,
        )

    def _reboot(self) -> CommandResponse:
        auth_required = self._require_auth()
        if auth_required:
            return auth_required
        if not self._state.purged:
            return CommandResponse(messages=[Message("Nejdriv purge ROOTWORM.", "err")])
        if self._state.rebooted:
            return CommandResponse(
                messages=[Message("System uz bezi ve stabilnim rezimu.", "dim")]
            )

        def complete() -> CommandResponse:
            # Finalni stav mise - po kratke chvili se hra sama zavre.
            self._state.rebooted = True
            return CommandResponse(
                messages=[
                    Message("REBOOT OK - jadro stabilni. Pristup se uzavira...", "sys"),
                    Message("ACCESS GRANTED", "sys"),
                    Message("Diky, ze jsi to neudelal z kavarny.", "dim"),
                ],
                close_delay_ms=900,
            )

        return CommandResponse(
            sequence=[
                SequenceStep("Flushuji cache policy...", 220),
                SequenceStep("Rotuji klice relace...", 240),
                SequenceStep("Restartuji sluzby OZ...", 260),
            ],
            on_sequence_complete=complete,
        )


class TerminalGame(tk.Tk):
    """Tkinter vrstva: sbira vstup, vola engine a vykresluje odpoved."""
    def __init__(self) -> None:
        super().__init__()
        # Nastaveni okna.
        self.title("ClientRadar // OVERRIDE")
        self.geometry("900x560")
        self.minsize(720, 480)

        self._engine = SecurityGameEngine()
        self._prompt = "OZ> "
        # _busy zabrani tomu, aby bezely dve sekvence naraz.
        self._busy = False

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
        # err/dim/sys jsou jen jmena stylu, ktere pak pouzivame pri vypisu.

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
        self._entry.focus_set()

        self._print_messages(self._engine.banner())

    def _println(self, line: str, tag: TextTag = None) -> None:
        # Text widget prepiname do "normal", zapiseme radek a vratime na "disabled",
        # aby uzivatel nemohl menit historii vystupu mysi/klavesnici.
        self._text.configure(state="normal")
        if tag:
            self._text.insert("end", line + "\n", tag)
        else:
            self._text.insert("end", line + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def _print_messages(self, messages: list[Message]) -> None:
        for message in messages:
            self._println(message.text, message.tag)

    def _echo_cmd(self, raw: str) -> None:
        self._println(self._prompt + raw)

    def _on_submit(self, _event=None) -> None:
        # Cteni vstupu z dolniho inputu.
        raw = self._entry.get().strip()
        self._entry.delete(0, "end")
        if not raw:
            return
        self._echo_cmd(raw)

        if self._busy:
            # Pokud bezi sekvence, jen upozornime a dalsi prikaz nespoustime.
            self._println("Probihajici operace... pockej na dokonceni.", "dim")
            return

        response = self._engine.execute(raw)
        self._render_response(response)

    def _render_response(self, response: CommandResponse) -> None:
        # UI neobsahuje herni pravidla, pouze interpretuje odpoved enginu.
        if response.clear_screen:
            self._clear_screen()
            self._print_messages(self._engine.banner())

        self._print_messages(response.messages)

        if response.sequence:
            # Sekvence se vypisuje postupne, ne najednou.
            self._run_sequence(response.sequence, response.on_sequence_complete)

        if response.should_exit:
            self.destroy()
            return

        if response.close_delay_ms is not None:
            self.after(response.close_delay_ms, self.destroy)

    def _clear_screen(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    def _run_sequence(
        self,
        steps: list[SequenceStep],
        on_finish: Callable[[], CommandResponse] | None,
    ) -> None:
        # Behem sekvence blokujeme vstup, aby nemohly bezet dve operace najednou.
        self._busy = True
        self._entry.configure(state="disabled")

        def done() -> None:
            # Odblokujeme input a pripadne vykreslime follow-up response.
            self._busy = False
            self._entry.configure(state="normal")
            self._entry.focus_set()
            if on_finish is not None:
                self._render_response(on_finish())

        if not steps:
            done()
            return

        def run(index: int) -> None:
            if index >= len(steps):
                done()
                return
            step = steps[index]
            self._println(step.text, step.tag)
            # after zavola funkci po danem case bez blokovani celeho GUI.
            self.after(step.delay_ms, lambda: run(index + 1))

        run(0)


def main() -> None:
    """Spousti GUI aplikaci."""
    app = TerminalGame()
    app.mainloop()


if __name__ == "__main__":
    main()
