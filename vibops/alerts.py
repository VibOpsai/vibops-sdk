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
        severity: str | None = None,
        resolved: bool | None = None,
    ) -> list[dict[str, Any]]:
        """List alerts with optional filters."""
        return await self._get("alerts", severity=severity, resolved=resolved)

    async def rules(self) -> list[dict[str, Any]]:
        """List all alert rules."""
        return await self._get("alert-rules")

    async def create_rule(
        self,
        name: str,
        condition: str,
        action: str,
        *,
        severity: str | None = None,
        cooldown_minutes: int | None = None,
    ) -> dict[str, Any]:
        """Create a new alert rule."""
        body: dict[str, Any] = {"name": name, "condition": condition, "action": action}
        if severity is not None:
            body["severity"] = severity
        if cooldown_minutes is not None:
            body["cooldown_minutes"] = cooldown_minutes
        return await self._post("alert-rules", json=body)

    async def delete_rule(self, rule_id: str) -> dict[str, Any]:
        """Delete an alert rule."""
        return await self._delete(f"alert-rules/{rule_id}")
