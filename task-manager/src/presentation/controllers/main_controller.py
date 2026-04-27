from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb

from application.services.pomodoro_service import PomodoroService
from application.services.stats_service import StatsService
from application.services.task_service import TaskService
from presentation.themes.theme import Theme
from presentation.views.dashboard_view import DashboardView


class MainController:
    def __init__(
        self,
        root: tk.Tk,
        task_service: TaskService,
        pomodoro_service: PomodoroService,
        stats_service: StatsService,
    ) -> None:
        self._root = root
        self._theme = Theme()
        self._configure_window()
        self._dashboard = DashboardView(
            root,
            task_service=task_service,
            pomodoro_service=pomodoro_service,
            stats_service=stats_service,
            theme=self._theme,
        )

    def _configure_window(self) -> None:
        self._root.title("task-manager")
        self._root.geometry("1280x760")
        self._root.minsize(980, 640)
        self._root.configure(bg=self._theme.background)
        tb.Style(theme="darkly")
        self._root.option_add("*Font", (self._theme.font_family, 10))
        self._root.option_add("*TCombobox*Listbox.font", (self._theme.font_family, 10))
        self._theme.configure_ttk_styles(ttk.Style())
