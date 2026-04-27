from __future__ import annotations

import tkinter as tk

from application.services.pomodoro_service import PomodoroService
from application.services.stats_service import StatsService
from application.services.task_service import TaskService
from core.config import AppConfig
from infrastructure.db.sqlite_connection import SQLiteDatabase
from infrastructure.repositories.sqlite_repositories import (
    SQLitePomodoroSessionRepository,
    SQLiteProjectRepository,
    SQLiteTagRepository,
    SQLiteTaskRepository,
)
from presentation.controllers.main_controller import MainController


class TaskManagerApp:
    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()
        self._db = SQLiteDatabase(self._config.db_path)
        self._db.initialize_schema()

        task_repo = SQLiteTaskRepository(self._db)
        project_repo = SQLiteProjectRepository(self._db)
        tag_repo = SQLiteTagRepository(self._db)
        pomodoro_repo = SQLitePomodoroSessionRepository(self._db)

        self._task_service = TaskService(task_repo, project_repo, tag_repo)
        self._pomodoro_service = PomodoroService(
            pomodoro_repo,
            work_minutes=self._config.work_minutes,
            short_break_minutes=self._config.short_break_minutes,
        )
        self._stats_service = StatsService(task_repo, pomodoro_repo)

    def run(self) -> None:
        root = tk.Tk()
        MainController(
            root=root,
            task_service=self._task_service,
            pomodoro_service=self._pomodoro_service,
            stats_service=self._stats_service,
        )
        root.mainloop()


def main() -> None:
    TaskManagerApp().run()


if __name__ == "__main__":
    main()
