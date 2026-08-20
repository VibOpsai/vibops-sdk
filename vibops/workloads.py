"""Workloads resource — workload inventory and cost summary."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["WorkloadsResource"]


class WorkloadsResource(Resource):
    """Workload operations."""

    async def list(
        self,
        *,
        cluster_name: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List workloads with optional filters."""
        data = await self._get("workloads", cluster_name=cluster_name, status=status)
        if isinstance(data, dict):
            return data.get("workloads", [])
        return data

    async def get(self, workload_id: str) -> dict[str, Any]:
        """Get a single workload by ID."""
        return await self._get(f"workloads/{workload_id}")

    async def cost_summary(self, *, cluster_name: str) -> dict[str, Any]:
        """Get workload cost summary for a cluster."""
        return await self._get("workloads/cost-summary", cluster_name=cluster_name)
