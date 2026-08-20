"""Eval resource — evaluation rubrics and job quality scoring."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["EvalResource"]


class EvalResource(Resource):
    """Evaluation and quality scoring operations."""

    async def rubrics(self) -> list[dict[str, Any]]:
        """List all evaluation rubrics."""
        return await self._get("eval/rubrics")

    async def create_rubric(self, name: str, criteria: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a new evaluation rubric."""
        return await self._post("eval/rubrics", json={"name": name, "criteria": criteria})

    async def evaluate(self, job_id: str, rubric_id: str) -> dict[str, Any]:
        """Evaluate a job against a rubric."""
        return await self._post(f"eval/jobs/{job_id}/evaluate", json={"rubric_id": rubric_id})

    async def results(self, job_id: str) -> list[dict[str, Any]]:
        """Get evaluation results for a job."""
        return await self._get(f"eval/jobs/{job_id}/evaluations")
