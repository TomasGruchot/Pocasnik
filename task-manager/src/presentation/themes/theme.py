from __future__ import annotations

from dataclasses import dataclass
from tkinter import ttk


@dataclass(frozen=True, slots=True)
class Theme:
    background: str = "#09090B"
    surface_1: str = "#0B0B10"
    panel: str = "#18181B"
    panel_alt: str = "#111827"
    accent: str = "#8B5CF6"
    accent_hover: str = "#7C3AED"
    accent_soft: str = "#2A1F46"
    text_primary: str = "#F9FAFB"
    text_secondary: str = "#9CA3AF"
    text_tertiary: str = "#6B7280"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    border: str = "#27272A"
    border_strong: str = "#3F3F46"
    shadow: str = "#000000"
    radius: int = 14
    font_family: str = "Segoe UI"
    row_alt: str = "#101015"
    info: str = "#38BDF8"
    focus: str = "#A78BFA"

    # spacing tokens (px)
    space_1: int = 6
    space_2: int = 10
    space_3: int = 14
    space_4: int = 18

    # typography tokens
    font_sm: int = 9
    font_md: int = 10
    font_lg: int = 12
    font_xl: int = 16

    def configure_ttk_styles(self, style: ttk.Style) -> None:
        # Containers
        style.configure(
            "Premium.TFrame",
            background=self.panel,
            borderwidth=1,
            relief="solid",
        )

        style.configure(
            "Surface.TFrame",
            background=self.background,
            borderwidth=0,
            relief="flat",
        )

        style.configure(
            "Card.TFrame",
            background=self.panel,
            borderwidth=1,
            relief="solid",
        )

        # Typography
        style.configure(
            "Premium.TLabel",
            background=self.panel,
            foreground=self.text_primary,
            font=(self.font_family, self.font_md),
        )
        style.configure(
            "Muted.TLabel",
            background=self.panel,
            foreground=self.text_secondary,
            font=(self.font_family, self.font_sm),
        )

        style.configure(
            "Title.TLabel",
            background=self.panel,
            foreground=self.text_primary,
            font=(self.font_family, self.font_xl, "bold"),
        )

        style.configure(
            "Section.TLabel",
            background=self.panel,
            foreground=self.text_primary,
            font=(self.font_family, self.font_lg, "bold"),
        )

        # Inputs
        style.configure(
            "TEntry",
            padding=(10, 8),
            relief="flat",
            borderwidth=1,
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", self.focus), ("!focus", self.border)],
            lightcolor=[("focus", self.focus), ("!focus", self.border)],
            darkcolor=[("focus", self.focus), ("!focus", self.border)],
        )
        style.configure(
            "TCombobox",
            padding=(10, 8),
            relief="flat",
            borderwidth=1,
        )
        style.map(
            "TCombobox",
            bordercolor=[("focus", self.focus), ("!focus", self.border)],
            lightcolor=[("focus", self.focus), ("!focus", self.border)],
            darkcolor=[("focus", self.focus), ("!focus", self.border)],
        )

        # Progress
        style.configure(
            "TProgressbar",
            troughcolor=self.panel_alt,
            bordercolor=self.border,
            lightcolor=self.accent,
            darkcolor=self.accent,
            background=self.accent,
            thickness=10,
        )

        # Tables / lists
        style.configure(
            "Tasks.Treeview",
            background=self.panel_alt,
            fieldbackground=self.panel_alt,
            foreground=self.text_primary,
            bordercolor=self.border,
            lightcolor=self.border,
            darkcolor=self.border,
            rowheight=28,
            font=(self.font_family, 10),
        )
        style.configure(
            "Tasks.Treeview.Heading",
            background=self.panel,
            foreground=self.text_secondary,
            relief="flat",
            font=(self.font_family, 9, "bold"),
            padding=(10, 10),
        )
        style.map(
            "Tasks.Treeview",
            background=[("selected", self.accent)],
            foreground=[("selected", self.text_primary)],
        )

        # Buttons
        style.configure(
            "Premium.TButton",
            font=(self.font_family, self.font_md, "bold"),
            padding=(10, 8),
        )
        style.map(
            "Premium.TButton",
            background=[("active", self.accent_hover), ("!disabled", self.accent)],
            foreground=[("disabled", self.text_secondary), ("!disabled", self.text_primary)],
        )

        style.configure(
            "Ghost.TButton",
            font=(self.font_family, self.font_md, "bold"),
            padding=(10, 8),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", self.panel_alt), ("!disabled", self.panel)],
            foreground=[("disabled", self.text_tertiary), ("!disabled", self.text_secondary)],
        )
