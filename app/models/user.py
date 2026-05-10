from __future__ import annotations

import re
from typing import Any

from app.models.base import Entity, ValidationError

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")


class User(Entity):
    """Uživatel aplikace."""

    def __init__(
        self,
        username: str,
        password_hash: str,
        salt: str,
        id: int | None = None,
    ) -> None:
        super().__init__(id=id)
        self.username = username
        self.password_hash = password_hash
        self.salt = salt

    def validate(self) -> None:
        if not isinstance(self.username, str) or not _USERNAME_RE.match(self.username):
            raise ValidationError(
                "Uživatelské jméno musí mít 3–32 znaků (a–z, A–Z, 0–9, _)."
            )
        if not self.password_hash or not self.salt:
            raise ValidationError("Chybí hash hesla nebo sůl.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "salt": self.salt,
        }
