from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from app.app import Application


class BaseView(ctk.CTkFrame):
    """Společný předek všech obrazovek (polymorfismus přes `build()`/`on_show()`).

    Konkrétní view implementují `build()` (sestavení widgetů) a mohou
    přepsat `on_show()` (např. pro načtení dat).
    """

    def __init__(self, app: "Application") -> None:
        super().__init__(master=app.root, fg_color="transparent")
        self.app = app
        self.build()

    @abstractmethod
    def build(self) -> None: ...

    def on_show(self) -> None:
        """Volá se při zobrazení obrazovky (default no-op)."""
        return None

    def show(self) -> None:
        self.pack(fill="both", expand=True)
        self.on_show()

    def hide(self) -> None:
        self.pack_forget()
