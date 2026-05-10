"""Hlavní řízení aplikace – přepínání obrazovek, registrace easter-eggu."""

from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk

from app.database import Database
from app.easter_egg.terminal_game import TerminalGameWindow
from app.models.user import User
from app.viewmodels.auth_vm import AuthViewModel
from app.viewmodels.weather_vm import WeatherViewModel
from app.views.base_view import BaseView
from app.views.login_view import LoginView
from app.views.main_view import MainView
from app.views.map_view import MapView
from app.views.register_view import RegisterView
from app.views.search_city_view import SearchCityView


def _asset_path(name: str) -> Path:
    """Cesta k souboru z app/assets/ – funguje i v PyInstaller bundlu."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent
    return base / "assets" / name


class Application:
    """Vstupní fasáda – drží root okno, viewmodely a slovník obrazovek."""

    APP_TITLE = "POČASNÍK"
    WINDOW_SIZE = "1024x680"

    def __init__(self) -> None:
        Database.get_instance()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(self.APP_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        self.root.minsize(820, 560)
        self._set_icon()

        self.auth_vm = AuthViewModel()
        self.weather_vm: WeatherViewModel | None = None

        self._views: dict[str, BaseView] = {}
        self._current: BaseView | None = None
        self._egg_window: TerminalGameWindow | None = None

        self._views["login"] = LoginView(self)
        self._views["register"] = RegisterView(self)

        self._bind_easter_egg()

        self.show("login")

    def _set_icon(self) -> None:
        try:
            self.root.iconbitmap(default=str(_asset_path("icon.ico")))
        except Exception:
            pass

    def _bind_easter_egg(self) -> None:
        """Skrytá zkratka Ctrl+Shift+E – otevře terminálový minigame."""
        self.root.bind_all("<Control-Shift-KeyPress-E>", lambda _e: self._open_egg())
        self.root.bind_all("<Control-Shift-KeyPress-e>", lambda _e: self._open_egg())

    def _open_egg(self) -> None:
        if self._egg_window is not None and self._egg_window.winfo_exists():
            self._egg_window.lift()
            self._egg_window.focus_set()
            return
        self._egg_window = TerminalGameWindow(master=self.root)

    def show(self, name: str) -> None:
        if name not in self._views:
            raise KeyError(f"Neznámá obrazovka: {name}")
        if self._current is not None:
            self._current.hide()
        self._current = self._views[name]
        self._current.show()

    def on_user_logged_in(self, user: User) -> None:
        self.weather_vm = WeatherViewModel(user)
        if "main" not in self._views:
            self._views["main"] = MainView(self)
            self._views["search"] = SearchCityView(self)
            self._views["map"] = MapView(self)
        self.show("main")

    def on_user_logout(self) -> None:
        self.auth_vm.logout()
        self.weather_vm = None
        for key in ("main", "search", "map"):
            if key in self._views:
                self._views[key].destroy()
                del self._views[key]
        self.show("login")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    Application().run()
