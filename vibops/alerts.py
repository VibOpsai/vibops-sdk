"""Alerts resource — alert listing and alert-rule management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["AlertsResource"]


class AlertsResource(Resource):
    """Alert and alert-rule operations."""

    async def list(
        self,
        *,
        cluster: str | None = None,
        severity: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """List alert history with optional filters."""
        return await self._get(
            "alert-history",
            cluster=cluster,
            severity=severity,
            limit=limit,
        )

    async def rules(self) -> list[dict[str, Any]]:
        """List all alert rules."""
        return await self._get("alert-rules")

    async def create_rule(
        self,
        cluster_name: str = "*",
        *,
        warn_pct: int = 80,
        crit_pct: int = 95,
        cooldown_secs: int = 300,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a new alert rule."""
        return await self._post("alert-rules", json={
            "cluster_name": cluster_name,
            "warn_pct": warn_pct,
            "crit_pct": crit_pct,
            "cooldown_secs": cooldown_secs,
            "enabled": enabled,
        })

    async def delete_rule(
        self, rule_id: str, *, confirmed: bool = False,
    ) -> dict[str, Any]:
        """Delete an alert rule. confirmed=True to execute, else dry-run."""
        return await self._delete(
            f"alert-rules/{rule_id}", confirmed=confirmed,
        )
