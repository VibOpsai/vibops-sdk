"""VibOps SDK clients — async-first with sync wrapper."""

from __future__ import annotations

import asyncio
import functools
import warnings
from typing import Any

import httpx

from vibops.agents import AgentsResource
from vibops.alerts import AlertsResource
from vibops.anomalies import AnomaliesResource
from vibops.audit import AuditResource
from vibops.auth import AuthResource
from vibops.clusters import ClustersResource
from vibops.compliance import ComplianceResource
from vibops.eval import EvalResource
from vibops.exceptions import VibOpsError
from vibops.finops import FinOpsResource
from vibops.gateways import GatewaysResource
from vibops.gpu_health import GpuHealthResource
from vibops.identities import IdentitiesResource
from vibops.insights import InsightsResource
from vibops.jobs import JobsResource
from vibops.metrics import MetricsResource
from vibops.models import ModelsResource
from vibops.notifications import NotificationsResource
from vibops.orgs import OrgsResource
from vibops.pipelines import PipelinesResource
from vibops.policy import PolicyResource
from vibops.reselling import ResellingResource
from vibops.secrets import SecretsResource
from vibops.security import SecurityResource
from vibops.tokens import TokensResource
from vibops.triggers import TriggersResource
from vibops.webhooks import WebhooksResource
from vibops.workloads import WorkloadsResource


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
        if url.startswith("http://"):
            warnings.warn(
                "Using unencrypted HTTP. Tokens will be sent in plaintext. "
                "Use https:// in production.",
                stacklevel=2,
            )

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
        self.auth = AuthResource(self._http, **resource_kwargs)
        self.audit = AuditResource(self._http, **resource_kwargs)
        self.anomalies = AnomaliesResource(self._http, **resource_kwargs)
        self.alerts = AlertsResource(self._http, **resource_kwargs)
        self.secrets = SecretsResource(self._http, **resource_kwargs)
        self.pipelines = PipelinesResource(self._http, **resource_kwargs)
        self.tokens = TokensResource(self._http, **resource_kwargs)
        self.notifications = NotificationsResource(self._http, **resource_kwargs)
        self.policy = PolicyResource(self._http, **resource_kwargs)
        self.identities = IdentitiesResource(self._http, **resource_kwargs)
        self.orgs = OrgsResource(self._http, **resource_kwargs)
        self.metrics = MetricsResource(self._http, **resource_kwargs)
        self.triggers = TriggersResource(self._http, **resource_kwargs)
        self.eval = EvalResource(self._http, **resource_kwargs)
        self.workloads = WorkloadsResource(self._http, **resource_kwargs)
        self.webhooks = WebhooksResource(self._http, **resource_kwargs)
        self.gpu_health = GpuHealthResource(self._http, **resource_kwargs)
        self.reselling = ResellingResource(self._http, **resource_kwargs)

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
        self.auth = _SyncProxy(self._async.auth, run)
        self.audit = _SyncProxy(self._async.audit, run)
        self.anomalies = _SyncProxy(self._async.anomalies, run)
        self.alerts = _SyncProxy(self._async.alerts, run)
        self.secrets = _SyncProxy(self._async.secrets, run)
        self.pipelines = _SyncProxy(self._async.pipelines, run)
        self.tokens = _SyncProxy(self._async.tokens, run)
        self.notifications = _SyncProxy(self._async.notifications, run)
        self.policy = _SyncProxy(self._async.policy, run)
        self.identities = _SyncProxy(self._async.identities, run)
        self.orgs = _SyncProxy(self._async.orgs, run)
        self.metrics = _SyncProxy(self._async.metrics, run)
        self.triggers = _SyncProxy(self._async.triggers, run)
        self.eval = _SyncProxy(self._async.eval, run)
        self.workloads = _SyncProxy(self._async.workloads, run)
        self.webhooks = _SyncProxy(self._async.webhooks, run)
        self.gpu_health = _SyncProxy(self._async.gpu_health, run)
        self.reselling = _SyncProxy(self._async.reselling, run)

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
