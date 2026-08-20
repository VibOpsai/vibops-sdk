"""Tests for the VibOps Python SDK."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio

from vibops import AsyncVibOps, VibOps
from vibops.exceptions import (
    AuthenticationError,
    ConflictError,
    ConnectionError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    VibOpsError,
)
from vibops.types import Budget, Cluster, Insight, Job, parse


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
        method = request.method

        # --- clusters ---
        if path == "/api/v1/clusters" and method == "GET":
            return _json_response({"clusters": [{"name": "gpu-prod", "gpu_total": 8, "gpu_used": 4, "online": True}], "total": 1})
        if path == "/api/v1/clusters/gpu-prod/deployments" and method == "GET":
            return _json_response([{"name": "api-server", "replicas": 3}])
        if path == "/api/v1/clusters/gpu-prod/gpu-metrics/top" and method == "GET":
            return _json_response({"utilization": 0.75, "top_workloads": []})

        # --- jobs ---
        if path == "/api/v1/jobs" and method == "GET":
            return _json_response({"items": [], "total": 0})
        if path == "/api/v1/jobs" and method == "POST":
            body = json.loads(request.content)
            return _json_response({"id": "job-001", "action": body["action"], "status": "pending"}, 201)
        if path == "/api/v1/jobs/job-123" and method == "GET":
            return _json_response({"id": "job-123", "status": "completed"})
        if path == "/api/v1/jobs/job-123/cancel" and method == "POST":
            return _json_response({"id": "job-123", "status": "cancelled"})

        # --- gateways ---
        if path == "/api/v1/gateways" and method == "GET":
            return _json_response([{"id": "gw-1", "name": "edge-01"}])
        if path == "/api/v1/gateways" and method == "POST":
            body = json.loads(request.content)
            return _json_response({"id": "gw-new", "name": body["name"], "api_key": "secret"}, 201)
        if path == "/api/v1/gateways/gw-1" and method == "DELETE":
            return _json_response({"deleted": True, "gateway_id": "gw-1", "jobs_cancelled": 0})

        # --- insights ---
        if path == "/api/v1/insights" and method == "GET":
            return _json_response([{"id": "ins-1", "severity": "warning", "insight_type": "idle_gpu", "title": "Idle GPU", "description": "GPU idle", "acknowledged": False}])
        if path == "/api/v1/insights/ins-1/acknowledge" and method == "POST":
            return _json_response({"id": "ins-1", "acknowledged": True})

        # --- security ---
        if path == "/api/v1/security/scan" and method == "POST":
            return _json_response({"scan_id": "scan-001", "status": "running"})
        if path == "/api/v1/security/findings" and method == "GET":
            return _json_response([{"id": "f-1", "severity": "HIGH", "title": "Open port"}])

        # --- compliance ---
        if path == "/api/v1/compliance/check" and method == "POST":
            return _json_response({"check_id": "chk-001", "status": "running"})
        if path == "/api/v1/compliance/check/results" and method == "GET":
            return _json_response([{"control_id": "AC-1", "status": "pass"}])

        # --- finops ---
        if path == "/api/v1/finops/budget" and method == "GET":
            return _json_response({"monthly_limit_usd": 5000, "spent_usd": 1234, "utilization_pct": 24.68})
        if path == "/api/v1/finops/spend/trend" and method == "GET":
            return _json_response([{"month": "2026-07", "total_usd": 4200}])
        if path == "/api/v1/finops/chargeback" and method == "GET":
            return _json_response([{"team": "ml", "cost_usd": 1500}])
        if path == "/api/v1/finops/waste" and method == "GET":
            return _json_response({"idle_gpus": 3, "potential_savings_usd": 900})
        if path == "/api/v1/finops/workloads/live-cost" and method == "GET":
            return _json_response([{"workload": "inference-a", "cost_per_hour": 2.5}])

        # --- agent usage ---
        if path == "/api/v1/finops/agent-usage" and method == "GET":
            return _json_response([{"agent_id": "a1", "total_cost_usd": 42.0}])
        if path == "/api/v1/finops/agent-usage/a1" and method == "GET":
            return _json_response({"agent_id": "a1", "daily": [], "models": {}})
        if path == "/api/v1/finops/agent-budgets/a1" and method == "GET":
            return _json_response({"agent_id": "a1", "monthly_limit_usd": 100})
        if path == "/api/v1/finops/agent-budgets" and method == "POST":
            return _json_response({"agent_id": "a1", "monthly_limit_usd": 200}, 201)
        if path == "/api/v1/finops/agent-budgets" and method == "GET":
            return _json_response([{"agent_id": "a1", "monthly_limit_usd": 100}])

        # --- auth ---
        if path == "/api/v1/auth/login" and method == "POST":
            return _json_response({"access_token": "tok-123", "token_type": "bearer"})
        if path == "/api/v1/auth/me" and method == "GET":
            return _json_response({"username": "admin", "email": "admin@example.com"})
        if path == "/api/v1/auth/refresh" and method == "POST":
            return _json_response({"access_token": "tok-456"})
        if path == "/api/v1/auth/forgot-password" and method == "POST":
            return _json_response({"status": "sent"})
        if path == "/api/v1/auth/reset-password" and method == "POST":
            return httpx.Response(204)

        # --- audit ---
        if path == "/api/v1/audit" and method == "GET":
            return _json_response({"total": 1, "items": [{"id": "aud-1", "action": "login", "user": "admin"}]})
        if path == "/api/v1/audit/verify" and method == "GET":
            return _json_response({"valid": True, "entries_checked": 42})
        if path == "/api/v1/audit/export" and method == "GET":
            return _json_response({"format": "json", "entries": 42})

        # --- anomalies ---
        if path == "/api/v1/anomalies" and method == "GET":
            return _json_response([{"id": "anom-1", "type": "idle_gpu", "status": "open"}])
        if path == "/api/v1/anomalies/open" and method == "GET":
            return _json_response([{"id": "anom-1", "type": "idle_gpu"}])
        if path == "/api/v1/anomalies/anom-1/resolve" and method == "POST":
            return _json_response({"id": "anom-1", "status": "resolved"})

        # --- alerts ---
        if path == "/api/v1/alert-history" and method == "GET":
            return _json_response([{"id": "alert-1", "severity": "critical"}])
        if path == "/api/v1/alert-rules" and method == "GET":
            return _json_response([{"id": "rule-1", "name": "gpu-idle"}])
        if path == "/api/v1/alert-rules" and method == "POST":
            return _json_response({"id": "rule-2", "name": "gpu-temp"}, 201)
        if path == "/api/v1/alert-rules/rule-1" and method == "DELETE":
            return _json_response({"deleted": True})

        # --- secrets ---
        if path == "/api/v1/secrets" and method == "GET":
            return _json_response([{"name": "DB_PASSWORD"}])
        if path == "/api/v1/secrets" and method == "POST":
            return _json_response({"name": "API_KEY"}, 201)
        if path == "/api/v1/secrets/DB_PASSWORD" and method == "DELETE":
            return _json_response({"deleted": True})

        # --- pipelines ---
        if path == "/api/v1/pipelines" and method == "GET":
            return _json_response([{"id": "pipe-1", "name": "deploy-ml"}])
        if path == "/api/v1/pipelines" and method == "POST":
            return _json_response({"id": "pipe-2", "name": "retrain"}, 201)
        if path == "/api/v1/pipelines/pipe-1/trigger" and method == "POST":
            return _json_response({"run_id": "run-1", "status": "started"})

        # --- tokens ---
        if path == "/api/v1/tokens" and method == "GET":
            return _json_response([{"id": "tok-1", "name": "ci-token"}])
        if path == "/api/v1/tokens" and method == "POST":
            return _json_response({"id": "tok-2", "name": "new-token", "token": "vib_xxx"}, 201)
        if path == "/api/v1/tokens/tok-1" and method == "DELETE":
            return _json_response({"deleted": True})

        # --- notifications ---
        if path == "/api/v1/notifications/channels" and method == "GET":
            return _json_response([{"id": "ch-1", "name": "slack-ops", "type": "slack"}])
        if path == "/api/v1/notifications/channels" and method == "POST":
            return _json_response({"id": "ch-2", "name": "pagerduty"}, 201)
        if path == "/api/v1/notifications/channels/ch-1" and method == "DELETE":
            return _json_response({"deleted": True})
        if path == "/api/v1/notifications/channels/ch-1/test" and method == "POST":
            return _json_response({"status": "sent"})

        # --- policy ---
        if path == "/api/v1/policy" and method == "GET":
            return _json_response({"version": 3, "rules": []})
        if path == "/api/v1/policy" and method == "PUT":
            return _json_response({"version": 4})
        if path == "/api/v1/policy/agent-model-rules" and method == "GET":
            return _json_response([{"id": "mr-1", "agent_id_pattern": "agent-*"}])
        if path == "/api/v1/policy/agent-model-rules" and method == "POST":
            return _json_response({"id": "mr-2", "agent_id_pattern": "bot-*"}, 201)

        # --- identities ---
        if path == "/api/v1/agent-identities" and method == "GET":
            return _json_response([{"id": "id-1", "name": "worker-1"}])
        if path == "/api/v1/agent-identities" and method == "POST":
            return _json_response({"id": "id-2", "name": "worker-2", "key": "secret"}, 201)
        if path == "/api/v1/agent-identities/id-1/rotate" and method == "POST":
            return _json_response({"id": "id-1", "key": "new-secret"})
        if path == "/api/v1/agent-identities/id-1/revoke" and method == "POST":
            return _json_response({"id": "id-1", "revoked": True})

        # --- orgs ---
        if path == "/api/v1/orgs/org-1" and method == "GET":
            return _json_response({"id": "org-1", "name": "Acme Corp"})
        if path == "/api/v1/orgs/org-1" and method == "PATCH":
            return _json_response({"id": "org-1", "name": "Acme Inc"})
        if path == "/api/v1/orgs/org-1/users" and method == "GET":
            return _json_response([{"username": "alice"}])
        if path == "/api/v1/orgs/org-1/users" and method == "POST":
            return _json_response({"username": "bob"}, 201)
        if path == "/api/v1/orgs/org-1/teams" and method == "GET":
            return _json_response([{"name": "ml-team"}])
        if path == "/api/v1/orgs/org-1/teams" and method == "POST":
            return _json_response({"name": "infra-team"}, 201)
        if path == "/api/v1/orgs/org-1/invites" and method == "POST":
            return _json_response({"email": "new@acme.com", "status": "invited"}, 201)

        # --- metrics ---
        if path == "/api/v1/metrics/gpu" and method == "GET":
            return _json_response({"hours": 24, "points": [{"gpu_id": "0", "utilization": 0.85}]})
        if path == "/api/v1/metrics/cost" and method == "GET":
            return _json_response({"estimated_cost_usd": 1234.56})
        if path == "/api/v1/metrics/workloads" and method == "GET":
            return _json_response({"training": 60, "inference": 40})
        if path == "/api/v1/metrics/mttr" and method == "GET":
            return _json_response({"mttr_seconds": 120})
        if path == "/api/v1/metrics/jobs" and method == "GET":
            return _json_response({"success_rate": 0.95, "avg_duration_s": 45})

        # --- triggers ---
        if path == "/api/v1/triggers" and method == "GET":
            return _json_response([{"id": "trig-1", "name": "auto-scale"}])
        if path == "/api/v1/triggers" and method == "POST":
            return _json_response({"id": "trig-2", "name": "auto-restart"}, 201)
        if path == "/api/v1/triggers/trig-1/enable" and method == "POST":
            return _json_response({"id": "trig-1", "enabled": True})
        if path == "/api/v1/triggers/trig-1/disable" and method == "POST":
            return _json_response({"id": "trig-1", "enabled": False})
        if path == "/api/v1/triggers/trig-1" and method == "DELETE":
            return _json_response({"deleted": True})

        # --- eval ---
        if path == "/api/v1/eval/rubrics" and method == "GET":
            return _json_response([{"id": "rub-1", "name": "quality-v1"}])
        if path == "/api/v1/eval/rubrics" and method == "POST":
            return _json_response({"id": "rub-2", "name": "quality-v2"}, 201)
        if path == "/api/v1/eval/jobs/job-1/evaluate" and method == "POST":
            return _json_response({"score": 0.87, "rubric_id": "rub-1"})
        if path == "/api/v1/eval/jobs/job-1/evaluations" and method == "GET":
            return _json_response([{"score": 0.87}])

        # --- workloads ---
        if path == "/api/v1/workloads" and method == "GET":
            return _json_response([{"id": "wl-1", "name": "llama-inference"}])
        if path == "/api/v1/workloads/wl-1" and method == "GET":
            return _json_response({"id": "wl-1", "name": "llama-inference", "status": "running"})
        if path == "/api/v1/workloads/cost-summary" and method == "GET":
            return _json_response({"total_cost_usd": 5000})

        # --- webhooks ---
        if path == "/api/v1/webhooks/subscriptions" and method == "GET":
            return _json_response([{"id": "sub-1", "repo": "org/model"}])
        if path == "/api/v1/webhooks/subscriptions" and method == "POST":
            return _json_response({"id": "sub-2", "repo": "org/new-model"}, 201)
        if path == "/api/v1/webhooks/subscriptions/sub-1" and method == "DELETE":
            return _json_response({"deleted": True})

        # --- gpu health ---
        if path == "/api/v1/gpu/health-predictions" and method == "GET":
            return _json_response([{"gpu_id": "0", "failure_probability": 0.02}])

        # --- reselling ---
        if path == "/api/v1/resellers/me" and method == "GET":
            return _json_response({"id": "res-1", "name": "CloudPartner"})
        if path == "/api/v1/resellers/me/customers" and method == "GET":
            return _json_response([{"id": "cust-1", "name": "Customer A"}])
        if path == "/api/v1/resellers/me/customers" and method == "POST":
            return _json_response({"id": "cust-2", "name": "Customer B"}, 201)
        if path == "/api/v1/resellers/me/pricing-rules" and method == "GET":
            return _json_response([{"id": "pr-1", "markup_pct": 20}])

        # --- _put test ---
        if path == "/api/v1/test/put" and method == "PUT":
            return _json_response({"updated": True})

        # --- models ---
        # scale goes through /jobs POST (same as deploy)

        return httpx.Response(404, json={"detail": "Not Found"})

    async_client = AsyncVibOps(url="https://vibops.test", token="test-token")
    async_client._http = httpx.AsyncClient(
        transport=_make_transport(handler),
        base_url="https://vibops.test",
        headers={"Authorization": "Bearer test-token"},
    )
    # Re-bind resources to new http client
    from vibops.alerts import AlertsResource
    from vibops.anomalies import AnomaliesResource
    from vibops.audit import AuditResource
    from vibops.auth import AuthResource
    from vibops.clusters import ClustersResource
    from vibops.compliance import ComplianceResource
    from vibops.eval import EvalResource
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
    from vibops.agents import AgentsResource
    from vibops.tokens import TokensResource
    from vibops.triggers import TriggersResource
    from vibops.webhooks import WebhooksResource
    from vibops.workloads import WorkloadsResource

    async_client.clusters = ClustersResource(async_client._http)
    async_client.jobs = JobsResource(async_client._http)
    async_client.gateways = GatewaysResource(async_client._http)
    async_client.models = ModelsResource(async_client._http)
    async_client.finops = FinOpsResource(async_client._http)
    async_client.agents = AgentsResource(async_client._http)
    async_client.security = SecurityResource(async_client._http)
    async_client.compliance = ComplianceResource(async_client._http)
    async_client.insights = InsightsResource(async_client._http)
    async_client.auth = AuthResource(async_client._http)
    async_client.audit = AuditResource(async_client._http)
    async_client.anomalies = AnomaliesResource(async_client._http)
    async_client.alerts = AlertsResource(async_client._http)
    async_client.secrets = SecretsResource(async_client._http)
    async_client.pipelines = PipelinesResource(async_client._http)
    async_client.tokens = TokensResource(async_client._http)
    async_client.notifications = NotificationsResource(async_client._http)
    async_client.policy = PolicyResource(async_client._http)
    async_client.identities = IdentitiesResource(async_client._http)
    async_client.orgs = OrgsResource(async_client._http)
    async_client.metrics = MetricsResource(async_client._http)
    async_client.triggers = TriggersResource(async_client._http)
    async_client.eval = EvalResource(async_client._http)
    async_client.workloads = WorkloadsResource(async_client._http)
    async_client.webhooks = WebhooksResource(async_client._http)
    async_client.gpu_health = GpuHealthResource(async_client._http)
    async_client.reselling = ResellingResource(async_client._http)

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

    def test_max_retries_configurable(self):
        c = AsyncVibOps(url="https://example.com", token="tok", max_retries=5)
        assert c.clusters._max_retries == 5

    def test_retry_statuses_configurable(self):
        c = AsyncVibOps(url="https://example.com", token="tok", retry_statuses={500, 502})
        assert c.clusters._retry_statuses == {500, 502}

    def test_event_hooks_passed_to_httpx(self):
        hooks_called = []

        async def on_request(request):
            hooks_called.append(request)

        c = AsyncVibOps(
            url="https://example.com",
            token="tok",
            event_hooks={"request": [on_request]},
        )
        assert "request" in c._http.event_hooks
        assert len(c._http.event_hooks["request"]) >= 1


# ---------------------------------------------------------------------------
# Repr tests (M1)
# ---------------------------------------------------------------------------

class TestRepr:
    def test_async_repr_masks_token(self):
        c = AsyncVibOps(url="https://vibops.example.com", token="vib_super_secret")
        r = repr(c)
        assert "vib_super_secret" not in r
        assert "***" in r
        assert "AsyncVibOps" in r

    def test_sync_repr_masks_token(self):
        c = VibOps(url="https://vibops.example.com", token="vib_super_secret")
        r = repr(c)
        assert "vib_super_secret" not in r
        assert "***" in r
        assert "VibOps(" in r


# ---------------------------------------------------------------------------
# Resource completeness (L5)
# ---------------------------------------------------------------------------

class TestResourceCompleteness:
    _ALL_RESOURCES = {
        "clusters", "jobs", "gateways", "models", "finops",
        "agents", "security", "compliance", "insights",
        "auth", "audit", "anomalies", "alerts", "secrets",
        "pipelines", "tokens", "notifications", "policy",
        "identities", "orgs", "metrics", "triggers", "eval",
        "workloads", "webhooks", "gpu_health", "reselling",
    }

    def test_all_resources_present_on_async_client(self):
        """Every resource namespace must exist on the async client."""
        c = AsyncVibOps(url="https://example.com", token="tok")
        for name in self._ALL_RESOURCES:
            assert hasattr(c, name), f"AsyncVibOps missing resource: {name}"

    def test_all_resources_present_on_sync_client(self):
        """Every resource namespace must exist on the sync client."""
        c = VibOps(url="https://example.com", token="tok")
        for name in self._ALL_RESOURCES:
            assert hasattr(c, name), f"VibOps missing resource: {name}"


# ---------------------------------------------------------------------------
# Resource tests
# ---------------------------------------------------------------------------

class TestClusters:
    @pytest.mark.asyncio
    async def test_list_calls_correct_endpoint(self, client):
        result = await client.clusters.list()
        assert isinstance(result, list)
        assert isinstance(result[0], Cluster)
        assert result[0].name == "gpu-prod"

    @pytest.mark.asyncio
    async def test_deployments(self, client):
        result = await client.clusters.deployments("gpu-prod")
        assert isinstance(result, list)
        assert result[0]["name"] == "api-server"

    @pytest.mark.asyncio
    async def test_gpu_metrics(self, client):
        result = await client.clusters.gpu_metrics("gpu-prod")
        assert result["utilization"] == 0.75


class TestJobs:
    @pytest.mark.asyncio
    async def test_list_jobs(self, client):
        result = await client.jobs.list()
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_job(self, client):
        result = await client.jobs.get("job-123")
        assert isinstance(result, Job)
        assert result.id == "job-123"

    @pytest.mark.asyncio
    async def test_create_job(self, client):
        result = await client.jobs.create("restart_service", payload={"name": "api"})
        assert isinstance(result, Job)
        assert result.action == "restart_service"
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_cancel_job(self, client):
        result = await client.jobs.cancel("job-123")
        assert isinstance(result, Job)
        assert result.status == "cancelled"


class TestModelsDeploy:
    @pytest.mark.asyncio
    async def test_deploy_sends_correct_payload(self, client):
        """deploy() should POST to /jobs with action=deploy_model."""
        result = await client.models.deploy("llama3", "gpu-prod", replicas=2)
        assert isinstance(result, Job)
        assert result.action == "deploy_model"
        assert result.id == "job-001"

    @pytest.mark.asyncio
    async def test_scale(self, client):
        result = await client.models.scale("llama3", "inference", 3, "gpu-prod")
        assert isinstance(result, Job)
        assert result.action == "scale_deployment"
        assert result.id == "job-001"


class TestGateways:
    @pytest.mark.asyncio
    async def test_list_gateways(self, client):
        result = await client.gateways.list()
        assert result[0]["id"] == "gw-1"

    @pytest.mark.asyncio
    async def test_register_gateway(self, client):
        result = await client.gateways.register("new-gw", clusters=["gpu-prod"])
        assert result["id"] == "gw-new"
        assert result["name"] == "new-gw"

    @pytest.mark.asyncio
    async def test_delete_gateway(self, client):
        result = await client.gateways.delete("gw-1", confirmed=True)
        assert result["deleted"] is True


class TestInsights:
    @pytest.mark.asyncio
    async def test_list_insights(self, client):
        result = await client.insights.list()
        assert isinstance(result[0], Insight)
        assert result[0].severity == "warning"

    @pytest.mark.asyncio
    async def test_acknowledge_insight(self, client):
        result = await client.insights.acknowledge("ins-1")
        assert result["acknowledged"] is True


class TestSecurity:
    @pytest.mark.asyncio
    async def test_trigger_scan(self, client):
        result = await client.security.scan()
        assert result["scan_id"] == "scan-001"

    @pytest.mark.asyncio
    async def test_findings(self, client):
        result = await client.security.findings(severity="HIGH")
        assert isinstance(result, list)
        assert result[0]["severity"] == "HIGH"


class TestCompliance:
    @pytest.mark.asyncio
    async def test_trigger_check(self, client):
        result = await client.compliance.check()
        assert result["check_id"] == "chk-001"

    @pytest.mark.asyncio
    async def test_results(self, client):
        result = await client.compliance.results(status="pass")
        assert isinstance(result, list)
        assert result[0]["status"] == "pass"


class TestFinOps:
    @pytest.mark.asyncio
    async def test_budget(self, client):
        result = await client.finops.budget()
        assert isinstance(result, Budget)
        assert result.monthly_limit_usd == 5000

    @pytest.mark.asyncio
    async def test_spend_trend(self, client):
        result = await client.finops.spend_trend()
        assert isinstance(result, list)
        assert result[0]["month"] == "2026-07"

    @pytest.mark.asyncio
    async def test_chargeback(self, client):
        result = await client.finops.chargeback()
        assert isinstance(result, list)
        assert result[0]["team"] == "ml"

    @pytest.mark.asyncio
    async def test_waste(self, client):
        result = await client.finops.waste()
        assert result["idle_gpus"] == 3

    @pytest.mark.asyncio
    async def test_live_cost(self, client):
        result = await client.finops.live_cost()
        assert isinstance(result, list)
        assert result[0]["workload"] == "inference-a"


class TestAgents:
    @pytest.mark.asyncio
    async def test_usage(self, client):
        result = await client.agents.usage()
        assert result[0]["agent_id"] == "a1"

    @pytest.mark.asyncio
    async def test_usage_detail(self, client):
        result = await client.agents.usage_detail("a1")
        assert result["agent_id"] == "a1"

    @pytest.mark.asyncio
    async def test_budget(self, client):
        result = await client.agents.budget("a1")
        assert result["agent_id"] == "a1"
        assert result["monthly_limit_usd"] == 100

    @pytest.mark.asyncio
    async def test_set_budget(self, client):
        result = await client.agents.set_budget("a1", 200.0)
        assert result["monthly_limit_usd"] == 200

    @pytest.mark.asyncio
    async def test_list_budgets(self, client):
        result = await client.agents.list_budgets()
        assert isinstance(result, list)
        assert result[0]["agent_id"] == "a1"


# ---------------------------------------------------------------------------
# New resource tests
# ---------------------------------------------------------------------------


class TestAuth:
    @pytest.mark.asyncio
    async def test_login(self, client):
        result = await client.auth.login("admin", "secret")
        assert result["access_token"] == "tok-123"

    @pytest.mark.asyncio
    async def test_me(self, client):
        result = await client.auth.me()
        assert result["username"] == "admin"

    @pytest.mark.asyncio
    async def test_refresh(self, client):
        result = await client.auth.refresh("refresh-tok-123")
        assert result["access_token"] == "tok-456"

    @pytest.mark.asyncio
    async def test_forgot_password(self, client):
        result = await client.auth.forgot_password("admin@example.com")
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_reset_password(self, client):
        result = await client.auth.reset_password("reset-tok", "new-pass")
        assert result is None


class TestAudit:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.audit.list()
        assert result["total"] == 1
        assert result["items"][0]["action"] == "login"

    @pytest.mark.asyncio
    async def test_verify_chain(self, client):
        result = await client.audit.verify_chain()
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_export(self, client):
        result = await client.audit.export()
        assert result["entries"] == 42


class TestAnomalies:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.anomalies.list()
        assert isinstance(result, list)
        assert result[0]["type"] == "idle_gpu"

    @pytest.mark.asyncio
    async def test_open(self, client):
        result = await client.anomalies.open()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_resolve(self, client):
        result = await client.anomalies.resolve("anom-1", reason="fixed")
        assert result["status"] == "resolved"


class TestAlerts:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.alerts.list()
        assert result[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_rules(self, client):
        result = await client.alerts.rules()
        assert result[0]["name"] == "gpu-idle"

    @pytest.mark.asyncio
    async def test_create_rule(self, client):
        result = await client.alerts.create_rule("gpu-temp", "temp > 90", "notify")
        assert result["name"] == "gpu-temp"

    @pytest.mark.asyncio
    async def test_delete_rule(self, client):
        result = await client.alerts.delete_rule("rule-1")
        assert result["deleted"] is True


class TestSecrets:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.secrets.list()
        assert result[0]["name"] == "DB_PASSWORD"

    @pytest.mark.asyncio
    async def test_create(self, client):
        result = await client.secrets.create("API_KEY", "s3cret")
        assert result["name"] == "API_KEY"

    @pytest.mark.asyncio
    async def test_delete(self, client):
        result = await client.secrets.delete("DB_PASSWORD")
        assert result["deleted"] is True


class TestPipelines:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.pipelines.list()
        assert result[0]["name"] == "deploy-ml"

    @pytest.mark.asyncio
    async def test_create(self, client):
        result = await client.pipelines.create("retrain", [{"action": "run"}])
        assert result["name"] == "retrain"

    @pytest.mark.asyncio
    async def test_trigger(self, client):
        result = await client.pipelines.trigger("pipe-1")
        assert result["status"] == "started"


class TestTokens:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.tokens.list()
        assert result[0]["name"] == "ci-token"

    @pytest.mark.asyncio
    async def test_create(self, client):
        result = await client.tokens.create("new-token")
        assert result["token"] == "vib_xxx"

    @pytest.mark.asyncio
    async def test_delete(self, client):
        result = await client.tokens.delete("tok-1")
        assert result["deleted"] is True


class TestNotifications:
    @pytest.mark.asyncio
    async def test_channels(self, client):
        result = await client.notifications.channels()
        assert result[0]["name"] == "slack-ops"

    @pytest.mark.asyncio
    async def test_create_channel(self, client):
        result = await client.notifications.create_channel("pagerduty", "pagerduty", "https://pd.example.com")
        assert result["name"] == "pagerduty"

    @pytest.mark.asyncio
    async def test_delete_channel(self, client):
        result = await client.notifications.delete_channel("ch-1")
        assert result["deleted"] is True

    @pytest.mark.asyncio
    async def test_test_channel(self, client):
        result = await client.notifications.test_channel("ch-1")
        assert result["status"] == "sent"


class TestPolicy:
    @pytest.mark.asyncio
    async def test_get(self, client):
        result = await client.policy.get()
        assert result["version"] == 3

    @pytest.mark.asyncio
    async def test_update(self, client):
        result = await client.policy.update("rules: []")
        assert result["version"] == 4

    @pytest.mark.asyncio
    async def test_model_rules(self, client):
        result = await client.policy.model_rules()
        assert result[0]["agent_id_pattern"] == "agent-*"

    @pytest.mark.asyncio
    async def test_create_model_rule(self, client):
        result = await client.policy.create_model_rule("bot-*", allowed_models=["gpt-4"])
        assert result["agent_id_pattern"] == "bot-*"


class TestIdentities:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.identities.list()
        assert result[0]["name"] == "worker-1"

    @pytest.mark.asyncio
    async def test_create(self, client):
        result = await client.identities.create("worker-2")
        assert result["key"] == "secret"

    @pytest.mark.asyncio
    async def test_rotate(self, client):
        result = await client.identities.rotate("id-1")
        assert result["key"] == "new-secret"

    @pytest.mark.asyncio
    async def test_revoke(self, client):
        result = await client.identities.revoke("id-1")
        assert result["revoked"] is True


class TestOrgs:
    @pytest.mark.asyncio
    async def test_get(self, client):
        result = await client.orgs.get("org-1")
        assert result["name"] == "Acme Corp"

    @pytest.mark.asyncio
    async def test_update(self, client):
        result = await client.orgs.update("org-1", name="Acme Inc")
        assert result["name"] == "Acme Inc"

    @pytest.mark.asyncio
    async def test_users(self, client):
        result = await client.orgs.users("org-1")
        assert result[0]["username"] == "alice"

    @pytest.mark.asyncio
    async def test_create_user(self, client):
        result = await client.orgs.create_user("org-1", "bob", "pass123")
        assert result["username"] == "bob"

    @pytest.mark.asyncio
    async def test_teams(self, client):
        result = await client.orgs.teams("org-1")
        assert result[0]["name"] == "ml-team"

    @pytest.mark.asyncio
    async def test_create_team(self, client):
        result = await client.orgs.create_team("org-1", "infra-team")
        assert result["name"] == "infra-team"

    @pytest.mark.asyncio
    async def test_invite(self, client):
        result = await client.orgs.invite("org-1", "new@acme.com")
        assert result["status"] == "invited"


class TestMetrics:
    @pytest.mark.asyncio
    async def test_gpu(self, client):
        result = await client.metrics.gpu("gpu-prod")
        assert result["points"][0]["utilization"] == 0.85

    @pytest.mark.asyncio
    async def test_cost_estimate(self, client):
        result = await client.metrics.cost_estimate()
        assert result["estimated_cost_usd"] == 1234.56

    @pytest.mark.asyncio
    async def test_workload_breakdown(self, client):
        result = await client.metrics.workload_breakdown()
        assert result["training"] == 60

    @pytest.mark.asyncio
    async def test_mttr(self, client):
        result = await client.metrics.mttr()
        assert result["mttr_seconds"] == 120

    @pytest.mark.asyncio
    async def test_job_metrics(self, client):
        result = await client.metrics.job_metrics()
        assert result["success_rate"] == 0.95


class TestTriggers:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.triggers.list()
        assert result[0]["name"] == "auto-scale"

    @pytest.mark.asyncio
    async def test_create(self, client):
        result = await client.triggers.create("auto-restart", "pod_crash > 3", "restart")
        assert result["name"] == "auto-restart"

    @pytest.mark.asyncio
    async def test_enable(self, client):
        result = await client.triggers.enable("trig-1")
        assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_disable(self, client):
        result = await client.triggers.disable("trig-1")
        assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_delete(self, client):
        result = await client.triggers.delete("trig-1")
        assert result["deleted"] is True


class TestEval:
    @pytest.mark.asyncio
    async def test_rubrics(self, client):
        result = await client.eval.rubrics()
        assert result[0]["name"] == "quality-v1"

    @pytest.mark.asyncio
    async def test_create_rubric(self, client):
        result = await client.eval.create_rubric("quality-v2", [{"name": "accuracy"}])
        assert result["name"] == "quality-v2"

    @pytest.mark.asyncio
    async def test_evaluate(self, client):
        result = await client.eval.evaluate("job-1", "rub-1")
        assert result["score"] == 0.87

    @pytest.mark.asyncio
    async def test_results(self, client):
        result = await client.eval.results("job-1")
        assert result[0]["score"] == 0.87


class TestWorkloads:
    @pytest.mark.asyncio
    async def test_list(self, client):
        result = await client.workloads.list()
        assert result[0]["name"] == "llama-inference"

    @pytest.mark.asyncio
    async def test_get(self, client):
        result = await client.workloads.get("wl-1")
        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_cost_summary(self, client):
        result = await client.workloads.cost_summary()
        assert result["total_cost_usd"] == 5000


class TestWebhooks:
    @pytest.mark.asyncio
    async def test_subscriptions(self, client):
        result = await client.webhooks.subscriptions()
        assert result[0]["repo"] == "org/model"

    @pytest.mark.asyncio
    async def test_create_subscription(self, client):
        result = await client.webhooks.create_subscription("org/new-model")
        assert result["repo"] == "org/new-model"

    @pytest.mark.asyncio
    async def test_delete_subscription(self, client):
        result = await client.webhooks.delete_subscription("sub-1")
        assert result["deleted"] is True


class TestGpuHealth:
    @pytest.mark.asyncio
    async def test_predictions(self, client):
        result = await client.gpu_health.predictions()
        assert result[0]["failure_probability"] == 0.02


class TestReselling:
    @pytest.mark.asyncio
    async def test_profile(self, client):
        result = await client.reselling.profile()
        assert result["name"] == "CloudPartner"

    @pytest.mark.asyncio
    async def test_customers(self, client):
        result = await client.reselling.customers()
        assert result[0]["name"] == "Customer A"

    @pytest.mark.asyncio
    async def test_create_customer(self, client):
        result = await client.reselling.create_customer("Customer B", "cust-b")
        assert result["name"] == "Customer B"

    @pytest.mark.asyncio
    async def test_pricing_rules(self, client):
        result = await client.reselling.pricing_rules()
        assert result[0]["markup_pct"] == 20


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

    @pytest.mark.asyncio
    async def test_forbidden_raises(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"detail": "Forbidden"})

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with pytest.raises(ForbiddenError, match="Forbidden"):
            await c.clusters.list()
        await c.close()

    @pytest.mark.asyncio
    async def test_conflict_raises(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(409, json={"detail": "Resource already exists"})

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.gateways import GatewaysResource
        c.gateways = GatewaysResource(c._http)

        with pytest.raises(ConflictError, match="Resource already exists"):
            await c.gateways.register("dup-gw")
        await c.close()

    @pytest.mark.asyncio
    async def test_validation_error_raises(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json={"detail": "Invalid field"})

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.jobs import JobsResource
        c.jobs = JobsResource(c._http)

        with pytest.raises(ValidationError, match="Invalid field"):
            await c.jobs.create("bad_action")
        await c.close()

    @pytest.mark.asyncio
    async def test_rate_limit_raises(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"detail": "Too Many Requests"})

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with pytest.raises(RateLimitError, match="Too Many Requests"):
            await c.clusters.list()
        await c.close()

    @pytest.mark.asyncio
    async def test_connection_timeout_raises(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out")

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with pytest.raises(TimeoutError, match="timed out"):
            await c.clusters.list()
        await c.close()

    @pytest.mark.asyncio
    async def test_connection_refused_raises(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with pytest.raises(ConnectionError, match="Cannot connect to VibOps"):
            await c.clusters.list()
        await c.close()


# ---------------------------------------------------------------------------
# Retry on 429/502/503
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
        assert (result[0].name if hasattr(result[0], 'name') else result[0]["name"]) == "gpu-prod"
        await c.close()

    @pytest.mark.asyncio
    async def test_retry_on_429(self):
        call_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(429, json={"detail": "Too Many Requests"})
            return httpx.Response(200, json=[{"name": "gpu-prod"}])

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with patch("vibops.resources.asyncio.sleep", new_callable=AsyncMock):
            result = await c.clusters.list()
            assert call_count == 2
            assert (result[0].name if hasattr(result[0], 'name') else result[0]["name"]) == "gpu-prod"
        await c.close()

    @pytest.mark.asyncio
    async def test_retry_429_uses_retry_after_header(self):
        """When 429 includes Retry-After, that value should be used as sleep duration."""
        call_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(
                    429,
                    json={"detail": "Too Many Requests"},
                    headers={"Retry-After": "3"},
                )
            return httpx.Response(200, json=[{"name": "gpu-prod"}])

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with patch("vibops.resources.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await c.clusters.list()
            assert call_count == 2
            mock_sleep.assert_called_once_with(3.0)
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

    @pytest.mark.asyncio
    async def test_retry_backoff_sleeps(self):
        """Verify exponential backoff sleeps are called during retries."""
        call_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return httpx.Response(502, json={"detail": "Bad Gateway"})
            return httpx.Response(200, json=[{"name": "gpu-prod"}])

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.clusters import ClustersResource
        c.clusters = ClustersResource(c._http)

        with patch("vibops.resources.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await c.clusters.list()
            assert call_count == 3
            assert (result[0].name if hasattr(result[0], 'name') else result[0]["name"]) == "gpu-prod"
            # Should have slept twice: 0.5s then 1.0s
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(0.5)
            mock_sleep.assert_any_call(1.0)
        await c.close()


# ---------------------------------------------------------------------------
# _put helper (M6)
# ---------------------------------------------------------------------------

class TestPutHelper:
    @pytest.mark.asyncio
    async def test_put_method(self, client):
        """The _put helper should send a PUT request."""
        from vibops.resources import Resource
        resource = Resource(client._http)
        result = await resource._put("test/put", json={"key": "value"})
        assert result["updated"] is True


# ---------------------------------------------------------------------------
# Typed responses (M4)
# ---------------------------------------------------------------------------

class TestTypes:
    def test_parse_cluster(self):
        data = {"name": "gpu-prod", "gpu_total": 8, "gpu_used": 4, "online": True}
        result = parse(Cluster, data)
        assert isinstance(result, Cluster)
        assert result.name == "gpu-prod"
        assert result.gpu_total == 8

    def test_parse_job(self):
        data = {"id": "j-1", "action": "deploy", "status": "running", "payload": {"x": 1}}
        result = parse(Job, data)
        assert isinstance(result, Job)
        assert result.id == "j-1"
        assert result.payload == {"x": 1}

    def test_parse_budget(self):
        data = {"monthly_limit_usd": 5000, "spent_usd": 1234, "utilization_pct": 24.68}
        result = parse(Budget, data)
        assert isinstance(result, Budget)
        assert result.monthly_limit_usd == 5000

    def test_parse_insight(self):
        data = {"id": "i-1", "insight_type": "idle_gpu", "severity": "warning",
                "title": "Idle GPU", "description": "GPU is idle", "acknowledged": False}
        result = parse(Insight, data)
        assert isinstance(result, Insight)
        assert result.id == "i-1"
        assert result.recommendation is None

    def test_parse_with_extra_fields_ignores_them(self):
        data = {"name": "gpu-prod", "gpu_total": 8, "extra_field": "ignored"}
        result = parse(Cluster, data)
        assert isinstance(result, Cluster)
        assert result.name == "gpu-prod"

    def test_parse_with_missing_required_field_returns_dict(self):
        """If the required 'name' field is missing, parse returns the raw dict."""
        data = {"gpu_total": 8}
        result = parse(Cluster, data)
        assert isinstance(result, dict)

    def test_parse_non_dict_returns_as_is(self):
        result = parse(Cluster, "not a dict")  # type: ignore[arg-type]
        assert result == "not a dict"


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

class TestStreaming:
    @pytest.mark.asyncio
    async def test_stream_logs_method_exists(self, client):
        """Verify stream_logs exists and is callable."""
        assert hasattr(client.jobs, "stream_logs")
        assert callable(client.jobs.stream_logs)

    @pytest.mark.asyncio
    async def test_stream_logs_calls_correct_endpoint(self):
        """Verify stream_logs calls the correct SSE endpoint."""
        streamed_url = None

        class FakeStreamResponse:
            async def aiter_lines(self):
                yield "data: line1"
                yield "data: line2"
                yield "ignore this"

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                pass

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        c = AsyncVibOps(url="https://vibops.test", token="tok")
        c._http = httpx.AsyncClient(
            transport=_make_transport(handler),
            base_url="https://vibops.test",
        )
        from vibops.jobs import JobsResource
        c.jobs = JobsResource(c._http)

        fake_response = FakeStreamResponse()

        with patch.object(c._http, "stream", return_value=fake_response) as mock_stream:
            lines = []
            async for line in c.jobs.stream_logs("job-99"):
                lines.append(line)

            mock_stream.assert_called_once_with("GET", "/api/v1/jobs/job-99/logs/stream")
            assert lines == ["line1", "line2"]
        await c.close()


# ---------------------------------------------------------------------------
# Sync wrapper
# ---------------------------------------------------------------------------

class TestSyncWrapper:
    def test_sync_wrapper_works(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[{"name": "gpu-prod", "gpu_total": 8, "gpu_used": 4, "online": True}])

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
        assert result[0].name == "gpu-prod"
        client.close()
