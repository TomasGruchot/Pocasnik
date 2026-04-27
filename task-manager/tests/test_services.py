from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.services.pomodoro_service import PomodoroService
from application.services.stats_service import StatsService
from application.services.task_service import TaskService
from domain.models.entities import PomodoroSession
from domain.value_objects.enums import Priority, TaskStatus, TimerState
from infrastructure.db.sqlite_connection import SQLiteDatabase
from infrastructure.repositories.sqlite_repositories import (
    SQLitePomodoroSessionRepository,
    SQLiteProjectRepository,
    SQLiteTagRepository,
    SQLiteTaskRepository,
)


def _build_services(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "test.db")
    db.initialize_schema()
    task_repo = SQLiteTaskRepository(db)
    project_repo = SQLiteProjectRepository(db)
    tag_repo = SQLiteTagRepository(db)
    pom_repo = SQLitePomodoroSessionRepository(db)
    return (
        TaskService(task_repo, project_repo, tag_repo),
        PomodoroService(pom_repo, work_minutes=1, short_break_minutes=1),
        StatsService(task_repo, pom_repo),
        pom_repo,
    )


def test_task_lifecycle(tmp_path: Path) -> None:
    task_service, _, _, _ = _build_services(tmp_path)
    task = task_service.create_task("Napsat OOP modul", priority=Priority.HIGH)
    assert task.id is not None
    updated = task_service.update_status(task.id, TaskStatus.DONE)
    assert updated.status == TaskStatus.DONE
    listed = task_service.list_tasks(status=TaskStatus.DONE)
    assert len(listed) == 1


def test_stats_with_sessions(tmp_path: Path) -> None:
    task_service, _, stats_service, pom_repo = _build_services(tmp_path)
    task = task_service.create_task("Pocitat statistiky")
    task_service.update_status(task.id, TaskStatus.DONE)  # type: ignore[arg-type]
    now = datetime.now(UTC)
    pom_repo.create(
        PomodoroSession(
            id=None,
            task_id=task.id,
            started_at=now - timedelta(minutes=26),
            ended_at=now - timedelta(minutes=1),
            duration_sec=25 * 60,
            session_type="work",
        )
    )
    stats = stats_service.get_dashboard_stats(now=now)
    assert stats.completed_today >= 1
    assert stats.focused_minutes_today >= 25


def test_pomodoro_reset_state(tmp_path: Path) -> None:
    _, pomodoro_service, _, _ = _build_services(tmp_path)
    pomodoro_service.start()
    snapshot = pomodoro_service.pause()
    assert snapshot.state == TimerState.PAUSED
    reset = pomodoro_service.reset()
    assert reset.state == TimerState.IDLE
