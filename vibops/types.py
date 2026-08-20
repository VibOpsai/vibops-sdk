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

    name: str
    gpu_total: int = 0
    gpu_used: int = 0
    online: bool = True


@dataclass
class Job:
    """A VibOps job."""

    id: str
    action: str = ""
    status: str = ""
    payload: dict = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.payload is None:
            self.payload = {}


@dataclass
class Budget:
    """FinOps budget summary."""

    monthly_limit_usd: float = 0.0
    spent_usd: float = 0.0
    utilization_pct: float = 0.0


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
