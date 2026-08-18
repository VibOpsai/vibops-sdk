"""Models resource — deploy and scale inference models."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource
from vibops.types import Job, parse

__all__ = ["ModelsResource"]


class ModelsResource(Resource):
    """Deploy and scale AI models on GPU clusters."""

    async def deploy(
        self,
        model: str,
        cluster: str,
        *,
        namespace: str = "inference",
        replicas: int = 1,
        gateway_id: str | None = None,
        gpu_type: str | None = None,
        image: str | None = None,
        env: dict[str, str] | None = None,
    ) -> Job | dict[str, Any]:
        """Deploy a model. Returns the created job."""
        payload: dict[str, Any] = {
            "model": model,
            "cluster": cluster,
            "namespace": namespace,
            "replicas": replicas,
        }
        if gpu_type is not None:
            payload["gpu_type"] = gpu_type
        if image is not None:
            payload["image"] = image
        if env is not None:
            payload["env"] = env
        body: dict[str, Any] = {
            "action": "deploy_model",
            "payload": payload,
            "triggered_by": "sdk",
        }
        if gateway_id is not None:
            body["gateway_id"] = gateway_id
        data = await self._post("jobs", json=body)
        return parse(Job, data)

    async def scale(
        self,
        name: str,
        namespace: str,
        replicas: int,
        cluster: str,
        *,
        gateway_id: str | None = None,
    ) -> Job | dict[str, Any]:
        """Scale a model deployment. Returns the created job."""
        payload = {
            "name": name,
            "namespace": namespace,
            "replicas": replicas,
            "cluster": cluster,
        }
        body: dict[str, Any] = {
            "action": "scale_deployment",
            "payload": payload,
            "triggered_by": "sdk",
        }
        if gateway_id is not None:
            body["gateway_id"] = gateway_id
        data = await self._post("jobs", json=body)
        return parse(Job, data)
