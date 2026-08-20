"""Triggers resource — automated trigger management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["TriggersResource"]


class TriggersResource(Resource):
    """Automated trigger operations."""

    async def list(self) -> list[dict[str, Any]]:
        """List all triggers."""
        return await self._get("triggers")

    async def create(
        self,
        name: str,
        condition: str,
        action: str,
        *,
        cooldown_minutes: int = 15,
    ) -> dict[str, Any]:
        """Create a new trigger."""
        return await self._post("triggers", json={
            "name": name,
            "condition": condition,
            "action": action,
            "cooldown_minutes": cooldown_minutes,
        })

    async def enable(self, trigger_id: str) -> dict[str, Any]:
        """Enable a trigger."""
        return await self._post(f"triggers/{trigger_id}/enable")

    async def disable(self, trigger_id: str) -> dict[str, Any]:
        """Disable a trigger."""
        return await self._post(f"triggers/{trigger_id}/disable")

    async def delete(self, trigger_id: str) -> dict[str, Any]:
        """Delete a trigger."""
        return await self._delete(f"triggers/{trigger_id}")
