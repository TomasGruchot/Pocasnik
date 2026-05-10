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


_FONT = "Segoe UI"
_FONT_EMOJI = "Segoe UI Emoji"

_BG = "#0E1521"
_SIDEBAR_BG = "#0A0F18"
_CARD_BG = "#1A2235"
_CARD_BG_HOVER = "#222C42"
_TEXT_DIM = "#9AA4B8"
_TEXT_FAINT = "#5C6477"


class MainView(BaseView):
    """Hlavní obrazovka v Apple-Weather stylu.

    Levý sidebar = seznam měst, pravá strana = hero (lokace, velká teplota,
    emoji), hodinová předpověď, 7denní předpověď, statistiky.
    """

    def build(self) -> None:
        self._cities: list[City] = []
        self._selected: City | None = None
        self._city_buttons: dict[int, ctk.CTkButton] = {}

        self.configure(fg_color=_BG)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_detail()
        self._show_empty_state()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=_SIDEBAR_BG)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)

        self._user_label = ctk.CTkLabel(
            sidebar,
            text="",
            font=ctk.CTkFont(family=_FONT, size=15, weight="bold"),
            anchor="w",
        )
        self._user_label.grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 4))

        ctk.CTkLabel(
            sidebar,
            text="MOJE MĚSTA",
            text_color=_TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=_FONT, size=11, weight="bold"),
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 6))

        self._cities_list = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent", scrollbar_button_color=_CARD_BG
        )
        self._cities_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=2)

        ctk.CTkButton(
            sidebar,
            text="+  Přidat město",
            height=40,
            corner_radius=12,
            font=ctk.CTkFont(family=_FONT, size=13, weight="bold"),
            command=lambda: self.app.show("search"),
        ).grid(row=3, column=0, sticky="ew", padx=14, pady=(10, 6))

        ctk.CTkButton(
            sidebar,
            text="Odhlásit",
            fg_color="transparent",
            hover_color=_CARD_BG,
            border_width=1,
            border_color=_CARD_BG,
            text_color=_TEXT_DIM,
            height=36,
            corner_radius=12,
            command=self._do_logout,
        ).grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 18))

    def _build_detail(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=_CARD_BG
        )
        self._scroll.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self._scroll.grid_columnconfigure(0, weight=1)

        self._hero = ctk.CTkFrame(self._scroll, fg_color=_CARD_BG, corner_radius=20)
        self._hero.grid(row=0, column=0, sticky="ew")
        self._hero.grid_columnconfigure(0, weight=1)

        self._hero_emoji = ctk.CTkLabel(
            self._hero,
            text="",
            font=ctk.CTkFont(family=_FONT_EMOJI, size=72),
        )
        self._hero_emoji.grid(row=0, column=0, pady=(28, 0))

        self._hero_city = ctk.CTkLabel(
            self._hero,
            text="",
            font=ctk.CTkFont(family=_FONT, size=24, weight="bold"),
        )
        self._hero_city.grid(row=1, column=0, pady=(16, 0))

        self._hero_temp = ctk.CTkLabel(
            self._hero,
            text="",
            font=ctk.CTkFont(family=_FONT, size=84, weight="normal"),
        )
        self._hero_temp.grid(row=2, column=0, pady=(2, 0))

        self._hero_desc = ctk.CTkLabel(
            self._hero,
            text="",
            text_color=_TEXT_DIM,
            font=ctk.CTkFont(family=_FONT, size=14),
        )
        self._hero_desc.grid(row=3, column=0, pady=(2, 4))

        self._hero_minmax = ctk.CTkLabel(
            self._hero,
            text="",
            text_color=_TEXT_DIM,
            font=ctk.CTkFont(family=_FONT, size=13),
        )
        self._hero_minmax.grid(row=4, column=0, pady=(0, 28))

        self._hourly_card = ctk.CTkFrame(
            self._scroll, fg_color=_CARD_BG, corner_radius=18
        )
        self._hourly_card.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        self._hourly_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._hourly_card,
            text="HODINOVÁ PŘEDPOVĚĎ",
            text_color=_TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=_FONT, size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))

        self._hourly_strip = ctk.CTkScrollableFrame(
            self._hourly_card,
            orientation="horizontal",
            fg_color="transparent",
            height=130,
            scrollbar_button_color=_CARD_BG_HOVER,
        )
        self._hourly_strip.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 14))

        self._daily_card = ctk.CTkFrame(
            self._scroll, fg_color=_CARD_BG, corner_radius=18
        )
        self._daily_card.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        self._daily_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._daily_card,
            text="7DENNÍ PŘEDPOVĚĎ",
            text_color=_TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=_FONT, size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))

        self._daily_box = ctk.CTkFrame(self._daily_card, fg_color="transparent")
        self._daily_box.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        self._daily_box.grid_columnconfigure(0, weight=1)

        self._stats_card = ctk.CTkFrame(
            self._scroll, fg_color=_CARD_BG, corner_radius=18
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
        )
        self._refresh_btn.pack(side="left", padx=(0, 8))

        self._delete_btn = ctk.CTkButton(
            self._actions,
            text="Odebrat město",
            fg_color="#7F1D1D",
            hover_color="#991B1B",
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
            text_color=_TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=_FONT, size=11, weight="bold"),
        ).pack(anchor="w", padx=8)
        value = ctk.CTkLabel(
            cell,
            text="—",
            anchor="w",
            font=ctk.CTkFont(family=_FONT, size=22, weight="bold"),
        )
        value.pack(anchor="w", padx=8, pady=(2, 0))
        sub = ctk.CTkLabel(
            cell,
            text="",
            text_color=_TEXT_DIM,
            anchor="w",
            font=ctk.CTkFont(family=_FONT, size=12),
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
        self._city_buttons.clear()

        self._cities = self.app.weather_vm.list_cities()

        if not self._cities:
            ctk.CTkLabel(
                self._cities_list,
                text="Zatím žádná města.\nKlikni „+ Přidat město“.",
                text_color=_TEXT_FAINT,
                justify="center",
                font=ctk.CTkFont(family=_FONT, size=12),
            ).pack(pady=18, padx=8)
            self._show_empty_state()
            return

        for city in self._cities:
            btn = ctk.CTkButton(
                self._cities_list,
                text=city.label,
                anchor="w",
                fg_color="transparent",
                hover_color=_CARD_BG,
                text_color="#E5E7EB",
                height=42,
                corner_radius=10,
                font=ctk.CTkFont(family=_FONT, size=13),
                command=lambda c=city: self._select_city(c),
            )
            btn.pack(fill="x", padx=4, pady=2)
            if city.id is not None:
                self._city_buttons[city.id] = btn

        if self._selected is not None and any(
            c.id == self._selected.id for c in self._cities
        ):
            self._highlight_selected()
        else:
            self._select_city(self._cities[0])

    def _highlight_selected(self) -> None:
        for cid, btn in self._city_buttons.items():
            if self._selected is not None and cid == self._selected.id:
                btn.configure(fg_color=_CARD_BG, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#E5E7EB")

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
                text_color=_TEXT_DIM,
                font=ctk.CTkFont(family=_FONT, size=12, weight="bold"),
            ).pack()
            ctk.CTkLabel(
                cell,
                text=weather_emoji(code, report.current_is_day),
                font=ctk.CTkFont(family=_FONT_EMOJI, size=22),
            ).pack(pady=(4, 4))
            ctk.CTkLabel(
                cell,
                text=f"{temp:.0f}°",
                font=ctk.CTkFont(family=_FONT, size=14, weight="bold"),
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
            row.grid_columnconfigure(3, weight=1)

            day_label = "Dnes" if i == 0 else format_weekday(date)
            ctk.CTkLabel(
                row,
                text=day_label,
                width=70,
                anchor="w",
                font=ctk.CTkFont(family=_FONT, size=14, weight="bold"),
            ).grid(row=0, column=0, padx=(4, 0), pady=8)

            ctk.CTkLabel(
                row,
                text=weather_emoji(code, True),
                width=40,
                font=ctk.CTkFont(family=_FONT_EMOJI, size=20),
            ).grid(row=0, column=1, padx=(0, 6))

            chance_text = f"{chance}%" if chance > 0 else ""
            ctk.CTkLabel(
                row,
                text=chance_text,
                text_color="#7DD3FC",
                width=46,
                anchor="w",
                font=ctk.CTkFont(family=_FONT, size=12),
            ).grid(row=0, column=2, padx=(0, 8))

            ctk.CTkLabel(
                row,
                text=f"{tmin:.0f}°",
                text_color=_TEXT_DIM,
                width=36,
                anchor="e",
                font=ctk.CTkFont(family=_FONT, size=14),
            ).grid(row=0, column=3, sticky="e")

            bar = ctk.CTkProgressBar(
                row,
                height=6,
                corner_radius=3,
                progress_color="#60A5FA",
                fg_color="#2B3552",
            )
            bar.grid(row=0, column=4, sticky="ew", padx=12)
            bar.set(min(max((tmax - global_min) / span, 0.0), 1.0))

            ctk.CTkLabel(
                row,
                text=f"{tmax:.0f}°",
                width=36,
                anchor="w",
                font=ctk.CTkFont(family=_FONT, size=14, weight="bold"),
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
