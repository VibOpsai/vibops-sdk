# Changelog

## [0.1.0] — 2026-08-18

### Added
- Initial release
- 9 resource namespaces: clusters, jobs, models, gateways, finops, agents, security, compliance, insights
- Async-first with sync wrapper
- Auto-retry with exponential backoff (429 with Retry-After, 502, 503)
- Typed exceptions (including ConflictError for 409)
- Typed response dataclasses: Cluster, Job, Budget, Insight
- Pagination support (list_all)
- SSE streaming (stream_logs)
- Per-request timeout support
- Configurable retry_statuses and event_hooks
- py.typed marker for PEP 561
