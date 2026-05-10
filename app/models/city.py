from __future__ import annotations

from typing import Any

from app.models.base import Entity, ValidationError


class City(Entity):
    """Oblíbené město uživatele (souřadnice si pamatujeme z geokódování)."""

    def __init__(
        self,
        user_id: int,
        name: str,
        country: str,
        latitude: float,
        longitude: float,
        id: int | None = None,
    ) -> None:
        super().__init__(id=id)
        self.user_id = user_id
        self.name = name
        self.country = country
        self.latitude = latitude
        self.longitude = longitude

    def validate(self) -> None:
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValidationError("City musí být přiřazeno k existujícímu uživateli.")
        if not self.name or len(self.name) > 80:
            raise ValidationError("Název města musí mít 1–80 znaků.")
        if not self.country or len(self.country) > 80:
            raise ValidationError("Název země musí mít 1–80 znaků.")
        if not (-90.0 <= float(self.latitude) <= 90.0):
            raise ValidationError("Zeměpisná šířka mimo rozsah -90 až 90.")
        if not (-180.0 <= float(self.longitude) <= 180.0):
            raise ValidationError("Zeměpisná délka mimo rozsah -180 až 180.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    @property
    def label(self) -> str:
        return f"{self.name}, {self.country}"
