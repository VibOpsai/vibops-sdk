"""Secrets resource — secret management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["SecretsResource"]


class SecretsResource(Resource):
    """Secret management operations."""

    async def list(self) -> list[dict[str, Any]]:
        """List all secrets (names only, no values)."""
        return await self._get("secrets")

    async def create(
        self,
        name: str,
        value: str,
        *,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new secret."""
        body: dict[str, Any] = {"name": name, "value": value}
        if description is not None:
            body["description"] = description
        return await self._post("secrets", json=body)

    async def delete(self, name: str) -> dict[str, Any]:
        """Delete a secret by name."""
        return await self._delete(f"secrets/{name}")
