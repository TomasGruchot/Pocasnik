from __future__ import annotations

import threading
from queue import Empty, Queue

import customtkinter as ctk

from clientradar.core.config_manager import ConfigManager
from clientradar.core.database import DatabaseManager
from clientradar.core.exporter import ExcelExporter
from clientradar.easter_egg.launcher import launch_easter_egg
from clientradar.models.lead import Lead, LeadStatus
from clientradar.models.search_config import SearchConfig
from clientradar.ui.detail_panel import LeadDetailPanel
from clientradar.ui.dialogs import ConfirmDialog, ExportDialog
from clientradar.ui.leads_table import LeadsTable
from clientradar.ui.sidebar import Sidebar
from clientradar.ui.status_bar import StatusBar


class ClientRadarApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("ClientRadar 📡")
        self.geometry("1400x820")
        self.minsize(1100, 650)

        self._db = DatabaseManager("clientradar.db")
        self._config_mgr = ConfigManager("config.json")
        self._exporter = ExcelExporter()
        self._scraper = None
        self._scrape_queue: Queue = Queue()
        self._scrape_thread: threading.Thread | None = None
        self._current_leads: list[Lead] = []
        self._active_filter_query: str = ""
        self._active_status_filter: str = "Vše"

        self._restore_geometry()
        self._build_layout()
        self._load_initial_data()
        self.bind_all("<Control-Shift-G>", self._launch_easter_egg)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def run(self) -> None:
        self.mainloop()

    def _restore_geometry(self) -> None:
        saved = self._config_mgr.get("geometry")
        if saved:
            try:
                self.geometry(saved)
            except Exception:
                pass

    def _save_geometry(self) -> None:
        try:
            self._config_mgr.set("geometry", self.geometry())
        except Exception:
            pass

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(
            self,
            on_start_scraping=self._start_scraping,
            on_stop_scraping=self._stop_scraping,
            on_search_filter=self._on_search_filter,
            on_status_filter=self._on_status_filter,
            on_export=self._on_export,
            on_launch_easter_egg=self._launch_easter_egg,
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._table = LeadsTable(
            self,
            on_select_callback=self._on_lead_selected,
            on_delete_callback=self._on_delete_lead,
            on_status_change_callback=self._on_status_change,
        )
        self._table.grid(row=0, column=1, sticky="nsew", padx=(2, 2))

        self._detail_panel = LeadDetailPanel(
            self,
            on_save=self._on_save_lead,
        )
        self._detail_panel.grid(row=0, column=2, sticky="nsew")

        self._status_bar = StatusBar(self)
        self._status_bar.grid(row=1, column=0, columnspan=3, sticky="ew")

    def _load_initial_data(self) -> None:
        self._current_leads = self._db.get_all_leads()
        self._table.load_leads(self._current_leads)
        self._refresh_stats()
        self._status_bar.show_idle()

    def _refresh_stats(self) -> None:
        stats = self._db.get_stats()
        self._sidebar.refresh_stats(stats)
        self._status_bar.update_stats(stats)

    def _start_scraping(self, config: SearchConfig) -> None:
        from clientradar.core.scraper import GoogleMapsScraper

        self._scrape_queue = Queue()
        self._scraper = GoogleMapsScraper(config, result_queue=self._scrape_queue)

        self._status_bar.set_message("Spouštím scraping…")
        self._status_bar.set_progress(0, 1)

        self._scrape_thread = threading.Thread(
            target=self._run_scraper, daemon=True,
        )
        self._scrape_thread.start()
        self.after(100, self._poll_queue)

    def _run_scraper(self) -> None:
        try:
            self._scraper.search()
        except Exception as exc:
            self._scrape_queue.put(("error", str(exc)))

    def _stop_scraping(self) -> None:
        if self._scraper:
            self._scraper.stop()
        self._sidebar.set_scraping(False)
        self._status_bar.set_message("Scraping zastaven.")
        self._status_bar.hide_progress()

    def _poll_queue(self) -> None:
        done = False
        try:
            while True:
                msg = self._scrape_queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "progress":
                    _, current, total, message = msg
                    if total > 0:
                        self._status_bar.set_progress(current, total)
                    self._status_bar.set_message(message)

                elif msg_type == "result":
                    _, lead = msg
                    saved = self._db.save_lead(lead)
                    if saved:
                        self._current_leads.insert(0, lead)

                elif msg_type == "done":
                    _, total_found = msg
                    self._sidebar.set_scraping(False)
                    self._status_bar.hide_progress()
                    self._status_bar.set_message(
                        f"Hotovo! Nalezeno {total_found} výsledků."
                    )
                    self._apply_filters()
                    self._refresh_stats()
                    done = True

                elif msg_type == "error":
                    _, error_msg = msg
                    self._sidebar.set_scraping(False)
                    self._status_bar.hide_progress()
                    self._status_bar.set_message(f"Chyba: {error_msg[:80]}")
                    done = True

        except Empty:
            pass

        if not done:
            self.after(100, self._poll_queue)

    def _on_lead_selected(self, lead: Lead) -> None:
        self._detail_panel.load_lead(lead)

    def _on_status_change(self, lead: Lead, new_status: LeadStatus) -> None:
        lead.status = new_status
        self._db.update_lead(lead)
        self._table.update_row(lead)
        self._detail_panel.load_lead(lead)
        self._refresh_stats()

    def _on_save_lead(self, lead: Lead) -> None:
        self._db.update_lead(lead)
        self._table.update_row(lead)
        self._refresh_stats()
        self._status_bar.set_message(f"Lead '{lead.name}' uložen.")

    def _on_delete_lead(self, lead: Lead) -> None:
        ConfirmDialog(
            self,
            title="Smazat lead",
            message=f"Opravdu chcete smazat lead '{lead.name}'?",
            on_confirm=lambda: self._do_delete_lead(lead),
        )

    def _do_delete_lead(self, lead: Lead) -> None:
        self._db.delete_lead(lead.id)
        self._current_leads = [l for l in self._current_leads if l.id != lead.id]
        self._apply_filters()
        self._detail_panel.clear()
        self._refresh_stats()
        self._status_bar.set_message(f"Lead '{lead.name}' smazán.")

    def _on_search_filter(self, query: str) -> None:
        self._active_filter_query = query
        self._apply_filters()

    def _on_status_filter(self, status_value: str) -> None:
        self._active_status_filter = status_value
        self._apply_filters()

    def _apply_filters(self) -> None:
        if self._active_filter_query:
            leads = self._db.search_leads(self._active_filter_query)
        else:
            leads = self._db.get_all_leads()

        if self._active_status_filter and self._active_status_filter != "Vše":
            status = LeadStatus.from_value(self._active_status_filter)
            leads = [l for l in leads if l.status == status]

        self._current_leads = leads
        self._table.load_leads(leads)

    def _on_export(self) -> None:
        ExportDialog(self, on_export=self._do_export)

    def _launch_easter_egg(self, _event=None) -> None:
        try:
            launch_easter_egg()
            self._status_bar.set_message("Easter egg launch: NEON BREACH")
        except Exception as exc:
            self._status_bar.set_message(f"Easter egg nelze spustit: {exc}")

    def _do_export(self, filepath: str, scope: str | None) -> None:
        try:
            if scope and scope != "all" and scope != "filtered":
                status = LeadStatus.from_value(scope)
                leads = self._db.get_leads_by_status(status)
            elif scope == "filtered":
                leads = self._current_leads
            else:
                leads = self._db.get_all_leads()

            self._exporter.export(leads, filepath)
            self._status_bar.set_message(f"Exportováno {len(leads)} leadů do {filepath}")
        except Exception as exc:
            self._status_bar.set_message(f"Chyba exportu: {exc}")

    def _on_closing(self) -> None:
        self._save_geometry()
        if self._scraper:
            self._scraper.stop()
            self._scraper.close()
        self._db.close()
        self.destroy()
