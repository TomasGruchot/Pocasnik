from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from presentation.themes.theme import Theme


class GlassCard(ttk.Frame):
    def __init__(self, master, theme: Theme, **kwargs):
        super().__init__(master, style="Premium.TFrame", padding=12, **kwargs)
        self.configure(style="Premium.TFrame")


class PrimaryButton(ttk.Button):
    def __init__(self, master, theme: Theme, **kwargs):
        super().__init__(master, style="Premium.TButton", cursor="hand2", **kwargs)


class StatusBadge(ttk.Label):
    def __init__(self, master, theme: Theme, text: str, color: str):
        style_name = f"Badge.{color}.TLabel"
        style = ttk.Style(master)
        style.configure(
            style_name,
            background=color,
            foreground=theme.text_primary,
            font=(theme.font_family, 9, "bold"),
            padding=(8, 3),
        )
        super().__init__(master, text=text, style=style_name)
