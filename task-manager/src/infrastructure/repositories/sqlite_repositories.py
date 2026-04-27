from __future__ import annotations

from datetime import UTC, datetime

from domain.models.entities import PomodoroSession, Project, Tag, Task
from domain.repositories.interfaces import (
    PomodoroSessionRepository,
    ProjectRepository,
    TagRepository,
    TaskRepository,
)
from domain.value_objects.enums import Priority, TaskStatus
from infrastructure.db.sqlite_connection import SQLiteDatabase


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def create(self, task: Task, tag_ids: list[int] | None = None) -> Task:
        now = datetime.now(UTC).isoformat()
        due_at = task.due_at.isoformat() if task.due_at else None
        with self._db.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks(title, description, priority, status, due_at, project_id, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.title,
                    task.description,
                    task.priority.value,
                    task.status.value,
                    due_at,
                    task.project_id,
                    now,
                    now,
                ),
            )
            task_id = int(cursor.lastrowid)
            self._sync_tags(conn, task_id, tag_ids or [])
        return self.get_by_id(task_id)  # type: ignore[return-value]

    def update(self, task: Task, tag_ids: list[int] | None = None) -> Task:
        if task.id is None:
            raise ValueError("Task must have an id for update.")
        due_at = task.due_at.isoformat() if task.due_at else None
        with self._db.connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, priority = ?, status = ?, due_at = ?, project_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    task.title,
                    task.description,
                    task.priority.value,
                    task.status.value,
                    due_at,
                    task.project_id,
                    datetime.now(UTC).isoformat(),
                    task.id,
                ),
            )
            if tag_ids is not None:
                self._sync_tags(conn, task.id, tag_ids)
        return self.get_by_id(task.id)  # type: ignore[return-value]

    def delete(self, task_id: int) -> None:
        with self._db.connect() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_by_id(self, task_id: int) -> Task | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def list_all(
        self,
        status: str | None = None,
        project_id: int | None = None,
        search: str | None = None,
        priority: str | None = None,
        sort_by: str = "created_desc",
    ) -> list[Task]:
        sql = "SELECT * FROM tasks WHERE 1 = 1"
        params: list[object] = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if project_id:
            sql += " AND project_id = ?"
            params.append(project_id)
        if search:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            token = f"%{search}%"
            params.extend([token, token])
        if priority:
            sql += " AND priority = ?"
            params.append(priority)
        order_map = {
            "created_desc": "created_at DESC",
            "created_asc": "created_at ASC",
            "due_asc": "COALESCE(due_at, '9999-12-31T23:59:59') ASC",
            "priority_desc": "CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END ASC",
        }
        sql += f" ORDER BY {order_map.get(sort_by, order_map['created_desc'])}"
        with self._db.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_done_between(self, start: datetime, end: datetime) -> list[Task]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? AND updated_at BETWEEN ? AND ?",
                (TaskStatus.DONE.value, start.isoformat(), end.isoformat()),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def _sync_tags(self, conn, task_id: int, tag_ids: list[int]) -> None:
        conn.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
        for tag_id in tag_ids:
            conn.execute(
                "INSERT OR IGNORE INTO task_tags(task_id, tag_id) VALUES(?, ?)",
                (task_id, tag_id),
            )

    def _row_to_task(self, row) -> Task:
        due_at = datetime.fromisoformat(row["due_at"]) if row["due_at"] else None
        return Task(
            id=int(row["id"]),
            title=row["title"],
            description=row["description"],
            priority=Priority(row["priority"]),
            status=TaskStatus(row["status"]),
            due_at=due_at,
            project_id=row["project_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


class SQLitePomodoroSessionRepository(PomodoroSessionRepository):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def create(self, session: PomodoroSession) -> PomodoroSession:
        with self._db.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pomodoro_sessions(task_id, started_at, ended_at, duration_sec, session_type)
                VALUES(?, ?, ?, ?, ?)
                """,
                (
                    session.task_id,
                    session.started_at.isoformat(),
                    session.ended_at.isoformat(),
                    session.duration_sec,
                    session.session_type,
                ),
            )
            created_id = int(cursor.lastrowid)
        return PomodoroSession(
            id=created_id,
            task_id=session.task_id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_sec=session.duration_sec,
            session_type=session.session_type,
        )

    def list_between(self, start: datetime, end: datetime) -> list[PomodoroSession]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM pomodoro_sessions WHERE started_at BETWEEN ? AND ? ORDER BY started_at DESC",
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return [
            PomodoroSession(
                id=int(row["id"]),
                task_id=row["task_id"],
                started_at=datetime.fromisoformat(row["started_at"]),
                ended_at=datetime.fromisoformat(row["ended_at"]),
                duration_sec=int(row["duration_sec"]),
                session_type=row["session_type"],
            )
            for row in rows
        ]


class SQLiteProjectRepository(ProjectRepository):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def create(self, project: Project) -> Project:
        with self._db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO projects(name, color) VALUES(?, ?)",
                (project.name, project.color),
            )
        return Project(id=int(cursor.lastrowid), name=project.name, color=project.color)

    def list_all(self) -> list[Project]:
        with self._db.connect() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY name ASC").fetchall()
        return [Project(id=int(row["id"]), name=row["name"], color=row["color"]) for row in rows]


class SQLiteTagRepository(TagRepository):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def create(self, tag: Tag) -> Tag:
        with self._db.connect() as conn:
            cursor = conn.execute("INSERT INTO tags(name) VALUES(?)", (tag.name,))
        return Tag(id=int(cursor.lastrowid), name=tag.name)

    def list_all(self) -> list[Tag]:
        with self._db.connect() as conn:
            rows = conn.execute("SELECT * FROM tags ORDER BY name ASC").fetchall()
        return [Tag(id=int(row["id"]), name=row["name"]) for row in rows]
