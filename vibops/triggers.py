"""Triggers resource — automated trigger management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["TriggersResource"]


class TriggersResource(Resource):
    """Automated trigger operations."""

    async def list(self) -> list[dict[str, Any]]:
        """List all triggers."""
        data = await self._get("triggers")
        return data.get("items", []) if isinstance(data, dict) else data

    async def create(
        self,
        name: str,
        metric: str,
        condition: str,
        threshold: float,
        action: str,
        *,
        payload: dict[str, Any] | None = None,
        cooldown_minutes: int = 10,
        source: str = "datadog",
        prometheus_url: str | None = None,
    ) -> dict[str, Any]:
        """Create a new trigger.

        Args:
            name: Human-readable trigger name.
            metric: Datadog query or PromQL expression.
            condition: Comparison operator (``"gt"``/``"lt"``/``"gte"``/``"lte"``).
            threshold: Numeric threshold for the condition.
            action: Action to run when triggered (e.g. ``"scale_cluster"``).
            payload: Base payload passed to the triggered job.
            cooldown_minutes: Min minutes between consecutive firings (0=off).
            source: Metric source — ``"datadog"`` or ``"prometheus"``.
            prometheus_url: Required when *source* is ``"prometheus"``.
        """
        body: dict[str, Any] = {
            "name": name,
            "metric": metric,
            "condition": condition,
            "threshold": threshold,
            "action": action,
            "cooldown_minutes": cooldown_minutes,
            "source": source,
        }
        if payload is not None:
            body["payload"] = payload
        if prometheus_url is not None:
            body["prometheus_url"] = prometheus_url
        return await self._post("triggers", json=body)

    async def enable(self, trigger_id: str) -> dict[str, Any]:
        """Enable a trigger."""
        return await self._post(f"triggers/{trigger_id}/enable")

    async def disable(self, trigger_id: str) -> dict[str, Any]:
        """Disable a trigger."""
        return await self._post(f"triggers/{trigger_id}/disable")

    async def delete(self, trigger_id: str) -> dict[str, Any]:
        """Delete a trigger."""
        return await self._delete(f"triggers/{trigger_id}")
