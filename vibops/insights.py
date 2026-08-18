"""Insights resource — proactive recommendations."""

from __future__ import annotations

from typing import Any, AsyncIterator

from vibops.resources import Resource
from vibops.types import Insight, parse

__all__ = ["InsightsResource"]


class InsightsResource(Resource):
    """Proactive infrastructure insights and recommendations."""

    async def list(
        self,
        *,
        limit: int = 20,
        insight_type: str | None = None,
        severity: str | None = None,
        acknowledged: bool | None = None,
    ) -> list[Insight | dict[str, Any]]:
        """List recent proactive insights."""
        data = await self._get(
            "insights",
            limit=limit,
            insight_type=insight_type,
            severity=severity,
            acknowledged=acknowledged,
        )
        if isinstance(data, list):
            return [parse(Insight, item) for item in data]
        return data

    async def acknowledge(self, insight_id: str) -> dict[str, Any]:
        """Mark an insight as acknowledged."""
        return await self._post(f"insights/{insight_id}/acknowledge")

    async def list_all(
        self,
        *,
        limit: int = 100,
        insight_type: str | None = None,
        severity: str | None = None,
        acknowledged: bool | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Auto-paginating iterator over all insights."""
        async for item in self._paginate(
            "insights",
            limit=limit,
            insight_type=insight_type,
            severity=severity,
            acknowledged=acknowledged,
        ):
            yield item
