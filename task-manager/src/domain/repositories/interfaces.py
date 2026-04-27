from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from domain.models.entities import PomodoroSession, Project, Tag, Task


class TaskRepository(ABC):
    @abstractmethod
    def create(self, task: Task, tag_ids: list[int] | None = None) -> Task: ...

    @abstractmethod
    def update(self, task: Task, tag_ids: list[int] | None = None) -> Task: ...

    @abstractmethod
    def delete(self, task_id: int) -> None: ...

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None: ...

    @abstractmethod
    def list_all(
        self,
        status: str | None = None,
        project_id: int | None = None,
        search: str | None = None,
        priority: str | None = None,
        sort_by: str = "created_desc",
    ) -> list[Task]: ...

    @abstractmethod
    def list_done_between(self, start: datetime, end: datetime) -> list[Task]: ...


class PomodoroSessionRepository(ABC):
    @abstractmethod
    def create(self, session: PomodoroSession) -> PomodoroSession: ...

    @abstractmethod
    def list_between(self, start: datetime, end: datetime) -> list[PomodoroSession]: ...


class ProjectRepository(ABC):
    @abstractmethod
    def create(self, project: Project) -> Project: ...

    @abstractmethod
    def list_all(self) -> list[Project]: ...


class TagRepository(ABC):
    @abstractmethod
    def create(self, tag: Tag) -> Tag: ...

    @abstractmethod
    def list_all(self) -> list[Tag]: ...
