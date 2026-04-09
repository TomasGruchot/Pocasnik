from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class LeadStatus(Enum):
    NEW = "Nový"
    CONTACTED = "Kontaktován"
    INTERESTED = "Má zájem"
    REJECTED = "Nezájem"
    IGNORED = "Ignorován"

    @classmethod
    def from_value(cls, value: str) -> LeadStatus:
        for member in cls:
            if member.value == value:
                return member
        return cls.NEW

    @classmethod
    def all_values(cls) -> list[str]:
        return [member.value for member in cls]


@dataclass
class Lead:
    id: int | None
    name: str
    category: str
    address: str
    city: str
    phone: str
    website: str
    email: str
    rating: float
    review_count: int
    google_maps_url: str
    scraped_at: datetime
    status: LeadStatus = field(default=LeadStatus.NEW)
    notes: str = ""

    def rating_stars(self) -> str:
        full = int(self.rating)
        half = 1 if (self.rating - full) >= 0.3 else 0
        empty = 5 - full - half
        return "★" * full + ("½" if half else "") + "☆" * empty + f" {self.rating}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "address": self.address,
            "city": self.city,
            "phone": self.phone,
            "website": self.website,
            "email": self.email,
            "rating": self.rating,
            "review_count": self.review_count,
            "google_maps_url": self.google_maps_url,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else "",
            "status": self.status.value,
            "notes": self.notes,
        }
