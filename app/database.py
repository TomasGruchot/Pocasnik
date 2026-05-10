from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path


def _default_db_path() -> Path:
    """Cesta k DB. U .exe (PyInstaller) ukládáme vedle exáče,
    při běhu ze zdrojáků do kořene repa."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "pocasnik.db"


class Database:
    """Jednoduchý wrapper nad sqlite3 (singleton-like přes `get_instance`)."""

    _instance: "Database | None" = None

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else _default_db_path()
        self._conn: sqlite3.Connection | None = None

    @classmethod
    def get_instance(cls) -> "Database":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.connect()
            cls._instance.init_schema()
        return cls._instance

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    @property
    def conn(self) -> sqlite3.Connection:
        return self.connect()

    def init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                salt          TEXT    NOT NULL,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS cities (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                name       TEXT    NOT NULL,
                country    TEXT    NOT NULL,
                latitude   REAL    NOT NULL,
                longitude  REAL    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
