# VibOps Python SDK

Typed Python SDK for the [VibOps](https://vibops.ai) API -- The AI Infrastructure Engine.

## Install

```bash
pip install vibops
```

## Quick start

```python
from vibops import VibOps

v = VibOps(url="https://vibops.example.com", token="vib_...")

# List GPU clusters
clusters = v.clusters.list()

# Deploy a model
job = v.models.deploy("llama3", "gpu-prod", replicas=2)

# Check FinOps budget
budget = v.finops.budget()

# List proactive insights
insights = v.insights.list(severity="critical")
```

### Async usage

```python
import asyncio
from vibops import AsyncVibOps

async def main():
    async with AsyncVibOps(url="https://vibops.example.com", token="vib_...") as v:
        clusters = await v.clusters.list()
        jobs = await v.jobs.list(status="running")
        waste = await v.finops.waste(sustained_hours=6)

asyncio.run(main())
```

## Resources

| Resource | Methods |
|----------|---------|
| `clusters` | `list()`, `deployments(cluster)`, `gpu_metrics(cluster)` |
| `jobs` | `list()`, `get(id)`, `create(action, payload)`, `cancel(id)` |
| `models` | `deploy(model, cluster)`, `scale(name, namespace, replicas, cluster)` |
| `gateways` | `list()`, `register(name)`, `delete(id)` |
| `finops` | `budget()`, `spend_trend()`, `chargeback()`, `waste()`, `live_cost()` |
| `agents` | `usage()`, `usage_detail(id)`, `budget(id)`, `set_budget(id, limit)`, `list_budgets()` |
| `security` | `scan()`, `findings()` |
| `compliance` | `check()`, `results()` |
| `insights` | `list()`, `acknowledge(id)` |

## Error handling

```python
from vibops.exceptions import AuthenticationError, NotFoundError, RateLimitError

try:
    job = v.jobs.get("nonexistent")
except NotFoundError:
    print("Job not found")
except AuthenticationError:
    print("Check your token")
```

Auto-retry is built in for 502/503 responses (1 retry).

## License

MIT
