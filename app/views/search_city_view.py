from __future__ import annotations

import threading

import customtkinter as ctk

from app.services.weather_service import GeoCity
from app.views.base_view import BaseView


class SearchCityView(BaseView):
    """Vyhledávání města přes Open-Meteo Geocoding API."""

    def build(self) -> None:
        self._results: list[GeoCity] = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))

        ctk.CTkButton(
            header,
            text="← Zpět",
            width=80,
            fg_color="transparent",
            border_width=1,
            command=lambda: self.app.show("main"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Přidat město",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=16)

        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=24, pady=8)

        self._query = ctk.CTkEntry(
            search_row, placeholder_text="Název města (např. Praha)…", height=38
        )
        self._query.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._query.bind("<Return>", lambda _e: self._do_search())

        self._search_btn = ctk.CTkButton(
            search_row, text="Hledat", width=120, height=38, command=self._do_search
        )
        self._search_btn.pack(side="left")

        self._status = ctk.CTkLabel(self, text="", text_color="#9CA3AF")
        self._status.pack(fill="x", padx=24, pady=(4, 0))

        self._results_box = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._results_box.pack(fill="both", expand=True, padx=24, pady=(8, 24))

    def on_show(self) -> None:
        self._status.configure(text="")
        self._query.delete(0, "end")
        for child in self._results_box.winfo_children():
            child.destroy()
        self._query.focus_set()

    def _do_search(self) -> None:
        query = self._query.get().strip()
        if not query:
            self._status.configure(text="Zadej název města.")
            return
        self._status.configure(text="Hledám…")
        self._search_btn.configure(state="disabled")
        for child in self._results_box.winfo_children():
            child.destroy()

        def worker() -> None:
            try:
                results = self.app.weather_vm.search_city(query)
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))
                return
            self.after(0, lambda: self._on_results(results))

        threading.Thread(target=worker, daemon=True).start()

    def _on_error(self, msg: str) -> None:
        self._search_btn.configure(state="normal")
        self._status.configure(text=f"Chyba: {msg}")

    def _on_results(self, results: list[GeoCity]) -> None:
        self._search_btn.configure(state="normal")
        self._results = results
        if not results:
            self._status.configure(text="Nic se nenašlo.")
            return
        self._status.configure(text=f"Nalezeno: {len(results)}")
        for geo in results:
            row = ctk.CTkFrame(self._results_box, corner_radius=10)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row,
                text=f"{geo.name}, {geo.country}",
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="left", padx=12, pady=8, fill="x", expand=True)
            ctk.CTkLabel(
                row,
                text=f"{geo.latitude:.3f}, {geo.longitude:.3f}",
                text_color="#9CA3AF",
            ).pack(side="left", padx=8)
            ctk.CTkButton(
                row,
                text="Přidat",
                width=100,
                command=lambda g=geo: self._add(g),
            ).pack(side="right", padx=8, pady=6)

    def _add(self, geo: GeoCity) -> None:
        try:
            self.app.weather_vm.add_city(geo)
        except Exception as e:
            self._status.configure(text=str(e))
            return
        self.app.show("main")
