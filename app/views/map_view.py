"""Mapa měst s počasím (Apple Weather inspirace).

Používá knihovnu `tkintermapview` (OpenStreetMap dlaždice). Markery:
  • uložená města uživatele – vždy viditelná, akcent v Apple-šedém tónu
  • katalogová města (cities.json) – objevují se podle úrovně zoomu
    (logika v `CityCatalogService.min_population_for_zoom`)

Zoom/pan se sleduje přes 500 ms polling (knihovna nemá nativní hook).
Počasí se cachuje, aby se neopakovaly HTTP requesty po každém panu.
"""

from __future__ import annotations

import math
import threading
import time
from typing import Any

import customtkinter as ctk

from app.services.city_catalog import CatalogCity, CityCatalogService
from app.services.weather_service import WeatherService, weather_emoji
from app.views.base_view import BaseView
from app.views.theme import (
    BG,
    CARD,
    CARD_BORDER,
    CARD_HOVER,
    FONT,
    FONT_EMOJI,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
)

try:
    from tkintermapview import TkinterMapView
except ImportError:
    TkinterMapView = None  # type: ignore[assignment]


_POLL_MS = 500
_CACHE_TTL_S = 1800
_USER_MARKER_COLOR = "#5E83A9"
_USER_MARKER_RING = "#A6BFD6"
_CATALOG_MARKER_COLOR = "#5C6477"
_CATALOG_MARKER_RING = "#9AA4B8"


