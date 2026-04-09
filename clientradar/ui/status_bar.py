from __future__ import annotations

import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, height=36, corner_radius=0, **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        self._info_label = ctk.CTkLabel(
            self, text="📡 ClientRadar | Celkem: 0", anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self._info_label.grid(row=0, column=0, padx=10, sticky="w")

        self._message_label = ctk.CTkLabel(
            self, text="Připraveno", anchor="e",
            font=ctk.CTkFont(size=12),
        )
        self._message_label.grid(row=0, column=2, padx=10, sticky="e")

        self._progress = ctk.CTkProgressBar(self, width=200)
        self._progress.grid(row=0, column=1, padx=5)
        self._progress.set(0)
        self._progress.grid_remove()

    def update_stats(self, stats: dict) -> None:
        total = stats.get("total", 0)
        new = stats.get("new", 0)
        contacted = stats.get("contacted", 0)
        interested = stats.get("interested", 0)
        text = (
            f"📡 ClientRadar | Celkem: {total} | "
            f"Nových: {new} | Kontaktováno: {contacted} | "
            f"Zájem: {interested}"
        )
        self._info_label.configure(text=text)

    def set_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._progress.grid()
            self._progress.set(current / total)
        else:
            self._progress.set(0)

    def set_message(self, text: str) -> None:
        self._message_label.configure(text=text)

    def hide_progress(self) -> None:
        self._progress.grid_remove()
        self._progress.set(0)

    def show_idle(self) -> None:
        self.hide_progress()
        self.set_message("Připraveno")
