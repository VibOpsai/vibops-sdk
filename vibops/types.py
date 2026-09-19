"""VibOps SDK response types — lightweight dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, TypeVar

T = TypeVar("T")

__all__ = [
    "Budget",
    "Cluster",
    "Insight",
    "Job",
    "parse",
]


@dataclass
class Cluster:
    """A GPU cluster registered in VibOps."""

    cluster_name: str
    gateway_id: str = ""
    gateway_name: str = ""
    status: str = "online"
    gpu_total: int | None = 0
    gpu_used: int | None = 0


@dataclass
class Job:
    """A VibOps job — every field `GET /api/v1/jobs/{id}` returns.

    It used to carry four of the twenty-two. `parse()` filters a response to the
    fields a dataclass declares and discards the rest in silence, so an SDK caller
    could not see why a job had failed: `error`, `result`, `logs`, `exit_code` and
    `failure_reason_category` were all dropped before reaching them. The figure
    was not wrong, it was absent — which is the same defect wearing a different
    face, and `tests/test_sdk_field_parity.py` now prevents it recurring.
    """

    id: str
    action: str = ""
    status: str = ""
    payload: dict = None  # type: ignore[assignment]

    # ── Outcome ──────────────────────────────────────────────────────────────
    result: dict | None = None
    error: str | None = None
    logs: str | None = None
    outcome: str | None = None
    exit_code: int | None = None
    failure_reason_category: str | None = None

    # ── Provenance and timing ────────────────────────────────────────────────
    triggered_by: str | None = None
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    actual_duration_s: float | None = None

    # ── Workload identity and cost ───────────────────────────────────────────
    workload_signature: dict | None = None
    vendor: str | None = None
    accelerator_type: str | None = None
    framework: str | None = None
    framework_version: str | None = None
    model_name: str | None = None
    actual_cost_usd: float | None = None

    def __post_init__(self) -> None:
        if self.payload is None:
            self.payload = {}


@dataclass
class Budget:
    """A budget — every field `GET /api/v1/finops/budget` returns.

    It used to carry three of the seventeen, and the two it dropped first were
    `gpu_spend_usd` and `vm_spend_usd` — precisely the pair OpContract rule 2
    binds to the total. The console showed them, the agent could report them, and
    an SDK caller could not reach them at all.
    """

    # ── Identity ─────────────────────────────────────────────────────────────
    id: str = ""
    org_id: str = ""
    currency: str = "USD"
    is_active: bool = True
    created_at: str = ""

    # ── Limits ───────────────────────────────────────────────────────────────
    monthly_limit_usd: float = 0.0
    soft_cap_pct: float = 0.0
    hard_cap_pct: float = 0.0

    # ── Spend — current_spend_usd = gpu_spend_usd + vm_spend_usd (rule 2) ────
    current_spend_usd: float = 0.0
    gpu_spend_usd: float = 0.0
    vm_spend_usd: float = 0.0
    waste_usd_per_month: float = 0.0
    spend_pct: float = 0.0

    # ── Forecast ─────────────────────────────────────────────────────────────
    daily_burn_rate_usd: float = 0.0
    spend_forecast_eom_usd: float = 0.0
    days_elapsed: int = 0
    days_in_month: int = 0


@dataclass
class Insight:
    """Proactive infrastructure insight."""

    id: str
    insight_type: str = ""
    severity: str = ""
    title: str = ""
    description: str = ""
    recommendation: str | None = None
    acknowledged: bool = False


def parse(cls: type[T], data: dict[str, Any]) -> T | dict[str, Any]:
    """Convert a dict to a dataclass instance.

    Returns the raw dict if required fields are missing or if *data* is not
    a dict. This keeps backward compatibility — callers that relied on raw
    dicts will still work.
    """
    if not isinstance(data, dict):
        return data  # type: ignore[return-value]
    field_names = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    try:
        filtered = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered)  # type: ignore[call-arg]
    except TypeError:
        return data
