from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from clientradar.models.lead import Lead, LeadStatus


class DatabaseManager:
    def __init__(self, db_path: str = "clientradar.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def initialize(self) -> None:
        conn = self._connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                address TEXT DEFAULT '',
                city TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                website TEXT DEFAULT '',
                email TEXT DEFAULT '',
                rating REAL DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                google_maps_url TEXT DEFAULT '',
                scraped_at TEXT NOT NULL,
                status TEXT DEFAULT 'Nový',
                notes TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_name_city
            ON leads (name, city)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_status
            ON leads (status)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_category
            ON leads (category)
        """)
        conn.commit()

    def save_lead(self, lead: Lead) -> bool:
        conn = self._connect()
        existing = conn.execute(
            "SELECT id FROM leads WHERE name = ? AND city = ?",
            (lead.name, lead.city),
        ).fetchone()
        if existing:
            return False
        conn.execute(
            """INSERT INTO leads
               (name, category, address, city, phone, website, email,
                rating, review_count, google_maps_url, scraped_at, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lead.name, lead.category, lead.address, lead.city,
                lead.phone, lead.website, lead.email, lead.rating,
                lead.review_count, lead.google_maps_url,
                lead.scraped_at.isoformat() if lead.scraped_at else datetime.now().isoformat(),
                lead.status.value, lead.notes,
            ),
        )
        conn.commit()
        lead.id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return True

    def get_all_leads(self) -> list[Lead]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
        return [self._row_to_lead(r) for r in rows]

    def get_leads_by_status(self, status: LeadStatus) -> list[Lead]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY id DESC",
            (status.value,),
        ).fetchall()
        return [self._row_to_lead(r) for r in rows]

    def update_lead(self, lead: Lead) -> None:
        conn = self._connect()
        conn.execute(
            """UPDATE leads SET
               name=?, category=?, address=?, city=?, phone=?, website=?,
               email=?, rating=?, review_count=?, google_maps_url=?,
               status=?, notes=?
               WHERE id=?""",
            (
                lead.name, lead.category, lead.address, lead.city,
                lead.phone, lead.website, lead.email, lead.rating,
                lead.review_count, lead.google_maps_url,
                lead.status.value, lead.notes, lead.id,
            ),
        )
        conn.commit()

    def delete_lead(self, lead_id: int) -> None:
        conn = self._connect()
        conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()

    def search_leads(self, query: str) -> list[Lead]:
        conn = self._connect()
        pattern = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM leads
               WHERE name LIKE ? OR city LIKE ? OR category LIKE ?
                     OR phone LIKE ? OR email LIKE ?
               ORDER BY id DESC""",
            (pattern, pattern, pattern, pattern, pattern),
        ).fetchall()
        return [self._row_to_lead(r) for r in rows]

    def get_stats(self) -> dict:
        conn = self._connect()
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        stats: dict = {"total": total}
        for s in LeadStatus:
            count = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE status = ?", (s.value,)
            ).fetchone()[0]
            stats[s.name.lower()] = count
        return stats

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _row_to_lead(self, row: sqlite3.Row) -> Lead:
        scraped_raw = row["scraped_at"]
        try:
            scraped_dt = datetime.fromisoformat(scraped_raw)
        except (ValueError, TypeError):
            scraped_dt = datetime.now()
        return Lead(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            address=row["address"],
            city=row["city"],
            phone=row["phone"],
            website=row["website"],
            email=row["email"],
            rating=row["rating"],
            review_count=row["review_count"],
            google_maps_url=row["google_maps_url"],
            scraped_at=scraped_dt,
            status=LeadStatus.from_value(row["status"]),
            notes=row["notes"],
        )
