from __future__ import annotations

import threading

import customtkinter as ctk

from app.models.city import City
from app.services.weather_service import WeatherReport, describe_weather_code
from app.views.base_view import BaseView


class MainView(BaseView):
    """Hlavní obrazovka po přihlášení – levý sidebar + detail počasí."""

    def build(self) -> None:
        self._cities: list[City] = []
        self._selected: City | None = None
        self._city_buttons: list[ctk.CTkButton] = []

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_detail()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)

        self._user_label = ctk.CTkLabel(
            sidebar, text="", font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        self._user_label.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 4))

        ctk.CTkLabel(
            sidebar, text="Moje města", text_color="#9CA3AF", anchor="w"
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 4))

        self._cities_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self._cities_list.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)

        ctk.CTkButton(
            sidebar,
            text="+ Přidat město",
            command=lambda: self.app.show("search"),
        ).grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 6))

        ctk.CTkButton(
            sidebar,
            text="Odhlásit",
            fg_color="transparent",
            border_width=1,
            command=self._do_logout,
        ).grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))

    def _build_detail(self) -> None:
        self._detail = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._detail.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self._detail.grid_columnconfigure(0, weight=1)

        self._title = ctk.CTkLabel(
            self._detail, text="", font=ctk.CTkFont(size=28, weight="bold"), anchor="w"
        )
        self._title.grid(row=0, column=0, sticky="ew")

        self._subtitle = ctk.CTkLabel(
            self._detail, text="", text_color="#9CA3AF", anchor="w"
        )
        self._subtitle.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        self._current_box = ctk.CTkFrame(self._detail, corner_radius=12)
        self._current_box.grid(row=2, column=0, sticky="ew", pady=(0, 16))

        self._current_label = ctk.CTkLabel(
            self._current_box,
            text="Vyber město vlevo, nebo přidej nové.",
            font=ctk.CTkFont(size=18),
            anchor="w",
            justify="left",
        )
        self._current_label.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            self._detail,
            text="7denní předpověď",
            text_color="#9CA3AF",
            anchor="w",
        ).grid(row=3, column=0, sticky="ew", pady=(8, 4))

        self._forecast_box = ctk.CTkFrame(self._detail, fg_color="transparent")
        self._forecast_box.grid(row=4, column=0, sticky="ew")

        self._action_row = ctk.CTkFrame(self._detail, fg_color="transparent")
        self._action_row.grid(row=5, column=0, sticky="ew", pady=(16, 0))

        self._refresh_btn = ctk.CTkButton(
            self._action_row, text="Obnovit", command=self._refresh_weather, width=140
        )
        self._refresh_btn.pack(side="left", padx=(0, 8))

        self._delete_btn = ctk.CTkButton(
            self._action_row,
            text="Odebrat město",
            fg_color="#7F1D1D",
            hover_color="#991B1B",
            command=self._delete_selected,
            width=160,
        )
        self._delete_btn.pack(side="left")

        self._refresh_btn.configure(state="disabled")
        self._delete_btn.configure(state="disabled")

    def on_show(self) -> None:
        user = self.app.weather_vm.user
        self._user_label.configure(text=f"@{user.username}")
        self._reload_cities()

    def _reload_cities(self) -> None:
        for btn in self._city_buttons:
            btn.destroy()
        self._city_buttons.clear()

        self._cities = self.app.weather_vm.list_cities()

        if not self._cities:
            empty = ctk.CTkLabel(
                self._cities_list,
                text="Zatím žádná města.",
                text_color="#6B7280",
            )
            empty.pack(pady=8)
            self._city_buttons.append(empty)  # type: ignore[arg-type]
            return

        for city in self._cities:
            btn = ctk.CTkButton(
                self._cities_list,
                text=city.label,
                anchor="w",
                fg_color="transparent",
                hover_color="#1F2937",
                command=lambda c=city: self._select_city(c),
            )
            btn.pack(fill="x", padx=4, pady=2)
            self._city_buttons.append(btn)

    def _select_city(self, city: City) -> None:
        self._selected = city
        self._title.configure(text=city.label)
        self._subtitle.configure(
            text=f"Souřadnice: {city.latitude:.3f}, {city.longitude:.3f}"
        )
        self._current_label.configure(text="Načítám počasí…")
        for child in self._forecast_box.winfo_children():
            child.destroy()
        self._refresh_btn.configure(state="normal")
        self._delete_btn.configure(state="normal")
        self._refresh_weather()

    def _refresh_weather(self) -> None:
        city = self._selected
        if city is None:
            return

        def worker() -> None:
            try:
                report = self.app.weather_vm.fetch_weather(city)
            except Exception as e:
                self.after(0, lambda: self._current_label.configure(text=f"Chyba: {e}"))
                return
            self.after(0, lambda: self._render_report(report))

        threading.Thread(target=worker, daemon=True).start()

    def _render_report(self, report: WeatherReport) -> None:
        self._current_label.configure(
            text=(
                f"{report.current_temperature:.1f} °C   ·   "
                f"{describe_weather_code(report.current_code)}\n"
                f"Vítr: {report.current_wind:.0f} km/h"
            )
        )
        for child in self._forecast_box.winfo_children():
            child.destroy()
        for date, tmax, tmin, code in zip(
            report.daily_dates,
            report.daily_max,
            report.daily_min,
            report.daily_codes,
        ):
            card = ctk.CTkFrame(self._forecast_box, corner_radius=10)
            card.pack(side="left", fill="y", padx=4, pady=4, ipadx=10, ipady=8)
            ctk.CTkLabel(card, text=date, text_color="#9CA3AF").pack()
            ctk.CTkLabel(
                card,
                text=f"{tmax:.0f}° / {tmin:.0f}°",
                font=ctk.CTkFont(size=16, weight="bold"),
            ).pack()
            ctk.CTkLabel(
                card,
                text=describe_weather_code(code),
                wraplength=110,
                justify="center",
            ).pack()

    def _delete_selected(self) -> None:
        if self._selected is None:
            return
        self.app.weather_vm.remove_city(self._selected)
        self._selected = None
        self._title.configure(text="")
        self._subtitle.configure(text="")
        self._current_label.configure(text="Vyber město vlevo, nebo přidej nové.")
        for child in self._forecast_box.winfo_children():
            child.destroy()
        self._refresh_btn.configure(state="disabled")
        self._delete_btn.configure(state="disabled")
        self._reload_cities()

    def _do_logout(self) -> None:
        self.app.on_user_logout()
