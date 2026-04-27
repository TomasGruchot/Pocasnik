from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.value_objects.enums import Priority, TaskStatus


@dataclass(slots=True)
class Project:
    id: int | None
    name: str
    color: str = "#7C3AED"


@dataclass(slots=True)
class Tag:
    id: int | None
    name: str


@dataclass(slots=True)
class Task:
    id: int | None
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_at: Optional[datetime] = None
    project_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def mark_done(self) -> None:
        self.status = TaskStatus.DONE


@dataclass(slots=True)
class PomodoroSession:
    id: int | None
    task_id: int | None
    started_at: datetime
    ended_at: datetime
    duration_sec: int
    session_type: str
