from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.database import Database
from app.models.base import Entity

T = TypeVar("T", bound=Entity)


class Repository(ABC, Generic[T]):
    """Abstraktní repozitář – generická šablona CRUD operací nad SQLite.

    Polymorfismus: konkrétní repozitáře (`UserRepository`, `CityRepository`)
    přepisují `_table_name`, `_columns` a `_row_to_entity()`.
    """

    def __init__(self, db: Database | None = None) -> None:
        self._db = db or Database.get_instance()

    @property
    def conn(self) -> sqlite3.Connection:
        return self._db.conn

    @property
    @abstractmethod
    def _table_name(self) -> str: ...

    @property
    @abstractmethod
    def _columns(self) -> tuple[str, ...]: ...

    @abstractmethod
    def _row_to_entity(self, row: sqlite3.Row) -> T: ...

    def get(self, id_: int) -> T | None:
        cur = self.conn.execute(
            f"SELECT * FROM {self._table_name} WHERE id = ?", (id_,)
        )
        row = cur.fetchone()
        return self._row_to_entity(row) if row else None

    def all(self) -> list[T]:
        cur = self.conn.execute(f"SELECT * FROM {self._table_name} ORDER BY id ASC")
        return [self._row_to_entity(r) for r in cur.fetchall()]

    def save(self, entity: T) -> T:
        """Validuje entitu a uloží/aktualizuje. Vrací entitu s případně doplněným id."""
        entity.validate()
        data = entity.to_dict()
        cols = self._columns
        if entity.id is None:
            placeholders = ", ".join(["?"] * len(cols))
            values = tuple(data[c] for c in cols)
            cur = self.conn.execute(
                f"INSERT INTO {self._table_name} ({', '.join(cols)}) VALUES ({placeholders})",
                values,
            )
            entity.id = cur.lastrowid
        else:
            assignments = ", ".join(f"{c} = ?" for c in cols)
            values = tuple(data[c] for c in cols) + (entity.id,)
            self.conn.execute(
                f"UPDATE {self._table_name} SET {assignments} WHERE id = ?", values
            )
        self.conn.commit()
        return entity

    def delete(self, id_: int) -> None:
        self.conn.execute(f"DELETE FROM {self._table_name} WHERE id = ?", (id_,))
        self.conn.commit()
