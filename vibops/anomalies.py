"""Anomalies resource — GPU anomaly detection and resolution."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["AnomaliesResource"]


class AnomaliesResource(Resource):
    """GPU anomaly operations."""

    async def list(
        self,
        *,
        cluster: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List anomalies with optional filters."""
        return await self._get("anomalies", cluster=cluster, status=status)

    async def open(self) -> list[dict[str, Any]]:
        """List currently open (unresolved) anomalies."""
        return await self._get("anomalies/open")

    async def resolve(self, anomaly_id: str, *, reason: str | None = None) -> dict[str, Any]:
        """Resolve an anomaly."""
        body: dict[str, Any] = {}
        if reason is not None:
            body["reason"] = reason
        return await self._post(f"anomalies/{anomaly_id}/resolve", json=body or None)
