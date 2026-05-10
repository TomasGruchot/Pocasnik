from __future__ import annotations

import threading

import customtkinter as ctk

from app.models.city import City
from app.services.weather_service import (
    WeatherReport,
    describe_weather_code,
    format_hour,
    format_weekday,
    weather_emoji,
)
from app.views.base_view import BaseView
from app.views.theme import (
    ACCENT_PROGRESS,
    ACCENT_PROGRESS_BG,
    BG,
    CARD,
    CARD_ACTIVE,
    CARD_BORDER,
    CARD_HOVER,
    CHANCE_BLUE,
    DANGER,
    DANGER_HOVER,
    FONT,
    FONT_EMOJI,
    SIDEBAR,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
)


class _CityListItem(ctk.CTkFrame):
    """Karta města v sidebaru s emoji počasí a aktuální teplotou."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        city: City,
        on_click,
    ) -> None:
        super().__init__(
            master,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=CARD_BORDER,
            height=64,
        )
        self._city = city
        self._on_click = on_click
        self._is_active = False

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._name = ctk.CTkLabel(
            self,
            text=city.name,
            anchor="w",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
        )
        self._name.grid(row=0, column=0, sticky="sw", padx=(12, 4), pady=(8, 0))

        self._sub = ctk.CTkLabel(
            self,
            text=city.country,
            anchor="w",
            text_color=TEXT_FAINT,
            font=ctk.CTkFont(family=FONT, size=11),
        )
        self._sub.grid(row=1, column=0, sticky="nw", padx=(12, 4), pady=(0, 8))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="e", padx=(0, 12))
        self._emoji = ctk.CTkLabel(
            right,
            text="…",
            text_color=TEXT_DIM,
            font=ctk.CTkFont(family=FONT_EMOJI, size=22),
        )
        self._emoji.pack()
        self._temp = ctk.CTkLabel(
            right,
            text="—",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
        )
        self._temp.pack()

        self.bind("<Button-1>", self._fire_click)
        for child in (self._name, self._sub, self._emoji, self._temp, right):
            child.bind("<Button-1>", self._fire_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    @property
    def city(self) -> City:
        return self._city

    def set_weather(self, emoji: str, temp_c: float) -> None:
        self._emoji.configure(text=emoji)
        self._temp.configure(text=f"{temp_c:.0f}°")

    def set_loading(self) -> None:
        self._emoji.configure(text="…")
        self._temp.configure(text="—")

    def set_error(self) -> None:
        self._emoji.configure(text="⚠")
        self._temp.configure(text="—")

    def set_active(self, active: bool) -> None:
        self._is_active = active
        self._apply_bg()

    def _apply_bg(self) -> None:
        if self._is_active:
            self.configure(fg_color=CARD_ACTIVE, border_color=ACCENT_PROGRESS)
        else:
            self.configure(fg_color=CARD, border_color=CARD_BORDER)

    def _on_enter(self, _e=None) -> None:
        if not self._is_active:
            self.configure(fg_color=CARD_HOVER)

    def _on_leave(self, _e=None) -> None:
        self._apply_bg()

    def _fire_click(self, _e=None) -> None:
        self._on_click(self._city)


class MainView(BaseView):
    """Hlavní obrazovka – Apple Weather feel (šedá frosted paleta)."""

    def build(self) -> None:
        self._cities: list[City] = []
        self._selected: City | None = None
        self._city_items: dict[int, _CityListItem] = {}

        self.configure(fg_color=BG)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_detail()
        self._show_empty_state()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(3, weight=1)

        self._user_label = ctk.CTkLabel(
            sidebar,
            text="",
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
        )
        self._user_label.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 4))

        ctk.CTkButton(
            sidebar,
            text="🗺️   Mapa",
            height=42,
            corner_radius=12,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_color=CARD_BORDER,
            border_width=1,
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
            command=lambda: self.app.show("map"),
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 12))

        ctk.CTkLabel(
            sidebar,
            text="MOJE MĚSTA",
            text_color=TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=2, column=0, sticky="ew", padx=20, pady=(2, 6))

        self._cities_list = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent", scrollbar_button_color=CARD_BORDER
        )
        self._cities_list.grid(row=3, column=0, sticky="nsew", padx=10, pady=2)

        ctk.CTkButton(
            sidebar,
            text="+   Přidat město",
            height=40,
            corner_radius=12,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_color=CARD_BORDER,
            border_width=1,
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
            command=lambda: self.app.show("search"),
        ).grid(row=4, column=0, sticky="ew", padx=14, pady=(10, 6))

        ctk.CTkButton(
            sidebar,
            text="Odhlásit",
            fg_color="transparent",
            hover_color=CARD,
            border_width=1,
            border_color=CARD_BORDER,
            text_color=TEXT_DIM,
            height=36,
            corner_radius=12,
            command=self._do_logout,
        ).grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 18))

    def _build_detail(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=CARD_BORDER
        )
        self._scroll.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self._scroll.grid_columnconfigure(0, weight=1)

        self._hero = ctk.CTkFrame(
            self._scroll,
            fg_color=CARD,
            corner_radius=20,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self._hero.grid(row=0, column=0, sticky="ew")
        self._hero.grid_columnconfigure(0, weight=1)

        self._hero_emoji = ctk.CTkLabel(
            self._hero, text="", font=ctk.CTkFont(family=FONT_EMOJI, size=72)
        )
        self._hero_emoji.grid(row=0, column=0, pady=(28, 0))

        self._hero_city = ctk.CTkLabel(
            self._hero,
            text="",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=24, weight="bold"),
        )
        self._hero_city.grid(row=1, column=0, pady=(16, 0))

        self._hero_temp = ctk.CTkLabel(
            self._hero,
            text="",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=84),
        )
        self._hero_temp.grid(row=2, column=0, pady=(2, 0))

        self._hero_desc = ctk.CTkLabel(
            self._hero,
            text="",
            text_color=TEXT_DIM,
            font=ctk.CTkFont(family=FONT, size=14),
        )
        self._hero_desc.grid(row=3, column=0, pady=(2, 4))

        self._hero_minmax = ctk.CTkLabel(
            self._hero,
            text="",
            text_color=TEXT_DIM,
            font=ctk.CTkFont(family=FONT, size=13),
        )
        self._hero_minmax.grid(row=4, column=0, pady=(0, 28))

        self._hourly_card = ctk.CTkFrame(
            self._scroll,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self._hourly_card.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        self._hourly_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._hourly_card,
            text="HODINOVÁ PŘEDPOVĚĎ",
            text_color=TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))

        self._hourly_strip = ctk.CTkScrollableFrame(
            self._hourly_card,
            orientation="horizontal",
            fg_color="transparent",
            height=130,
            scrollbar_button_color=CARD_BORDER,
        )
        self._hourly_strip.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 14))

        self._daily_card = ctk.CTkFrame(
            self._scroll,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self._daily_card.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        self._daily_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._daily_card,
            text="7DENNÍ PŘEDPOVĚĎ",
            text_color=TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))

        self._daily_box = ctk.CTkFrame(self._daily_card, fg_color="transparent")
        self._daily_box.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        self._daily_box.grid_columnconfigure(0, weight=1)

        self._stats_card = ctk.CTkFrame(
            self._scroll,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self._stats_card.grid(row=3, column=0, sticky="ew", pady=(16, 4))
        self._stats_card.grid_columnconfigure((0, 1, 2), weight=1, uniform="stats")

        self._stat_humidity = self._build_stat(self._stats_card, "💧", "VLHKOST", 0)
        self._stat_wind = self._build_stat(self._stats_card, "💨", "VÍTR", 1)
        self._stat_feel = self._build_stat(self._stats_card, "🌡️", "POCITOVÁ", 2)

        self._actions = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._actions.grid(row=4, column=0, sticky="ew", pady=(14, 4))

        self._refresh_btn = ctk.CTkButton(
            self._actions,
            text="Obnovit",
            command=self._refresh_weather,
            width=130,
            height=36,
            corner_radius=10,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_color=CARD_BORDER,
            border_width=1,
            text_color=TEXT,
        )
        self._refresh_btn.pack(side="left", padx=(0, 8))

        self._delete_btn = ctk.CTkButton(
            self._actions,
            text="Odebrat město",
            fg_color=DANGER,
            hover_color=DANGER_HOVER,
            command=self._delete_selected,
            width=160,
            height=36,
            corner_radius=10,
        )
        self._delete_btn.pack(side="left")

    def _build_stat(self, parent: ctk.CTkFrame, emoji: str, label: str, col: int) -> dict:
        cell = ctk.CTkFrame(parent, fg_color="transparent")
        cell.grid(row=0, column=col, sticky="nsew", padx=10, pady=14)
        ctk.CTkLabel(
            cell,
            text=f"{emoji}  {label}",
            text_color=TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).pack(anchor="w", padx=8)
        value = ctk.CTkLabel(
            cell,
            text="—",
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=22, weight="bold"),
        )
        value.pack(anchor="w", padx=8, pady=(2, 0))
        sub = ctk.CTkLabel(
            cell,
            text="",
            text_color=TEXT_DIM,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=12),
        )
        sub.pack(anchor="w", padx=8)
        return {"value": value, "sub": sub}

    def on_show(self) -> None:
        user = self.app.weather_vm.user
        self._user_label.configure(text=f"@{user.username}")
        self._reload_cities()

    def _reload_cities(self) -> None:
        for child in self._cities_list.winfo_children():
            child.destroy()
        self._city_items.clear()

        self._cities = self.app.weather_vm.list_cities()

        if not self._cities:
            ctk.CTkLabel(
                self._cities_list,
                text="Zatím žádná města.\nKlikni „+ Přidat město“.",
                text_color=TEXT_FAINT,
                justify="center",
                font=ctk.CTkFont(family=FONT, size=12),
            ).pack(pady=18, padx=8)
            self._show_empty_state()
            return

        for city in self._cities:
            item = _CityListItem(
                self._cities_list, city=city, on_click=self._select_city
            )
            item.pack(fill="x", padx=4, pady=4)
            if city.id is not None:
                self._city_items[city.id] = item
            self._fetch_weather_for_item(item)

        if self._selected is not None and any(
            c.id == self._selected.id for c in self._cities
        ):
            self._highlight_selected()
        else:
            self._select_city(self._cities[0])

    def _fetch_weather_for_item(self, item: _CityListItem) -> None:
        item.set_loading()
        city = item.city

        def worker() -> None:
            try:
                report = self.app.weather_vm.fetch_weather(city)
            except Exception:
                self.after(0, item.set_error)
                return

            def apply():
                if not item.winfo_exists():
                    return
                item.set_weather(
                    weather_emoji(report.current_code, report.current_is_day),
                    report.current_temperature,
                )

            self.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _highlight_selected(self) -> None:
        for cid, item in self._city_items.items():
            item.set_active(self._selected is not None and cid == self._selected.id)

    def _show_empty_state(self) -> None:
        self._selected = None
        self._hero_emoji.configure(text="🌍")
        self._hero_city.configure(text="Přidej si první město")
        self._hero_temp.configure(text="—")
        self._hero_desc.configure(text="Klikni vlevo na „+ Přidat město“")
        self._hero_minmax.configure(text="")
        for child in self._hourly_strip.winfo_children():
            child.destroy()
        for child in self._daily_box.winfo_children():
            child.destroy()
        for stat in (self._stat_humidity, self._stat_wind, self._stat_feel):
            stat["value"].configure(text="—")
            stat["sub"].configure(text="")
        self._refresh_btn.configure(state="disabled")
        self._delete_btn.configure(state="disabled")

    def _select_city(self, city: City) -> None:
        self._selected = city
        self._highlight_selected()
        self._hero_city.configure(text=city.label)
        self._hero_emoji.configure(text="…")
        self._hero_temp.configure(text="—")
        self._hero_desc.configure(text="Načítám počasí…")
        self._hero_minmax.configure(text="")
        for child in self._hourly_strip.winfo_children():
            child.destroy()
        for child in self._daily_box.winfo_children():
            child.destroy()
        for stat in (self._stat_humidity, self._stat_wind, self._stat_feel):
            stat["value"].configure(text="—")
            stat["sub"].configure(text="")
        self._refresh_btn.configure(state="normal")
        self._delete_btn.configure(state="normal")
        self._refresh_weather()

    def _refresh_weather(self) -> None:
        city = self._selected
        if city is None:
            return
        self._hero_desc.configure(text="Načítám počasí…")

        def worker() -> None:
            try:
                report = self.app.weather_vm.fetch_weather(city)
            except Exception as e:
                self.after(
                    0, lambda err=str(e): self._hero_desc.configure(text=f"Chyba: {err}")
                )
                return
            self.after(0, lambda r=report: self._render_report(r))

        threading.Thread(target=worker, daemon=True).start()

    def _render_report(self, report: WeatherReport) -> None:
        self._hero_emoji.configure(
            text=weather_emoji(report.current_code, report.current_is_day)
        )
        self._hero_temp.configure(text=f"{report.current_temperature:.0f}°")
        self._hero_desc.configure(text=describe_weather_code(report.current_code))

        if report.daily_max and report.daily_min:
            self._hero_minmax.configure(
                text=(
                    f"Max.: {report.daily_max[0]:.0f}°   "
                    f"Min.: {report.daily_min[0]:.0f}°"
                )
            )

        if self._selected is not None and self._selected.id in self._city_items:
            self._city_items[self._selected.id].set_weather(
                weather_emoji(report.current_code, report.current_is_day),
                report.current_temperature,
            )

        self._render_hourly(report)
        self._render_daily(report)
        self._render_stats(report)

    def _render_hourly(self, report: WeatherReport) -> None:
        for child in self._hourly_strip.winfo_children():
            child.destroy()
        for time_iso, code, temp in zip(
            report.hourly_times, report.hourly_codes, report.hourly_temps
        ):
            cell = ctk.CTkFrame(self._hourly_strip, fg_color="transparent")
            cell.pack(side="left", padx=10, pady=4)

            ctk.CTkLabel(
                cell,
                text=format_hour(time_iso),
                text_color=TEXT_DIM,
                font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
            ).pack()
            ctk.CTkLabel(
                cell,
                text=weather_emoji(code, report.current_is_day),
                font=ctk.CTkFont(family=FONT_EMOJI, size=22),
            ).pack(pady=(4, 4))
            ctk.CTkLabel(
                cell,
                text=f"{temp:.0f}°",
                text_color=TEXT,
                font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
            ).pack()

    def _render_daily(self, report: WeatherReport) -> None:
        for child in self._daily_box.winfo_children():
            child.destroy()

        if not report.daily_dates:
            return

        global_min = min(report.daily_min)
        global_max = max(report.daily_max)
        span = max(global_max - global_min, 1.0)

        for i, date in enumerate(report.daily_dates):
            tmin = report.daily_min[i]
            tmax = report.daily_max[i]
            code = report.daily_codes[i]
            chance = (
                report.daily_precip_chance[i]
                if i < len(report.daily_precip_chance)
                else 0
            )

            row = ctk.CTkFrame(self._daily_box, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            row.grid_columnconfigure(4, weight=1)

            day_label = "Dnes" if i == 0 else format_weekday(date)
            ctk.CTkLabel(
                row,
                text=day_label,
                width=70,
                anchor="w",
                text_color=TEXT,
                font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
            ).grid(row=0, column=0, padx=(4, 0), pady=8)

            ctk.CTkLabel(
                row,
                text=weather_emoji(code, True),
                width=40,
                font=ctk.CTkFont(family=FONT_EMOJI, size=20),
            ).grid(row=0, column=1, padx=(0, 6))

            chance_text = f"{chance}%" if chance > 0 else ""
            ctk.CTkLabel(
                row,
                text=chance_text,
                text_color=CHANCE_BLUE,
                width=46,
                anchor="w",
                font=ctk.CTkFont(family=FONT, size=12),
            ).grid(row=0, column=2, padx=(0, 8))

            ctk.CTkLabel(
                row,
                text=f"{tmin:.0f}°",
                text_color=TEXT_DIM,
                width=36,
                anchor="e",
                font=ctk.CTkFont(family=FONT, size=14),
            ).grid(row=0, column=3, sticky="e")

            bar = ctk.CTkProgressBar(
                row,
                height=6,
                corner_radius=3,
                progress_color=ACCENT_PROGRESS,
                fg_color=ACCENT_PROGRESS_BG,
            )
            bar.grid(row=0, column=4, sticky="ew", padx=12)
            bar.set(min(max((tmax - global_min) / span, 0.0), 1.0))

            ctk.CTkLabel(
                row,
                text=f"{tmax:.0f}°",
                text_color=TEXT,
                width=36,
                anchor="w",
                font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
            ).grid(row=0, column=5, sticky="w", padx=(0, 4))

    def _render_stats(self, report: WeatherReport) -> None:
        self._stat_humidity["value"].configure(text=f"{report.current_humidity:.0f}%")
        self._stat_humidity["sub"].configure(text="relativní")

        self._stat_wind["value"].configure(text=f"{report.current_wind:.0f}")
        self._stat_wind["sub"].configure(text="km/h")

        self._stat_feel["value"].configure(text=f"{report.current_apparent:.0f}°")
        diff = report.current_apparent - report.current_temperature
        if abs(diff) < 0.5:
            sub = "stejně jako teplota"
        elif diff < 0:
            sub = f"chladnější o {abs(diff):.0f}°"
        else:
            sub = f"teplejší o {diff:.0f}°"
        self._stat_feel["sub"].configure(text=sub)

    def _delete_selected(self) -> None:
        if self._selected is None:
            return
        self.app.weather_vm.remove_city(self._selected)
        self._selected = None
        self._reload_cities()

    def _do_logout(self) -> None:
        self.app.on_user_logout()
