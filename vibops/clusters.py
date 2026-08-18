"""Clusters resource."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource


class ClustersResource(Resource):
    """Operations on GPU clusters."""

    async def list(self) -> list[dict[str, Any]]:
        """List all clusters registered in VibOps."""
        return await self._get("clusters")

    async def deployments(
        self,
        cluster: str,
        *,
        namespace: str | None = None,
    ) -> list[dict[str, Any]]:
        """List deployments for a cluster."""
        return await self._get(
            f"clusters/{cluster}/deployments",
            namespace=namespace,
        )

    async def gpu_metrics(self, cluster: str) -> dict[str, Any]:
        """Get GPU metrics for a cluster (top workloads)."""
        return await self._get(f"clusters/{cluster}/gpu-metrics/top")
