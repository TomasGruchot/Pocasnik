from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import customtkinter as ctk

from clientradar.models.lead import LeadStatus
from clientradar.models.search_config import SearchConfig

if TYPE_CHECKING:
    pass


class Sidebar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_start_scraping: Callable[[SearchConfig], None],
        on_stop_scraping: Callable[[], None],
        on_search_filter: Callable[[str], None],
        on_status_filter: Callable[[str], None],
        on_export: Callable[[], None],
        on_launch_easter_egg: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, width=280, corner_radius=0, **kwargs)
        self.grid_propagate(False)

        self._on_start = on_start_scraping
        self._on_stop = on_stop_scraping
        self._on_search = on_search_filter
        self._on_status_filter = on_status_filter
        self._on_export = on_export
        self._on_launch_easter_egg = on_launch_easter_egg
        self._is_scraping = False

        self._build_search_section()
        self._build_filter_section()
        self._build_stats_section()
        self._build_export_button()
        self._build_easter_egg_button()

    def _build_search_section(self) -> None:
        ctk.CTkLabel(
            self, text="🔍 Hledat klienty",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=15, pady=(15, 8), anchor="w")

        self._keyword_entry = ctk.CTkEntry(
            self, placeholder_text="Např. instalatér, účetní…", width=250,
        )
        self._keyword_entry.pack(padx=15, pady=4)

        self._location_entry = ctk.CTkEntry(
            self, placeholder_text="Např. Praha, Brno…", width=250,
        )
        self._location_entry.pack(padx=15, pady=4)

        slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        slider_frame.pack(padx=15, pady=4, fill="x")

        ctk.CTkLabel(slider_frame, text="Max. výsledků:", font=ctk.CTkFont(size=12)).pack(anchor="w")

        self._slider_value_label = ctk.CTkLabel(
            slider_frame, text="50", font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._slider_value_label.pack(anchor="e")

        self._max_results_slider = ctk.CTkSlider(
            slider_frame, from_=10, to=200, number_of_steps=19,
            command=self._on_slider_change,
        )
        self._max_results_slider.set(50)
        self._max_results_slider.pack(fill="x")

        self._headless_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Headless (na pozadí)", variable=self._headless_var,
        ).pack(padx=15, pady=4, anchor="w")

        self._fetch_emails_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self, text="Hledat emaily z webu", variable=self._fetch_emails_var,
        ).pack(padx=15, pady=4, anchor="w")

        self._start_btn = ctk.CTkButton(
            self, text="📡 Spustit hledání", width=250,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            command=self._handle_start,
        )
        self._start_btn.pack(padx=15, pady=(10, 2))

        self._stop_btn = ctk.CTkButton(
            self, text="⏹ Zastavit", width=250,
            fg_color="#dc3545", hover_color="#c82333",
            command=self._handle_stop,
        )
        self._stop_btn.pack(padx=15, pady=2)
        self._stop_btn.pack_forget()

    def _build_filter_section(self) -> None:
        sep = ctk.CTkFrame(self, height=2, fg_color="gray30")
        sep.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            self, text="🗂 Filtrovat",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=15, pady=(0, 8), anchor="w")

        self._filter_entry = ctk.CTkEntry(
            self, placeholder_text="Hledat v leadech…", width=250,
        )
        self._filter_entry.pack(padx=15, pady=4)
        self._filter_entry.bind("<KeyRelease>", self._on_filter_keypress)

        self._status_filter_menu = ctk.CTkOptionMenu(
            self, values=["Vše"] + LeadStatus.all_values(),
            width=250, command=self._on_status_menu_change,
        )
        self._status_filter_menu.set("Vše")
        self._status_filter_menu.pack(padx=15, pady=4)

    def _build_stats_section(self) -> None:
        sep = ctk.CTkFrame(self, height=2, fg_color="gray30")
        sep.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            self, text="📊 Statistiky",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=15, pady=(0, 8), anchor="w")

        self._stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._stats_frame.pack(padx=15, fill="x")

        self._stat_labels: dict[str, ctk.CTkLabel] = {}
        stat_items = [
            ("total", "Celkem", "#0d6efd"),
            ("new", "Nových", "#ffc107"),
            ("contacted", "Kontaktováno", "#17a2b8"),
            ("interested", "Zájem", "#28a745"),
            ("rejected", "Nezájem", "#dc3545"),
            ("ignored", "Ignorováno", "#6c757d"),
        ]
        for key, label_text, color in stat_items:
            row = ctk.CTkFrame(self._stats_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"  {label_text}:", font=ctk.CTkFont(size=12), anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(
                row, text="0", font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color, anchor="e",
            )
            lbl.pack(side="right", padx=5)
            self._stat_labels[key] = lbl

    def _build_export_button(self) -> None:
        sep = ctk.CTkFrame(self, height=2, fg_color="gray30")
        sep.pack(fill="x", padx=15, pady=12)

        ctk.CTkButton(
            self, text="📤 Export do Excelu", width=250,
            fg_color="#198754", hover_color="#157347",
            command=self._on_export,
        ).pack(padx=15, pady=4)

    def _build_easter_egg_button(self) -> None:
        ctk.CTkButton(
            self,
            text="🕹 Spustit Easter Egg",
            width=250,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self._on_launch_easter_egg,
        ).pack(padx=15, pady=(8, 4))

    def _on_slider_change(self, value: float) -> None:
        self._slider_value_label.configure(text=str(int(value)))

    def _handle_start(self) -> None:
        config = SearchConfig(
            keyword=self._keyword_entry.get().strip(),
            location=self._location_entry.get().strip(),
            max_results=int(self._max_results_slider.get()),
            headless=self._headless_var.get(),
            fetch_emails=self._fetch_emails_var.get(),
        )
        error = config.validate()
        if error:
            from tkinter import messagebox
            messagebox.showwarning("Chyba", error, parent=self)
            return
        self.set_scraping(True)
        self._on_start(config)

    def _handle_stop(self) -> None:
        self.set_scraping(False)
        self._on_stop()

    def set_scraping(self, active: bool) -> None:
        self._is_scraping = active
        if active:
            self._start_btn.pack_forget()
            self._stop_btn.pack(padx=15, pady=(10, 2))
            self._keyword_entry.configure(state="disabled")
            self._location_entry.configure(state="disabled")
            self._max_results_slider.configure(state="disabled")
        else:
            self._stop_btn.pack_forget()
            self._start_btn.pack(padx=15, pady=(10, 2))
            self._keyword_entry.configure(state="normal")
            self._location_entry.configure(state="normal")
            self._max_results_slider.configure(state="normal")

    def _on_filter_keypress(self, event) -> None:
        self._on_search(self._filter_entry.get().strip())

    def _on_status_menu_change(self, value: str) -> None:
        self._on_status_filter(value)

    def refresh_stats(self, stats: dict) -> None:
        for key, label in self._stat_labels.items():
            label.configure(text=str(stats.get(key, 0)))
