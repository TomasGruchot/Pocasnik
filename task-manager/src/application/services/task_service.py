from __future__ import annotations

from datetime import datetime

from domain.models.entities import Project, Tag, Task
from domain.repositories.interfaces import ProjectRepository, TagRepository, TaskRepository
from domain.value_objects.enums import Priority, TaskStatus


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        project_repository: ProjectRepository,
        tag_repository: TagRepository,
    ) -> None:
        self._task_repository = task_repository
        self._project_repository = project_repository
        self._tag_repository = tag_repository

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        due_at: datetime | None = None,
        project_id: int | None = None,
    ) -> Task:
        if not title.strip():
            raise ValueError("Task title cannot be empty.")
        task = Task(
            id=None,
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            status=TaskStatus.TODO,
            due_at=due_at,
            project_id=project_id,
        )
        return self._task_repository.create(task)

    def update_task(
        self,
        task_id: int,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        due_at: datetime | None = None,
        project_id: int | None = None,
        tag_ids: list[int] | None = None,
    ) -> Task:
        task = self._task_repository.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        if not title.strip():
            raise ValueError("Task title cannot be empty.")
        task.title = title.strip()
        task.description = description.strip()
        task.priority = priority
        task.due_at = due_at
        task.project_id = project_id
        return self._task_repository.update(task, tag_ids=tag_ids)

    def update_status(self, task_id: int, status: TaskStatus) -> Task:
        task = self._task_repository.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        task.status = status
        return self._task_repository.update(task)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        project_id: int | None = None,
        search: str | None = None,
        priority: Priority | None = None,
        sort_by: str = "created_desc",
    ) -> list[Task]:
        return self._task_repository.list_all(
            status=status.value if status else None,
            project_id=project_id,
            search=search,
            priority=priority.value if priority else None,
            sort_by=sort_by,
        )

    def delete_task(self, task_id: int) -> None:
        self._task_repository.delete(task_id)

    def set_many_status(self, task_ids: list[int], status: TaskStatus) -> None:
        for task_id in task_ids:
            self.update_status(task_id, status)

    def delete_many(self, task_ids: list[int]) -> None:
        for task_id in task_ids:
            self.delete_task(task_id)

    def create_project(self, name: str, color: str = "#7C3AED") -> Project:
        if not name.strip():
            raise ValueError("Project name cannot be empty.")
        return self._project_repository.create(Project(id=None, name=name.strip(), color=color))

    def list_projects(self) -> list[Project]:
        return self._project_repository.list_all()

    def create_tag(self, name: str) -> Tag:
        if not name.strip():
            raise ValueError("Tag name cannot be empty.")
        return self._tag_repository.create(Tag(id=None, name=name.strip()))

    def list_tags(self) -> list[Tag]:
        return self._tag_repository.list_all()
