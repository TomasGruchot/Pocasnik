from __future__ import annotations

import threading

import customtkinter as ctk

from app.services.weather_service import GeoCity
from app.views.base_view import BaseView


_FONT = "Segoe UI"
_FONT_EMOJI = "Segoe UI Emoji"
_BG = "#0E1521"
_CARD_BG = "#1A2235"
_CARD_BG_HOVER = "#222C42"
_TEXT_DIM = "#9AA4B8"
_TEXT_FAINT = "#5C6477"

_DEBOUNCE_MS = 300


class SearchCityView(BaseView):
    """Živé vyhledávání města – výsledky se nahrávají při psaní."""

    def build(self) -> None:
        self.configure(fg_color=_BG)
        self._results: list[GeoCity] = []
        self._debounce_after_id: str | None = None
        self._search_seq: int = 0

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 6))

        ctk.CTkButton(
            header,
            text="←  Zpět",
            width=80,
            height=36,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=_CARD_BG,
            text_color=_TEXT_DIM,
            command=lambda: self.app.show("main"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Přidat město",
            font=ctk.CTkFont(family=_FONT, size=22, weight="bold"),
        ).pack(side="left", padx=16)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(4, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            body,
            text="HLEDAT MĚSTO",
            anchor="w",
            text_color=_TEXT_FAINT,
            font=ctk.CTkFont(family=_FONT, size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", pady=(4, 4))

        search_row = ctk.CTkFrame(body, fg_color=_CARD_BG, corner_radius=12)
        search_row.grid(row=1, column=0, sticky="ew")
        search_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            search_row,
            text="🔍",
            font=ctk.CTkFont(family=_FONT_EMOJI, size=16),
            width=44,
        ).grid(row=0, column=0, sticky="w", padx=(8, 0))

        self._query = ctk.CTkEntry(
            search_row,
            placeholder_text="Začni psát název města (Praha, Brno, Plzeň…) – výsledky se objeví hned",
            height=44,
            border_width=0,
            fg_color=_CARD_BG,
            font=ctk.CTkFont(family=_FONT, size=14),
        )
        self._query.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        self._query.bind("<KeyRelease>", self._on_typing)
        self._query.bind("<Return>", lambda _e: self._search_now(self._query.get()))

        self._status = ctk.CTkLabel(
            body,
            text="Najdu jakékoliv město na světě.",
            text_color=_TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=_FONT, size=12),
        )
        self._status.grid(row=2, column=0, sticky="ew", pady=(8, 4))

        self._results_box = ctk.CTkScrollableFrame(
            body, fg_color="transparent", scrollbar_button_color=_CARD_BG
        )
        self._results_box.grid(row=3, column=0, sticky="nsew", pady=(4, 0))

    def on_show(self) -> None:
        self._cancel_debounce()
        self._search_seq += 1
        self._status.configure(text="Najdu jakékoliv město na světě.")
        self._query.delete(0, "end")
        for child in self._results_box.winfo_children():
            child.destroy()
        self._query.focus_set()

    def _cancel_debounce(self) -> None:
        if self._debounce_after_id is not None:
            try:
                self.after_cancel(self._debounce_after_id)
            except Exception:
                pass
            self._debounce_after_id = None

    def _on_typing(self, _event=None) -> None:
        text = self._query.get()
        self._cancel_debounce()
        if not text.strip():
            self._search_seq += 1
            self._status.configure(text="Začni psát název města.")
            for child in self._results_box.winfo_children():
                child.destroy()
            return
        self._debounce_after_id = self.after(
            _DEBOUNCE_MS, lambda t=text: self._search_now(t)
        )

    def _search_now(self, query: str) -> None:
        self._cancel_debounce()
        query = query.strip()
        if not query:
            return
        self._search_seq += 1
        seq = self._search_seq
        self._status.configure(text="Hledám…")

        def worker() -> None:
            try:
                results = self.app.weather_vm.search_city(query)
            except Exception as e:
                self.after(0, lambda err=str(e), s=seq: self._on_error(err, s))
                return
            self.after(0, lambda r=results, s=seq: self._on_results(r, s))

        threading.Thread(target=worker, daemon=True).start()

    def _on_error(self, msg: str, seq: int) -> None:
        if seq != self._search_seq:
            return
        self._status.configure(text=f"Chyba: {msg}")

    def _on_results(self, results: list[GeoCity], seq: int) -> None:
        if seq != self._search_seq:
            return
        self._results = results
        for child in self._results_box.winfo_children():
            child.destroy()
        if not results:
            self._status.configure(text="Nic se nenašlo. Zkus zadat jiné jméno.")
            return
        self._status.configure(text=f"Nalezeno: {len(results)}")

        for geo in results:
            row = ctk.CTkFrame(self._results_box, fg_color=_CARD_BG, corner_radius=12)
            row.pack(fill="x", pady=4, padx=2)

            ctk.CTkLabel(
                row,
                text="📍",
                font=ctk.CTkFont(family=_FONT_EMOJI, size=18),
                width=44,
            ).pack(side="left", padx=(8, 0), pady=10)

            text_box = ctk.CTkFrame(row, fg_color="transparent")
            text_box.pack(side="left", fill="x", expand=True, padx=(2, 8), pady=10)
            ctk.CTkLabel(
                text_box,
                text=geo.name,
                anchor="w",
                font=ctk.CTkFont(family=_FONT, size=14, weight="bold"),
            ).pack(fill="x")
            ctk.CTkLabel(
                text_box,
                text=f"{geo.country}   ·   {geo.latitude:.3f}, {geo.longitude:.3f}",
                anchor="w",
                text_color=_TEXT_DIM,
                font=ctk.CTkFont(family=_FONT, size=12),
            ).pack(fill="x")

            ctk.CTkButton(
                row,
                text="Přidat",
                width=100,
                height=34,
                corner_radius=10,
                font=ctk.CTkFont(family=_FONT, size=13, weight="bold"),
                command=lambda g=geo: self._add(g),
            ).pack(side="right", padx=10)

    def _add(self, geo: GeoCity) -> None:
        try:
            self.app.weather_vm.add_city(geo)
        except Exception as e:
            self._status.configure(text=str(e))
            return
        self.app.show("main")
