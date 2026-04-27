from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime

from domain.models.entities import PomodoroSession
from domain.repositories.interfaces import PomodoroSessionRepository
from domain.value_objects.enums import TimerState


@dataclass(slots=True)
class TimerSnapshot:
    state: TimerState
    remaining_seconds: int
    active_task_id: int | None
    cycle_type: str


class PomodoroService:
    def __init__(
        self,
        repository: PomodoroSessionRepository,
        work_minutes: int = 25,
        short_break_minutes: int = 5,
    ) -> None:
        self._repository = repository
        self._work_seconds = work_minutes * 60
        self._break_seconds = short_break_minutes * 60
        self._state = TimerState.IDLE
        self._cycle_type = "work"
        self._active_task_id: int | None = None
        self._end_monotonic: float | None = None
        self._paused_remaining = self._work_seconds
        self._started_at: datetime | None = None

    @property
    def work_minutes(self) -> int:
        return self._work_seconds // 60

    @property
    def short_break_minutes(self) -> int:
        return self._break_seconds // 60

    def update_settings(self, work_minutes: int, short_break_minutes: int) -> TimerSnapshot:
        if work_minutes < 1 or short_break_minutes < 1:
            raise ValueError("Timer values must be at least 1 minute.")
        self._work_seconds = work_minutes * 60
        self._break_seconds = short_break_minutes * 60
        if self._state in (TimerState.IDLE, TimerState.PAUSED):
            self._paused_remaining = self._work_seconds if self._cycle_type == "work" else self._break_seconds
            self._end_monotonic = None
        return self.snapshot()

    def start(self, task_id: int | None = None) -> TimerSnapshot:
        self._active_task_id = task_id
        if self._state == TimerState.PAUSED:
            duration = self._paused_remaining
        else:
            duration = self._work_seconds if self._cycle_type == "work" else self._break_seconds
            self._started_at = datetime.now(UTC)
        self._state = TimerState.RUNNING if self._cycle_type == "work" else TimerState.BREAK
        self._end_monotonic = time.monotonic() + duration
        return self.snapshot()

    def pause(self) -> TimerSnapshot:
        if self._end_monotonic is None:
            return self.snapshot()
        self._paused_remaining = max(0, int(self._end_monotonic - time.monotonic()))
        self._end_monotonic = None
        self._state = TimerState.PAUSED
        return self.snapshot()

    def reset(self) -> TimerSnapshot:
        self._state = TimerState.IDLE
        self._cycle_type = "work"
        self._active_task_id = None
        self._end_monotonic = None
        self._paused_remaining = self._work_seconds
        self._started_at = None
        return self.snapshot()

    def tick(self) -> TimerSnapshot:
        if self._end_monotonic is None:
            return self.snapshot()
        if time.monotonic() >= self._end_monotonic:
            self._complete_cycle()
        return self.snapshot()

    def snapshot(self) -> TimerSnapshot:
        if self._end_monotonic is not None:
            remaining = max(0, int(self._end_monotonic - time.monotonic()))
        else:
            remaining = self._paused_remaining
        return TimerSnapshot(
            state=self._state,
            remaining_seconds=remaining,
            active_task_id=self._active_task_id,
            cycle_type=self._cycle_type,
        )

    def _complete_cycle(self) -> None:
        if self._started_at is not None and self._cycle_type == "work":
            ended_at = datetime.now(UTC)
            session = PomodoroSession(
                id=None,
                task_id=self._active_task_id,
                started_at=self._started_at,
                ended_at=ended_at,
                duration_sec=self._work_seconds,
                session_type="work",
            )
            self._repository.create(session)
        self._cycle_type = "break" if self._cycle_type == "work" else "work"
        self._state = TimerState.IDLE
        self._end_monotonic = None
        self._paused_remaining = self._work_seconds if self._cycle_type == "work" else self._break_seconds
        self._started_at = None
