"""Agents resource — usage tracking and budget management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["AgentsResource"]


class AgentsResource(Resource):
    """Agent inference usage and budget controls."""

    async def usage(
        self,
        *,
        period: str = "30d",
        agent_id: str | None = None,
        team: str | None = None,
        model: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get aggregated inference usage per agent."""
        return await self._get(
            "finops/agent-usage",
            period=period,
            agent_id=agent_id,
            team=team,
            model=model,
        )

    async def usage_detail(
        self, agent_id: str, *, period: str = "30d",
    ) -> dict[str, Any]:
        """Get detailed usage for a single agent."""
        return await self._get(f"finops/agent-usage/{agent_id}", period=period)

    async def budget(self, agent_id: str) -> dict[str, Any]:
        """Get budget + MTD spend for a single agent."""
        return await self._get(f"finops/agent-budgets/{agent_id}")

    async def set_budget(
        self,
        agent_id: str,
        monthly_limit_usd: float,
        *,
        soft_cap_pct: float = 80.0,
        hard_cap_pct: float = 100.0,
        action: str = "reject",
    ) -> dict[str, Any]:
        """Create or update an agent budget."""
        return await self._post(
            "finops/agent-budgets",
            json={
                "agent_id": agent_id,
                "monthly_limit_usd": monthly_limit_usd,
                "soft_cap_pct": soft_cap_pct,
                "hard_cap_pct": hard_cap_pct,
                "action": action,
            },
        )

    async def list_budgets(self) -> list[dict[str, Any]]:
        """List all active agent budgets."""
        return await self._get("finops/agent-budgets")
