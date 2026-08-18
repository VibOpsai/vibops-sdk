"""Gateways resource."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["GatewaysResource"]


class GatewaysResource(Resource):
    """Operations on VibOps Connect gateways."""

    async def list(self) -> list[dict[str, Any]]:
        """List all gateways."""
        return await self._get("gateways")

    async def register(
        self,
        name: str,
        *,
        clusters: list[str] | None = None,
        description: str | None = None,
        gateway_type: str = "kubernetes",
        prometheus_url: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Register a new gateway. Returns gateway info including the API key (shown once)."""
        body: dict[str, Any] = {"name": name, "gateway_type": gateway_type}
        if clusters is not None:
            body["clusters"] = clusters
        if description is not None:
            body["description"] = description
        if prometheus_url is not None:
            body["prometheus_url"] = prometheus_url
        if labels is not None:
            body["labels"] = labels
        return await self._post("gateways", json=body)

    async def delete(self, gateway_id: str, *, confirmed: bool = True) -> dict[str, Any]:
        """Delete (revoke) a gateway."""
        return await self._delete(f"gateways/{gateway_id}", confirmed=confirmed)
