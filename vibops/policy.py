"""Policy resource — policy and agent model-rule management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["PolicyResource"]


class PolicyResource(Resource):
    """Policy and agent model-rule operations."""

    async def get(self) -> dict[str, Any]:
        """Get the current policy document."""
        return await self._get("policy")

    async def update(self, policy_yaml: str) -> dict[str, Any]:
        """Update the policy document."""
        return await self._put("policy", json={"yaml_text": policy_yaml})

    async def model_rules(self) -> list[dict[str, Any]]:
        """List agent model rules."""
        data = await self._get("policy/agent-model-rules")
        return data.get("rules", []) if isinstance(data, dict) else data

    async def create_model_rule(
        self,
        agent_id_pattern: str,
        *,
        allowed_models: list[str] | None = None,
        denied_models: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new agent model rule."""
        body: dict[str, Any] = {"agent_id_pattern": agent_id_pattern}
        if allowed_models is not None:
            body["allowed_models"] = allowed_models
        if denied_models is not None:
            body["denied_models"] = denied_models
        return await self._post("policy/agent-model-rules", json=body)
