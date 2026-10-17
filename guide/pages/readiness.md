# Readiness

`GET /health/readyz` runs a check for each system the app depends on, and reports each by name.
Kubernetes' readiness probe reads its status code. These rules say who registers a check, when it
fails the probe, and how it bounds its own time.

### READY-1 — A service registers the check of the system it depends on { #ready-1 }

A service that depends on an external system MUST register the readiness check for that system
itself, with `HealthService.register_check()`. The container passes the service its
`health_service`. A `Singleton` registers in its constructor, as `SSEConnectionManager` does; a
`Factory`, built anew for each use, registers once, from its startup hook, as `S3Service.startup()`
does. A new integration brings its check in the same change.

**Why.** Readyz reports what is registered and nothing else, so a dependency without a check is
down without the probe or the readyz body saying so. Owned by the service, the check comes and goes
with it, and there is no list elsewhere for a new integration to be missing from.

### READY-2 — A check is critical only when the app cannot serve without its system { #ready-2 }

`register_check()` takes `critical` with no default. It MUST be `True` only when the app cannot
serve its requests without the system, as for the database and S3. Any other check MUST be
`critical=False`, as the SSE gateway's is.

**Why.** Readyz answers `503` when a critical check fails, and Kubernetes takes the pod out of
service. Every replica shares the system, so its outage takes every pod out at once, and the app
then serves nothing, not even the pages that never needed that system. A failing non-critical
check is reported, with the body's `status` at `degraded`, and the pod goes on serving.

### READY-3 — A check is one quick call, and its I/O times out { #ready-3 }

A check MUST make one cheap call to its system, such as a bucket's `head_bucket` or the gateway's
own readyz. It returns a `CheckResult`: `CheckStatus.OK`, or `CheckStatus.ERROR` with a `detail`;
an exception it raises is reported as an error. Its I/O MUST carry a timeout of its own.

**Why.** Readyz waits for each check for its `timeout`, 0.8 seconds by default, under the probe's
1-second timeout, and runs the checks side by side. A check that outlives its `timeout` is reported
as an error and goes on running in its own thread, and the probes after it wait on that same run.
Only the I/O's own timeout ends that run, so a check without one holds its thread for as long as
the system hangs, and its recovery shows only once the run ends. A passing result is cached for 30
seconds; a failing one is not, so a recovery shows at the next probe after the run.

## Recipe

A service that calls a search cluster, which the app can serve without:

```python
class SearchService:
    def __init__(self, settings: Settings, health_service: HealthService) -> None:
        self.settings = settings
        # Not critical: every page renders without search.
        health_service.register_check("search", self.check_readiness, critical=False)

    def check_readiness(self) -> CheckResult:
        """Readiness check: the cluster answers its health endpoint."""
        response = requests.get(f"{self.settings.search_url}/_cluster/health", timeout=2)
        if response.status_code != 200:
            return CheckResult(CheckStatus.ERROR, f"cluster answered {response.status_code}")
        return CheckResult(CheckStatus.OK)
```

In `app/services/container.py`, below `health_service`:

```python
search_service = providers.Singleton(SearchService, settings=config, health_service=health_service)
```
