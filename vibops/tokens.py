"""Tokens resource — API token management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["TokensResource"]


class TokensResource(Resource):
    """API token operations."""

    async def list(self) -> list[dict[str, Any]]:
        """List all API tokens."""
        data = await self._get("tokens")
        return data.get("tokens", []) if isinstance(data, dict) else data

    async def create(
        self, name: str, *, expires_at: str | None = None,
    ) -> dict[str, Any]:
        """Create a new API token."""
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expires_at"] = expires_at
        return await self._post("tokens", json=body)

    async def delete(
        self, token_id: str, *, confirmed: bool = False,
    ) -> dict[str, Any]:
        """Delete an API token. confirmed=True to execute, else dry-run."""
        return await self._delete(
            f"tokens/{token_id}", confirmed=confirmed,
        )
