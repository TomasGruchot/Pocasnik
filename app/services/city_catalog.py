from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CatalogCity:
    """Záznam z bundlovaného katalogu hlavních měst."""

    name: str
    country: str
    latitude: float
    longitude: float
    population: int

    @property
    def label(self) -> str:
        return f"{self.name}, {self.country}"


def _catalog_path() -> Path:
    """Cesta k cities.json – funguje i v PyInstaller bundlu."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS) / "app"  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "assets" / "cities.json"


class CityCatalogService:
    """Service nad bundlovaným seznamem hlavních měst (offline).

    Singleton-like (lazy-loaded). Slouží mapě na rozhodování,
    která města vykreslit v dané úrovni zoomu.
    """

    _cached: list[CatalogCity] | None = None

    @classmethod
    def all(cls) -> list[CatalogCity]:
        if cls._cached is None:
            try:
                with _catalog_path().open("r", encoding="utf-8") as f:
                    raw = json.load(f)
            except FileNotFoundError:
                cls._cached = []
                return cls._cached
            cls._cached = [
                CatalogCity(
                    name=str(item["name"]),
                    country=str(item["country"]),
                    latitude=float(item["lat"]),
                    longitude=float(item["lon"]),
                    population=int(item["population"]),
                )
                for item in raw
            ]
        return cls._cached

    @staticmethod
    def min_population_for_zoom(zoom: float) -> int:
        """Při menším zoomu (=oddálená mapa) zobrazuj jen velká města.

        Tabulka má reálnou logiku Apple-mapy: jak se přibližuješ,
        spadne práh a začnou se objevovat menší města.
        """
        if zoom < 4:
            return 8_000_000
        if zoom < 5:
            return 3_000_000
        if zoom < 6:
            return 1_500_000
        if zoom < 7:
            return 700_000
        if zoom < 8:
            return 300_000
        if zoom < 9:
            return 150_000
        if zoom < 10:
            return 80_000
        return 0

    @classmethod
    def for_view(
        cls, zoom: float, bbox: tuple[float, float, float, float] | None = None
    ) -> list[CatalogCity]:
        """Vrátí katalogová města vhodná pro daný zoom (a volitelně bbox).

        bbox = (lat_min, lon_min, lat_max, lon_max).
        """
        threshold = cls.min_population_for_zoom(zoom)
        out: list[CatalogCity] = []
        for c in cls.all():
            if c.population < threshold:
                continue
            if bbox is not None:
                lat_min, lon_min, lat_max, lon_max = bbox
                if not (lat_min <= c.latitude <= lat_max):
                    continue
                if not (lon_min <= c.longitude <= lon_max):
                    continue
            out.append(c)
        return out
