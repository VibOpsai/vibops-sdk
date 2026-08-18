"""Metrics resource — GPU metrics, cost estimates, workload breakdown, MTTR."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["MetricsResource"]


class MetricsResource(Resource):
    """Cross-cluster metrics and analytics."""

    async def gpu(self, cluster: str, *, hours: int = 24) -> list[dict[str, Any]]:
        """Get GPU utilization metrics for a cluster."""
        return await self._get("gpu-metrics", cluster=cluster, hours=hours)

    async def cost_estimate(self, *, hours: int = 24) -> dict[str, Any]:
        """Get a cost estimate for the current period."""
        return await self._get("cost-estimate", hours=hours)

    async def workload_breakdown(self) -> dict[str, Any]:
        """Get workload-type breakdown across all clusters."""
        return await self._get("workload-breakdown")

    async def mttr(self) -> dict[str, Any]:
        """Get mean time to recovery statistics."""
        return await self._get("mttr")

    async def job_metrics(self) -> dict[str, Any]:
        """Get aggregate job metrics (success rate, latency)."""
        return await self._get("metrics/jobs")
