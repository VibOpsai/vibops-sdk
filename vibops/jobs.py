"""Jobs resource."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource


class JobsResource(Resource):
    """Operations on VibOps jobs."""

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        action: str | None = None,
        triggered_by: str | None = None,
        gateway_id: str | None = None,
    ) -> dict[str, Any]:
        """List jobs with optional filters. Returns {items, total}."""
        return await self._get(
            "jobs",
            limit=limit,
            offset=offset,
            status=status,
            action=action,
            triggered_by=triggered_by,
            gateway_id=gateway_id,
        )

    async def get(self, job_id: str) -> dict[str, Any]:
        """Get a single job by ID."""
        return await self._get(f"jobs/{job_id}")

    async def create(
        self,
        action: str,
        *,
        payload: dict[str, Any] | None = None,
        triggered_by: str = "sdk",
        gateway_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new job."""
        body: dict[str, Any] = {"action": action, "triggered_by": triggered_by}
        if payload is not None:
            body["payload"] = payload
        if gateway_id is not None:
            body["gateway_id"] = gateway_id
        return await self._post("jobs", json=body)

    async def cancel(self, job_id: str) -> dict[str, Any]:
        """Cancel a running job."""
        return await self._post(f"jobs/{job_id}/cancel")
