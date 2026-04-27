from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from domain.repositories.interfaces import PomodoroSessionRepository, TaskRepository


@dataclass(slots=True)
class DashboardStats:
    completed_today: int
    completed_this_week: int
    focused_minutes_today: int
    completion_ratio_today: float
    completion_ratio_week: float
    focused_minutes_this_week: int


class StatsService:
    def __init__(
        self,
        task_repository: TaskRepository,
        pomodoro_repository: PomodoroSessionRepository,
    ) -> None:
        self._task_repository = task_repository
        self._pomodoro_repository = pomodoro_repository

    def get_dashboard_stats(self, now: datetime | None = None) -> DashboardStats:
        timestamp = now or datetime.now(UTC)
        day_start = datetime(timestamp.year, timestamp.month, timestamp.day)
        week_start = day_start - timedelta(days=timestamp.weekday())

        done_today = len(self._task_repository.list_done_between(day_start, timestamp))
        done_week = len(self._task_repository.list_done_between(week_start, timestamp))
        all_today = len(self._task_repository.list_all())
        completion_ratio_today = (done_today / all_today) if all_today else 0.0
        completion_ratio_week = (done_week / all_today) if all_today else 0.0
        today_sessions = self._pomodoro_repository.list_between(day_start, timestamp)
        week_sessions = self._pomodoro_repository.list_between(week_start, timestamp)
        focused_minutes = sum(item.duration_sec for item in today_sessions if item.session_type == "work") // 60
        focused_minutes_week = sum(item.duration_sec for item in week_sessions if item.session_type == "work") // 60
        return DashboardStats(
            completed_today=done_today,
            completed_this_week=done_week,
            focused_minutes_today=focused_minutes,
            completion_ratio_today=completion_ratio_today,
            completion_ratio_week=completion_ratio_week,
            focused_minutes_this_week=focused_minutes_week,
        )
