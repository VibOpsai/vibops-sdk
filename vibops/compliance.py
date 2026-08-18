"""Compliance resource — checks and results."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["ComplianceResource"]


class ComplianceResource(Resource):
    """SOC 2 compliance checks and reporting."""

    async def check(self) -> dict[str, Any]:
        """Trigger an on-demand compliance check."""
        return await self._post("compliance/check")

    async def results(
        self,
        *,
        control_id: str | None = None,
        check_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List compliance check results."""
        return await self._get(
            "compliance/check/results",
            control_id=control_id,
            check_id=check_id,
            status=status,
            limit=limit,
        )
