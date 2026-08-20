"""GPU Health resource — predictive GPU health analysis."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["GpuHealthResource"]


class GpuHealthResource(Resource):
    """GPU health prediction operations."""

    async def predictions(self, *, cluster: str | None = None) -> list[dict[str, Any]]:
        """Get GPU health predictions."""
        data = await self._get("gpu/health-predictions", cluster=cluster)
        if isinstance(data, dict):
            return data.get("warnings", [])
        return data
