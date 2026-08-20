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
| `jobs` | `list()`, `get(id)`, `create(action, payload)`, `cancel(id)`, `stream_logs(id)` |
| `models` | `deploy(model, cluster)`, `scale(name, namespace, replicas, cluster)` |
| `gateways` | `list()`, `register(name)`, `delete(id)` |
| `finops` | `budget()`, `spend_trend()`, `chargeback()`, `waste()`, `live_cost()` |
| `agents` | `usage()`, `usage_detail(id)`, `budget(id)`, `set_budget(id, limit)`, `list_budgets()` |
| `security` | `scan()`, `findings()` |
| `compliance` | `check()`, `results()` |
| `insights` | `list()`, `acknowledge(id)` |
| `auth` | `login(user, password)`, `me()`, `refresh(token)`, `forgot_password()`, `reset_password()` |
| `audit` | `list()`, `verify_chain()`, `export()` |
| `anomalies` | `list()`, `open()`, `resolve(id)` |
| `alerts` | `list()`, `rules()`, `create_rule()`, `delete_rule(id)` |
| `secrets` | `list()`, `create(name, value)`, `delete(name)` |
| `pipelines` | `list()`, `create()`, `trigger(id)` |
| `tokens` | `list()`, `create()`, `delete(id)` |
| `notifications` | `channels()`, `create_channel()`, `delete_channel(id)`, `test_channel(id)` |
| `policy` | `get()`, `update()`, `model_rules()`, `create_model_rule()` |
| `identities` | `list()`, `create()`, `rotate(id)`, `revoke(id)` |
| `orgs` | `get(id)`, `update(id)`, `users(id)`, `create_user()`, `teams()`, `invite()` |
| `metrics` | `gpu()`, `cost_estimate()`, `workload_breakdown()`, `mttr()`, `job_metrics()` |
| `triggers` | `list()`, `create()`, `enable(id)`, `disable(id)`, `delete(id)` |
| `eval` | `rubrics()`, `create_rubric()`, `evaluate(job_id, rubric_id)`, `results(job_id)` |
| `workloads` | `list()`, `get(id)`, `cost_summary()` |
| `webhooks` | `subscriptions()`, `create_subscription()`, `delete_subscription(id)` |
| `gpu_health` | `predictions()` |
| `reselling` | `profile()`, `customers()`, `create_customer()`, `pricing_rules()` |

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

Auto-retry is built in for 429/502/503 responses (2 retries with exponential backoff).

## License

MIT
