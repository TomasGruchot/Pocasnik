from __future__ import annotations

import customtkinter as ctk

from app.views.base_view import BaseView


class LoginView(BaseView):
    """Přihlašovací obrazovka."""

    def build(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            wrapper,
            text="POČASNÍK",
            font=ctk.CTkFont(size=32, weight="bold"),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="Přihlaš se a sleduj počasí svých měst.",
            text_color="#9CA3AF",
        ).pack(pady=(0, 24))

        self._username = ctk.CTkEntry(
            wrapper, placeholder_text="Uživatelské jméno", width=280, height=38
        )
        self._username.pack(pady=6)

        self._password = ctk.CTkEntry(
            wrapper, placeholder_text="Heslo", show="•", width=280, height=38
        )
        self._password.pack(pady=6)
        self._password.bind("<Return>", lambda _e: self._do_login())

        self._error = ctk.CTkLabel(wrapper, text="", text_color="#F87171")
        self._error.pack(pady=(6, 0))

        ctk.CTkButton(
            wrapper, text="Přihlásit", width=280, height=40, command=self._do_login
        ).pack(pady=(16, 6))

        ctk.CTkButton(
            wrapper,
            text="Vytvořit účet",
            width=280,
            height=36,
            fg_color="transparent",
            border_width=1,
            command=lambda: self.app.show("register"),
        ).pack()

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
