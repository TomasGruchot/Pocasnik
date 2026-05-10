from __future__ import annotations

import hashlib
import os

from app.models.user import User
from app.repositories.user_repo import UserRepository


class AuthError(Exception):
    """Chybový stav přihlášení/registrace."""


class AuthService:
    """Hashování hesel (sha256 + náhodná sůl) a basic login/register."""

    _ITERATIONS = 100_000

    def __init__(self, users: UserRepository | None = None) -> None:
        self._users = users or UserRepository()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            AuthService._ITERATIONS,
        )
        return dk.hex()

    @staticmethod
    def _generate_salt() -> str:
        return os.urandom(16).hex()

    def register(self, username: str, password: str, password2: str) -> User:
        if password != password2:
            raise AuthError("Hesla se neshodují.")
        if len(password) < 6:
            raise AuthError("Heslo musí mít alespoň 6 znaků.")
        if self._users.find_by_username(username) is not None:
            raise AuthError("Uživatel s tímto jménem už existuje.")
        salt = self._generate_salt()
        user = User(
            username=username,
            password_hash=self._hash_password(password, salt),
            salt=salt,
        )
        return self._users.save(user)

    def login(self, username: str, password: str) -> User:
        user = self._users.find_by_username(username)
        if user is None:
            raise AuthError("Uživatel nebo heslo nesouhlasí.")
        if self._hash_password(password, user.salt) != user.password_hash:
            raise AuthError("Uživatel nebo heslo nesouhlasí.")
        return user
