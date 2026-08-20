"""Metrics resource — GPU metrics, cost estimates, workload breakdown, MTTR."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["MetricsResource"]


class MetricsResource(Resource):
    """Cross-cluster metrics and analytics."""

    async def gpu(
        self, cluster: str | None = None, *, hours: int = 24,
    ) -> dict[str, Any]:
        """Get GPU utilization metrics, optionally filtered by cluster."""
        return await self._get("metrics/gpu", cluster=cluster, hours=hours)

    async def cost_estimate(self, *, hours: int = 24) -> dict[str, Any]:
        """Get a cost estimate for the current period."""
        return await self._get("metrics/cost", hours=hours)

    async def workload_breakdown(self, *, hours: int = 24) -> dict[str, Any]:
        """Get workload-type breakdown across all clusters."""
        return await self._get("metrics/workloads", hours=hours)

    async def mttr(self, *, hours: int = 168) -> dict[str, Any]:
        """Get mean time to recovery statistics."""
        return await self._get("metrics/mttr", hours=hours)

    async def job_metrics(self, *, hours: int = 24) -> dict[str, Any]:
        """Get aggregate job metrics (success rate, latency)."""
        return await self._get("metrics/jobs", hours=hours)
