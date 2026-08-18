"""Security resource — scans and findings."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource


class SecurityResource(Resource):
    """Security scanning and findings."""

    async def scan(self) -> dict[str, Any]:
        """Trigger an on-demand security scan."""
        return await self._post("security/scan")

    async def findings(
        self,
        *,
        severity: str | None = None,
        scan_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List security scan findings."""
        return await self._get(
            "security/findings",
            severity=severity,
            scan_id=scan_id,
            limit=limit,
        )
