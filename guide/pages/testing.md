# Testing

An app has two suites: the backend's pytest suite, and the frontend's Playwright specs, which run
against a real backend. These rules hold for both, and for the backend's tests. The Playwright
specs have [their own page](playwright.md).

### TEST-1 — Tests run against the real infrastructure { #test-1 }

A test MUST run against the real systems the app runs on: PostgreSQL, the S3 storage, any other
service the app's environment provides, and, under Playwright, the backend. A test MUST NOT replace
one of them with a mock or a fake, unless the operator approved that mock.

Signing in is where the template stands in for the identity provider: the backend's tests use its
token fixtures, and the specs its test sessions (`/api/testing/auth/session`).

**Why.** A mock behaves as its author expects the system to, so the test passes where the system
would fail. The bugs that matter sit where the app meets the system: a query the database refuses,
a migration that leaves the schema short, an object the storage does not hold, an event the
backend's stream does not deliver. The dev environment and CI run each of these systems for the
tests, and every test database is built by the app's migrations.

### TEST-2 — A missing system stops the run { #test-2 }

A suite that needs a system MUST check that the system answers before the first test, and stop
the run with `pytest.exit()` and a message that says how to fix it, as the template does for
PostgreSQL and S3. A test MUST NOT skip because a system is down, as with `skipif`.

**Why.** A skipped test reports nothing: a run with the system down comes out green, and the tests
that would have failed are never seen. Stopped at once, the run fails with one message that names
the system, instead of a page of connection errors.

### TEST-3 — A failing test is a regression { #test-3 }

A test that fails after a change MUST be taken as broken by that change, and fixed. It MUST NOT be
dismissed as flaky. A failure is a flake only when it is intermittent under load and passes on a
retry, and CI's retries absorb those: the suite runner retries a failed spec twice
(`run-suite --retries 2`). Test code MUST NOT retry on its own, beyond waiting for a system that is
eventually consistent.

**Why.** The suite is green before the change, so a failure after it is the change's until shown
otherwise. A failure called flaky is one that nobody fixes, and a suite with known failures hides
the next real one. A retry in test code turns a real race into a slower pass.

### TEST-4 — A backend test module mirrors the module it tests { #test-4 }

The tests of `app/<path>/<module>.py` MUST be in `tests/<path>/test_<module>.py`, grouped in
`Test<Name>` classes: `TestProjectService` for a service, `TestProjectsApi` for an endpoint module.
They use the template's fixtures: `app`, `session`, `container` and `client`.

**Why.** A module's tests, or the lack of them, are found without a search. pytest collects
`test_*.py`, `Test*` and `test_*` (`pyproject.toml`), so a test named any other way never runs.

### TEST-5 — A service and an endpoint are tested in full { #test-5 }

A service's tests MUST cover every public method: the success paths with their combinations of
input, every error the method raises, the edge cases such as empty data and boundaries, and the
database constraints it relies on.

An endpoint module's tests MUST cover every endpoint and method: request validation, with invalid
and missing fields, the response's shape, and every status code, its errors included.

**Why.** A change breaks a caller most often on a path the author did not exercise: an error, an
empty list, a boundary. A test of the success path shows that the code runs, not that it refuses
what it must.

### TEST-6 — A testing endpoint comes before the UI that needs it { #test-6 }

When a spec needs state the UI cannot make, such as a seeded record, a session or a forced
failure, the backend's testing endpoint for it MUST be in place before the frontend work starts.
A testing endpoint lives under `/api/testing/`, in a blueprint whose `before_request` hook calls
`reject_if_not_testing()` (`app/api/testing_guard.py`).

**Why.** Without the endpoint the spec cannot be written, so the UI ships without its coverage
([PW-1](playwright.md#pw-1)) or with a mock ([TEST-1](#test-1)). The guard refuses every call
unless the backend runs with `FLASK_ENV=testing` and a `STAGE` other than `prd`, so a testing
endpoint never runs in production, although its blueprint is registered there.

## Recipe

A pre-flight for a system the app adds, in `tests/conftest.py`. The template's pre-flight is the
`pytest_configure` hook that `tests/conftest.py` imports from `conftest_infrastructure.py` with
`*`, so a `pytest_configure` of the app's own there would replace it. The app's check is a
`pytest_sessionstart` hook, which pytest runs after it:

```python
def pytest_sessionstart(session: pytest.Session) -> None:
    """Stop the run before the first test when the search cluster is down."""
    url = os.environ.get("SEARCH_URL", "")
    try:
        requests.get(f"{url}/_cluster/health", timeout=3)
    except requests.RequestException:
        pytest.exit(
            f"The search cluster is not reachable at {url!r}. "
            "Start it, or set SEARCH_URL in .env.test.",
            returncode=1,
        )
```
