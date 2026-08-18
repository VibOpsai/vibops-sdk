"""Notifications resource — notification channel management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["NotificationsResource"]


class NotificationsResource(Resource):
    """Notification channel operations."""

    async def channels(self) -> list[dict[str, Any]]:
        """List all notification channels."""
        return await self._get("notifications/channels")

    async def create_channel(
        self,
        name: str,
        channel_type: str,
        url: str,
    ) -> dict[str, Any]:
        """Create a new notification channel."""
        return await self._post(
            "notifications/channels",
            json={"name": name, "type": channel_type, "url": url},
        )

    async def delete_channel(self, channel_id: str) -> dict[str, Any]:
        """Delete a notification channel."""
        return await self._delete(f"notifications/channels/{channel_id}")

    async def test_channel(self, channel_id: str) -> dict[str, Any]:
        """Send a test notification to a channel."""
        return await self._post(f"notifications/channels/{channel_id}/test")
