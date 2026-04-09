from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchConfig:
    keyword: str
    location: str
    max_results: int
    headless: bool
    fetch_emails: bool

    def search_query(self) -> str:
        return f"{self.keyword} {self.location}".strip()

    def validate(self) -> str | None:
        if not self.keyword.strip():
            return "Klíčové slovo nesmí být prázdné."
        if not self.location.strip():
            return "Lokalita nesmí být prázdná."
        if self.max_results < 1:
            return "Minimálně 1 výsledek."
        return None
