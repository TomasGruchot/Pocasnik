from .database import DatabaseManager
from .config_manager import ConfigManager
from .exporter import ExcelExporter
from .parser import DataParser

__all__ = [
    "DatabaseManager",
    "ConfigManager",
    "ExcelExporter",
    "DataParser",
    "GoogleMapsScraper",
]


def __getattr__(name: str):
    if name == "GoogleMapsScraper":
        from .scraper import GoogleMapsScraper
        return GoogleMapsScraper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
