from __future__ import annotations

import customtkinter as ctk

from app.views.base_view import BaseView
from app.views.theme import (
    BG,
    CARD,
    CARD_BORDER,
    CARD_HOVER,
    FONT,
    FONT_EMOJI,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
)


class LoginView(BaseView):
    """Přihlašovací obrazovka – frosted-glass šedá paleta."""

    def build(self) -> None:
        self.configure(fg_color=BG)

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            wrapper,
            text="🌤️",
            font=ctk.CTkFont(family=FONT_EMOJI, size=44),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="POČASNÍK",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=30, weight="bold"),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="Přihlaš se a sleduj počasí svých měst.",
            text_color=TEXT_DIM,
            font=ctk.CTkFont(family=FONT, size=13),
        ).pack(pady=(0, 24))

        self._add_field(
            wrapper,
            label="Uživatelské jméno",
            placeholder="např. petr_novak",
            attr="_username",
        )
        self._add_field(
            wrapper,
            label="Heslo",
            placeholder="zadej své heslo",
            attr="_password",
            secret=True,
        )
        self._password.bind("<Return>", lambda _e: self._do_login())

        self._error = ctk.CTkLabel(
            wrapper,
            text="",
            text_color="#D88A8A",
            font=ctk.CTkFont(family=FONT, size=12),
        )
        self._error.pack(pady=(8, 0))

        ctk.CTkButton(
            wrapper,
            text="Přihlásit",
            width=300,
            height=42,
            corner_radius=12,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_color=CARD_BORDER,
            border_width=1,
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
            command=self._do_login,
        ).pack(pady=(14, 6))

        ctk.CTkButton(
            wrapper,
            text="Nemám účet — registrovat se",
            width=300,
            height=38,
            corner_radius=12,
            fg_color="transparent",
            border_width=1,
            border_color=CARD_BORDER,
            text_color=TEXT_DIM,
            font=ctk.CTkFont(family=FONT, size=13),
            command=lambda: self.app.show("register"),
        ).pack()

    def _add_field(
        self,
        parent: ctk.CTkBaseClass,
        *,
        label: str,
        placeholder: str,
        attr: str,
        secret: bool = False,
    ) -> None:
        ctk.CTkLabel(
            parent,
            text=label,
            anchor="w",
            text_color=TEXT_FAINT,
            font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
        ).pack(fill="x", padx=2, pady=(8, 2))
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=300,
            height=40,
            corner_radius=10,
            border_width=1,
            border_color=CARD_BORDER,
            fg_color=CARD,
            font=ctk.CTkFont(family=FONT, size=13),
            show="•" if secret else "",
        )
        entry.pack()
        setattr(self, attr, entry)

    def on_show(self) -> None:
        self._error.configure(text="")
        self._username.delete(0, "end")
        self._password.delete(0, "end")
        self._username.focus_set()

    def _do_login(self) -> None:
        try:
            user = self.app.auth_vm.login(
                self._username.get(), self._password.get()
            )
        except Exception as e:
            self._error.configure(text=str(e))
            return
        self.app.on_user_logged_in(user)
