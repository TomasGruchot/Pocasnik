from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from application.services.pomodoro_service import PomodoroService
from application.services.stats_service import StatsService
from application.services.task_service import TaskService
from domain.value_objects.enums import Priority, TaskStatus
from presentation.themes.theme import Theme
from presentation.widgets.components import GlassCard, GhostButton, PrimaryButton, StatusBadge


class DashboardView(tk.Frame):
    def __init__(
        self,
        master,
        task_service: TaskService,
        pomodoro_service: PomodoroService,
        stats_service: StatsService,
        theme: Theme,
    ) -> None:
        super().__init__(master, bg=theme.background)
        self._task_service = task_service
        self._pomodoro_service = pomodoro_service
        self._stats_service = stats_service
        self._theme = theme

        self._search_var = tk.StringVar()
        self._title_var = tk.StringVar()
        self._desc_var = tk.StringVar()
        self._priority_var = tk.StringVar(value=Priority.MEDIUM.value)
        self._status_filter_var = tk.StringVar(value="all")
        self._sort_by_var = tk.StringVar(value="created_desc")
        self._project_filter_var = tk.StringVar(value="all")
        self._work_minutes_var = tk.StringVar(value=str(self._pomodoro_service.work_minutes))
        self._break_minutes_var = tk.StringVar(value=str(self._pomodoro_service.short_break_minutes))
        self._selected_task_id: int | None = None

        self._timer_label: tk.Label | None = None
        self._timer_state_label: ttk.Label | None = None
        self._timer_progress: ttk.Progressbar | None = None
        self._stats_label: tk.Label | None = None
        self._task_tree: ttk.Treeview | None = None
        self._project_name_to_id: dict[str, int] = {}
        self._build_ui()
        self.refresh()
        self._schedule_timer_tick()

    def _build_ui(self) -> None:
        self.pack(fill="both", expand=True, padx=12, pady=12)

        shell = ttk.Frame(self, style="Surface.TFrame")
        shell.pack(fill="both", expand=True)

        top = GlassCard(shell, self._theme)
        top.pack(fill="x", pady=(0, 10))

        body = ttk.Frame(shell, style="Surface.TFrame")
        body.pack(fill="both", expand=True)

        left = GlassCard(body, self._theme)
        center = GlassCard(body, self._theme)
        right = GlassCard(body, self._theme)

        left.pack(side="left", fill="y", padx=(0, 10))
        center.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right.pack(side="left", fill="y")

        self._build_topbar(top)
        self._build_sidebar(left)
        self._build_task_panel(center)
        self._build_timer_panel(right)

    def _build_topbar(self, parent: tk.Frame) -> None:
        bar = ttk.Frame(parent, style="Premium.TFrame")
        bar.pack(fill="x", padx=14, pady=(12, 12))

        ttk.Label(bar, text="Task Manager", style="Title.TLabel").pack(side="left")
        StatusBadge(bar, self._theme, "MVP+", self._theme.success).pack(side="left", padx=(10, 0))

        right = ttk.Frame(bar, style="Premium.TFrame")
        right.pack(side="right")

        ttk.Entry(right, textvariable=self._search_var, width=32).pack(side="left", padx=(0, 10))
        GhostButton(right, self._theme, text="Refresh", command=self.refresh).pack(side="left", padx=(0, 8))
        PrimaryButton(right, self._theme, text="+ Task", command=self._create_task).pack(side="left")

    def _build_sidebar(self, parent: tk.Frame) -> None:
        ttk.Label(
            parent,
            text="Filtry",
            style="Section.TLabel",
        ).pack(anchor="w", padx=14, pady=(14, 8))

        ttk.Label(parent, text="Status", style="Muted.TLabel").pack(anchor="w", padx=14, pady=(6, 4))
        ttk.Combobox(
            parent,
            textvariable=self._status_filter_var,
            values=["all", TaskStatus.TODO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.DONE.value],
            state="readonly",
        ).pack(fill="x", padx=14)
        ttk.Label(parent, text="Projekt", style="Muted.TLabel").pack(anchor="w", padx=14, pady=(6, 4))
        self._project_filter_combo = ttk.Combobox(parent, textvariable=self._project_filter_var, state="readonly")
        self._project_filter_combo.pack(fill="x", padx=14)
        ttk.Label(parent, text="Řazení", style="Muted.TLabel").pack(anchor="w", padx=14, pady=(6, 4))
        ttk.Combobox(
            parent,
            textvariable=self._sort_by_var,
            values=["created_desc", "created_asc", "due_asc", "priority_desc"],
            state="readonly",
        ).pack(fill="x", padx=14)
        PrimaryButton(parent, self._theme, text="Použít filtry", command=self.refresh).pack(fill="x", padx=14, pady=10)

        ttk.Label(parent, text="Akce", style="Muted.TLabel").pack(anchor="w", padx=14, pady=(10, 4))
        GhostButton(parent, self._theme, text="Nový projekt", command=self._create_project).pack(
            fill="x", padx=14, pady=(0, 8)
        )
        GhostButton(parent, self._theme, text="Nový tag", command=self._create_tag).pack(fill="x", padx=14, pady=(0, 8))
        GhostButton(parent, self._theme, text="Nastavení timeru", command=self._open_preferences).pack(
            fill="x", padx=14, pady=(0, 8)
        )

        self._stats_label = ttk.Label(
            parent,
            text="",
            justify="left",
            style="Muted.TLabel",
        )
        self._stats_label.pack(anchor="w", padx=14, pady=(8, 14))

    def _build_task_panel(self, parent: tk.Frame) -> None:
        header = ttk.Frame(parent, style="Premium.TFrame")
        header.pack(fill="x", padx=14, pady=(14, 8))
        ttk.Label(
            header,
            text="Tasky",
            style="Premium.TLabel",
        ).pack(side="left")
        StatusBadge(header, self._theme, "MVP+", self._theme.success).pack(side="right")

        table_wrap = ttk.Frame(parent, style="Premium.TFrame")
        table_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        columns = ("status", "title", "priority", "due")
        self._task_tree = ttk.Treeview(
            table_wrap,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Tasks.Treeview",
        )
        self._task_tree.heading("status", text="Status")
        self._task_tree.heading("title", text="Task")
        self._task_tree.heading("priority", text="Priority")
        self._task_tree.heading("due", text="Due")

        self._task_tree.column("status", width=110, anchor="w", stretch=False)
        self._task_tree.column("title", width=520, anchor="w", stretch=True)
        self._task_tree.column("priority", width=110, anchor="w", stretch=False)
        self._task_tree.column("due", width=120, anchor="w", stretch=False)

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self._task_tree.yview)
        self._task_tree.configure(yscrollcommand=scrollbar.set)
        self._task_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._task_tree.bind("<<TreeviewSelect>>", self._on_task_selected)

        form = ttk.Frame(parent, style="Premium.TFrame")
        form.pack(fill="x", padx=14, pady=(0, 14))
        ttk.Entry(form, textvariable=self._title_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Entry(form, textvariable=self._desc_var).grid(row=0, column=1, sticky="ew")
        ttk.Combobox(
            form,
            textvariable=self._priority_var,
            values=[item.value for item in Priority],
            state="readonly",
            width=10,
        ).grid(row=0, column=2, padx=(8, 8))
        PrimaryButton(form, self._theme, text="Přidat", command=self._create_task).grid(row=0, column=3)
        PrimaryButton(
            form,
            self._theme,
            text="Hotovo",
            command=lambda: self._set_selected_status_many(TaskStatus.DONE),
        ).grid(row=1, column=3, pady=(8, 0))
        PrimaryButton(
            form,
            self._theme,
            text="Rozpracováno",
            command=lambda: self._set_selected_status_many(TaskStatus.IN_PROGRESS),
        ).grid(row=1, column=2, pady=(8, 0))
        PrimaryButton(form, self._theme, text="Smazat výběr", command=self._delete_selected_tasks).grid(
            row=1, column=1, pady=(8, 0), sticky="ew"
        )
        PrimaryButton(form, self._theme, text="Upravit vybraný", command=self._edit_selected_task).grid(
            row=1, column=0, pady=(8, 0), sticky="ew", padx=(0, 8)
        )
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

    def _build_timer_panel(self, parent: tk.Frame) -> None:
        ttk.Label(
            parent,
            text="Pomodoro",
            style="Premium.TLabel",
        ).pack(anchor="w", padx=14, pady=(14, 10))

        self._timer_label = ttk.Label(
            parent,
            text="25:00",
            style="Premium.TLabel",
            font=(self._theme.font_family, 28, "bold"),
        )
        self._timer_label.pack(anchor="center", padx=14, pady=(10, 14))
        self._timer_state_label = ttk.Label(parent, text="idle", style="Muted.TLabel")
        self._timer_state_label.pack(anchor="center", padx=14, pady=(0, 8))
        self._timer_progress = ttk.Progressbar(parent, mode="determinate", maximum=100)
        self._timer_progress.pack(fill="x", padx=14, pady=(0, 10))

        PrimaryButton(parent, self._theme, text="Start", command=self._start_timer).pack(
            fill="x", padx=14, pady=(0, 8)
        )
        PrimaryButton(parent, self._theme, text="Pause", command=self._pause_timer).pack(
            fill="x", padx=14, pady=(0, 8)
        )
        PrimaryButton(parent, self._theme, text="Reset", command=self._reset_timer).pack(
            fill="x", padx=14, pady=(0, 14)
        )

    def _get_selected_ids(self) -> list[int]:
        if self._task_tree is None:
            return []
        ids: list[int] = []
        for item_id in self._task_tree.selection():
            try:
                ids.append(int(item_id))
            except ValueError:
                continue
        return ids

    def _create_task(self) -> None:
        try:
            self._task_service.create_task(
                title=self._title_var.get(),
                description=self._desc_var.get(),
                priority=Priority(self._priority_var.get()),
                due_at=None,
            )
        except ValueError as exc:
            messagebox.showerror("Chyba", str(exc))
            return
        self._title_var.set("")
        self._desc_var.set("")
        self.refresh()

    def _delete_selected_tasks(self) -> None:
        selected_ids = self._get_selected_ids()
        if not selected_ids:
            return
        self._task_service.delete_many(selected_ids)
        self._selected_task_id = None
        self.refresh()

    def _set_selected_status_many(self, status: TaskStatus) -> None:
        selected_ids = self._get_selected_ids()
        if not selected_ids:
            return
        self._task_service.set_many_status(selected_ids, status)
        self.refresh()

    def _on_task_selected(self, _event) -> None:
        if self._task_tree is None:
            return
        selection = self._task_tree.selection()
        if not selection:
            self._selected_task_id = None
            return
        try:
            self._selected_task_id = int(selection[0])
        except ValueError:
            self._selected_task_id = None

    def _edit_selected_task(self) -> None:
        if self._selected_task_id is None:
            return
        try:
            self._task_service.update_task(
                task_id=self._selected_task_id,
                title=self._title_var.get(),
                description=self._desc_var.get(),
                priority=Priority(self._priority_var.get()),
                due_at=None,
            )
        except ValueError as exc:
            messagebox.showerror("Chyba", str(exc))
            return
        self.refresh()

    def _start_timer(self) -> None:
        self._pomodoro_service.start(task_id=self._selected_task_id)

    def _pause_timer(self) -> None:
        self._pomodoro_service.pause()

    def _reset_timer(self) -> None:
        self._pomodoro_service.reset()

    def _schedule_timer_tick(self) -> None:
        snapshot = self._pomodoro_service.tick()
        if self._timer_label is not None:
            mins, secs = divmod(snapshot.remaining_seconds, 60)
            self._timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        if self._timer_state_label is not None:
            active_task = f"task #{snapshot.active_task_id}" if snapshot.active_task_id else "bez tasku"
            self._timer_state_label.configure(text=f"{snapshot.state.value} | {snapshot.cycle_type} | {active_task}")
        if self._timer_progress is not None:
            total = (
                self._pomodoro_service.work_minutes * 60
                if snapshot.cycle_type == "work"
                else self._pomodoro_service.short_break_minutes * 60
            )
            progress = 0 if total <= 0 else int(((total - snapshot.remaining_seconds) / total) * 100)
            self._timer_progress.configure(value=max(0, min(progress, 100)))
        self.after(1000, self._schedule_timer_tick)

    def _create_project(self) -> None:
        name = self._title_var.get().strip()
        if not name:
            messagebox.showerror("Chyba", "Nejdřív zadej název projektu do pole titulku.")
            return
        try:
            self._task_service.create_project(name)
            self._title_var.set("")
            self.refresh()
        except ValueError as exc:
            messagebox.showerror("Chyba", str(exc))

    def _create_tag(self) -> None:
        name = self._title_var.get().strip()
        if not name:
            messagebox.showerror("Chyba", "Nejdřív zadej název tagu do pole titulku.")
            return
        try:
            self._task_service.create_tag(name)
            self._title_var.set("")
        except ValueError as exc:
            messagebox.showerror("Chyba", str(exc))

    def _open_preferences(self) -> None:
        popup = tk.Toplevel(self)
        popup.title("Nastavení Pomodoro")
        popup.configure(bg=self._theme.panel)
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Work (min)", style="Muted.TLabel").grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        ttk.Entry(popup, textvariable=self._work_minutes_var).grid(row=0, column=1, padx=12, pady=(12, 6))
        ttk.Label(popup, text="Break (min)", style="Muted.TLabel").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        ttk.Entry(popup, textvariable=self._break_minutes_var).grid(row=1, column=1, padx=12, pady=6)

        def _save() -> None:
            try:
                self._pomodoro_service.update_settings(
                    work_minutes=int(self._work_minutes_var.get()),
                    short_break_minutes=int(self._break_minutes_var.get()),
                )
            except ValueError as exc:
                messagebox.showerror("Chyba", str(exc))
                return
            popup.destroy()

        PrimaryButton(popup, self._theme, text="Uložit", command=_save).grid(row=2, column=0, columnspan=2, padx=12, pady=(6, 12), sticky="ew")

    def refresh(self) -> None:
        projects = self._task_service.list_projects()
        self._project_name_to_id = {project.name: project.id for project in projects if project.id is not None}
        project_values = ["all", *self._project_name_to_id.keys()]
        self._project_filter_combo.configure(values=project_values)
        if self._project_filter_var.get() not in project_values:
            self._project_filter_var.set("all")

        status_value = self._status_filter_var.get()
        status_filter = TaskStatus(status_value) if status_value in {item.value for item in TaskStatus} else None
        project_filter = None
        if self._project_filter_var.get() in self._project_name_to_id:
            project_filter = self._project_name_to_id[self._project_filter_var.get()]
        priority_filter = (
            Priority(self._priority_var.get())
            if self._priority_var.get() in {item.value for item in Priority}
            else None
        )
        tasks = self._task_service.list_tasks(
            search=self._search_var.get().strip() or None,
            status=status_filter,
            project_id=project_filter,
            priority=priority_filter,
            sort_by=self._sort_by_var.get(),
        )
        if self._task_tree is not None:
            for child in self._task_tree.get_children():
                self._task_tree.delete(child)
            for task in tasks:
                if task.id is None:
                    continue
                due = task.due_at.strftime("%Y-%m-%d") if task.due_at else "-"
                self._task_tree.insert(
                    "",
                    "end",
                    iid=str(task.id),
                    values=(task.status.value, task.title, task.priority.value, due),
                )

        stats = self._stats_service.get_dashboard_stats()
        if self._stats_label is not None:
            self._stats_label.configure(
                text=(
                    f"Dnes hotovo: {stats.completed_today}\n"
                    f"Týden hotovo: {stats.completed_this_week}\n"
                    f"Focus min dnes: {stats.focused_minutes_today}\n"
                    f"Focus min týden: {stats.focused_minutes_this_week}\n"
                    f"Completion ratio today: {stats.completion_ratio_today:.0%}"
                )
            )
