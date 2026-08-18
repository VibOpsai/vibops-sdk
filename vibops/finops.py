"""FinOps resource — budgets, spend, chargeback, waste."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource
from vibops.types import Budget, parse

__all__ = ["FinOpsResource"]


class FinOpsResource(Resource):
    """GPU cost management and FinOps analytics."""

    async def budget(self) -> Budget | dict[str, Any] | None:
        """Get the active budget and current month spend."""
        data = await self._get("finops/budget")
        if data is None:
            return None
        return parse(Budget, data)

    async def spend_trend(self) -> list[dict[str, Any]]:
        """Get monthly spend trend (last 12 months)."""
        return await self._get("finops/spend/trend")

    async def chargeback(self, year: int | None = None, month: int | None = None) -> Any:
        """Get chargeback reports. If year/month given, returns a single report."""
        if year is not None and month is not None:
            return await self._get(f"finops/chargeback/{year}/{month}")
        return await self._get("finops/chargeback")

    async def waste(self, *, sustained_hours: int = 0) -> dict[str, Any]:
        """Get GPU waste analysis."""
        return await self._get("finops/waste", sustained_hours=sustained_hours)

    async def live_cost(self) -> list[dict[str, Any]]:
        """Get real-time cost attribution per running workload."""
        return await self._get("finops/workloads/live-cost")
