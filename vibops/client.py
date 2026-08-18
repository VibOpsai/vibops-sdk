"""VibOps SDK clients — async-first with sync wrapper."""

from __future__ import annotations

import asyncio
import functools
from typing import Any

import httpx

from vibops.agents import AgentsResource
from vibops.clusters import ClustersResource
from vibops.compliance import ComplianceResource
from vibops.exceptions import VibOpsError
from vibops.finops import FinOpsResource
from vibops.gateways import GatewaysResource
from vibops.insights import InsightsResource
from vibops.jobs import JobsResource
from vibops.models import ModelsResource
from vibops.security import SecurityResource


class AsyncVibOps:
    """Async VibOps SDK client.

    Usage::

        async with AsyncVibOps(url="https://vibops.example.com", token="vib_...") as v:
            clusters = await v.clusters.list()
    """

    def __init__(self, url: str, token: str, *, timeout: float = 30.0, max_retries: int = 2) -> None:
        if not url:
            raise VibOpsError("url is required")
        if not token:
            raise VibOpsError("token is required")

        self._http = httpx.AsyncClient(
            base_url=url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

        self.clusters = ClustersResource(self._http, max_retries=max_retries)
        self.jobs = JobsResource(self._http, max_retries=max_retries)
        self.gateways = GatewaysResource(self._http, max_retries=max_retries)
        self.models = ModelsResource(self._http, max_retries=max_retries)
        self.finops = FinOpsResource(self._http, max_retries=max_retries)
        self.agents = AgentsResource(self._http, max_retries=max_retries)
        self.security = SecurityResource(self._http, max_retries=max_retries)
        self.compliance = ComplianceResource(self._http, max_retries=max_retries)
        self.insights = InsightsResource(self._http, max_retries=max_retries)

    async def __aenter__(self) -> AsyncVibOps:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()


class _SyncProxy:
    """Wraps an async resource so every method call runs through asyncio.run()."""

    def __init__(self, resource: Any, loop_runner: Any) -> None:
        self._resource = resource
        self._run = loop_runner

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._resource, name)
        if not callable(attr):
            return attr

        @functools.wraps(attr)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._run(attr(*args, **kwargs))

        return wrapper


class VibOps:
    """Synchronous VibOps SDK client.

    Usage::

        with VibOps(url="https://vibops.example.com", token="vib_...") as v:
            clusters = v.clusters.list()
    """

    def __init__(self, url: str, token: str, *, timeout: float = 30.0, max_retries: int = 2) -> None:
        self._async = AsyncVibOps(url, token, timeout=timeout, max_retries=max_retries)
        self._loop: asyncio.AbstractEventLoop | None = None

        run = self._run_sync
        self.clusters = _SyncProxy(self._async.clusters, run)
        self.jobs = _SyncProxy(self._async.jobs, run)
        self.gateways = _SyncProxy(self._async.gateways, run)
        self.models = _SyncProxy(self._async.models, run)
        self.finops = _SyncProxy(self._async.finops, run)
        self.agents = _SyncProxy(self._async.agents, run)
        self.security = _SyncProxy(self._async.security, run)
        self.compliance = _SyncProxy(self._async.compliance, run)
        self.insights = _SyncProxy(self._async.insights, run)

    def _run_sync(self, coro: Any) -> Any:
        """Run a coroutine synchronously, reusing a background event loop."""
        try:
            asyncio.get_running_loop()
            # Already inside an event loop — can't use asyncio.run().
            # Fall back to a thread-based approach.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        except RuntimeError:
            return asyncio.run(coro)

    def __enter__(self) -> VibOps:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._run_sync(self._async.close())
