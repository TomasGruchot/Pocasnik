from __future__ import annotations

import sqlite3

from app.models.user import User
from app.repositories.base import Repository


class UserRepository(Repository[User]):
    @property
    def _table_name(self) -> str:
        return "users"

    @property
    def _columns(self) -> tuple[str, ...]:
        return ("username", "password_hash", "salt")

    def _row_to_entity(self, row: sqlite3.Row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
        )

    def find_by_username(self, username: str) -> User | None:
        cur = self.conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        row = cur.fetchone()
        return self._row_to_entity(row) if row else None
