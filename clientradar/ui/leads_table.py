from __future__ import annotations

import webbrowser
from tkinter import ttk
from typing import Callable

import customtkinter as ctk

from clientradar.models.lead import Lead, LeadStatus


class LeadsTable(ctk.CTkFrame):
    _COLUMNS = {
        "name": ("Název", 200),
        "category": ("Kategorie", 130),
        "city": ("Město", 110),
        "phone": ("Telefon", 130),
        "website": ("Web", 150),
        "rating": ("Hodnocení", 80),
        "status": ("Status", 100),
    }

    _STATUS_COLORS = {
        LeadStatus.NEW: ("#ffffff", "#1a1a2e"),
        LeadStatus.CONTACTED: ("#cce5ff", "#1a1a2e"),
        LeadStatus.INTERESTED: ("#d4edda", "#1a1a2e"),
        LeadStatus.REJECTED: ("#f8d7da", "#1a1a2e"),
        LeadStatus.IGNORED: ("#6c757d", "#1a1a2e"),
    }

    def __init__(
        self,
        master,
        on_select_callback: Callable[[Lead], None],
        on_delete_callback: Callable[[Lead], None],
        on_status_change_callback: Callable[[Lead, LeadStatus], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_select = on_select_callback
        self._on_delete = on_delete_callback
        self._on_status_change = on_status_change_callback
        self._leads: list[Lead] = []
        self._sort_column: str = "name"
        self._sort_reverse: bool = False

        self._setup_style()
        self._build_tree()

    def _setup_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.Treeview",
            background="#2b2b3d",
            foreground="#e0e0e0",
            fieldbackground="#2b2b3d",
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=28,
        )
        style.configure("Dark.Treeview.Heading",
            background="#1a1a2e",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="flat",
        )
        style.map("Dark.Treeview",
            background=[("selected", "#3d5a80")],
            foreground=[("selected", "#ffffff")],
        )
        style.map("Dark.Treeview.Heading",
            background=[("active", "#2a2a4a")],
        )

        style.configure("Dark.Vertical.TScrollbar",
            background="#3b3b5c",
            troughcolor="#2b2b3d",
            borderwidth=0,
            arrowsize=14,
        )

    def _build_tree(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        col_ids = list(self._COLUMNS.keys())
        self._tree = ttk.Treeview(
            container,
            columns=col_ids,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
        )

        for col_id, (heading, width) in self._COLUMNS.items():
            self._tree.heading(
                col_id, text=heading,
                command=lambda c=col_id: self._on_sort(c),
            )
            self._tree.column(col_id, width=width, minwidth=60)

        scrollbar_y = ttk.Scrollbar(
            container, orient="vertical", command=self._tree.yview,
            style="Dark.Vertical.TScrollbar",
        )
        self._tree.configure(yscrollcommand=scrollbar_y.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._tree.bind("<Button-3>", self._on_right_click)

        for status in LeadStatus:
            fg, _ = self._STATUS_COLORS.get(status, ("#ffffff", "#1a1a2e"))
            self._tree.tag_configure(status.name, foreground=fg)

        self._tree.tag_configure(LeadStatus.CONTACTED.name, foreground="#66b2ff")
        self._tree.tag_configure(LeadStatus.INTERESTED.name, foreground="#66ff66")
        self._tree.tag_configure(LeadStatus.REJECTED.name, foreground="#ff6666")
        self._tree.tag_configure(LeadStatus.IGNORED.name, foreground="#888888")
        self._tree.tag_configure(LeadStatus.NEW.name, foreground="#e0e0e0")

    def load_leads(self, leads: list[Lead]) -> None:
        self._leads = leads
        self._tree.delete(*self._tree.get_children())
        for lead in leads:
            self._insert_lead(lead)

    def _insert_lead(self, lead: Lead) -> None:
        values = (
            lead.name,
            lead.category,
            lead.city,
            lead.phone,
            lead.website[:40] + "…" if lead.website and len(lead.website) > 40 else lead.website,
            f"★ {lead.rating}" if lead.rating > 0 else "—",
            lead.status.value,
        )
        self._tree.insert(
            "", "end",
            iid=str(lead.id),
            values=values,
            tags=(lead.status.name,),
        )

    def update_row(self, lead: Lead) -> None:
        iid = str(lead.id)
        if self._tree.exists(iid):
            values = (
                lead.name,
                lead.category,
                lead.city,
                lead.phone,
                lead.website[:40] + "…" if lead.website and len(lead.website) > 40 else lead.website,
                f"★ {lead.rating}" if lead.rating > 0 else "—",
                lead.status.value,
            )
            self._tree.item(iid, values=values, tags=(lead.status.name,))

    def get_selected_lead(self) -> Lead | None:
        selection = self._tree.selection()
        if not selection:
            return None
        lead_id = int(selection[0])
        for lead in self._leads:
            if lead.id == lead_id:
                return lead
        return None

    def _on_tree_select(self, event) -> None:
        lead = self.get_selected_lead()
        if lead:
            self._on_select(lead)

    def _on_sort(self, column: str) -> None:
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False

        def sort_key(lead: Lead):
            val = getattr(lead, column, "")
            if isinstance(val, str):
                return val.lower()
            return val

        self._leads.sort(key=sort_key, reverse=self._sort_reverse)
        self.load_leads(self._leads)

    def _on_right_click(self, event) -> None:
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        self._tree.selection_set(iid)
        lead = self.get_selected_lead()
        if not lead:
            return

        from tkinter import Menu
        menu = Menu(self._tree, tearoff=0, bg="#2b2b3d", fg="#e0e0e0",
                    activebackground="#3d5a80", activeforeground="#ffffff",
                    font=("Segoe UI", 10))

        menu.add_command(
            label="✏️ Označit jako Kontaktován",
            command=lambda: self._on_status_change(lead, LeadStatus.CONTACTED),
        )
        menu.add_command(
            label="⭐ Má zájem",
            command=lambda: self._on_status_change(lead, LeadStatus.INTERESTED),
        )
        menu.add_command(
            label="❌ Ignorovat",
            command=lambda: self._on_status_change(lead, LeadStatus.IGNORED),
        )
        menu.add_separator()
        menu.add_command(
            label="🗺 Otevřít v prohlížeči",
            command=lambda: webbrowser.open(lead.google_maps_url) if lead.google_maps_url else None,
        )
        menu.add_separator()
        menu.add_command(
            label="🗑 Smazat lead",
            command=lambda: self._on_delete(lead),
        )

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
