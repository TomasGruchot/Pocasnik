from __future__ import annotations

import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self, config_path: str = "config.json") -> None:
        self._path = Path(config_path)
        self._data: dict = {}
        self.load()

    def load(self) -> dict:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    self._data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}
        return self._data

    def save(self, data: dict | None = None) -> None:
        if data is not None:
            self._data = data
        try:
            os.makedirs(self._path.parent, exist_ok=True) if str(self._path.parent) != "." else None
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()
