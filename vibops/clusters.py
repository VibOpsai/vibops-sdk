"""Clusters resource."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource
from vibops.types import Cluster, parse

__all__ = ["ClustersResource"]


class ClustersResource(Resource):
    """Operations on GPU clusters."""

    async def list(self) -> list[Cluster | dict[str, Any]]:
        """List all clusters registered in VibOps."""
        data = await self._get("clusters")
        if isinstance(data, list):
            return [parse(Cluster, item) for item in data]
        return data

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
