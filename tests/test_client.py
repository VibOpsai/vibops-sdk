"""Tests for the VibOps Python SDK."""

from __future__ import annotations

import json

import httpx
import pytest
import pytest_asyncio

from vibops import AsyncVibOps, VibOps
from vibops.exceptions import AuthenticationError, NotFoundError, ServerError, VibOpsError


def _make_transport(handler):
    """Create an httpx.MockTransport from an async handler."""
    return httpx.MockTransport(handler)


def _json_response(data, status_code=200):
    return httpx.Response(status_code, json=data)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    """AsyncVibOps client wired to a mock transport."""

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path

        # --- clusters ---
        if path == "/api/v1/clusters" and request.method == "GET":
            return _json_response([{"name": "gpu-prod", "gpus": 8}])

        # --- jobs ---
        if path == "/api/v1/jobs" and request.method == "GET":
            return _json_response({"items": [], "total": 0})
        if path == "/api/v1/jobs" and request.method == "POST":
            body = json.loads(request.content)
            return _json_response({"id": "job-001", "action": body["action"], "status": "pending"}, 201)
        if path == "/api/v1/jobs/job-123" and request.method == "GET":
            return _json_response({"id": "job-123", "status": "completed"})

        # --- gateways ---
        if path == "/api/v1/gateways" and request.method == "GET":
            return _json_response([{"id": "gw-1", "name": "edge-01"}])

        # --- insights ---
        if path == "/api/v1/insights" and request.method == "GET":
            return _json_response([{"id": "ins-1", "severity": "warning"}])

        # --- security ---
        if path == "/api/v1/security/scan" and request.method == "POST":
            return _json_response({"scan_id": "scan-001", "status": "running"})

        # --- compliance ---
        if path == "/api/v1/compliance/check" and request.method == "POST":
            return _json_response({"check_id": "chk-001", "status": "running"})

        # --- finops ---
        if path == "/api/v1/finops/budget" and request.method == "GET":
            return _json_response({"monthly_limit_usd": 5000, "spent_usd": 1234})

        # --- agent usage ---
        if path == "/api/v1/finops/agent-usage" and request.method == "GET":
            return _json_response([{"agent_id": "a1", "total_cost_usd": 42.0}])

        return httpx.Response(404, json={"detail": "Not Found"})

    async_client = AsyncVibOps(url="https://vibops.test", token="test-token")
    async_client._http = httpx.AsyncClient(
        transport=_make_transport(handler),
        base_url="https://vibops.test",
        headers={"Authorization": "Bearer test-token"},
    )
    # Re-bind resources to new http client
    from vibops.clusters import ClustersResource
    from vibops.jobs import JobsResource
    from vibops.gateways import GatewaysResource
    from vibops.models import ModelsResource
    from vibops.finops import FinOpsResource
    from vibops.agents import AgentsResource
    from vibops.security import SecurityResource
    from vibops.compliance import ComplianceResource
    from vibops.insights import InsightsResource

    async_client.clusters = ClustersResource(async_client._http)
    async_client.jobs = JobsResource(async_client._http)
    async_client.gateways = GatewaysResource(async_client._http)
    async_client.models = ModelsResource(async_client._http)
    async_client.finops = FinOpsResource(async_client._http)
    async_client.agents = AgentsResource(async_client._http)
    async_client.security = SecurityResource(async_client._http)
    async_client.compliance = ComplianceResource(async_client._http)
    async_client.insights = InsightsResource(async_client._http)

    yield async_client
    await async_client.close()


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------

class TestClientInit:
    def test_init_sets_auth_header(self):
        c = AsyncVibOps(url="https://example.com", token="my-token")
        assert c._http.headers["authorization"] == "Bearer my-token"

    def test_raises_on_missing_url(self):
        with pytest.raises(VibOpsError, match="url is required"):
            AsyncVibOps(url="", token="tok")

    def test_raises_on_missing_token(self):
        with pytest.raises(VibOpsError, match="token is required"):
            AsyncVibOps(url="https://example.com", token="")


