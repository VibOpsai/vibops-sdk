"""Identities resource — agent identity (machine key) management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["IdentitiesResource"]


class IdentitiesResource(Resource):
    """Agent identity operations."""

    async def list(self) -> list[dict[str, Any]]:
        """List all agent identities."""
        data = await self._get("agent-identities")
        return data.get("items", []) if isinstance(data, dict) else data

    async def create(
        self, name: str, *, expires_at: str | None = None,
    ) -> dict[str, Any]:
        """Create a new agent identity. The key is returned only once."""
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expires_at"] = expires_at
        return await self._post("agent-identities", json=body)

    async def rotate(self, identity_id: str) -> dict[str, Any]:
        """Rotate the key for an agent identity."""
        return await self._post(f"agent-identities/{identity_id}/rotate")

    async def revoke(self, identity_id: str) -> dict[str, Any]:
        """Revoke an agent identity."""
        return await self._post(f"agent-identities/{identity_id}/revoke")
