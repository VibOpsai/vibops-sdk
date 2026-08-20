"""Pipelines resource — CI/CD pipeline management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["PipelinesResource"]


class PipelinesResource(Resource):
    """Pipeline operations."""

    async def list(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """List pipelines."""
        return await self._get("pipelines", limit=limit)

    async def create(self, name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a new pipeline."""
        return await self._post("pipelines", json={"name": name, "steps": steps})

    async def trigger(
        self, pipeline_id: str, *, payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trigger a pipeline run."""
        return await self._post(
            f"pipelines/{pipeline_id}/trigger", json=payload,
        )
