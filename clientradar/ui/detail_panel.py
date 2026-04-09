from __future__ import annotations

import webbrowser
from typing import Callable

import customtkinter as ctk

from clientradar.models.lead import Lead, LeadStatus


class LeadDetailPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_save: Callable[[Lead], None],
        **kwargs,
    ) -> None:
        super().__init__(master, width=300, corner_radius=0, **kwargs)
        self.grid_propagate(False)

        self._on_save = on_save
        self._current_lead: Lead | None = None

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self._title_label = ctk.CTkLabel(
            self._scroll, text="Vyberte lead ze seznamu",
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=270,
        )
        self._title_label.pack(padx=10, pady=(10, 5), anchor="w")

        self._details_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._details_frame.pack(fill="x", padx=10, pady=5)

        self._field_labels: dict[str, ctk.CTkLabel] = {}
        fields = [
            ("category", "Kategorie"),
            ("address", "Adresa"),
            ("city", "Město"),
            ("phone", "Telefon"),
            ("website", "Web"),
            ("email", "Email"),
            ("rating_display", "Hodnocení"),
            ("reviews", "Recenze"),
            ("scraped", "Datum"),
        ]
        for key, label_text in fields:
            row = ctk.CTkFrame(self._details_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row, text=f"{label_text}:", font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w", width=80,
            ).pack(side="left")
            val_label = ctk.CTkLabel(
                row, text="—", font=ctk.CTkFont(size=12),
                anchor="w", wraplength=180,
            )
            val_label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            self._field_labels[key] = val_label

        sep = ctk.CTkFrame(self._scroll, height=2, fg_color="gray30")
        sep.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            self._scroll, text="Status:", font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(padx=10, anchor="w")
        self._status_menu = ctk.CTkOptionMenu(
            self._scroll, values=LeadStatus.all_values(), width=260,
        )
        self._status_menu.pack(padx=10, pady=4)

        ctk.CTkLabel(
            self._scroll, text="Poznámky:", font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(padx=10, anchor="w", pady=(5, 0))
        self._notes_textbox = ctk.CTkTextbox(self._scroll, height=100, width=260)
        self._notes_textbox.pack(padx=10, pady=4)

        self._save_btn = ctk.CTkButton(
            self._scroll, text="💾 Uložit změny", width=260,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            command=self._handle_save,
        )
        self._save_btn.pack(padx=10, pady=6)

        btn_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=4)

        self._web_btn = ctk.CTkButton(
            btn_row, text="🌐 Otevřít web", width=125,
            fg_color="#6c757d", hover_color="#5a6268",
            command=self._open_website,
        )
        self._web_btn.pack(side="left", padx=(0, 5))

        self._maps_btn = ctk.CTkButton(
            btn_row, text="🗺 Mapy", width=125,
            fg_color="#6c757d", hover_color="#5a6268",
            command=self._open_maps,
        )
        self._maps_btn.pack(side="left")

        self._controls_visible = False
        self._set_controls_visible(False)

    def load_lead(self, lead: Lead) -> None:
        self._current_lead = lead
        self._title_label.configure(text=lead.name)
        self._field_labels["category"].configure(text=lead.category or "—")
        self._field_labels["address"].configure(text=lead.address or "—")
        self._field_labels["city"].configure(text=lead.city or "—")
        self._field_labels["phone"].configure(text=lead.phone or "—")
        self._field_labels["website"].configure(text=lead.website or "—")
        self._field_labels["email"].configure(text=lead.email or "—")
        self._field_labels["rating_display"].configure(text=lead.rating_stars())
        self._field_labels["reviews"].configure(text=str(lead.review_count))
        self._field_labels["scraped"].configure(
            text=lead.scraped_at.strftime("%d.%m.%Y %H:%M") if lead.scraped_at else "—"
        )
        self._status_menu.set(lead.status.value)
        self._notes_textbox.delete("1.0", "end")
        self._notes_textbox.insert("1.0", lead.notes or "")
        self._set_controls_visible(True)

    def clear(self) -> None:
        self._current_lead = None
        self._title_label.configure(text="Vyberte lead ze seznamu")
        for lbl in self._field_labels.values():
            lbl.configure(text="—")
        self._notes_textbox.delete("1.0", "end")
        self._set_controls_visible(False)

    def _set_controls_visible(self, visible: bool) -> None:
        self._controls_visible = visible
        if visible:
            self._save_btn.configure(state="normal")
            self._web_btn.configure(state="normal")
            self._maps_btn.configure(state="normal")
            self._status_menu.configure(state="normal")
            self._notes_textbox.configure(state="normal")
        else:
            self._save_btn.configure(state="disabled")
            self._web_btn.configure(state="disabled")
            self._maps_btn.configure(state="disabled")
            self._status_menu.configure(state="disabled")
            self._notes_textbox.configure(state="disabled")

    def _handle_save(self) -> None:
        if not self._current_lead:
            return
        self._current_lead.status = LeadStatus.from_value(self._status_menu.get())
        self._current_lead.notes = self._notes_textbox.get("1.0", "end").strip()
        self._on_save(self._current_lead)

    def _open_website(self) -> None:
        if self._current_lead and self._current_lead.website:
            url = self._current_lead.website
            if not url.startswith("http"):
                url = "https://" + url
            webbrowser.open(url)

    def _open_maps(self) -> None:
        if self._current_lead and self._current_lead.google_maps_url:
            webbrowser.open(self._current_lead.google_maps_url)
