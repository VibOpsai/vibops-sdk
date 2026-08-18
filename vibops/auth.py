"""Auth resource — login, token refresh, password reset."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["AuthResource"]


class AuthResource(Resource):
    """Authentication operations."""

    async def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate and obtain an access token."""
        return await self._post("auth/login", json={"username": username, "password": password})

    async def me(self) -> dict[str, Any]:
        """Get the current authenticated user profile."""
        return await self._get("auth/me")

    async def refresh(self) -> dict[str, Any]:
        """Refresh the current access token."""
        return await self._post("auth/refresh")

    async def forgot_password(self, email: str) -> dict[str, Any]:
        """Request a password reset email."""
        return await self._post("auth/forgot-password", json={"email": email})

    async def reset_password(self, token: str, new_password: str) -> dict[str, Any]:
        """Reset password using a reset token."""
        return await self._post("auth/reset-password", json={"token": token, "new_password": new_password})
