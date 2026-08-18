"""Reselling resource — reseller profile, customers, and pricing rules."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["ResellingResource"]


class ResellingResource(Resource):
    """Reseller operations."""

    async def profile(self) -> dict[str, Any]:
        """Get the current reseller profile."""
        return await self._get("resellers/me")

    async def customers(self) -> list[dict[str, Any]]:
        """List all customers for the current reseller."""
        return await self._get("resellers/me/customers")

    async def create_customer(self, name: str, slug: str) -> dict[str, Any]:
        """Create a new customer under the current reseller."""
        return await self._post("resellers/me/customers", json={"name": name, "slug": slug})

    async def pricing_rules(self) -> list[dict[str, Any]]:
        """List pricing rules for the current reseller."""
        return await self._get("resellers/me/pricing-rules")
