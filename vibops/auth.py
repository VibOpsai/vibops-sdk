"""Auth resource — login, token refresh, password reset."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["AuthResource"]


class AuthResource(Resource):
    """Authentication operations."""

    async def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate and obtain an access token."""
        return await self._post(
            "auth/login",
            json={"username": username, "password": password},
        )

    async def me(self) -> dict[str, Any]:
        """Get the current authenticated user profile."""
        return await self._get("auth/me")

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Refresh the current access token."""
        return await self._post("auth/refresh", json={"refresh_token": refresh_token})

    async def forgot_password(self, username_or_email: str) -> dict[str, Any]:
        """Request a password reset email."""
        return await self._post(
            "auth/forgot-password",
            json={"username_or_email": username_or_email},
        )

    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset password using a reset token."""
        await self._post(
            "auth/reset-password",
            json={"token": token, "new_password": new_password},
        )
