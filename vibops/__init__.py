"""VibOps Python SDK — The AI Infrastructure Engine."""

from vibops.alerts import AlertsResource
from vibops.anomalies import AnomaliesResource
from vibops.audit import AuditResource
from vibops.auth import AuthResource
from vibops.client import AsyncVibOps, VibOps
from vibops.eval import EvalResource
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
from vibops.gpu_health import GpuHealthResource
from vibops.identities import IdentitiesResource
from vibops.metrics import MetricsResource
from vibops.notifications import NotificationsResource
from vibops.orgs import OrgsResource
from vibops.pipelines import PipelinesResource
from vibops.policy import PolicyResource
from vibops.reselling import ResellingResource
from vibops.secrets import SecretsResource
from vibops.tokens import TokensResource
from vibops.triggers import TriggersResource
from vibops.types import Budget, Cluster, Insight, Job
from vibops.webhooks import WebhooksResource
from vibops.workloads import WorkloadsResource

__all__ = [
    "AsyncVibOps",
    "VibOps",
    # Types
    "Budget",
    "Cluster",
    "Insight",
    "Job",
    # Resource classes
    "AlertsResource",
    "AnomaliesResource",
    "AuditResource",
    "AuthResource",
    "EvalResource",
    "GpuHealthResource",
    "IdentitiesResource",
    "MetricsResource",
    "NotificationsResource",
    "OrgsResource",
    "PipelinesResource",
    "PolicyResource",
    "ResellingResource",
    "SecretsResource",
    "TokensResource",
    "TriggersResource",
    "WebhooksResource",
    "WorkloadsResource",
    # Exceptions
    "VibOpsError",
    "AuthenticationError",
    "ConflictError",
    "ConnectionError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
]
__version__ = "0.1.0"
