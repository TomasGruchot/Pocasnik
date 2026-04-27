from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    db_path: Path = Path("task-manager/taskmanager.db")
    work_minutes: int = 25
    short_break_minutes: int = 5
