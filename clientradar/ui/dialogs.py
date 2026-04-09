from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from clientradar.models.lead import LeadStatus


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, message: str, on_confirm: Callable[[], None]) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("400x180")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._on_confirm = on_confirm

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame, text=message, wraplength=350,
            font=ctk.CTkFont(size=14),
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame, text="✓ Ano", width=100,
            fg_color="#28a745", hover_color="#218838",
            command=self._confirm,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="✗ Ne", width=100,
            fg_color="#6c757d", hover_color="#5a6268",
            command=self.destroy,
        ).pack(side="left", padx=10)

        self.after(100, self.focus_force)

    def _confirm(self) -> None:
        self._on_confirm()
        self.destroy()


class ExportDialog(ctk.CTkToplevel):
    def __init__(self, master, on_export: Callable[[str, str | None], None]) -> None:
        super().__init__(master)
        self.title("📤 Export do Excelu")
        self.geometry("420x280")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._on_export = on_export

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame, text="Vyberte rozsah exportu:",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        self._scope_var = ctk.StringVar(value="all")

        ctk.CTkRadioButton(
            frame, text="Všechny leady", variable=self._scope_var, value="all",
        ).pack(anchor="w", pady=3)
        ctk.CTkRadioButton(
            frame, text="Pouze filtrované", variable=self._scope_var, value="filtered",
        ).pack(anchor="w", pady=3)
        ctk.CTkRadioButton(
            frame, text="Podle statusu:", variable=self._scope_var, value="status",
        ).pack(anchor="w", pady=3)

        self._status_menu = ctk.CTkOptionMenu(
            frame,
            values=LeadStatus.all_values(),
            width=200,
        )
        self._status_menu.pack(anchor="w", padx=(25, 0), pady=(0, 15))
        self._status_menu.set(LeadStatus.NEW.value)

        ctk.CTkButton(
            frame, text="💾 Exportovat", width=160,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            command=self._do_export,
        ).pack(pady=5)

        self.after(100, self.focus_force)

    def _do_export(self) -> None:
        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Uložit jako…",
            defaultextension=".xlsx",
            filetypes=[("Excel soubory", "*.xlsx"), ("Všechny soubory", "*.*")],
            initialfile="clientradar_export.xlsx",
        )
        if not filepath:
            return
        scope = self._scope_var.get()
        status_filter = self._status_menu.get() if scope == "status" else None
        self._on_export(filepath, status_filter if scope == "status" else scope)
        self.destroy()
