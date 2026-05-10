from __future__ import annotations

import customtkinter as ctk

from app.views.base_view import BaseView


class RegisterView(BaseView):
    """Registrační obrazovka."""

    def build(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            wrapper, text="Vytvořit účet", font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="3–32 znaků (a–z, A–Z, 0–9, _), heslo min. 6 znaků.",
            text_color="#9CA3AF",
        ).pack(pady=(0, 20))

        self._username = ctk.CTkEntry(
            wrapper, placeholder_text="Uživatelské jméno", width=280, height=38
        )
        self._username.pack(pady=6)

        self._password = ctk.CTkEntry(
            wrapper, placeholder_text="Heslo", show="•", width=280, height=38
        )
        self._password.pack(pady=6)

        self._password2 = ctk.CTkEntry(
            wrapper, placeholder_text="Heslo znovu", show="•", width=280, height=38
        )
        self._password2.pack(pady=6)
        self._password2.bind("<Return>", lambda _e: self._do_register())

        self._error = ctk.CTkLabel(wrapper, text="", text_color="#F87171")
        self._error.pack(pady=(6, 0))

        ctk.CTkButton(
            wrapper,
            text="Zaregistrovat",
            width=280,
            height=40,
            command=self._do_register,
        ).pack(pady=(16, 6))

        ctk.CTkButton(
            wrapper,
            text="Zpět na přihlášení",
            width=280,
            height=36,
            fg_color="transparent",
            border_width=1,
            command=lambda: self.app.show("login"),
        ).pack()

    def on_show(self) -> None:
        self._error.configure(text="")
        for entry in (self._username, self._password, self._password2):
            entry.delete(0, "end")
        self._username.focus_set()

    def _do_register(self) -> None:
        try:
            user = self.app.auth_vm.register(
                self._username.get(),
                self._password.get(),
                self._password2.get(),
            )
        except Exception as e:
            self._error.configure(text=str(e))
            return
        self.app.on_user_logged_in(user)
