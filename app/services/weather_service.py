from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime


class WeatherError(Exception):
    """Chyba komunikace s Open-Meteo API."""


@dataclass(frozen=True)
class GeoCity:
    """Výsledek geokódování (Open-Meteo Geocoding API)."""

    name: str
    country: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class WeatherReport:
    """Kompletní zpráva: aktuální stav + hodinová + denní předpověď.

    Hodinová předpověď je oříznutá od aktuální hodiny (24 položek).
    """

    current_temperature: float
    current_apparent: float
    current_humidity: float
    current_wind: float
    current_code: int
    current_is_day: bool

    hourly_times: list[str]
    hourly_temps: list[float]
    hourly_codes: list[int]

    daily_dates: list[str]
    daily_max: list[float]
    daily_min: list[float]
    daily_codes: list[int]
    daily_precip_chance: list[int]
    daily_sunrise: list[str]
    daily_sunset: list[str]


class WeatherService:
    """Klient pro veřejné Open-Meteo API (žádný klíč není potřeba)."""

    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    _TIMEOUT = 8

    @classmethod
    def _get_json(cls, url: str, params: dict) -> dict:
        query = urllib.parse.urlencode(params)
        full = f"{url}?{query}"
        req = urllib.request.Request(full, headers={"User-Agent": "Pocasnik/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=cls._TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise WeatherError(f"Síťová chyba: {e}") from e
        except json.JSONDecodeError as e:
            raise WeatherError("Nepodařilo se parsovat odpověď API.") from e

    def search_city(self, query: str, limit: int = 8) -> list[GeoCity]:
        if not query or not query.strip():
            return []
        data = self._get_json(
            self.GEO_URL,
            {"name": query.strip(), "count": limit, "language": "cs", "format": "json"},
        )
        out: list[GeoCity] = []
        for item in data.get("results") or []:
            try:
                out.append(
                    GeoCity(
                        name=str(item["name"]),
                        country=str(item.get("country", "")),
                        latitude=float(item["latitude"]),
                        longitude=float(item["longitude"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return out

    def fetch_weather(self, latitude: float, longitude: float) -> WeatherReport:
        data = self._get_json(
            self.FORECAST_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,apparent_temperature,relative_humidity_2m,"
                    "wind_speed_10m,weather_code,is_day"
                ),
                "hourly": "temperature_2m,weather_code",
                "daily": (
                    "temperature_2m_max,temperature_2m_min,weather_code,"
                    "precipitation_probability_max,sunrise,sunset"
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
        )
        current = data.get("current") or {}
        hourly = data.get("hourly") or {}
        daily = data.get("daily") or {}

        try:
            hourly_times = list(hourly.get("time", []))
            hourly_temps = [float(x) for x in hourly.get("temperature_2m", [])]
            hourly_codes = [int(x) for x in hourly.get("weather_code", [])]

            now_iso = current.get("time")
            start_idx = 0
            if now_iso and hourly_times:
                try:
                    now_dt = datetime.fromisoformat(str(now_iso))
                    for i, t in enumerate(hourly_times):
                        if datetime.fromisoformat(t) >= now_dt:
                            start_idx = i
                            break
                except ValueError:
                    start_idx = 0

            slice_end = start_idx + 24
            hourly_times = hourly_times[start_idx:slice_end]
            hourly_temps = hourly_temps[start_idx:slice_end]
            hourly_codes = hourly_codes[start_idx:slice_end]

            return WeatherReport(
                current_temperature=float(current.get("temperature_2m", 0.0)),
                current_apparent=float(current.get("apparent_temperature", 0.0)),
                current_humidity=float(current.get("relative_humidity_2m", 0.0)),
                current_wind=float(current.get("wind_speed_10m", 0.0)),
                current_code=int(current.get("weather_code", 0)),
                current_is_day=bool(int(current.get("is_day", 1))),
                hourly_times=hourly_times,
                hourly_temps=hourly_temps,
                hourly_codes=hourly_codes,
                daily_dates=list(daily.get("time", [])),
                daily_max=[float(x) for x in daily.get("temperature_2m_max", [])],
                daily_min=[float(x) for x in daily.get("temperature_2m_min", [])],
                daily_codes=[int(x) for x in daily.get("weather_code", [])],
                daily_precip_chance=[
                    int(x or 0) for x in daily.get("precipitation_probability_max", [])
                ],
                daily_sunrise=list(daily.get("sunrise", [])),
                daily_sunset=list(daily.get("sunset", [])),
            )
        except (TypeError, ValueError) as e:
            raise WeatherError("Neočekávaný formát odpovědi API.") from e


WEATHER_CODE_LABELS: dict[int, str] = {
    0: "Jasno",
    1: "Skoro jasno",
    2: "Polojasno",
    3: "Zataženo",
    45: "Mlha",
    48: "Námraza",
    51: "Slabé mrholení",
    53: "Mrholení",
    55: "Silné mrholení",
    61: "Slabý déšť",
    63: "Déšť",
    65: "Silný déšť",
    71: "Slabé sněžení",
    73: "Sněžení",
    75: "Silné sněžení",
    77: "Sněhová zrna",
    80: "Přeháňky",
    81: "Silné přeháňky",
    82: "Velmi silné přeháňky",
    85: "Sněhové přeháňky",
    86: "Silné sněhové přeháňky",
    95: "Bouřka",
    96: "Bouřka s krupobitím",
    99: "Silná bouřka s krupobitím",
}


_WEATHER_EMOJI_DAY: dict[int, str] = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    71: "🌨️",
    73: "🌨️",
    75: "❄️",
    77: "❄️",
    80: "🌦️",
    81: "🌧️",
    82: "⛈️",
    85: "🌨️",
    86: "❄️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}

_WEATHER_EMOJI_NIGHT: dict[int, str] = {
    0: "🌙",
    1: "🌙",
    2: "☁️",
    3: "☁️",
}


def describe_weather_code(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, "Neznámé")


def weather_emoji(code: int, is_day: bool = True) -> str:
    """Vrátí emoji odpovídající weather code (rozlišuje den/noc u jasné oblohy)."""
    if not is_day and code in _WEATHER_EMOJI_NIGHT:
        return _WEATHER_EMOJI_NIGHT[code]
    return _WEATHER_EMOJI_DAY.get(code, "❓")


_WEEKDAYS_CS = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]


def format_weekday(iso_date: str) -> str:
    """ISO datum (YYYY-MM-DD) → 'Po', 'Út', …"""
    try:
        dt = datetime.fromisoformat(iso_date)
        return _WEEKDAYS_CS[dt.weekday()]
    except (ValueError, IndexError):
        return iso_date


def format_hour(iso_datetime: str) -> str:
    """ISO datetime → '14h'."""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return f"{dt.hour}h"
    except ValueError:
        return iso_datetime
