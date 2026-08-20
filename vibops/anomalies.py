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
        anomaly_type: str | None = None,
        severity: str | None = None,
        open_only: bool | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """List anomalies with optional filters."""
        return await self._get(
            "anomalies",
            cluster=cluster,
            anomaly_type=anomaly_type,
            severity=severity,
            open_only=open_only,
            limit=limit,
        )

    async def open(self) -> list[dict[str, Any]]:
        """List currently open (unresolved) anomalies."""
        return await self._get("anomalies/open")

    async def resolve(self, anomaly_id: str) -> dict[str, Any]:
        """Resolve an anomaly."""
        return await self._post(f"anomalies/{anomaly_id}/resolve")
