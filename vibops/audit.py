"""Audit resource — audit log queries and chain verification."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["AuditResource"]


class AuditResource(Resource):
    """Audit log operations."""

    async def list(
        self,
        *,
        limit: int = 100,
        action: str | None = None,
        user: str | None = None,
    ) -> list[dict[str, Any]]:
        """List audit log entries."""
        return await self._get("audit", limit=limit, action=action, user=user)

    async def verify_chain(self) -> dict[str, Any]:
        """Verify the integrity of the audit log hash chain."""
        return await self._get("audit/verify")

    async def export(self, format: str = "json") -> dict[str, Any]:
        """Export audit logs in the specified format."""
        return await self._get("audit/export", format=format)
