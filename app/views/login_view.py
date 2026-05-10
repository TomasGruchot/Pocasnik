from __future__ import annotations

import customtkinter as ctk

from app.views.base_view import BaseView


_FONT = "Segoe UI"
_FONT_EMOJI = "Segoe UI Emoji"
_BG = "#0E1521"
_TEXT_DIM = "#9AA4B8"
_TEXT_FAINT = "#5C6477"


class LoginView(BaseView):
    """Přihlašovací obrazovka."""

    def build(self) -> None:
        self.configure(fg_color=_BG)

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            wrapper,
            text="🌤️",
            font=ctk.CTkFont(family=_FONT_EMOJI, size=44),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="POČASNÍK",
            font=ctk.CTkFont(family=_FONT, size=30, weight="bold"),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="Přihlaš se a sleduj počasí svých měst.",
            text_color=_TEXT_DIM,
            font=ctk.CTkFont(family=_FONT, size=13),
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
            text_color="#F87171",
            font=ctk.CTkFont(family=_FONT, size=12),
        )
        self._error.pack(pady=(8, 0))

        ctk.CTkButton(
            wrapper,
            text="Přihlásit",
            width=300,
            height=42,
            corner_radius=12,
            font=ctk.CTkFont(family=_FONT, size=14, weight="bold"),
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
            text_color=_TEXT_DIM,
            font=ctk.CTkFont(family=_FONT, size=13),
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
            text_color=_TEXT_FAINT,
            font=ctk.CTkFont(family=_FONT, size=12, weight="bold"),
        ).pack(fill="x", padx=2, pady=(8, 2))
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=300,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family=_FONT, size=13),
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