# ---------------------------------------------------------------------------
# Resource tests
# ---------------------------------------------------------------------------

class TestClusters:
    @pytest.mark.asyncio
    async def test_list_calls_correct_endpoint(self, client):
        result = await client.clusters.list()
        assert isinstance(result, list)
        assert result[0]["name"] == "gpu-prod"


class TestJobs:
    @pytest.mark.asyncio
    async def test_list_jobs(self, client):
        result = await client.jobs.list()
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_job(self, client):
        result = await client.jobs.get("job-123")
        assert result["id"] == "job-123"

    @pytest.mark.asyncio
    async def test_create_job(self, client):
        result = await client.jobs.create("restart_service", payload={"name": "api"})
        assert result["action"] == "restart_service"
        assert result["status"] == "pending"


class TestModelsDeploy:
    @pytest.mark.asyncio
    async def test_deploy_sends_correct_payload(self, client):
        """deploy() should POST to /jobs with action=deploy_model."""
        result = await client.models.deploy("llama3", "gpu-prod", replicas=2)
        assert result["action"] == "deploy_model"
        assert result["id"] == "job-001"


class TestGateways:
    @pytest.mark.asyncio
    async def test_list_gateways(self, client):
        result = await client.gateways.list()
        assert result[0]["id"] == "gw-1"


class TestInsights:
    @pytest.mark.asyncio
    async def test_list_insights(self, client):
        result = await client.insights.list()
        assert result[0]["severity"] == "warning"


class TestSecurity:
    @pytest.mark.asyncio
    async def test_trigger_scan(self, client):
        result = await client.security.scan()
        assert result["scan_id"] == "scan-001"


class TestCompliance:
    @pytest.mark.asyncio
    async def test_trigger_check(self, client):
        result = await client.compliance.check()
        assert result["check_id"] == "chk-001"


class TestFinOps:
    @pytest.mark.asyncio
    async def test_budget(self, client):
        result = await client.finops.budget()
        assert result["monthly_limit_usd"] == 5000


class TestAgents:
    @pytest.mark.asyncio
    async def test_usage(self, client):
        result = await client.agents.usage()
        assert result[0]["agent_id"] == "a1"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_auth_error_raises_exception(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"detail": "Invalid token"})

        c = AsyncVibOps(url="https://vibops.test", token="bad")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with pytest.raises(AuthenticationError, match="Invalid token"):
            await c.clusters.list()
        await c.close()

    @pytest.mark.asyncio
    async def test_not_found_raises(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"detail": "Not Found"})

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.jobs import JobsResource
        c.jobs = JobsResource(c._http)

        with pytest.raises(NotFoundError):
            await c.jobs.get("nonexistent")
        await c.close()


# ---------------------------------------------------------------------------
# Retry on 502/503
# ---------------------------------------------------------------------------

class TestRetry:
    @pytest.mark.asyncio
    async def test_retry_on_502(self):
        call_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(502, json={"detail": "Bad Gateway"})
            return httpx.Response(200, json=[{"name": "gpu-prod"}])

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        result = await c.clusters.list()
        assert call_count == 2
        assert result[0]["name"] == "gpu-prod"
        await c.close()

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises_server_error(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"detail": "Unavailable"})

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with pytest.raises(ServerError):
            await c.clusters.list()
        await c.close()


# ---------------------------------------------------------------------------
# Sync wrapper
# ---------------------------------------------------------------------------

class TestSyncWrapper:
    def test_sync_wrapper_works(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[{"name": "gpu-prod"}])

        client = VibOps(url="https://vibops.test", token="tok")
        client._async._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        # Rebind resource
        from vibops.clusters import ClustersResource
        client._async.clusters = ClustersResource(client._async._http)
        from vibops.client import _SyncProxy
        client.clusters = _SyncProxy(client._async.clusters, client._run_sync)

        result = client.clusters.list()
        assert result[0]["name"] == "gpu-prod"
        client.close()
