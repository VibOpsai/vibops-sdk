"""Webhooks resource — webhook subscription management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["WebhooksResource"]


class WebhooksResource(Resource):
    """Webhook subscription operations."""

    async def subscriptions(self) -> list[dict[str, Any]]:
        """List all webhook subscriptions."""
        data = await self._get("webhooks/subscriptions")
        return data.get("items", []) if isinstance(data, dict) else data

    async def create_subscription(
        self,
        repo: str,
        *,
        branch: str = "main",
        action: str = "deploy_model",
    ) -> dict[str, Any]:
        """Create a new webhook subscription."""
        return await self._post("webhooks/subscriptions", json={
            "repo": repo,
            "branch": branch,
            "action": action,
        })

    async def delete_subscription(self, sub_id: str) -> dict[str, Any]:
        """Delete a webhook subscription."""
        return await self._delete(f"webhooks/subscriptions/{sub_id}")
