from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ValidationError(Exception):
    """Vyhazuje se z `Entity.validate()`, když data neprošla kontrolou."""


class Entity(ABC):
    """Abstraktní základ všech doménových entit.

    Definuje rozhraní `validate()` a `to_dict()`. Konkrétní entity
    (User, City) ho přepisují – ukázka polymorfismu.
    """

    id: int | None

    def __init__(self, id: int | None = None) -> None:
        self.id = id

    @abstractmethod
    def validate(self) -> None: ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...

    def __repr__(self) -> str:
        return f"<{type(self).__name__} id={self.id}>"
