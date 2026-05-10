from __future__ import annotations

import sqlite3

from app.models.city import City
from app.repositories.base import Repository


class CityRepository(Repository[City]):
    @property
    def _table_name(self) -> str:
        return "cities"

    @property
    def _columns(self) -> tuple[str, ...]:
        return ("user_id", "name", "country", "latitude", "longitude")

    def _row_to_entity(self, row: sqlite3.Row) -> City:
        return City(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            country=row["country"],
            latitude=row["latitude"],
            longitude=row["longitude"],
        )

    def list_for_user(self, user_id: int) -> list[City]:
        cur = self.conn.execute(
            "SELECT * FROM cities WHERE user_id = ? ORDER BY name ASC", (user_id,)
        )
        return [self._row_to_entity(r) for r in cur.fetchall()]

    def exists_for_user(self, user_id: int, lat: float, lon: float) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM cities WHERE user_id = ? AND ABS(latitude-?) < 0.001 AND ABS(longitude-?) < 0.001",
            (user_id, lat, lon),
        )
        return cur.fetchone() is not None
