from __future__ import annotations

from dataclasses import dataclass
from tkinter import ttk


@dataclass(frozen=True, slots=True)
class Theme:
    background: str = "#09090B"
    panel: str = "#18181B"
    panel_alt: str = "#111827"
    accent: str = "#8B5CF6"
    accent_hover: str = "#7C3AED"
    text_primary: str = "#F9FAFB"
    text_secondary: str = "#9CA3AF"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    border: str = "#27272A"
    radius: int = 14
    font_family: str = "Segoe UI"
    row_alt: str = "#101015"
    info: str = "#38BDF8"

    def configure_ttk_styles(self, style: ttk.Style) -> None:
        style.configure(
            "Premium.TFrame",
            background=self.panel,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Premium.TLabel",
            background=self.panel,
            foreground=self.text_primary,
            font=(self.font_family, 10),
        )
        style.configure(
            "Muted.TLabel",
            background=self.panel,
            foreground=self.text_secondary,
            font=(self.font_family, 9),
        )
        style.configure(
            "Premium.TButton",
            font=(self.font_family, 10, "bold"),
            padding=(10, 8),
        )
        style.map(
            "Premium.TButton",
            background=[("active", self.accent_hover), ("!disabled", self.accent)],
            foreground=[("disabled", self.text_secondary), ("!disabled", self.text_primary)],
        )