class MapView(BaseView):
    """Interaktivní mapa s počasím u jednotlivých měst."""

    def build(self) -> None:
        self.configure(fg_color=BG)
        self._weather_cache: dict[tuple[float, float], tuple[str, float, float]] = {}
        self._weather_inflight: set[tuple[float, float]] = set()
        self._user_markers: list[Any] = []
        self._catalog_markers: list[Any] = []
        self._last_zoom: int = -1
        self._last_center: tuple[float, float] | None = None
        self._poll_after_id: str | None = None
        self._service = WeatherService()
        self._is_visible = False

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(18, 8))

        ctk.CTkButton(
            header,
            text="←  Zpět",
            width=80,
            height=36,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=CARD_BORDER,
            text_color=TEXT_DIM,
            command=lambda: self.app.show("main"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Mapa",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=22, weight="bold"),
        ).pack(side="left", padx=14)

        self._zoom_info = ctk.CTkLabel(
            header,
            text="",
            text_color=TEXT_FAINT,
            font=ctk.CTkFont(family=FONT, size=12),
        )
        self._zoom_info.pack(side="left", padx=8)

        self._refresh_btn = ctk.CTkButton(
            header,
            text="Obnovit počasí",
            width=140,
            height=36,
            corner_radius=10,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_width=1,
            border_color=CARD_BORDER,
            text_color=TEXT,
            command=self._force_refresh,
        )
        self._refresh_btn.pack(side="right")

        body = ctk.CTkFrame(
            self,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=CARD_BORDER,
        )
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        if TkinterMapView is None:
            ctk.CTkLabel(
                body,
                text=(
                    "Mapa vyžaduje balíček `tkintermapview`.\n"
                    "Nainstaluj ho:  pip install tkintermapview"
                ),
                text_color=TEXT_DIM,
                font=ctk.CTkFont(family=FONT, size=14),
            ).pack(expand=True, pady=40)
            self._map = None
            return

        self._map = TkinterMapView(
            body,
            corner_radius=14,
            bg_color=CARD,
        )
        self._map.pack(fill="both", expand=True, padx=8, pady=8)
        self._map.set_tile_server(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png", max_zoom=19
        )

        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(
            legend,
            text=(
                "Tip: kolečkem myši přibližuj/oddaluj.  Při větším zoomu se objeví "
                "i menší města."
            ),
            text_color=TEXT_FAINT,
            anchor="w",
            font=ctk.CTkFont(family=FONT, size=11),
        ).pack(side="left")

    def on_show(self) -> None:
        self._is_visible = True
        if self._map is None:
            return
        if self._last_center is None:
            self._map.set_position(49.7, 15.5)
            self._map.set_zoom(6)
        self._refresh_markers(force=True)
        self._schedule_poll()

    def hide(self) -> None:
        self._is_visible = False
        self._cancel_poll()
        super().hide()

    def _schedule_poll(self) -> None:
        self._cancel_poll()
        if not self._is_visible:
            return
        self._poll_after_id = self.after(_POLL_MS, self._poll)

    def _cancel_poll(self) -> None:
        if self._poll_after_id is not None:
            try:
                self.after_cancel(self._poll_after_id)
            except Exception:
                pass
            self._poll_after_id = None

    def _poll(self) -> None:
        if not self._is_visible or self._map is None:
            return
        zoom = int(self._map.zoom)
        center = self._map.get_position()
        if zoom != self._last_zoom or self._center_changed(center):
            self._last_zoom = zoom
            self._last_center = center
            self._refresh_markers()
        self._schedule_poll()

    def _center_changed(self, center: tuple[float, float]) -> bool:
        if self._last_center is None:
            return True
        prev_lat, prev_lon = self._last_center
        return abs(center[0] - prev_lat) > 0.05 or abs(center[1] - prev_lon) > 0.05

    def _force_refresh(self) -> None:
        self._weather_cache.clear()
        self._refresh_markers(force=True)

    def _refresh_markers(self, force: bool = False) -> None:
        if self._map is None:
            return

        for m in self._user_markers:
            try:
                m.delete()
            except Exception:
                pass
        self._user_markers.clear()
        for m in self._catalog_markers:
            try:
                m.delete()
            except Exception:
                pass
        self._catalog_markers.clear()

        zoom = int(self._map.zoom)
        self._zoom_info.configure(
            text=f"Úroveň přiblížení: {zoom}  ·  zobrazují se "
            + self._zoom_label(zoom)
        )

        bbox = self._viewport_bbox()
        threshold = CityCatalogService.min_population_for_zoom(zoom)

        user_keys: set[tuple[float, float]] = set()
        if self.app.weather_vm is not None:
            for city in self.app.weather_vm.list_cities():
                key = self._weather_key(city.latitude, city.longitude)
                user_keys.add(key)
                marker = self._map.set_marker(
                    city.latitude,
                    city.longitude,
                    text=self._marker_label(key, city.name),
                    marker_color_circle=_USER_MARKER_COLOR,
                    marker_color_outside=_USER_MARKER_RING,
                    text_color="#0E1115",
                    font=("Segoe UI Semibold", 11, "bold"),
                )
                self._user_markers.append(marker)
                self._ensure_weather(
                    city.latitude, city.longitude, city.name, marker
                )

        for cc in CityCatalogService.all():
            if cc.population < threshold:
                continue
            if bbox is not None and not self._in_bbox(cc, bbox):
                continue
            key = self._weather_key(cc.latitude, cc.longitude)
            if key in user_keys:
                continue
            marker = self._map.set_marker(
                cc.latitude,
                cc.longitude,
                text=self._marker_label(key, cc.name),
                marker_color_circle=_CATALOG_MARKER_COLOR,
                marker_color_outside=_CATALOG_MARKER_RING,
                text_color="#0E1115",
                font=("Segoe UI", 10, "bold"),
            )
            self._catalog_markers.append(marker)
            self._ensure_weather(cc.latitude, cc.longitude, cc.name, marker)

    def _zoom_label(self, zoom: int) -> str:
        threshold = CityCatalogService.min_population_for_zoom(zoom)
        if threshold == 0:
            return "všechna katalogová města"
        if threshold >= 1_000_000:
            return f"města nad {threshold // 1_000_000} mil. obyv."
        return f"města nad {threshold // 1_000} tis. obyv."

    def _viewport_bbox(self) -> tuple[float, float, float, float] | None:
        if self._map is None:
            return None
        try:
            ul = self._map.upper_left_tile_pos
            lr = self._map.lower_right_tile_pos
            zoom = int(self._map.zoom)
        except Exception:
            return None
        lat_ul, lon_ul = self._tile_to_latlon(ul[0], ul[1], zoom)
        lat_lr, lon_lr = self._tile_to_latlon(lr[0], lr[1], zoom)
        lat_min = min(lat_ul, lat_lr)
        lat_max = max(lat_ul, lat_lr)
        lon_min = min(lon_ul, lon_lr)
        lon_max = max(lon_ul, lon_lr)
        return (lat_min, lon_min, lat_max, lon_max)

    @staticmethod
    def _tile_to_latlon(x: float, y: float, z: int) -> tuple[float, float]:
        n = 2.0**z
        lon = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat = math.degrees(lat_rad)
        return lat, lon

    @staticmethod
    def _in_bbox(
        city: CatalogCity, bbox: tuple[float, float, float, float]
    ) -> bool:
        lat_min, lon_min, lat_max, lon_max = bbox
        return (
            lat_min <= city.latitude <= lat_max
            and lon_min <= city.longitude <= lon_max
        )

    @staticmethod
    def _weather_key(lat: float, lon: float) -> tuple[float, float]:
        return (round(lat, 3), round(lon, 3))

    def _marker_label(self, key: tuple[float, float], name: str) -> str:
        cached = self._weather_cache.get(key)
        if cached is None:
            return name
        emoji, temp, _ts = cached
        return f"{emoji} {name} {temp:.0f}°"

    def _ensure_weather(
        self, lat: float, lon: float, name: str, marker: Any
    ) -> None:
        key = self._weather_key(lat, lon)
        cached = self._weather_cache.get(key)
        if cached is not None and time.time() - cached[2] < _CACHE_TTL_S:
            return
        if key in self._weather_inflight:
            return
        self._weather_inflight.add(key)

        def worker() -> None:
            try:
                report = self._service.fetch_weather(lat, lon)
            except Exception:
                self.after(0, lambda k=key: self._weather_inflight.discard(k))
                return
            emoji = weather_emoji(report.current_code, report.current_is_day)
            temp = report.current_temperature

            def apply(k=key, m=marker, e=emoji, t=temp, n=name):
                self._weather_inflight.discard(k)
                self._weather_cache[k] = (e, t, time.time())
                try:
                    if m is not None:
                        m.set_text(f"{e} {n} {t:.0f}°")
                except Exception:
                    pass

            self.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()
