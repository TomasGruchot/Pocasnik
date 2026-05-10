from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


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
    """Aktuální počasí + 7denní předpověď."""

    current_temperature: float
    current_wind: float
    current_code: int
    daily_dates: list[str]
    daily_max: list[float]
    daily_min: list[float]
    daily_codes: list[int]


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
                "current_weather": "true",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                "timezone": "auto",
                "forecast_days": 7,
            },
        )
        cw = data.get("current_weather") or {}
        daily = data.get("daily") or {}
        try:
            return WeatherReport(
                current_temperature=float(cw.get("temperature", 0.0)),
                current_wind=float(cw.get("windspeed", 0.0)),
                current_code=int(cw.get("weathercode", 0)),
                daily_dates=list(daily.get("time", [])),
                daily_max=[float(x) for x in daily.get("temperature_2m_max", [])],
                daily_min=[float(x) for x in daily.get("temperature_2m_min", [])],
                daily_codes=[int(x) for x in daily.get("weather_code", [])],
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


def describe_weather_code(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, "Neznámé")
