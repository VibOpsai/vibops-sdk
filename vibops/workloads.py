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
        cluster: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List workloads with optional filters."""
        return await self._get("workloads", cluster=cluster, status=status)

    async def get(self, workload_id: str) -> dict[str, Any]:
        """Get a single workload by ID."""
        return await self._get(f"workloads/{workload_id}")

    async def cost_summary(self, *, cluster: str | None = None) -> dict[str, Any]:
        """Get workload cost summary."""
        return await self._get("workloads/cost-summary", cluster=cluster)
