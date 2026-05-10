from __future__ import annotations

from app.models.user import User
from app.services.auth_service import AuthError, AuthService


class AuthViewModel:
    """ViewModel pro přihlašovací a registrační obrazovku.

    Drží referenci na přihlášeného uživatele, vystavuje `login()` a
    `register()` metody pro Views. Žádné UI neimportuje.
    """

    def __init__(self, auth: AuthService | None = None) -> None:
        self._auth = auth or AuthService()
        self._current_user: User | None = None

    @property
    def current_user(self) -> User | None:
        return self._current_user

    def login(self, username: str, password: str) -> User:
        user = self._auth.login(username.strip(), password)
        self._current_user = user
        return user

    def register(self, username: str, password: str, password2: str) -> User:
        user = self._auth.register(username.strip(), password, password2)
        self._current_user = user
        return user

    def logout(self) -> None:
        self._current_user = None

    @staticmethod
    def is_auth_error(exc: Exception) -> bool:
        return isinstance(exc, AuthError)
