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

    def __init__(
        self,
        url: str,
        token: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_statuses: set[int] | None = None,
        event_hooks: dict[str, list[Any]] | None = None,
    ) -> None:
        if not url:
            raise VibOpsError("url is required")
        if not token:
            raise VibOpsError("token is required")

        self._http = httpx.AsyncClient(
            base_url=url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            event_hooks=event_hooks or {},
        )

        resource_kwargs: dict[str, Any] = {"max_retries": max_retries}
        if retry_statuses is not None:
            resource_kwargs["retry_statuses"] = retry_statuses

        self.clusters = ClustersResource(self._http, **resource_kwargs)
        self.jobs = JobsResource(self._http, **resource_kwargs)
        self.gateways = GatewaysResource(self._http, **resource_kwargs)
        self.models = ModelsResource(self._http, **resource_kwargs)
        self.finops = FinOpsResource(self._http, **resource_kwargs)
        self.agents = AgentsResource(self._http, **resource_kwargs)
        self.security = SecurityResource(self._http, **resource_kwargs)
        self.compliance = ComplianceResource(self._http, **resource_kwargs)
        self.insights = InsightsResource(self._http, **resource_kwargs)

    def __repr__(self) -> str:
        return f"AsyncVibOps(url='{self._http.base_url}', token='***')"

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

    Each method call uses ``asyncio.run()`` internally. This creates a fresh
    event loop per call which is simple and safe, but adds minor overhead.
    For high-throughput use cases, prefer :class:`AsyncVibOps` directly.

    Usage::

        with VibOps(url="https://vibops.example.com", token="vib_...") as v:
            clusters = v.clusters.list()
    """

    def __init__(
        self,
        url: str,
        token: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_statuses: set[int] | None = None,
        event_hooks: dict[str, list[Any]] | None = None,
    ) -> None:
        self._async = AsyncVibOps(
            url,
            token,
            timeout=timeout,
            max_retries=max_retries,
            retry_statuses=retry_statuses,
            event_hooks=event_hooks,
        )
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

    def __repr__(self) -> str:
        return f"VibOps(url='{self._async._http.base_url}', token='***')"

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
