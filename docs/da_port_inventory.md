# DesignAssistant: candidate changes for the template

DesignAssistant (`pvginkel/DesignAssistant`, archived) was generated from backend template v0.12.0 and frontend template v0.18.1. The frontend template was used twice: `frontend/` with the app shell and `portal/` without. DA kept its own monorepo root, which pre-dates the root template. DA then grew into a product-grade app. This document lists every change in DA that the template could adopt, each with a recommendation. DA itself will not be synced.

**How it was built.** The template was rendered at DA's versions with DA's own copier answers, and every template-owned file was diffed against DA. DA's new files were surveyed for generic infrastructure, and DA's git history supplied the reasons (SHAs below are DA commits; the repo is cloned at `/work/scratch/DesignAssistant`). DA's root was only checked against the root template's file list.

**Not done yet:** checking which of these changes have already landed in the template or in another app. That is the next step, run over the items selected here. Some will turn out to be done already.

## Recommendation

113 items after merging duplicates: 27 Port, 31 Port-adapted, 4 Diff at dedup, 36 Optional, 15 Skip.

- **Port all of the Port items.** They are bug fixes and hardening in template-owned code, plus tests for template code. Nearly all are small and self-contained. The ones that matter most:
  - BE-C01: when `read_role` is unset, an authenticated user with none of the app's roles can call every GET endpoint, despite the documented blanket 403.
  - BE-C02: readiness stays green when the pending-migrations check throws.
  - BE-C03, BE-C04: SSE events fire before the transaction commits; DB connections from background threads sit idle-in-transaction until GC.
  - FE02, FE03: task events between the 202 and the subscribe are lost, and progress bars never pass 1% (the backend sends 0..1, the frontend reads a percentage).
  - FE07: the generated TypeScript request types make optional update fields required.
  - FE12: the Vite dev proxy can buffer an SSE stream forever.
  - FE04–FE06, FE09: the template's own Playwright infrastructure leaves orphaned servers after an interrupted run, and its infrastructure specs cannot pass with `use_oidc`.
  - BE-T04, BE-T05: about 100 tests for TaskService and the OIDC BFF, the least-tested template areas.
- **Port-adapted: take the generic half.** The largest is one cross-stack SSE/auth piece that must move together across the backend, frontend and SSE gateway: the connect callback rejects with 401/403 (BE-T11), the frontend handles `rejected` with refresh and reconnect (FE16), `connected` waits for the gateway's `ready` event (FE15), SSE targets are typed with no implicit broadcast (BE-T10), and the FrontendVersionService leak is fixed (BE-T12). The auth refactor (BE-C12 with BE-T09) and the health rework (BE-C02 → BE-C13 with BE-T13) are the other two medium-sized pieces. FE17 contains a plain bug: `vite.config.ts` has its test-mode logic inverted, so a production build can never carry the Playwright bridges.
- **Decisions for you.** Each is Port-adapted and changes something visible:
  1. Run backend tests against Postgres instead of SQLite, with a session-scoped app and rollback isolation (BE-T07, BE-T06, FE23). In DA this surfaced FK and CHECK bugs that SQLite hid, and the suite ran fast.
  2. Derive the OIDC `redirect_uri` from the request origin instead of `BASEURL` (BE-C15). The stricter relative-only redirect check is worth taking either way.
  3. Use the shared `modern-app-backend*` base images and the pnpm build cache in CI (BE-C17, RT05).
  4. Raw exception text in 500 responses (BE-C14): hide it outside debug, or keep it for internal hobby apps.
- **Conventions go into a skill**, not template docs (RT08, RT09, RT11, RT13, RT14, BE-T17). They cover exhaustive status enums, toast discipline, UUID paths, the 2-second background-task rule, testing against real dependencies, `perf_counter`, and failing fast.
- **Optional: leave these in DA until an app needs them.** These are the product-grade capabilities: the Celery worker and Beat (BE-C19), email (BE-C20), multi-tenancy (BE-C21), i18n (BE-C22, FE25), ICU collations (BE-C23), the RabbitMQ SSE transport (BE-T20), pagination and sorting (BE-C27, FE31), coverage, Vitest, the code-health grader, and staged deploys. DA stays readable as the reference implementation, and each item says what porting would cost.
- **Skip** includes two DA changes that are worse than the template: `DRAIN_AUTH_KEY` defaults to `changeme!` (BE-C33), and nginx caches `/version.json` for a year (FE35).

## Dependencies between items

- **SSE auth rejection:** BE-T11 (backend 401/403) + FE16 (frontend) + an SSEGateway version that emits `rejected`. FE16's spec needs FE17's preview mode, because the SharedWorker path doesn't run under the Vite dev server.
- **SSE readiness:** FE15 needs an SSEGateway version that emits a named `ready` event once bindings exist. DA tied that to its RabbitMQ transport (BE-T20), so check that the callback transport emits it too.
- **SSE targeting:** BE-T10 → BE-T04's assertions; BE-T12 depends on the stateless manager for its startup-only broadcast, so port only the parts that don't.
- **Testing log stream:** BE-T01 removes the `connection_close` event; DA's frontend had no consumer for it.
- **Auth:** BE-C01 → BE-C12 (`@no_role_check` keeps logout reachable) → BE-T09. BE-C15 ↔ BE-T05's redirect tests.
- **Health:** BE-C02 → BE-C13 → BE-T13. The readyz wire format changes, so the root template's probes and anything parsing the body move with it. FE18 deliberately does not accept a 503.
- **Config:** BE-C06 → BE-T15. BE-C18 is shared with the pytest settings.
- **Test database:** BE-T07 (Postgres) pairs with BE-T06 (session-scoped app) and FE23 (per-worker databases cloned from a seed). BE-C09's `--database-url` serves the same path.
- **Conventions skill:** RT08, RT09, RT11, RT13, RT14, BE-T17; RT13's preview-mode gotcha belongs with FE17.

## Summary by recommendation

### Port (27)

| ID | Change | Applies to | Effort |
|----|--------|------------|--------|
| BE-C01 | Hoist the "no recognized role" 403 above the per-tier role lookup | apps with `use_oidc` | S |
| BE-C02 | `get_pending_migrations` must not swallow errors | apps with `use_database` | S |
| BE-C03 | `add_after_commit`: run side effects only once the transaction is durable | apps with `use_database` + `use_sse` | S |
| BE-C04 | `scoped_session` / `scoped_savepoint` context managers | apps with `use_database` that touch the DB off the request path | S |
| BE-C05 | Always-on HTTP request metrics middleware | all apps | S |
| BE-C06 | Secret-redacting settings dump at boot, `LOG_LEVEL`, and `ExtraFieldFormatter` | all apps | S-M |
| BE-C08 | Pillow 12 typing fix and the version bumps that required it | apps with `use_s3` | S |
| BE-C09 | `testing-server.sh`: source `.env.test`, `--database-url`, and run through `poetry run dev` | all apps with Playwright | S |
| BE-C10 | `.gitignore`: ignore every `.env*` except `.env.example`; ignore `coverage/` | all apps | S |
| BE-C11 | `allow_empty` opt-out for empty-string normalization | apps with `use_database` | S |
| BE-T01 | Testing log stream: per-stream shutdown sentinel, `unregister_lifecycle_notification`, safe dispatch | all apps | S |
| BE-T04 | TaskService / TaskProgressHandle tests | all apps | S-M |
| BE-T05 | OIDC auth core tests: `AuthService`, `OidcClientService`, redirect validation | apps with `use_oidc` | S-M |
| FE01 | Tooltip title-mode clobbers the child's `data-testid` | all apps | S |
| FE02 | `useSSETask`: persistent task-event buffer (race between HTTP 202 and subscribe) | apps with `use_sse` that use background tasks | S |
| FE03 | Task progress values are 0..1 on the wire but treated as a percentage | apps with `use_sse` using `useSSETask` | S |
| FE04 | Playwright-managed service teardown kills the whole process tree | all apps | S |
| FE05 | Infrastructure specs need an auth session when `use_oidc` is on | apps with `use_oidc` and `use_sse` | S |
| FE06 | SSE/deployment test helpers: wait for bridges, longer timeouts | apps with `use_sse` | S |
| FE07 | `generate-api.js`: `--default-non-nullable false` | all apps | S |
| FE08 | `useUiStateInstrumentation`: emit `ready` when data is already cached on mount | all apps | S |
| FE09 | Console policy: allow `Toast exception` globally | all apps | S |
| FE10 | `.dockerignore` for the frontend image | all apps | S |
| FE11 | ESLint/knip configuration fixes | all apps | S |
| FE12 | Vite dev/preview proxy: forwarded headers, SSE header flush, `strictPort` | apps with `use_sse` | S |
| FE13 | nginx `Host $http_host` | all apps | S |
| FE14 | Playwright video off by default | all apps | S |

### Port-adapted (31)

| ID | Change | Applies to | Effort |
|----|--------|------------|--------|
| BE-C12 | `@public` becomes "auth-optional": tolerant mode, shared `resolve_auth_identity`, logout cookie clearing | apps with `use_oidc` | M-L |
| BE-C13 | `HealthService` rework: registration-driven, concurrent, cached, per-check timeout, readyz 503 on degraded | all apps | M |
| BE-C14 | Sanitize the generic 500 handler | all apps | S |
| BE-C15 | OIDC redirect URI derived from the request origin; redirect param must be a relative path | apps with `use_oidc` | M |
| BE-C16 | Enforce an upload size limit via `MAX_CONTENT_LENGTH` | apps with upload endpoints | S |
| BE-C17 | Dockerfile on shared base images | all apps | S |
| BE-C18 | Smaller SQLAlchemy pool in testing mode | apps with `use_database` | S |
| BE-T06 | Session-scoped Flask app with connection-level rollback isolation | all apps with `use_database` | M |
| BE-T07 | Real PostgreSQL test database (per-run unique DB, stale cleanup, ICU) instead of SQLite | apps with `use_database` that run PostgreSQL in production | M-L |
| BE-T09 | Auth middleware tests: tolerant vs throwing `authenticate_request`, `@public`, `@no_role_check`, `/api/auth/self` | apps with `use_oidc` | M |
| BE-T10 | Typed SSE `Target`; no implicit broadcast for task events | apps with `use_sse` | M |
| BE-T11 | SSE connect callback rejects unauthenticated or role-less connections; forced-rejection test hook | apps with `use_sse` + `use_oidc` | M |
| BE-T12 | `FrontendVersionService`: no per-connection pending state, no bogus "unknown" payload, skip in local stages | apps with `use_sse` | S-M |
| BE-T13 | HealthService tests (registration-driven checks, caching, shutdown, drain) | all apps | M |
| BE-T14 | S3 service unit tests (mocked boto3) | apps with `use_s3` | S-M |
| BE-T15 | Config tests: secret redaction guard, config dump coverage, log level, test pool | all apps | S |
| BE-T16 | Task endpoints restricted to an explicit role | apps with `use_oidc` that have more than one role | S |
| BE-T17 | Test conventions and SSE targeting docs | all apps | S |
| FE15 | SSE ready-event gating (late-joining tab fix included) | apps with `use_sse` | M |
| FE16 | SSE auth rejection: terminal `rejected`, token refresh, forced `reconnect` | apps with `use_sse` and `use_oidc` | M-L |
| FE17 | Opt-in preview mode for Playwright (production build under test) and the Vite test-mode build fix | apps with `use_sse` | M |
| FE18 | Playwright service startup robustness | all apps | S |
| FE19 | Toast diagnostics copy affordance | all apps | M |
| FE20 | `use_app_shell=false` renders shell leftovers (user dropdown, shell-dependent auth tests) | apps with `use_app_shell=false` | S |
| FE21 | `index.css` customisations in a template-owned file | all apps | S |
| RT05 | Pnpm build cache for CI and image builds | all apps with a frontend built in Jenkins/kaniko | S |
| RT08 | Cross-cutting convention: status enums are exhaustive end-to-end | all apps | S |
| RT09 | Cross-cutting convention: toast discipline | all apps | S |
| RT11 | Cross-cutting convention: UUID path params and long-running-operation rule | all apps | S |
| RT13 | Cross-cutting convention: tests use real dependencies; testability is a first-class requirement | all apps | S |
| RT14 | Cross-cutting code-style rules (backend/frontend `code-style.md`) | all apps | S |

### Diff at dedup (4)

| ID | Change | Applies to | Effort |
|----|--------|------------|--------|
| RT01 | Counterpart exists: suite runner (local), display and process helpers | all apps | S-M |
| RT02 | Counterpart exists: Jenkinsfile validation pipeline | all apps | S |
| RT03 | Counterpart exists: dev orchestration (Procfile.dev, dev.py, dev-sse-gateway.sh, regenerate-openapi.py) | all apps | S |
| RT04 | Counterpart exists: root `pyproject.toml`, `.kubecoder/` config, `.vscode/settings.json`, workspace file, root CLAUDE.md | all apps | S |

### Optional (36)

| ID | Change | Applies to | Effort |
|----|--------|------------|--------|
| BE-C19 | Mode-aware app: `backend` / `worker` / `beat` with an embedded Celery worker and Beat | DA-only today | L |
| BE-C20 | Email sending (Gmail API client, queued `EmailService`, HTML/text templates) | DA-only today | M-L |
| BE-C21 | Multi-tenancy infrastructure (query-level tenant isolation) | DA-only | L |
| BE-C22 | Server-side localization (i18n) | DA-only | M |
| BE-C23 | ICU collations (case/accent-insensitive columns), collation startup check, `cli prepare`/recreate flow | apps with `use_database` that want accent/case-insensitive uniqueness | L |
| BE-C24 | `STAGE` taxonomy with stage-derived defaults | DA-only | S-M |
| BE-C25 | `AuthService` cross-cutting `role_hierarchy` with cycle detection | DA-only | S-M |
| BE-C26 | S3 service additions: presigned GET/PUT URLs, streaming, listing with metadata | apps with `use_s3` | S |
| BE-C27 | Pagination and sorting helpers | apps with `use_database` list endpoints | S |
| BE-C28 | Extra exception types and error-response schemas | all apps | S |
| BE-C29 | Dev hot reload via `watchmedo`, Werkzeug reloader removed | all apps | S-M |
| BE-C30 | `poetry run coverage` script | all apps | S |
| BE-C32 | Container: `MetricsService(container=Self())` resolved to `None` | all apps if a service ever uses `self.container` | S |
| BE-T18 | Service-mocking fixtures and the preflight pattern | `mock_s3` for apps with `use_s3` | S |
| BE-T20 | Stateless AMQP-publishing `SSEConnectionManager` (RabbitMQ transport); retired | apps that publish SSE events from a separate process | L |
| FE22 | Istanbul coverage for Playwright runs | apps that want E2E coverage numbers | M |
| FE23 | Per-worker PostgreSQL databases cloned from a seed template | apps with `use_database` if the backend template standardises on PostgreSQL for tests | L |
| FE24 | Vitest unit/component runner | apps with non-trivial client-side logic | S-M |
| FE25 | Localisation with react-i18next (portal) | apps with non-English users or multi-locale content | L |
| FE26 | Route loaders with `ensureQueryData`, pending UI and navigation progress bar | apps with detail pages that benefit from prefetch | M |
| FE27 | Non-blocking `SseGate` (portal) | apps with `use_sse` where SSE is not needed for first paint | S |
| FE28 | Dialog `preventOutsideClose` (default true), overlay test id | all apps | S |
| FE29 | Button loading overlay and no-wrap | all apps | S |
| FE30 | PID-namespace wrapper for Playwright (`unshare`) | Linux dev containers | S |
| FE31 | Server-side sort/pagination building blocks | apps with large lists | M-L |
| FE32 | Dev health indicator and stage indicator | apps with `use_app_shell` | S-M |
| FE33 | Sidebar: collapse animation and badge render prop | apps with `use_app_shell` | S |
| FE34 | Workspace package shared by two frontends (`packages/shared-ui`) | DA-only today | L |
| RT06 | Federated architecture producer pipeline | all apps | S |
| RT07 | Dependency update checker | all apps | S |
| RT16 | Code health grader (`code-health`) | all apps | M-L |
| RT17 | Multi-frontend pnpm workspace at the monorepo root | apps with a second frontend or shared packages | L |
| RT18 | Playwright memory profiler | apps with a Playwright suite in CI | S-M |
| RT19 | Unified coverage report | all apps | M |
| RT20 | Promote-by-retag deploy pipelines (UAT and PRD) | apps that want a staged release | S-M |
| RT21 | Remote suite runner (run tests in a cluster pod) | environments without local sidecars | L |

### Skip (15)

| ID | Change | Applies to | Effort |
|----|--------|------------|--------|
| BE-C33 | `DRAIN_AUTH_KEY` default changed from empty to `"changeme!"` | |  |
| BE-C34 | `check` script drops pytest | |  |
| BE-C35 | Dependency pin style normalised to `^N` / `^0.N` | |  |
| BE-C36 | Deleted dev/build scripts and `Jenkinsfile` | |  |
| BE-C37 | Environment defaults specific to DA | |  |
| BE-T21 | DA-specific testing endpoints, worker task publishing, Celery | DA-only | n/a |
| FE35 | nginx cache-control restructure (`location /` immutable) | DA-only | n/a |
| FE36 | Global 409 suppression in `query-client.ts` | DA-only | S |
| FE37 | Role enforcement in `useAuth` / `AuthGate` copy | DA-only | n/a |
| FE38 | Other DA-specific changes in template-owned files | DA-only | n/a |
| FE39 | DA-specific Playwright harness parts | DA-only | n/a |
| RT22 | Init.d-style build/preflight scripts | DA workflow | S |
| RT23 | Agent/dev-workflow tooling | DA-only | n/a |
| RT24 | Misc one-off DA scripts | DA-only | S |
| RT25 | Product ADRs and architecture docs | DA-only | n/a |

# Details

## Backend — core runtime, auth, config, storage, packaging

Scope: `/work/scratch/DesignAssistant/backend` vs `/work/scratch/da-base/backend` (backend template v0.12.0, all flags on). SSE, tasks, testing endpoints and the test suite are covered by another section; where an item touches them it says so. SHAs are DA commits.

Ordering: Port (BE-C01..C11), Port-adapted (C12..C18), Optional (C19..C32), Skip (C33..C37).

### BE-C01 — Hoist the "no recognized role" 403 above the per-tier role lookup

- **Files:** `app/utils/auth.py` (`check_authorization`)
- **What changed:** In the baseline, `check_authorization` first resolves the required role for the HTTP method and returns early when none is required; the blanket "no recognized role -> 403" check sits after that. In an app that configures no `read_role` (the DA case, and the template's `AuthService` default), a GET endpoint therefore has no required role. An authenticated caller with no recognized role at all got through every GET endpoint. DA moved the check to the top (`configured = auth_service.configured_roles; if configured and not (auth_context.roles & configured): raise AuthorizationException`), so it fires on every endpoint. In the baseline only `/api/auth/self` guarded this itself, in its handler.
- **Why:** Slice 176 `aea3da3e`: "hoisted above the per-tier required-role short-circuit so it fires on GET endpoints (the project does not configure read_role)". The frontend depends on it to tell 401 (not logged in) from 403 (logged in, no access).
- **Kind:** hardening
- **Applies to:** apps with `use_oidc` (matters when roles are configured but `read_role` is not)
- **Port effort:** S. Standalone: in the baseline `@public` endpoints skip the middleware, so login/callback/logout stay reachable. If BE-C12 is also ported, the `@no_role_check` decorator (auth-flow endpoints only) is needed to keep logout reachable for role-less users.
- **Recommendation:** Port — closes a real authorization gap for apps that don't set `read_role`.

### BE-C02 — `get_pending_migrations` must not swallow errors

- **Files:** `app/database.py`
- **What changed:** The baseline wrapped the whole function in `try/except Exception: return []  # fail safe`. Any failure (broken alembic config, DB error, bad revision graph) was reported as "no pending migrations", so the readyz database check passed and `cli upgrade-db` reported "up to date". DA removed the try/except so the error surfaces.
- **Why:** `d0928257` "Don't suppress database migration errors." No further rationale given.
- **Kind:** bug fix
- **Applies to:** apps with `use_database`
- **Port effort:** S — delete the try/except. A caller that relied on the swallow (the health check) must now catch; DA's `HealthService._check_database` does (see BE-C13), and so would the baseline `_check_db_readiness` in `app/__init__.py`.
- **Recommendation:** Port — fail-safe-to-green is the wrong default for a readiness probe.

### BE-C03 — `add_after_commit`: run side effects only once the transaction is durable

- **Files:** new `app/utils/session_hooks.py`; imported from `app/__init__.py` (`from app.utils import empty_string_normalization, session_hooks, ...`)
- **What changed:** New helper `add_after_commit(session, callback)` stores no-arg callbacks in `session.info`. A module-level `after_commit` listener on the SQLAlchemy `Session` base class drains them, each in its own try/except. An `after_soft_rollback` listener discards them, so savepoint rollbacks (and tests running inside a connection-level savepoint) don't leak callbacks to a later commit.
- **Why:** `d795ad48`: the session-summary SSE event was dispatched before Flask's `teardown_request` committed, so clients that refetched on the event could see stale state. This race is inherent to the template's pattern (services dispatch SSE inside the request, commit happens in `teardown_request`).
- **Kind:** bug fix (race) / new utility
- **Applies to:** apps with `use_database` + `use_sse` (EI, IoTSupport)
- **Port effort:** S — one 76-line file plus one import; the apps then opt in per call site. DA's tests for it are in the test-suite section.
- **Merged in:** Tests: `tests/test_session_hooks.py` (6) pins run-after-commit, callback order, a raising callback not stopping the rest, discard on rollback, and a clean `session.info` afterwards. `tests/test_sse_post_commit_audit.py` is DA call-site coverage. (Merged from BE-T02.)
- **Recommendation:** Port — small, generic, fixes a latent SSE-vs-commit ordering race for every db+sse app.

### BE-C04 — `scoped_session` / `scoped_savepoint` context managers

- **Files:** `app/services/container.py` (module-level functions after the container)
- **What changed:** `scoped_session(container)` yields `container.db_session()`, commits on clean exit, rolls back on exception, and always calls `session.close()` followed by `container.db_session.reset()`. `scoped_savepoint(session)` wraps `begin_nested()` with commit/rollback. The baseline has only the Flask `teardown_request` pattern, with no equivalent for background threads or tasks.
- **Why:** `d108c86b`: `db_session.reset()` only clears the provider cache and does not close the Session; reference cycles kept connections "idle in transaction" until the cyclic GC ran. `fc4a2758` added `scoped_savepoint`.
- **Kind:** bug fix (connection leak) / utility
- **Applies to:** apps with `use_database` that touch the DB off the request path (TaskService threads, sweepers, CLI)
- **Port effort:** S — ~40 lines, no dependencies.
- **Recommendation:** Port — the leak mechanism (reset without close) applies to any background-thread DB use in the template.

### BE-C05 — Always-on HTTP request metrics middleware

- **Files:** new `app/utils/http_metrics.py`; `app/__init__.py` (`register_http_metrics(app)`); `app/services/diagnostics_service.py`
- **What changed:** `before_request`/`after_request` hooks record `http_request_total{method,endpoint,status}` and `http_request_duration_seconds{method,endpoint}` for every route. In the baseline the only duration histogram (`http_request_duration_seconds{method,endpoint,status}`) lives inside `DiagnosticsService`, so it exists only when `DIAGNOSTICS_ENABLED=true`. DA removed it from `DiagnosticsService` ("owned by app.utils.http_metrics") to avoid a duplicate metric registration.
- **Why:** `6af984f0` slice 032 "launch readiness audits (metrics ...)". Note the label set changes: the histogram loses `status` and gains the separate counter. Dashboards and alerts built on the old histogram's `status` label would break.
- **Kind:** feature / observability
- **Applies to:** all apps
- **Port effort:** S — one 48-line file, two edits in `DiagnosticsService`. Decide whether to keep `status` on the histogram (e.g. keep the baseline's label set and buckets) before porting.
- **Recommendation:** Port — request rate and latency should not depend on a diagnostics flag; keep the label set compatible.

### BE-C06 — Secret-redacting settings dump at boot, `LOG_LEVEL`, and `ExtraFieldFormatter`

- **Files:** `app/config.py` (`Sensitive`, `is_sensitive`, `dump_config_for_logging`, `Settings.dump_for_logging`, `LOG_LEVEL`), `app/app_config.py` (same for `AppSettings`), `run.py` (`_resolve_log_level`, `_log_app_config`, boot logging), new `app/utils/log_formatter.py`, `.env.example` (`LOG_LEVEL`)
- **What changed:**
  - Fields are annotated `Annotated[str, Sensitive]` (secret key, drain key, DB URL, OIDC client secret, S3 keys, SSE callback secret).
  - At startup `run.py` logs every resolved `Settings` and `AppSettings` value with secrets shown as `***`.
  - The root log level is configurable via `LOG_LEVEL`; the baseline hard-codes `logging.INFO` in `run.py`.
  - `ExtraFieldFormatter` appends `extra={...}` fields as ` | k=v` pairs. The baseline formatter silently drops them.
  - The same formatter is used for the testing-mode stderr handler in `create_app`.
- **Why:** `3487e2f0` slice 044 "startup logging & log level control"; formatter added with `416fd88a` (diagnostic logging).
- **Kind:** feature / diagnostics
- **Applies to:** all apps
- **Port effort:** S-M — `Settings`/`AppSettings` field annotations, `run.py` changes, one new util. Template apps then mark their own secrets in app-owned `app_config.py`. `sqlalchemy_engine_options` was marked Sensitive purely for log noise (DA comment); don't copy that.
- **Recommendation:** Port — "what config did this pod boot with" is the first question in any deployment problem, and redaction by annotation is cheap.

### BE-C07 — `LifecycleCoordinator.unregister_lifecycle_notification` and snapshot dispatch

Merged into BE-T01, which covers the coordinator change together with the log stream that needed it.

### BE-C08 — Pillow 12 typing fix and the version bumps that required it

- **Files:** `app/utils/image_processing.py`, `app/services/cas_image_service.py`, `pyproject.toml`, `app/database.py` (import order)
- **What changed:** `img = img.convert(...)` is replaced by `processed: Image.Image = img.convert(...) if ... else img` (Pillow 12 typing: `convert()` returns `Image.Image`, not `ImageFile`, so reassigning to the `with` variable fails mypy). `types-pillow` is removed (no Pillow-12 stubs on PyPI) along with `types-flask`. Bumps: pillow 10 to 12, spectree 1 to 2, flask-cors 4 to 6, pytest 7 to 9, pytest-cov 4 to 7, ruff 0.11 to 0.15 (ruff 0.15 import-sorting fix in `database.py`).
- **Why:** `07799e8c` "Normalize all Python dependency pins", with `78c6e094` "Fix pytest plugin resolution for pytest 9 in CI". Spectree 2 is the item most likely to affect template code, which DA ran against without other template edits in the files in my scope.
- **Kind:** refactor / tooling
- **Applies to:** apps with `use_s3` (image code); the bumps apply to all
- **Port effort:** S for the typing change; M for the bumps (regen, run check/pytest, look for spectree 2 behaviour changes). The pytest 9 plugin-resolution fix is in the test-suite section.
- **Recommendation:** Port — the image typing change is needed as soon as Pillow 12 is adopted, and DA shows the stack running on spectree 2 / flask-cors 6 / pytest 9 / ruff 0.15.

### BE-C09 — `testing-server.sh`: source `.env.test`, `--database-url`, and run through `poetry run dev`

- **Files:** `scripts/testing-server.sh`
- **What changed:**
  - The script now sources `.env.test` (`set -a; source; set +a`) so Playwright-managed backends get the same test overrides pytest gets from `load_dotenv()`.
  - New `--database-url` option, which takes precedence over `--sqlite-db`.
  - Args after `--` are passed to `poetry run dev`.
  - It execs `HOST=.. PORT=.. poetry run dev` instead of `python -m flask run`, so the testing server goes through `run.py` (same lifecycle coordinator, logging and Waitress/Werkzeug setup as dev/prod).
- **Why:** `a2718e83` "Fix test infrastructure env loading (testing-server.sh sources .env.test)"; `ed8504e9` "Add --database-url flag (slice 007b)"; the passthrough arguments came with the worker/beat modes (see BE-C19).
- **Kind:** test infra / bug fix
- **Applies to:** all apps with Playwright (`use_database` for `--database-url`)
- **Port effort:** S — one script. The `.env.test` sourcing and `poetry run dev` parts are independent of the passthrough args.
- **Merged in:** pytest side of the same divergence: `tests/conftest_infrastructure.py` loads `.env` and then `.env.test` with `override=True`, instead of `.env.test` alone (`a2718e83`). (Merged from BE-T03.)
- **Recommendation:** Port — the `.env.test` mismatch between pytest and the Playwright backend is a real divergence, and `flask run` skips `run.py`.

### BE-C10 — `.gitignore`: ignore every `.env*` except `.env.example`; ignore `coverage/`

- **Files:** `.gitignore`
- **What changed:** `.env` and `.env.test` become `.env*` plus `!.env.example`; `coverage/` is added (see BE-C30).
- **Why:** not stated (`da8437cb` ".gitignore cleanup"). Prevents `.env.local`, `.env.prod` and similar from being committed by accident.
- **Kind:** hardening
- **Applies to:** all apps
- **Port effort:** S. Check the interaction with the CLAUDE.md statement that new apps get `.env.test` seeded by `project.yaml`: it is already ignored in the baseline, so no change in behaviour.
- **Recommendation:** Port — one-line safety improvement.

### BE-C11 — `allow_empty` opt-out for empty-string normalization

- **Files:** `app/utils/empty_string_normalization.py`
- **What changed:** The before-insert/update listener converts `""` to `NULL` on every String/Text column. DA skips columns with `column.info.get("allow_empty")`, so a model can declare `mapped_column(..., info={"allow_empty": True})` for fields where `""` is meaningful.
- **Why:** `d0ca2f44` (gap found while making a content field accept empty text). Not stated beyond that.
- **Kind:** feature (small escape hatch)
- **Applies to:** apps with `use_database`
- **Port effort:** S — three lines.
- **Recommendation:** Port — without it the normalization is a silent data-mangling trap with no opt-out.

### BE-C12 — `@public` becomes "auth-optional": tolerant mode, shared `resolve_auth_identity`, logout cookie clearing

- **Files:** `app/utils/auth.py` (`resolve_auth_identity`, `authenticate_request(..., throw_on_error, testing_service)`, `no_role_check`), `app/api/oidc_hooks.py` (`before_request_authentication`), `app/api/auth.py` (`/self`, `/logout`)
- **What changed:**
  - Baseline: a `@public` endpoint skips the auth middleware, and `/api/auth/self` re-implements test-session lookup, local-admin fallback and token validation in its handler. `oidc_hooks.py` has a second copy of the test-session logic.
  - DA: one `resolve_auth_identity(token, ...)` implements the three paths (test session with `test-session-` prefix guard, OIDC-disabled local admin, JWT validation). `authenticate_request` is the single entry point and runs the access-then-refresh-then-validate flow for every endpoint.
  - For `@public` endpoints the flow runs in tolerant mode (`throw_on_error=False`): authentication failures return silently without setting `g.auth_context`, while authorization failures still propagate.
  - `g.clear_auth_cookies` is set only when a refresh was attempted and failed. `/logout` sets it explicitly so a mid-flight refresh cannot overwrite the cleared cookies. `after_request_set_cookies` owns cookie clearing.
  - `/auth/self` shrinks to reading `g.auth_context`.
  - New `@no_role_check` decorator, intended for login/callback/logout only, lets a role-less user still log out.
- **Why:** `17ce058b` (slice 088b, dedupe of the auth flow plus a normalised test-session prefix guard); `aea3da3e` (slice 176, tolerant `@public` with refresh). Without slice 176, a `@public` endpoint called with an expired access token sees an anonymous caller and does not refresh.
- **Kind:** refactor + feature (the dedupe part has a small bug-fix flavour)
- **Applies to:** apps with `use_oidc`
- **Port effort:** M-L. The code is interleaved with DA's `seed_user` (`g.current_user`, user rows) and tenant hooks, which must be left out. DA's OIDC-disabled behaviour (leave `g.auth_context` unset for `local-user` so seed_user does not run) is only meaningful with a user table. Needs BE-C01 (or the hoisted check will not fire for tolerant endpoints). Auth tests must be ported with it (test-suite section).
- **Recommendation:** Port-adapted — port the generic part: one identity-resolution helper, tolerant `@public` with refresh, `g.clear_auth_cookies` on logout and `@no_role_check`. Leave out the user-seeding glue.

### BE-C13 — `HealthService` rework: registration-driven, concurrent, cached, per-check timeout, readyz 503 on degraded

- **Files:** `app/services/health_service.py`, `app/schemas/health_schema.py` (`CheckResultSchema`, `ReadyzResponse`), `app/api/health.py`, `app/__init__.py` (inline DB / SSE-gateway check registration removed), `app/services/container.py` (`health_service` injected into `S3Service`, `RabbitMQPublisher`, `SSEConnectionManager` via late `add_kwargs`), `app/services/s3_service.py` (`startup()` registers an `s3` check using `head_bucket`)
- **What changed:**
  - Baseline: `register_healthz`/`register_readyz` callbacks, run sequentially and uncached. A check returns a dict with an `ok` key, and the response is `{"status":"ready","ready":true,<name>:{...}}`.
  - DA: a single `register_check(name, fn) -> CheckResult(status ok|error|disabled, detail)`. Checks run in a `ThreadPoolExecutor`, each inside an app context, with a 30 s result cache, a 10 s overall timeout (`as_completed`), and `pool.shutdown(wait=False, cancel_futures=True)`. Per-check Prometheus histogram and counter.
  - Response: `{status: ok|degraded|shutting_down, stage, checks: {name: {status, detail}}}`, HTTP 503 when any check errors. `disabled` does not degrade. `healthz` becomes a trivial 200.
  - Services register their own checks at startup (s3, rabbitmq, sse gateway, opensearch). DA's self-registered keycloak/openai/email checks are domain wiring.
- **Why:** `a3a498a4` slice 031 per-dependency readyz; `9655f6ad`: readyz always returned 200, and the `with ThreadPoolExecutor` form blocked on slow checks (the `shutdown(wait=False)` comment in the code explains it). Playwright fixtures started tests before dependencies were ready.
- **Kind:** hardening / feature
- **Applies to:** all apps
- **Port effort:** M. The wire format changes (`ready` bool, per-check keys moved under `checks`, `shutting down` becomes `shutting_down`), which affects the root template's readiness probes and the frontend template's dev health indicator, if they parse the body. Caveats: the `readyz` docstring in DA's `app/api/health.py` still says degraded returns 200, contradicting the code (stale). The 30 s cache means a failing dependency can take that long to show; fine for k8s, worth knowing for tests.
- **Merged in:** Rule from DA's conventions (ADR-022): a new external integration registers its own readiness probe; probes are owned by the services, not a hardcoded list. (Merged from RT15.)
- **Recommendation:** Port-adapted — take the framework (register_check, concurrent execution with `wait=False`, cache, timeout, 503 on error, `disabled` status). Drop the keycloak/openai/gmail checks and `stage` (or make it optional); keep generic database, OIDC issuer, S3 and SSE-gateway checks. Needs BE-C02.

### BE-C14 — Sanitize the generic 500 handler

- **Files:** `app/utils/flask_error_handlers.py` (`handle_generic_exception`)
- **What changed:** The baseline returns `{"message": str(error)}` in the 500 body for every unhandled exception, which can leak SQL, paths and library messages. DA replaces it with "An unexpected error occurred", but only for requests on the `portal` blueprint (customer-facing); employee endpoints still get `str(error)`.
- **Why:** `6af984f0` slice 032 launch-readiness audit ("Sanitize generic error handler responses for portal routes"), with a regression test `tests/test_error_handler_sanitization.py`.
- **Kind:** hardening
- **Applies to:** all apps
- **Port effort:** S — a few lines; the portal blueprint check is DA-specific.
- **Merged in:** DA's regression test is `tests/test_error_handler_sanitization.py` (2 tests). (Merged from BE-T19.)
- **Recommendation:** Port-adapted — generic version: return the full message only when `app.debug`/testing, otherwise the generic text (correlation id stays in the body/logs). Hobby apps may prefer detailed errors in the UI; make it a setting if so.

### BE-C15 — OIDC redirect URI derived from the request origin; redirect param must be a relative path

- **Files:** `app/api/auth.py` (`login`, `callback`, `logout`), `app/utils/auth.py` (`get_request_origin`, `validate_redirect_url(redirect_url)`, `AuthState.origin` in `serialize_auth_state`/`deserialize_auth_state`), `app/services/oidc_client_service.py` (`build_authorization_url(..., origin)`, `exchange_code_for_tokens(..., origin)`, `generate_authorization_url` removed)
- **What changed:**
  - Baseline: the OAuth `redirect_uri` is always `{BASEURL}/api/auth/callback`; `validate_redirect_url` accepts relative URLs or URLs on the BASEURL origin.
  - DA: the origin is `request.scheme://request.host` (resolved by the app's ProxyFix, which already trusts one proxy hop). It is stored in the encrypted OAuth `state` so the callback uses exactly the same `redirect_uri`, and the post-logout redirect uses it too. `redirect` params must be relative; absolute URLs are always rejected.
- **Why:** `bc797102` slice 005a introduced `ALLOWED_ORIGINS`; `238dcf21` simplified it to request-derived origin. Done so the employee app and the portal, on different origins, can share one backend. A side benefit: auth works when the app is reached via a hostname other than `BASEURL`, and `BASEURL` stops being load-bearing for auth. `.env.example` in DA still documents `ALLOWED_ORIGINS`, but nothing reads it (stale leftover; do not copy).
- **Kind:** feature, with a hardening component (stricter redirect validation)
- **Applies to:** apps with `use_oidc`; matters most for apps served on more than one hostname
- **Port effort:** M — signature changes in `OidcClientService`, and existing OIDC tests/IdP redirect-URI registrations need review. It makes Host-header handling security-relevant: a spoofed `X-Forwarded-Host` produces a `redirect_uri` the IdP will reject unless registered, but only if the proxy chain is configured (ProxyFix `x_host=1`).
- **Recommendation:** Port-adapted — the relative-only redirect check and the origin-in-state design are good for any app. Whether to also switch `redirect_uri` to the request origin is the operator's call, since it removes the BASEURL pin. Skipping that part and keeping only the stricter redirect check is a valid subset.

### BE-C16 — Enforce an upload size limit via `MAX_CONTENT_LENGTH`

- **Files:** `app/startup.py` (`register_blueprints`), `app/app_config.py` (`MAX_UPLOAD_SIZE_MB`, default 50)
- **What changed:** `app.config["MAX_CONTENT_LENGTH"] = max_upload_size_mb * 1024 * 1024`. The baseline sets no limit, so Flask accepts unbounded request bodies.
- **Why:** not stated (part of DA's document upload feature).
- **Kind:** hardening
- **Applies to:** apps with upload endpoints (`use_s3` apps such as EI)
- **Port effort:** S — one setting plus one line. The template needs a home for the setting (`Settings`, not the app-owned `AppSettings`).
- **Recommendation:** Port-adapted — add a template-level `MAX_UPLOAD_SIZE_MB` setting with a sane default (and document that 413 comes from Werkzeug).

### BE-C17 — Dockerfile on shared base images

- **Files:** `Dockerfile`
- **What changed:** The two-stage Dockerfile uses `registry:5000/modern-app-backend-build` (build stage) and `registry:5000/modern-app-backend` (runtime) instead of `python:3.13-slim` plus an inline `apt-get`/`pip install poetry` block in each stage (about 20 lines shorter). The runtime stage no longer lists `tini`, `libmagic1`, `libjpeg`, `libpng`, `libwebp`, `libpq5` and `netcat`; the base image supplies them. `Jenkinsfile` is deleted (monorepo root builds it).
- **Why:** `d211997f` "Switched to using base images"; `3e0ffde0` "Changed the build pipeline to support the monorepo". Main benefit: faster builds and one place to patch OS packages.
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S for the template change, but the template then depends on those two images existing in the registry the apps build against, and on them carrying `tini` and the libraries `use_s3`/`use_database` need. The base-image repo is not in my inputs.
- **Recommendation:** Port-adapted — adopt only if the `modern-app-backend*` images are the operator's standard (the root-tooling section may already cover it); otherwise Skip.

### BE-C18 — Smaller SQLAlchemy pool in testing mode

- **Files:** `app/config.py` (`TEST_DB_POOL_SIZE = 5`, `TEST_DB_POOL_MAX_OVERFLOW = 5`, resolution in `Settings.load`)
- **What changed:** When `FLASK_ENV=testing`, the pool defaults to 5+5 instead of 20+30. An explicitly set `DB_POOL_SIZE`/`DB_POOL_MAX_OVERFLOW` still wins; it is detected via `Environment.model_fields_set` and resolved per field.
- **Why:** `d599f929` slice 180: cuts the memory footprint of a Playwright suite run (single-browser backend plus solo Celery worker). The commit message gives the memory motive without numbers.
- **Kind:** test infra / performance
- **Applies to:** apps with `use_database`
- **Port effort:** S — the constants are also referenced by DA's pytest `_build_test_settings` helper (test-suite section) so the two stay in sync.
- **Merged in:** The pytest settings must set the whole `sqlalchemy_engine_options` dict (`pool_size`, `max_overflow`, `pool_timeout`, `pool_pre_ping`, `echo_pool`) from the shared constants, or the small pool is silently ignored. Tests: `test_config.py::TestTestModePool` (~8). (Merged from BE-T08.)
- **Recommendation:** Port-adapted — the `model_fields_set` trick for "explicit env beats a mode default" is the reusable bit; value of the constants is a judgement call for the hobby apps.

### BE-C19 — Mode-aware app: `backend` / `worker` / `beat` with an embedded Celery worker and Beat

- **Files:** `run.py` (`--mode`, `--queue`, `_run_worker`, `_run_beat`, `_build_worker_argv`, `_start_health_server`), `app/__init__.py` (`create_app(mode=...)`), `app/app.py` (`App.mode`), `app/startup.py` (`create_container(mode)`), `app/services/container.py` (`register_for_background_startup(fn, modes=...)`, `start_background_services(container, mode)`), `app/worker/` (`celery_app.py`, `celery_tasks.py`, `celery_signal_handlers.py`, `celery_health.py`, `progress.py`; handler modules under `app/worker/handlers/` are DA domain), `docs/beat-deployment.md`, config (`WORKER_*`, `CELERY_WORKER_POOL`, `CELERY_WORKER_CONCURRENCY`, `RABBITMQ_*`), `pyproject.toml` (celery, pika, `tools/` entry points)
- **What changed:** Replaces the baseline's in-process `TaskService` thread pool (still used for lightweight tasks) with a durable work queue. `poetry run dev --mode worker --queue ...` runs a Celery worker on a daemon thread inside the same Flask app image, with the lifecycle coordinator as sole SIGTERM owner and Waitress still serving `/health/readyz` on `WORKER_HEALTH_PORT` (3406). `--mode beat` runs a `TrackedBeat` scheduler (singleton enforced by `replicas: 1` plus `Recreate` at the Helm layer). Background services are tagged with the modes they run in, and `DiagnosticsService` is backend-only. Queue names get a per-environment RabbitMQ prefix (`RABBITMQ_ENV_PREFIX`, defaulting to the stage). Eager `@worker_ready` capture of the `WorkController` replaces pidbox-based shutdown because of RabbitMQ 4.3.
- **Why:** `85c84c2a` slice 018 DB-driven worker, `b1bd001d` WorkerService, `6712e167` mode-aware factory, `f14e2632` slice 173 "migrate worker from custom pika to Celery", `77560a5f` reliability, `d599f929` pool/concurrency settings; ADR-025 in `/work/scratch/DesignAssistant/docs/architecture_decisions.md`.
- **Kind:** feature
- **Applies to:** DA-only today; a future app with long-running or retryable jobs (document processing, imports) would want it
- **Port effort:** L — needs RabbitMQ in the dev stack and CI (root template), a second deployment (worker, beat), new dependencies (celery, pika, kombu), and test infrastructure for eager/real Celery. The pieces most reusable on their own are the mode-gated background starters (`modes=` tuple) and the multi-process `run.py` structure.
- **Recommendation:** Optional — no current app needs a broker-backed worker. If a future app does, port as a flag (`use_worker`) rather than all at once. The mode-gated starters alone are Port-adapted-sized if a second process type is ever added.

### BE-C20 — Email sending (Gmail API client, queued `EmailService`, HTML/text templates)

- **Files:** `app/services/gmail_client.py`, `app/services/email_service.py`, `app/templates/email/*`, `app/worker/handlers/email_send_handler.py`, `FlaskAppContext` (`app/services/flask_app_context.py`), config `GMAIL_*`
- **What changed:** `GmailClient` sends through a Google service account with domain-wide delegation, or logs the full email at INFO and reports success when `GMAIL_CREDENTIALS_JSON` is empty. It exposes `check_health()` used by the readyz `email` check (status `disabled` when unconfigured). `EmailService` renders templates and publishes the content as a Celery `send_email` task. `FlaskAppContext` is a small DI wrapper for threads needing an app context.
- **Why:** `d30bdaa7` slice 026 "email infrastructure — Gmail API async email pipeline".
- **Kind:** feature
- **Applies to:** DA-only today; apps that notify humans by email
- **Port effort:** M-L — Gmail specifics (Google Workspace delegation) and a hard dependency on BE-C19 for async sending. Would be more portable as an SMTP-or-Gmail abstraction, which the hobby apps' infrastructure (MX, relay) probably already has.
- **Recommendation:** Optional — only if a hobby app needs email. `FlaskAppContext` is the one generic piece (small, Port-adapted).

### BE-C21 — Multi-tenancy infrastructure (query-level tenant isolation)

- **Files:** `app/utils/tenant_filter.py`, `app/utils/tenant_middleware.py`, hooks in `app/api/oidc_hooks.py` (`before_request_resolve_tenant`) and `app/__init__.py`; models and tests are DA domain
- **What changed:** When `g.tenant_customer_id` is set, a `do_orm_execute` hook adds `with_loader_criteria(customer_id == tenant)` to every ORM SELECT on tenant-scoped models, including relationship loads. Insert/update guards raise `TenantViolationError` for cross-tenant writes. A middleware resolves tenant from the authenticated portal user or from an employee impersonation cookie. All hooks are no-ops outside an app context or without a tenant. Known limitation, documented in the code: `Session.get()` identity-map hits bypass the filter.
- **Why:** `71a93bd2` slice 109 "multitenancy infrastructure with transparent query-level tenant isolation".
- **Kind:** feature
- **Applies to:** DA-only; a future SaaS-style app with customer data separation
- **Port effort:** L — ties to a `customer_id` convention, the impersonation flow and a customer model; it is useful only with a tenant-scoped model base class.
- **Recommendation:** Optional — no hobby app has tenants. Revisit if one is planned.

### BE-C22 — Server-side localization (i18n)

- **Files:** `app/utils/i18n.py`, `app/locales/{en,nl}.json`, `schema.json`, `nl.meta.json`, `app/services/language_service.py`, `SUPPORTED_LANGUAGES` setting plus `Settings.validate_source_language_invariant`, `docs/localization.md`
- **What changed:** Locale bundles are loaded eagerly at startup (fail fast on missing or invalid files). A `before_request` hook sets `g.ui_locale` via `Accept-Language` matching (case-insensitive, subtag drop). `t(key, language=None, **params)` resolves a dotted key with fallback to the source language and `format_map` interpolation. `UnprocessableEntityException` messages go through `t()`.
- **Why:** `1518408a` slice 117 "Add localization backend infrastructure"; `c40a9383` slice 141 source-language guard (English-only source, temporary).
- **Kind:** feature
- **Applies to:** DA-only; a multilingual future app
- **Port effort:** M — needs a matching frontend convention (the frontend/portal sections may cover it), a locale-file schema and a translation workflow (`nl.meta.json` tracks stale translations).
- **Recommendation:** Optional — no current app is multilingual.

### BE-C23 — ICU collations (case/accent-insensitive columns), collation startup check, `cli prepare`/recreate flow

- **Files:** `app/utils/collation.py`, `app/database.py` (`recreate_database_with_icu`, `is_database_empty`, collation-aware `upgrade_database`), `app/cli.py` (`upgrade-db` becomes `prepare`; collation check and auto-fix in `handle_prepare`; `maintenance` command), `app/__init__.py` (`skip_collation_check`, fail-fast `SystemExit` outside tests), `docs/database-changes.md`
- **What changed:** Migrations create two non-deterministic ICU collations (`app_ci`, `app_ci_ai`). Text columns reference them for case/accent-insensitive uniqueness and sorting instead of `LOWER()` indexes. `create_app` refuses to start if the DB lacks them. The CLI creates them on an empty database or drops and recreates the database with ICU when wrong. `upgrade_database(recreate=True)` loses the SQLite shortcut.
- **Why:** `8bbff583` slice 064b "per-column ICU collations replacing LOWER() indexes"; `79889739` auto-create on an empty DB.
- **Kind:** feature
- **Applies to:** apps with `use_database` that want accent/case-insensitive uniqueness (EI part names, perhaps)
- **Port effort:** L — it changes DB creation requirements for every deployed Postgres, and CI and dev containers must create the DB with the ICU provider. Not backward compatible for existing databases.
- **Merged in:** The convention that comes with it (DA `docs/conventions.md` "Database"): every text column names `app_ci` or `app_ci_ai` or is on an allowlist (IDs, FKs, enums, hashes), enforced by a schema test; no `LOWER()` indexes, `citext` or `ILIKE`. (Merged from RT12.)
- **Recommendation:** Optional — good if an app needs case-insensitive unique names; do not force on all apps. `cli prepare`/`maintenance` are DA-specific (OpenSearch).

### BE-C24 — `STAGE` taxonomy with stage-derived defaults

- **Files:** `app/config.py` (`Stage`, `STAGE` env, S3 bucket and RabbitMQ prefix derived from the stage), `HealthService` (`stage` in readyz)
- **What changed:** Six-value deployment tier (`local-dev`, `dev`, `uat`, `prd`, `local-tst`, `tst`), orthogonal to `FLASK_ENV`, with a small immutable wrapper (`is_local()`, `is_env("dev")`). Empty `S3_BUCKET_NAME` becomes `design-assistant-documents-{stage}`, and the queue prefix defaults to the stage. DA also stage-gates destructive CLI commands and Keycloak provisioning.
- **Why:** `fb9117b1` slice 030, `8e195b3c` slice 030b.
- **Kind:** feature
- **Applies to:** DA-only; apps deployed to several tiers sharing infrastructure
- **Port effort:** S-M
- **Recommendation:** Optional — hobby apps have one environment.

### BE-C25 — `AuthService` cross-cutting `role_hierarchy` with cycle detection

- **Files:** `app/services/auth_service.py`, `app/utils/spectree_config.py` (adds `hierarchy` to the OpenAPI `x-auth-roles`), container wiring
- **What changed:** New `role_hierarchy={"editor": ["portal"]}` parameter beyond the linear read/write/admin chain. It validates that referenced roles are known, detects cycles (three-colour DFS), computes the transitive closure and merges it into the hierarchy map.
- **Why:** `bffb76f9` slice 033 (editor implies portal; lets endpoints say `@allow_roles("portal")`). 24 tests were added with it.
- **Kind:** feature
- **Applies to:** DA-only; apps with extra non-linear roles
- **Port effort:** S-M (about 100 lines plus tests, backward compatible: default is empty)
- **Recommendation:** Optional — nothing in the hobby apps needs it; low cost if a second role family appears.

### BE-C26 — S3 service additions: presigned GET/PUT URLs, streaming, listing with metadata

- **Files:** `app/services/s3_service.py` (`generate_presigned_get_url`, `generate_presigned_put_url`, `get_object_stream`, `list_objects_with_metadata`, `PRESIGNED_URL_EXPIRY_SECONDS`)
- **What changed:** Four generic methods wrapped in `InvalidOperationException`. The PUT URL bakes the Content-Type into the signature.
- **Why:** `79bbe153` slice 136, document conversion via presigned URLs (replaces a shared volume); the listing method serves the TTL sweep.
- **Kind:** feature
- **Applies to:** apps with `use_s3`
- **Port effort:** S — no dependencies. The `s3` readyz check also added in this file belongs to BE-C13.
- **Recommendation:** Optional — useful if an app lets browsers upload/download directly; EI currently proxies.

### BE-C27 — Pagination and sorting helpers

- **Files:** `app/utils/pagination.py`, `app/schemas/common.py` (`PaginationQuerySchema`, `PaginationMetaSchema` gains `sort_by`/`sort_dir`)
- **What changed:** `apply_sorting(query, model, sort_by, sort_dir)` with an `id` tiebreaker in the same direction (`cad98875`: deterministic pagination); `build_pagination_meta`; a base query schema (`page`, `per_page` 1..100, `sort_dir`). DA removed the baseline's `PaginatedResponseSchema` (do not copy that removal).
- **Why:** `855dd162` "server-side sorting for all paginated endpoints"; `cad98875` tiebreaker.
- **Kind:** feature / small bug fix (unstable page ordering)
- **Applies to:** apps with `use_database` list endpoints
- **Port effort:** S
- **Merged in:** The convention that comes with it (DA `docs/conventions.md` "Pagination & sorting"): paginate any list that could pass ~50 items; every list endpoint takes server-side `sort_by` (a `Literal`) and `sort_dir`; no client-side sorting; `id` as a stable tiebreaker. Frontend side: FE31. (Merged from RT10.)
- **Recommendation:** Optional — only if the template wants a canonical list-endpoint pattern; the tiebreaker idea is worth documenting even if the module is not ported.

### BE-C28 — Extra exception types and error-response schemas

- **Files:** `app/exceptions.py`, `app/utils/flask_error_handlers.py`, `app/schemas/common.py`
- **What changed:**
  - `ExternalServiceException` becomes 502 with the code `EXTERNAL_SERVICE_ERROR`.
  - `UnprocessableEntityException` becomes 422, with an i18n message.
  - Spectree-friendly `ApiErrorResponseSchema` / `ApiErrorDetailsSchema` mirror the `build_error_response` envelope, so 403/409 responses can be documented in the OpenAPI spec.
  - `TaskAcceptedSchema` is the 202 body for async dispatch.
  - `WorkspaceLockedError` and the `locked_by` field on `ResourceConflictException` are DA-specific.
- **Why:** various (`cb82d508` Keycloak admin, `d0ca2f44` portal); no explicit rationale.
- **Kind:** feature
- **Applies to:** all apps
- **Port effort:** S
- **Recommendation:** Optional — `ExternalServiceException` (502) and the error-envelope schemas are generic and cheap; take them when an app calls an upstream or wants documented error responses. The rest is DA-specific.

### BE-C29 — Dev hot reload via `watchmedo`, Werkzeug reloader removed

- **Files:** `run.py` (`app.run(..., use_reloader=False)`; `WERKZEUG_RUN_MAIN`/`is_reloader_parent` plumbing deleted), new `scripts/dev-watch.sh`, `pyproject.toml` (`watchdog[watchmedo]`)
- **What changed:** The baseline skips background services in the Werkzeug reloader parent process and guards `lifecycle_coordinator.initialize()` on `WERKZEUG_RUN_MAIN`, which cannot restart the Celery worker. DA runs the process under `watchmedo auto-restart` (SIGTERM, graceful drain; watches `*.py`, `*.env*`, `app/assets`; 3 s throttle after exit) and always runs with `use_reloader=False`. The same wrapper restarts the worker.
- **Why:** `77560a5f`, `e0640919`, `03d81d35`, `84e5a70d` (restart on asset change). Removes a double-process class of bugs, including the "duplicate MQTT connections" the baseline comment refers to.
- **Kind:** tooling / refactor
- **Applies to:** all apps
- **Port effort:** S-M. It needs a process manager (Procfile or the root template's dev orchestration) to invoke the wrapper, so it interacts with the root-tooling section.
- **Recommendation:** Optional — attractive (single process, honours the lifecycle coordinator, picks up `.env` edits), but only worth it together with the root dev orchestration.

### BE-C30 — `poetry run coverage` script

- **Files:** `scripts/run_coverage.py`, `pyproject.toml` (`coverage = "scripts.run_coverage:main"`), `.gitignore` (`coverage/`)
- **What changed:** Runs pytest with `--cov` and writes JSON, HTML and terminal reports to `coverage/`.
- **Why:** `19b6b4c1` (to feed coverage into the code-health tooling). `99df7168` adds a pytest plugin pre-importing numpy because of a numpy 2.4 plus coverage.py crash on 3.13; that plugin is test-suite-section material and only matters with numpy.
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S
- **Recommendation:** Optional — convenience only.

### BE-C31 — Backend `docs/` convention set

Merged into RT14 (the generic rules in DA's backend docs are the code-style rules listed there).

### BE-C32 — Container: `MetricsService(container=Self())` resolved to `None`

- **Files:** `app/startup.py` (`create_container`: `container.metrics_service.add_kwargs(container=container)`)
- **What changed:** DA overrides the `providers.Self()` kwarg after instantiating the container because `Self()` allegedly resolves to `None` for a declarative container. The baseline's `MetricsService` only stores `self.container` and never reads it, so the baseline is unaffected today.
- **Why:** `c132e907` ("Fix backend ServiceContainer providers.Self() bug: pass container instance instead of class"). I could not verify the `Self()` claim (dependency-injector is not importable in my sandbox).
- **Kind:** bug fix (latent)
- **Applies to:** all apps if a service ever uses `self.container`
- **Port effort:** S — one line
- **Recommendation:** Optional — verify against the template's pinned dependency-injector; fix only if `self.container` is ever dereferenced.

### BE-C33 — `DRAIN_AUTH_KEY` default changed from empty to `"changeme!"`

- **Files:** `app/config.py`
- **What changed:** The baseline default `""` makes the drain endpoint reject all requests (`DRAIN_AUTH_KEY not configured`). DA's default is a well-known string, so an unconfigured deployment accepts `Bearer changeme!`.
- **Why:** `5cd93b69` "Clean up env files: improve defaults"; not stated.
- **Kind:** hardening regression
- **Recommendation:** Skip — worse than baseline (fails open on a guessable secret). `validate_production_config` may paper over it; I did not check.

### BE-C34 — `check` script drops pytest

- **Files:** `scripts/check.py`
- **What changed:** `poetry run check` runs ruff, mypy and vulture only; pytest is run separately.
- **Why:** `5dfa2c04` "Removed running test suites from check commands" (DA runs several suites through its own suite runner).
- **Kind:** tooling
- **Recommendation:** Skip — the template's `kc project lint` / `test` already split these, and the template CLAUDE.md documents `check` as including pytest. A decision for the operator rather than a fix.

### BE-C35 — Dependency pin style normalised to `^N` / `^0.N`

- **Files:** `pyproject.toml`
- **What changed:** Every pin loosened to a major-only caret (e.g. `flask = "^3"`, `boto3 = "^1"`). The version bumps themselves are covered in BE-C08.
- **Why:** `07799e8c`
- **Kind:** style
- **Recommendation:** Skip — style preference; the lockfile pins the actual versions. `pyproject.toml` is app-owned anyway. Other generic `pyproject.toml` changes: `pythonpath = ["."]` under pytest, `radon` (DA's code-health grader), `mypy` ignore-missing-imports overrides for untyped libraries, and an `openai` marker, all DA-specific or covered by the test-suite section.

### BE-C36 — Deleted dev/build scripts and `Jenkinsfile`

- **Files:** `scripts/build.sh`, `dev-server.sh`, `dev-sse-gateway.sh`, `run.sh`, `stop.sh`, `Jenkinsfile`
- **What changed:** Removed in favour of DA's monorepo root tooling (honcho/Procfile, root pipeline). The new `dev-minio.sh`, `dev-opensearch.sh`, `dev-document-conversion.sh` run DA's sidecars.
- **Why:** `f906bc41` "Replace tmux dev setup with honcho process manager", `3e0ffde0` monorepo pipeline.
- **Kind:** tooling
- **Recommendation:** Skip — superseded by the root template, which the root-tooling section covers.

### BE-C37 — Environment defaults specific to DA

- **Files:** `.env.example`, `app/config.py`
- **What changed:** `OIDC_CLIENT_ID` default `design-assistant`, S3 `minioadmin` credentials and bucket name, `OIDC_COOKIE_SECURE=false` in `.env.example`, and the stale `ALLOWED_ORIGINS` block (nothing reads it).
- **Recommendation:** Skip — branding and local-sidecar values.

DA-specific, not candidates: customers/contacts/projects/workspaces/documents/content assets, sessions, timeline events, notifications, release notes, LLM configuration and prompts, AI pipeline (gates, conversation, edit execution, task lists, OpenAI/stub runners), OpenSearch document and content search, Keycloak admin service and cleanup CLI (`app/cli_commands/cleanup.py`), document conversion sidecar, portal auth/visibility/timeline utils, text-span narrowing (`text_utils.narrow_edit_span`), `diff_segments`/`edit_application`/`markdown_renderer`/`prompt_hash`/`text_metrics`, abuse-protection counters (`WorkspaceLockedError`), the prompt-tester tool, DA's `testing_auth.py` additions (user-row upsert, contact link-user), test data service and fixtures. Left to other sections: SSE force-callback-error (`testing_auth.py`), `rabbitmq_publisher`/`sse_connection_manager`, task service, `testing_*` endpoints, `log_capture` change, `pytest_plugins/`, `tests/`.

## Backend — SSE, tasks, testing endpoints, test suite

Notes for the reader:

- DA's backend test suite is 152 files / ~2480 test functions; the baseline render ships only `tests/conftest.py`, `tests/conftest_infrastructure.py` and `tests/__init__.py`. So every DA test that exercises template-owned code is a candidate addition. Test items below name files, counts and the behaviours pinned.
- DA changed the SSE transport (HTTP calls to the gateway -> RabbitMQ topic exchange, stateless manager). That is entangled with DA's Celery worker. Items BE-T10 and BE-T11 separate the portable ideas (typed targets, callback rejection) from the transport rewrite (BE-T20). Tests written against DA's manager assume the new transport; each test item says what needs adapting.
- DA has no pytest-xdist, no pytest-timeout, no custom plugins and no extra markers beyond `integration/slow/openai`. Test speed came from the session-scoped app plus rollback isolation (BE-T06/BE-T07). DA's `docs/conventions.md` mentions a "max-retry-2 pytest configuration" but it is not in the repo (probably the remote runner), so it is not a candidate.
- Overlaps with other sections (auth code, config, health, S3, database): this section only lists the *tests* for those areas, plus `add_after_commit` (BE-T02) because it exists for SSE. Dedupe on those at merge time.

### BE-T01 — Testing log stream: per-stream shutdown sentinel, `unregister_lifecycle_notification`, safe dispatch

- **Files:** `app/api/testing_logs.py`, `app/utils/lifecycle_coordinator.py` (protocol + `LifecycleCoordinator`), `app/utils/log_capture.py`; tests `tests/test_testing_logs_stream.py` (8 tests)
- **What changed:** Baseline `LogCaptureHandler` registered itself once with the lifecycle coordinator and broadcast a `connection_close` event to all log clients on SHUTDOWN; `LifecycleCoordinator` had no way to unregister, and `_raise_lifecycle_event` iterated the live `_lifecycle_notifications` list. DA adds `unregister_lifecycle_notification` (idempotent), makes `_raise_lifecycle_event` iterate a snapshot taken under the lock (so callbacks can self-unregister during dispatch), and makes each `/api/testing/logs/stream` generator register its own PREPARE_SHUTDOWN callback that pushes a module-level `_SHUTDOWN_SENTINEL` onto its queue. The generator breaks on the sentinel and its `finally` unregisters both the log client and the lifecycle callback, each in its own try/except so one failure cannot block the other. `LogCaptureHandler` no longer knows about the coordinator. The `connection_close` SSE event is removed; clients see the TCP close.
- **Why:** 5d89d6b1 (2026-04-05), "Remove connection_close SSE event from testing log stream"; fae31ad2 adds full-traceback logging for teardown failures. Fixes a leak of callbacks/clients per stream and the list-mutation-during-iteration hazard in the coordinator, which is a real bug for any service that unregisters from inside a callback.
- **Kind:** bug fix
- **Applies to:** all apps (testing log stream and lifecycle coordinator are in every app)
- **Port effort:** S — three template-owned files plus one test file; removes the `connection_close` event, so check whether template frontend/Playwright log collectors wait for it (DA's frontend had no consumer).
- **Recommendation:** Port — the snapshot and unregister parts are unambiguous fixes; the sentinel approach is cleaner than the shared-handler broadcast.

### BE-T02 — `add_after_commit` session hook: defer SSE dispatch until the transaction commits

Merged into BE-C03 (same change; its tests are listed there).

### BE-T03 — `.env` then `.env.test` loading; `testing-server.sh` passthrough and `--database-url`

Merged into BE-C09 (same script; the pytest `.env` loading is listed there).

### BE-T04 — TaskService / TaskProgressHandle tests

- **Files:** `tests/test_task_service.py` (38 tests)
- **What changed:** Tests for template-owned `TaskService`. They pin: progress is monotonically non-decreasing, text-only/value-only updates, SSE send exceptions are swallowed; `start_task` returns a pending response, registers the task, and raises during shutdown; success sets COMPLETED and emits `task_started`/`task_completed`, failure sets FAILED and emits `task_failed` with the traceback, a cancelled task stays cancelled; event serialised with `mode='json'`; status lookup, cancel (only running), remove (only terminal states); cleanup removes old completed tasks but not recent or running ones; lifecycle (`PREPARE_SHUTDOWN` sets the flag and the gauge, `wait_for_tasks` timeouts, `_check_tasks_complete` sets the event only when shutting down, `SHUTDOWN` clears state). Uses a small `_StubLifecycleCoordinator` and stub tasks.
- **Why:** Added 2026-03-30; extended with the Target-based assertions in the SSE refactor.
- **Kind:** test infra (tests of template code)
- **Applies to:** all apps (TaskService is unconditional)
- **Port effort:** S-M — assertions on `Target.subject(...)`/`Target.role("editor")` need adapting to the baseline's `target_subject`, or ride along with BE-T10.
- **Recommendation:** Port — broad, no DA domain content; most valuable template test file in this area.

### BE-T05 — OIDC auth core tests: `AuthService`, `OidcClientService`, redirect validation

- **Files:** `tests/test_auth_service.py` (32), `tests/test_oidc_client_service.py` (19), `tests/test_auth_redirect.py` (14)
- **What changed:** `test_auth_service`: `validate_token` success and failure modes (expired, bad signature, missing sub, bad issuer/audience, OIDC disabled, malformed token, generic error records metric, duration histogram), role extraction from realm and resource claims (missing/malformed claim shapes), JWKS discovery (HTTP error, missing `jwks_uri`), OIDC-enabled init failures (missing issuer or client id, JWKS client failure), and `resolve_required_role` (read/write role by method, `allow_roles` override, HEAD as read). `test_oidc_client_service`: endpoint discovery with retries, authorization-code and refresh-token exchange (success, missing access token, HTTP error with/without `error_description` or JSON body), PKCE challenge (S256, no padding, uniqueness), auth-state population, authorization URL params. `test_auth_redirect`: `validate_redirect_url` rejects absolute and protocol-relative URLs; login derives origin from the request host (ProxyFix) and stores it in auth state; callback uses `auth_state.origin` with `baseurl` fallback; logout origin and default redirect.
- **Why:** slices of 2026-03-15 to 03-30 (bc797102, 238dcf21, 3bcff9eb for the redirect/role fixes); not stated beyond coverage.
- **Kind:** test infra (tests of template code)
- **Applies to:** apps with `use_oidc`
- **Port effort:** S-M — tests use the `mock_oidc_discovery`/`generate_test_jwt`/`oidc_app` fixtures already in `conftest_infrastructure.py`; DA-modified bits (role hierarchy in `auth_service`, `configured_roles`) need splitting out. `test_auth_redirect` assumes DA's multi-origin behaviour (portal + frontend); keep only what matches the template's single-origin flow.
- **Recommendation:** Port — the OIDC BFF is in four of five downstream apps and has the least test coverage of any template area.

### BE-T06 — Session-scoped Flask app with connection-level rollback isolation

- **Files:** `tests/conftest_infrastructure.py` (template-owned): `app`, `session`, `container`, `_NoCloseSession`, `_clear_prometheus_once`, `oidc_app`
- **What changed:** Baseline built a fresh Flask app per test (cloning an in-memory SQLite template DB via `sqlite3.backup`) and cleared the Prometheus registry before and after every test. DA builds the app once per session and isolates tests by: `session` fixture = raw engine connection + real transaction + a `Session(bind=connection, join_transaction_mode="create_savepoint")`, torn down by rolling back the connection-level transaction (works even if the session is in a failed state). The session is a `_NoCloseSession` subclass whose `close()`, `commit()` and `rollback()` are no-ops, because Flask's `teardown_request` hook calls them and would otherwise detach ORM objects (DetachedInstanceError), release the savepoint under background threads, or roll back all of the test's earlier work on a 404. `container` fixture overrides `session_maker` with a sessionmaker subclass that always returns the test session and resets the `db_session` context-local singleton. Prometheus registry is cleared once per session (`_clear_prometheus_once`); `oidc_app` (second Flask app on the same DB) clears it itself and, in `finally`, re-runs `app.container.wire(packages=['app.api'])` because the second app's `wire()` poisons the DI wiring of the session-scoped app.
- **Why:** 008b phases 2-3 (7a44843d, 51996aff, 6cefa9b0): "626 passed, 0 failed, ~10s runtime" after the switch; later suite is ~2500 tests. 51996aff also fixes registry churn and `before_request` hook accumulation. The `_NoCloseSession` fix is in 6cefa9b0.
- **Kind:** test infra
- **Applies to:** all apps with `use_database`
- **Port effort:** M — rewrite of `app`/`session`/`container`/`oidc_app`; generated apps' own tests that rely on per-test app state, `app.test_client()` per test, or committing in tests would need a look. Pairs with BE-T07 (works with either DB, but see its note).
- **Recommendation:** Port-adapted — the isolation mechanics and `oidc_app` re-wire fix are generic and large speed wins; keep it behind the existing fixture names so downstream tests keep working.

### BE-T07 — Real PostgreSQL test database (per-run unique DB, stale cleanup, ICU) instead of SQLite

- **Files:** `tests/conftest_infrastructure.py` (`pg_seed_db`, `_pg_admin_url`, `_build_test_settings(database_url=...)`); `pyproject.toml` marker cleanup
- **What changed:** Session fixture `pg_seed_db` drops stale `<prefix>_*` databases from interrupted runs (`DROP DATABASE ... WITH (FORCE)`), creates a fresh DB named `<PYTEST_PG_DB_PREFIX or test_da_backend>_<uuid8>` from `template0` with UTF8 and ICU locale provider, runs Alembic via `upgrade_database()`, and drops it at session end. The prefix env var lets backend/frontend/portal Playwright runs coexist. SQLite-only workarounds (`with_variant(db.JSON, "sqlite")`, recreate path in `database.py`) were deleted.
- **Why:** 008b (6cefa9b0, 7a44843d, 5f685351): moving to PG surfaced "real bugs SQLite was hiding" (FK violations on delete, a CHECK constraint missing `md`, `::vector` cast syntax) and was required for DA's PG-only features (ICU collations, pgvector). Not stated as generic motivation; the evidence is the bugs it found.
- **Kind:** test infra
- **Applies to:** apps with `use_database` that run PostgreSQL in production
- **Port effort:** M-L — needs a PG sidecar/service in the dev env and CI validation Job (root template), a `postgres` superuser URL (hardcoded `postgres:postgres@localhost:5432` in DA), migration compatibility work in existing apps, and slower startup than in-memory SQLite.
- **Recommendation:** Port-adapted — operator decision: make PG the default for `use_database` (parity with prod, catches FK/CHECK/dialect bugs) or keep SQLite and at least ensure FK enforcement is on in the SQLite test path. If adopted, take the stale-DB cleanup and prefix env var as-is.

### BE-T08 — Test-mode DB pool sizing and complete `sqlalchemy_engine_options` in test settings

Merged into BE-C18 (same change; the engine-options detail is listed there).

### BE-T09 — Auth middleware tests: tolerant vs throwing `authenticate_request`, `@public`, `@no_role_check`, `/api/auth/self`

- **Files:** `tests/test_authenticate_request_tolerant.py` (14), `tests/test_auth_middleware_wrapper.py` (4), `tests/test_auth_no_role_check.py` (4), `tests/test_auth_self_api.py` (6), `tests/test_resolve_auth_identity.py` (11), `tests/test_auth_role_hierarchy.py` (25)
- **What changed:** These pin DA's slice 176 behaviour (aea3da3e): `@public` endpoints run the same access-then-refresh flow in tolerant mode; throwing mode raises 401 and sets `clear_auth_cookies` only after a failed refresh attempt, never on "no token at all" or a non-expiry validation failure; expired access plus valid refresh refreshes and sets cookies; authorization failures propagate even in tolerant mode; OIDC-disabled local-admin escape hatch; test-session tokens; the middleware wrapper picks mode from `is_public` and maps exceptions to 401/403; auth-flow endpoints (`login`, `callback`, `logout`) succeed for a caller with no recognised role; `/api/auth/self` end to end through the real hooks (valid, refresh, expired both, no cookies without clearing, 403 no role, forced-error short circuit); `resolve_auth_identity` three-path helper; role hierarchy expansion, cycle and unknown-role detection (DA-specific feature: editor implies portal).
- **Why:** slice 176 / 2026-05-09 (aea3da3e); role hierarchy 2026-03-22 (d4aef73f-era).
- **Kind:** test infra (depends on the auth code changes in the auth section)
- **Applies to:** apps with `use_oidc`, only if the corresponding auth changes are ported
- **Port effort:** M — meaningless without the auth-section items they cover; drop `test_auth_role_hierarchy` unless hierarchy is ported.
- **Recommendation:** Port-adapted — port the files together with whatever auth items the auth section recommends (tolerant `@public`, `@no_role_check`, cookie-clearing rules).

### BE-T10 — Typed SSE `Target`; no implicit broadcast for task events

- **Files:** `app/services/sse_connection_manager.py` (`Target`, `BROADCAST_TARGET`), `app/services/task_service.py`, `app/services/frontend_version_service.py`, `docs/sse-event-targeting.md`; tests `tests/test_sse_connection_manager.py::TestTarget` (about 17 tests)
- **What changed:** Baseline `send_event(request_id | None, ...)` treats `None` as broadcast and takes an optional `target_subject`; `TaskService` broadcast task events to everyone when the caller had no subject. DA introduces a `Target` class with factories (`connection`, `subject`, `role`, `workspace_events`) and a `BROADCAST_TARGET` constant; `None` now means "no recipient, skip". `TaskService._execute_task` builds a target explicitly: `Target.subject(caller_subject)` or `Target.role("editor")`, never broadcast; `TaskProgressHandle` takes a required `target`. `Target` has `routing_key`, `serialize`/`deserialize` (round-trip tested), `__eq__`/`__hash__`/`__repr__`. The doc states the rules: broadcast only for infrastructure events, explicit justified targets, no fallback chains.
- **Why:** 92aa46fd (021b), 14ab67cc (slice 073 "remove Target.broadcast(), enforce explicit SSE event targeting"). Intent is to stop domain events leaking to every connected user.
- **Kind:** hardening
- **Applies to:** apps with `use_sse`
- **Port effort:** M — touches `SSEConnectionManager`, `TaskService`, `FrontendVersionService`, every app call site of `send_event`; `Target.workspace_events()` and the `editor` role are DA-specific and would be dropped. Can sit on the existing HTTP transport (the routing key is only needed for BE-T20).
- **Recommendation:** Port-adapted — keep the typed target and the "task events go to the caller (or an explicit role), never broadcast" rule; leave out workspace/role names that belong to DA. In the baseline, an unauthenticated-subject task currently broadcasts to all connections.

### BE-T11 — SSE connect callback rejects unauthenticated or role-less connections; forced-rejection test hook

- **Files:** `app/api/sse.py`, `app/schemas/sse_gateway_schema.py` (`SSECallbackConnectResponse`), `app/services/testing_service.py` (`set/consume_forced_sse_callback_error`), `app/api/testing_auth.py` + `app/schemas/testing_auth.py` (`POST /api/testing/sse/force-callback-error?status=401|403`); tests `tests/test_sse_callback.py` (21 tests)
- **What changed:** Baseline `_bind_identity` logged a warning and let the connection proceed when the forwarded token was missing, invalid or expired, so the client got an open SSE stream that silently received nothing. DA inlines identity extraction before `on_connect`: OIDC disabled gives the `local-user` sentinel; otherwise a missing token or failed `validate_token` returns 401 and a valid token with no role in `auth_service.configured_roles` returns 403; `on_connect` (metrics) runs only after all rejection branches, so rejected sessions do not skew the connection gauge. A single-shot testing-only hook (consumed first, only when `settings.is_testing`) lets Playwright force the next connect callback to 401/403 to drive the rejected -> `/api/auth/self` -> reconnect flow. The 21 callback tests cover: bindings returned with OIDC off, `broadcast`/`connection.<id>` always present, missing or colon-containing request_id (400), disconnect, unknown action, bad body, OIDC-on cases (no token 401, expired 401, bad signature 401, no recognised role 403, valid editor/portal 200), and the hook (401/403, consumed once, endpoint arms it, rejects other status values).
- **Why:** b4997d67 (slice 175, 2026-05-09): "Replaces today's silent failure mode".
- **Kind:** bug fix / hardening
- **Applies to:** apps with `use_sse` + `use_oidc`; the testing hook applies to any `use_sse` app
- **Port effort:** M — the response-with-bindings part and `_select_role` ("editor", "portal") are DA/transport-specific; the 401/403 split and metrics-after-accept ordering port directly. The frontend must handle a rejected connect (DA did that in the frontend items), otherwise it just reconnects in a loop.
- **Recommendation:** Port-adapted — port the reject-before-register logic, the hook, and the tests minus the bindings assertions; coordinate with the frontend SSE section.

### BE-T12 — `FrontendVersionService`: no per-connection pending state, no bogus "unknown" payload, skip in local stages

- **Files:** `app/services/frontend_version_service.py`; tests `tests/test_frontend_version_service.py` (9 tests)
- **What changed:** Baseline kept `_pending_version: dict[request_id -> payload]` which was only cleared at SHUTDOWN (grows with every connection that ever called `queue_version_event`), fetched the version on each connect, and on fetch failure sent `{"version": "unknown", "error": ...}` to the client. DA's service drops the observer and the dict, broadcasts the fetched version on STARTUP, makes `_fetch_frontend_version` return `None` on failure (nothing is broadcast), and skips the startup broadcast in local stages (logged once). The tests pin: startup broadcast, no broadcast on fetch failure or in local stage, `queue_version_event` still broadcasts (with and without changelog, also in local stage), returns `False` while shutting down, and the shutdown flag.
- **Why:** 402fa755 (stateless manager), af1ab6a5/8a98f2ae (local-skip noise); 5969b6fe's race fix. Not stated whether clients connecting after startup still receive the version.
- **Kind:** bug fix (leak, bogus payload) / refactor
- **Applies to:** apps with `use_sse`
- **Port effort:** S-M — startup-only broadcast depends on the stateless manager; with the baseline stateful manager a late-joining client would no longer get a version on connect. Port the pieces that do not depend on it.
- **Recommendation:** Port-adapted — take `None`-on-failure (stop sending an "unknown" version to clients) and the unbounded `_pending_version` removal, keep the on-connect send; the tests then need the "on connect" variant.

### BE-T13 — HealthService tests (registration-driven checks, caching, shutdown, drain)

- **Files:** `tests/test_health_service.py` (29), `tests/test_health_api.py` (5)
- **What changed:** Tests pin: core checks self-registered, `register_check` adds/overwrites, `/readyz` returns only registered checks, 503 while shutting down, 503 when degraded, per-dependency failure modes (database connection and pending migrations, S3, SSE gateway, plus DA's Keycloak, RabbitMQ, OpenAI, OpenSearch), results cached for `_CACHE_TTL_SECONDS` and refreshed after expiry, metrics recorded, one failing check does not prevent the others, `/healthz` 200, `drain` auth (no key configured, invalid token, success).
- **Why:** 2026-03-22 onward; readyz 503-on-degraded (35b63065), mode-aware registration (7dbf9a1c).
- **Kind:** test infra (tests of template code; DA changed `health_service.py` heavily, see health section)
- **Applies to:** all apps
- **Port effort:** M — keep only checks that exist in the template (database, migrations, S3, SSE, drain, caching, shutdown, degradation); the others are DA services.
- **Recommendation:** Port-adapted — high value, shared by every app; depends on the health-section decisions (registration-driven design, caching).

### BE-T14 — S3 service unit tests (mocked boto3)

- **Files:** `tests/test_s3_service.py` (47 tests)
- **What changed:** Per-method coverage with mocked boto3: lazy cached client, missing-credentials error, upload with/without content type, download returns BytesIO at position 0, NoSuchKey -> not-found, copy, delete, exists (404 -> False, other errors raise), metadata, paginated list, delete_prefix (individual delete errors swallowed), `ensure_bucket_exists` branches, hash/CAS key format, health check and startup registration, presigned GET/PUT, `get_object_stream`, `list_objects_with_metadata`.
- **Why:** 2026-03-30 and 2026-04-15 (document conversion HTTP presigned-URL transport, 79bbe153).
- **Kind:** test infra (tests of template code)
- **Applies to:** apps with `use_s3`
- **Port effort:** S-M — presigned URL, `get_object_stream` and `list_objects_with_metadata` tests cover DA-added methods; port only if those methods are ported (S3 section).
- **Recommendation:** Port-adapted — core method and error-mapping tests are generic and cheap.

### BE-T15 — Config tests: secret redaction guard, config dump coverage, log level, test pool

- **Files:** `tests/test_config.py` (24 tests)
- **What changed:** Guard test that a canonical list of secret fields on `Settings` and `AppSettings` carries the `Sensitive` marker (fails when someone adds a secret and forgets it), `log_level` must not be sensitive; `dump_for_logging`/`dump_config_for_logging` redacts sensitive fields, shows `repr` for others and covers every field; invalid `LOG_LEVEL` falls back to INFO; `_resolve_log_level` is case-insensitive; test-mode pool constants resolve in testing, production stays 20/30, explicit env wins.
- **Why:** 3487e2f0 (slice 044 startup logging and log level), d599f929.
- **Kind:** test infra (depends on config-section changes: `Sensitive`, dump helpers)
- **Applies to:** all apps
- **Port effort:** S once the config items are ported
- **Recommendation:** Port-adapted — the "every field is dumped, secrets are marked" guard is especially useful.

### BE-T16 — Task endpoints restricted to an explicit role

- **Files:** `app/api/tasks.py`
- **What changed:** `GET /tasks/<id>/status`, `POST /tasks/<id>/cancel`, `DELETE /tasks/<id>` gain `@allow_roles("editor")`. Baseline decorated none, so with a tiered role config any authenticated caller (for DA: customer portal users) could read, cancel or remove any task by id.
- **Why:** not stated (part of the portal/role work, 2026-03).
- **Kind:** hardening
- **Applies to:** apps with `use_oidc` that have more than one role
- **Port effort:** S — role name is DA-specific.
- **Recommendation:** Port-adapted — generic form is "task endpoints require the app's top role" or an owner-subject check; hobby apps with one role gain nothing from it.

### BE-T17 — Test conventions and SSE targeting docs

- **Files:** `docs/testing.md`, `docs/sse-event-targeting.md`, `docs/conventions.md` (testing and flake sections), `CLAUDE.md` (testing expectations)
- **What changed:** Generic conventions worth carrying: tests mirror `app/`, `test_{module}.py` / `TestServiceName`; required coverage for services (all public methods, error conditions, edge cases, constraints) and APIs (all endpoints, invalid payloads, status codes, error format); service-backed factory fixtures; pre-flight with `pytest.exit` and an actionable start-the-service message instead of per-test `skipif` guards (6b5f9567: guards "hide real failures"); a testability rule that testing-only endpoints are a blocking prerequisite for any UI feature and live under `/api/testing/` behind the test-mode guard; "never dismiss test failures as flaky, the suite is green before every slice". The SSE targeting doc is the six rules in BE-T10.
- **Why:** 6b5f9567; 5b8fe7e0 (flaky-test policy).
- **Kind:** tooling / docs
- **Applies to:** all apps
- **Port effort:** S — doc text only; strip DA references (Keycloak `test-da-`, portal).
- **Recommendation:** Port-adapted — the operator's preference is to carry conventions via a skill; a skill pointing at these rules would reach the next author. Destination: the template conventions skill, not template docs.

### BE-T18 — Service-mocking fixtures and the preflight pattern

- **Files:** `tests/conftest.py` (`mock_s3`, `mock_keycloak`, `mock_ai_runner`, autouse `_mock_document_search` / `_mock_content_search`), `tests/conftest_infrastructure.py` (`_assert_s3_available` extended with more `pytest.exit` pre-flights)
- **What changed:** Pattern of overriding a container provider with a `MagicMock` in a fixture and calling `reset_override()` on teardown; autouse overrides for any service that would otherwise talk to a live external system; session pre-flights that abort the whole run with the exact script to start the missing service. `mock_s3` (upload, delete, copy, download returning a BytesIO) is generic.
- **Why:** 6b5f9567 for the pre-flight. Others not stated.
- **Kind:** test infra
- **Applies to:** `mock_s3` for apps with `use_s3`; the pattern for all
- **Port effort:** S
- **Recommendation:** Optional — template tests currently use a real S3 sidecar; a `mock_s3` fixture helps apps that want unit tests without it. The rest is DA domain.

### BE-T19 — Generic 500 detail suppression for public-facing blueprints

Merged into BE-C14 (same handler and test).

### BE-T20 — Stateless AMQP-publishing `SSEConnectionManager` (RabbitMQ transport)

- **Files:** `app/services/sse_connection_manager.py`, `app/services/rabbitmq_publisher.py` (new), `app/schemas/sse_gateway_schema.py`, `app/api/sse.py`; tests `tests/test_sse_connection_manager.py` (42 tests: bindings, metrics, publish failure, no publisher, mode-aware health registration)
- **What changed:** Baseline manager tracked connections in memory (`_connections`, token map, identity map, observers) and POSTed events to the gateway's HTTP `/internal/send`. DA publishes to a RabbitMQ topic exchange with routing keys derived from the `Target`; the connect callback now returns topic bindings (`broadcast`, `connection.<id>`, `subject.<sub>` or `subject.#` for `local-user`, `role.<role>`) that the gateway uses to subscribe the connection's queue. The manager keeps no per-connection state (removes `register_on_connect`, `bind_identity`, `has_connection`, `get_connection_info`), only metrics; `send_event` publishes unconditionally and returns `False` for a `None` target or a missing/failed publisher. Needs a gateway build with RabbitMQ transport and a RabbitMQ service; SSE gateway health check is registered in `backend` mode only.
- **Why:** 6cfec748 (slice 017), 402fa755 (064 R1: "Strip SSEConnectionManager to stateless AMQP publisher"), 5969b6fe (race fix: deferred observer callbacks, later replaced). Motivation is multi-process delivery: the Celery worker has no local connections and cannot call the gateway for connections held by another pod.
- **Kind:** feature / refactor
- **Applies to:** apps that publish SSE events from a separate process (worker, multiple replicas); none of the current downstream apps
- **Port effort:** L — new RabbitMQ service in dev env, CI and prod, new gateway version, new `rabbitmq_publisher.py` and health check, every `send_event` call site and test changes.
- **Recommendation:** Retired (operator, 2026-10-19). The SSE stream moved into the backend (`docs/sse_in_process_plan.md`): there is no gateway left to carry an AMQP transport, only the backend process holding a connection delivers to it, and the backend runs as one replica.

### BE-T21 — DA-specific testing endpoints, worker task publishing, Celery

- **Files:** `app/api/testing_sse.py` (`start_test_task` via `WorkspaceWorkItem`/`publish_worker_task`, `emit-content-updated`, `emit-timeline-event`, `simulate-chat-cycle`), `app/schemas/testing_sse.py` (matching schemas), `app/services/task_service.py` (`apply_queue_prefix`, `publish_worker_task`), `app/services/base_task.py` (`send_progress(..., **kwargs)`), `app/api/testing_auth.py` (`create_test_session` upserts `User`/release notes, `link-user`), `app/services/testing_service.py`; tests `test_testing_sse_api.py` (15), `test_testing_sessions_api.py`, `test_testing_edits_api.py`, `test_testing_auth_api.py`, `test_celery_*.py`, `test_publish_worker_task.py`, `test_apply_queue_prefix.py`, `test_run_worker.py`
- **What changed:** Baseline `start_test_task` ran in-process `_DemoTask`/`_FailingTask` through `TaskService`; DA replaces them with database work items processed by the Celery worker, and adds product-shaped simulation endpoints and Celery plumbing (including a worker task-publish helper that falls back to a Beat sweep when the broker is down). The per-task progress kwargs exist for DA's multi-task progress UI.
- **Why:** slices 074b, 082, 089, 173 (Celery migration f14e2632).
- **Kind:** DA-specific
- **Applies to:** DA-only
- **Port effort:** n/a
- **Recommendation:** Skip — DA domain. The generic idea (testing endpoints that emit canned SSE events for Playwright) already exists in the baseline (`send_test_task_event`, version trigger); `app.testing_guard` was only given a type annotation.

DA-specific, not candidates: customer/contact/project/document/content-asset/workspace/session/notification/release-notes/LLM-configuration/prompt/OpenSearch/search/conversation/portal/tenant/i18n/collation/Keycloak-admin/email/cleanup-CLI/maintenance-CLI domain tests and their factory fixtures (`customer_factory`, `contact_factory`, `document_factory`, `workspace_factory`, `session_factory`, `timeline_event_factory`, `notification_factory`, `user_factory`, `set_current_user`, the Keycloak `test-da-` session cleanup fixture), `tests/tools/`, `tests/worker/`, Celery and RabbitMQ publisher tests, and `test_sse_event_dispatcher.py`/`test_sse_post_commit_audit.py` call-site coverage.

## Frontend template (frontend/ and portal/)

Scope: DA's `frontend/` (employee app, `use_app_shell=true`) and `portal/` (customer app, `use_app_shell=false`), both from frontend template v0.18.1, diffed against `/work/scratch/da-base/{frontend,portal}`. A change present in both is one item; where the copies differ the better one is named. Commit SHAs are from `/work/scratch/DesignAssistant`. DA's `docs/` for frontend/portal are not in the baseline (they are app-created, largely copied conventions); the only generic content found there is the preview-mode section of `docs/testing.md` (folded into FE17).

Items are ordered Port, Port-adapted, Optional, Skip.

### FE01 — Tooltip title-mode clobbers the child's `data-testid`

- **Files:** `src/components/primitives/tooltip.tsx`
- **What changed:** In "title mode" the baseline does `React.cloneElement(child, { title, 'data-testid': testId })` unconditionally, so a Tooltip without a `testId` overwrites the child's own `data-testid` with `undefined`. DA only injects `data-testid` when `testId !== undefined`, in both the enabled-child clone and the disabled-wrapper `<div>`.
- **Why:** f70bf6f7 "preserve child data-testid in Tooltip title mode": a Button wrapped in a Tooltip became unreachable in Playwright.
- **Kind:** bug fix
- **Applies to:** all apps
- **Port effort:** S, self-contained (frontend copy only; portal never touched it, so portal still has the bug).
- **Recommendation:** Port — plain bug in template-owned code that breaks selectors.

### FE02 — `useSSETask`: persistent task-event buffer (race between HTTP 202 and subscribe)

- **Files:** `src/hooks/use-sse-task.ts` (frontend only; portal deleted the file because it does not use it)
- **What changed:** The baseline buffers `task_event` payloads (`bufferTaskEvent`) only inside the listener that `subscribeToTask` registers, so events fired between the 202 response and the subscribing `useEffect` are lost and the late-subscriber replay buffer never sees them. DA adds a mount-time `addEventListener('task_event', ...)` effect that always feeds the buffer, and removes the buffering call from the per-task listener.
- **Why:** 90cb758b "Fix SSE task event race condition in TaskProgressModal" (also dropped an `isSubscribed` gate on the in-progress UI in DA's modal, which is DA-specific).
- **Kind:** bug fix
- **Applies to:** apps with `use_sse` that use background tasks
- **Port effort:** S, self-contained.
- **Recommendation:** Port — fixes a real lost-event race in the template's task hook.

### FE03 — Task progress values are 0..1 on the wire but treated as a percentage

- **Files:** `src/hooks/use-sse-task.ts`
- **What changed:** `progress_update` maps `data.value` straight to `percentage`; the baseline backend schema (`TaskProgressUpdate.value`, `ge=0, le=1`) sends a 0.0-1.0 fraction while `ProgressBar` expects 0-100, so bars never move past 1%. DA multiplies by 100 (and maps a null value to `-1`, which is DA-specific and unneeded because the schema makes `value` required).
- **Why:** b7473fc8 "fix progress bar 0-1 to 0-100 scale".
- **Kind:** bug fix
- **Applies to:** apps with `use_sse` using `useSSETask`
- **Port effort:** S; same edit in one line. Pair with FE02 (same file).
- **Recommendation:** Port — template frontend and backend disagree on the unit.

### FE04 — Playwright-managed service teardown kills the whole process tree

- **Files:** `tests/support/process/servers.ts`, `scripts/testing-server.sh`
- **What changed:** Services are spawned with `detached: true` and stopped with `process.kill(-pid, 'SIGTERM'|'SIGKILL')` (process group) instead of `child.kill(...)`. The process-exit shutdown hook sends `SIGKILL` to the group instead of `SIGTERM` to the leader. `testing-server.sh` execs `node_modules/.bin/vite` directly instead of `pnpm exec vite`, which left a resident ~84 MB pnpm Node wrapper as Vite's parent.
- **Why:** 251a4363 "bigger effort to kill worker processes in the Playwright suites" (orphaned Python/Vite children after a crashed or interrupted run); dc943599 (direct vite binary). Note both copies are identical here.
- **Kind:** test infra
- **Applies to:** all apps
- **Port effort:** S; no other items needed. Group-kill relies on `detached: true` (POSIX only, which matches the dev environment).
- **Recommendation:** Port — orphaned servers hold ports and memory on every interrupted run.

### FE05 — Infrastructure specs need an auth session when `use_oidc` is on

- **Files:** `tests/infrastructure/sse/sse-connectivity.spec.ts`, `tests/infrastructure/sse/task-events.spec.ts`, `tests/infrastructure/deployment/deployment-banner.spec.ts` (frontend; portal did the same via a `beforeEach`), `tests/support/helpers/auth-factory.ts`
- **What changed:** Every test that touches the SSE/deployment bridges now calls `await auth.createSession()` before `page.goto`. Without a session `AuthGate` blocks `SseProviders` from mounting, so `window.__deploymentSseControls` is never registered and the baseline specs time out. `AuthFactory.createSession` also includes the response body in its error message.
- **Why:** 81c75cb1 (frontend), 0c241c6a (portal; also reverted a workaround that moved the bridge out of `SseGate`, which treated the symptom). The `roles ?? ['editor']` default and `confirmReleaseNotes` in `auth-factory.ts` are DA-specific and should not be ported.
- **Kind:** bug fix (test infra)
- **Applies to:** apps with `use_oidc` and `use_sse`
- **Port effort:** S; conditional on `use_oidc` in the spec templates.
- **Recommendation:** Port — the template's own infrastructure specs cannot pass against the template's own auth gate otherwise.

### FE06 — SSE/deployment test helpers: wait for bridges, longer timeouts

- **Files:** `tests/support/helpers/deployment-sse.ts`, `tests/support/helpers/deployment-reset.ts`, `tests/infrastructure/deployment/deployment-banner.spec.ts`, `tests/support/helpers/test-events.ts` (portal: default waits)
- **What changed:** `resetDeploymentRequestId` waits for `window.__resetDeploymentRequestId` to exist (the bridge registers at module load, which can land after `page.goto` resolves in a production build). `ensureConnected` waits for the bridge and `isConnected` in a single `waitForFunction`, closing a race where the bridge exists but refs are not yet populated. `disconnect` returns quietly when the bridge is absent instead of blocking 30 s. Bridge wait 5 s to 30 s, connection wait 20 s to 30 s. The banner spec waits for the bridge again after the reload click. Portal also raised `waitForEvent` / `waitForSseEvent` defaults from 5 s to 15 s (fixed "for remote pods") and the banner spec event waits from 15 s to 30 s. All `test-events.ts` throws pass `{ cause }` (ESLint 10 rule).
- **Why:** 5ad4522a (15 s default), 93144948 (30 s banner), d599a5c2 (`disconnect` tolerance and `ensureConnected` rewrite).
- **Kind:** test infra
- **Applies to:** apps with `use_sse`
- **Port effort:** S; the frontend copy of the helpers is the more complete one (portal lacks the `deployment-*` helper changes but has the longer default waits); take the union.
- **Recommendation:** Port — removes flakiness in template-owned helpers.

### FE07 — `generate-api.js`: `--default-non-nullable false`

- **Files:** `scripts/generate-api.js` (both)
- **What changed:** `openapi-typescript` is invoked with `--default-non-nullable false`. With v7 defaults a property that has `default: null` but is not in `required` loses its `?`, so Pydantic `*UpdateSchema` fields declared `str | None = Field(None)` become required properties in the generated TypeScript request types. The flag restores the optional modifier.
- **Why:** 23cf71e9 "BE-01" (lockstep in both apps).
- **Kind:** bug fix
- **Applies to:** all apps (any PATCH/update schema with optional defaulted fields)
- **Port effort:** S. Regenerating changes `types.ts` in every app, which is the point. DA's `shouldSkipPath` filter, `generateTableConfigs` and the hard-coded `sessionDocumentUsageTableSort` in the same file are DA-specific (see FE31) and must not travel with it.
- **Recommendation:** Port — contract fix; the dedicated generator should be correct for template backend schemas.

### FE08 — `useUiStateInstrumentation`: emit `ready` when data is already cached on mount

- **Files:** `src/lib/test/ui-state.ts` (portal only)
- **What changed:** The hook only ends a ui-state scope on a `loading -> ready` transition. When data is already in the query cache on first render (route loader pre-cached it) no transition ever happens and Playwright waiters on the scope hang. The portal copy tracks `mountedRef` and emits `endUiState` once on the first run when `!isLoading`. The frontend copy was not updated (latent same bug).
- **Why:** 47c74b05 "replace workspace loading spinner with route loader".
- **Kind:** bug fix
- **Applies to:** all apps (matters whenever a query can be cache-hot at mount: route loaders, prefetch, StrictMode remounts)
- **Port effort:** S, self-contained.
- **Recommendation:** Port — instrumentation must not depend on cold caches.

### FE09 — Console policy: allow `Toast exception` globally

- **Files:** `tests/support/fixtures-infrastructure.ts` (page fixture)
- **What changed:** The `page` fixture's console-error allowlist gains `Toast exception`, which `showException` logs in non-production builds. The baseline fails any test where a mutation error reaches `showException` (the global `onError` in `query-client.ts` does exactly that), forcing every error-path test to call `expectConsoleError` itself.
- **Why:** 7cc9d4e3 ("allow Toast exception console errors").
- **Kind:** test infra
- **Applies to:** all apps
- **Port effort:** S. The sibling allowances (`/health/readyz`, `net::ERR_`) are DA-specific (see Skip).
- **Recommendation:** Port — logging that is part of the template's own toast API should be allowlisted by the template.

### FE10 — `.dockerignore` for the frontend image

- **Files:** `.dockerignore` (new; also in portal)
- **What changed:** Excludes `**/node_modules`, `**/.git`, `**/.pnpm-store`, `**/test-results`, `**/.venv`, `**/__pycache__` from the Docker context. The baseline has none, so `COPY . .` after `pnpm install` can drag a developer's host `node_modules` into the image and overwrite the clean install.
- **Why:** 13243e28 (added with other Docker/help fixes; rationale not stated further).
- **Kind:** hardening
- **Applies to:** all apps
- **Port effort:** S; drop `.venv`/`__pycache__` for a frontend-only context if desired.
- **Recommendation:** Port — standard hygiene, no side effects.

### FE11 — ESLint/knip configuration fixes

- **Files:** `eslint.config.js`, `knip.config.ts`, `package.json` (devDependencies)
- **What changed:** (a) `react-refresh/only-export-components` is turned off for `src/routes/**` (TanStack file routes export `Route` plus components; 601470e1). (b) `@typescript-eslint/parser` and `@typescript-eslint/utils` are declared explicit devDependencies and listed in knip's `ignoreDependencies`, because the template-owned custom rule `scripts/eslint-rules/testing/no-route-mocks.ts` imports them but knip does not trace that directory and pnpm does not hoist them (0c302b47). (c) `coverage` added to ESLint `ignores` and `/coverage/`, `.env*` with `!.env.example` to `.gitignore` (the `.env*` form also covers `.env.development` etc.). (d) `package.json` gains `build-fast` (generate + vite build + verify, no `check`) with `build = build-fast && check` so CI can run lint/type-check once (aa1907ec).
- **Why:** as above.
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S; (c) coverage lines only matter if coverage (FE22) is adopted. DA removed `packageManager: pnpm@9.0.0` from `package.json` because its monorepo root pins pnpm 11; the baseline pin is stale either way.
- **Recommendation:** Port — (a) and (b) fix lint/knip noise on a fresh template app.

### FE12 — Vite dev/preview proxy: forwarded headers, SSE header flush, `strictPort`

- **Files:** `vite.config.ts`
- **What changed:** `xfwd: true` on `/api` and `/api/sse` proxies (backend sees `X-Forwarded-*`, needed for correct OIDC redirect URLs behind the dev proxy; 16a1c24c). `configureSseProxy`: on `proxyRes` with `Content-Type: text/event-stream`, write the status and headers and a `: proxy-connected` SSE comment so the browser sees `EventSource.onopen` immediately instead of waiting for the first heartbeat. `server.strictPort: true` so a busy port fails instead of silently moving (Playwright assumes the port). The portal copy of `configureSseProxy` is the correct one: it deletes `transfer-encoding` before `writeHead`, because http-proxy removes chunking only after `proxyRes`, and writing chunked headers made the browser buffer the stream forever (c35c4249); the frontend copy lacks that fix.
- **Why:** 96337889 (flush), c35c4249 (chunked fix), 16a1c24c (xfwd), 13243e28 (strictPort).
- **Kind:** bug fix
- **Applies to:** apps with `use_sse` (flush); all apps (xfwd, strictPort)
- **Port effort:** S; take the portal version of `configureSseProxy`, apply to both `server.proxy` and `preview.proxy`. DA's `/health`, `/docs/*` proxies, `fs.allow` and `manualsDevPlugin` are DA-specific.
- **Recommendation:** Port — real dev-server SSE stall and missing forwarded headers.

### FE13 — nginx `Host $http_host`

- **Files:** `snippets/proxy.conf` (both)
- **What changed:** `proxy_set_header Host $host` becomes `$http_host`, so the upstream sees the client's `Host` including a non-default port. `$host` strips the port, which skews absolute URLs the backend builds (redirects, OIDC callbacks) when served on a non-standard port.
- **Why:** 13243e28 (rationale not stated in the commit; bundled with the help-docs deployment fixes).
- **Kind:** hardening
- **Applies to:** all apps
- **Port effort:** S, one line.
- **Recommendation:** Port — low risk. Operator may want to confirm no app depends on the port-stripped host.

### FE14 — Playwright video off by default

- **Files:** `playwright.config.ts`
- **What changed:** `video: process.env.PLAYWRIGHT_VIDEO ? 'on' : 'off'` replaces `retain-on-failure` (with `PLAYWRIGHT_RETAIN_VIDEO` as the opt-in to always record). Recording a video for every test and discarding passes costs CPU and disk across many workers.
- **Why:** 97d89d3b "Don't record videos by default in Playwright"; no further rationale.
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S. Keep traces (`on-first-retry`) and screenshots as DA did. Consider `retain-on-failure` gated by an env var rather than fully off.
- **Recommendation:** Port — cheap speed-up; adjust to keep failure videos opt-in.

### FE15 — SSE ready-event gating (late-joining tab fix included)

- **Files:** `src/workers/sse-worker.ts`, `src/contexts/sse-context-provider.tsx` (identical in both apps)
- **What changed:** `connected` / `isConnected` is no longer set on `EventSource.onopen`; the worker and the direct-EventSource path wait for a named `ready` SSE event (`addEventListener('ready', ...)`, no data line) emitted by the SSE gateway once its consumer bindings exist. The worker tracks `readyReceived` (reset on close and on every `createEventSource`) and a late-joining tab is told `connected` only if `readyReceived`, instead of `eventSource.readyState === OPEN` (previously a new tab could be told "connected" before bindings existed). The unused `connection_close` listener is removed.
- **Why:** b11c5cc4 (slice 083), then 5a17a4c5 / facb8c37 once the gateway changed `ready` to a named event. Needs the matching SSEGateway build (DA bumped `ssegateway` `#stable` for it) and the gateway-side `ready` emission, which DA tied to its AMQP transport; confirm the template's gateway/backend path also emits `ready` for the callback transport.
- **Kind:** bug fix (race: events published right after connect are missed if the app treats `onopen` as ready)
- **Applies to:** apps with `use_sse`
- **Port effort:** M. Worker and provider edits are mechanical; depends on a gateway/backend item (BE section) and on the test-event emission moving from `onopen` to `ready`.
- **Recommendation:** Port-adapted — port the `readyReceived` / `ready` gating together with the gateway version; generic part is "connected means subscribed, not TCP-open".

### FE16 — SSE auth rejection: terminal `rejected`, token refresh, forced `reconnect`

- **Files:** `src/workers/sse-worker.ts`, `src/contexts/sse-context-provider.tsx`, `src/types/playwright-binding.d.ts`, `tests/infrastructure/sse/sse-auth-recovery.spec.ts` (new in both), `docs/testing.md`
- **What changed:** The gateway can emit a named `rejected` event (`{status, message}`) when the connect callback returns 401/403. The worker treats it as terminal (sets `rejectedTerminal`, closes, suppresses the `onerror` reconnect loop, broadcasts typed `rejected` to all tabs; raw payload is logged truncated on parse failure). The provider probes `/api/auth/self` (refreshing OIDC cookies via the API client's auth middleware): 200 posts `{type:'reconnect'}` to the worker, 401 lets the existing middleware redirect to login, anything else shows a "connection lost, refresh" toast (kept in a ref to avoid rebuilding the SharedWorker on every toast render). New `reconnect` tab command (`handleReconnect`: close, clear terminal flag, new request id). The public `reconnect()` now actually asks a live-but-disconnected worker to reconnect (baseline did nothing when the worker ref existed) while keeping the `isConnected` short-circuit for window-focus calls. Test-only `window.__sseForceWorkerReconnect` bridge. Portal swaps the hard-coded toast string for `t('errors.connectionLost')`.
- **Why:** d599a5c2 / 3724faa8 (slice 175). Without it an expired session while the stream is open produces a tight reconnect loop against a gateway that keeps rejecting.
- **Kind:** hardening
- **Applies to:** apps with `use_sse` and `use_oidc` (the `rejected` path needs the auth flow)
- **Port effort:** M-L. Requires the SSEGateway version that emits `rejected` and a backend callback that maps auth failures to 401/403 (BE section); the Playwright spec needs a testing endpoint to make the gateway reject (DA used a `/api/testing` hook) and `PLAYWRIGHT_PREVIEW_MODE` (FE17) because the SharedWorker path is dead under the Vite dev server.
- **Recommendation:** Port-adapted — right behaviour for any OIDC + SSE app (session expiry is universal); port with the gateway/backend pieces and keep the toast string in the template's own wording.

### FE17 — Opt-in preview mode for Playwright (production build under test) and the Vite test-mode build fix

- **Files:** `scripts/testing-server.sh` (`--preview`), `tests/support/process/servers.ts` (`PLAYWRIGHT_PREVIEW_MODE`), `vite.config.ts` (`define` and `build.rolldownOptions.external`), `docs/testing.md` ("Production-build (preview-mode) tests" section)
- **What changed:** `testing-server.sh --preview` runs `vite preview` against `dist/`; `startFrontend` passes it when `PLAYWRIGHT_PREVIEW_MODE=true`. For that to work the baseline `vite.config.ts` had to be fixed: it forced `import.meta.env.VITE_TEST_MODE` to `'false'` whenever `NODE_ENV=production` and externalised `./src/lib/test/*` only when `NODE_ENV=production && VITE_TEST_MODE=true` (backwards), so a production build could never carry the Playwright bridges. DA defines `VITE_TEST_MODE` from the env and externalises the test directory unless `VITE_TEST_MODE === 'true'`. Specs that exercise the SharedWorker are gated with `test.skip(PLAYWRIGHT_PREVIEW_MODE !== 'true')` since `shouldUseSharedWorker()` is false under `import.meta.env.DEV`.
- **Why:** 7cc9d4e3 (preview flag), 0f8518f1 / ed93557d (`define`), 5ff5962e (`external`), 7ae01827 then 75cba9cc / efee7d42 (DA first made preview the default for stability against Vite dev-server dependency-optimiser 504s, then reverted to opt-in because it needed a build step in global-setup).
- **Kind:** test infra
- **Applies to:** apps with `use_sse` (SharedWorker coverage); build fix applies to all apps
- **Port effort:** M. Keep it opt-in; document `VITE_TEST_MODE=true pnpm build` plus `PLAYWRIGHT_PREVIEW_MODE=true`. Fixes to `vite.config.ts` are the load-bearing part.
- **Recommendation:** Port-adapted — port the config fix and the opt-in flag; do not make preview the default.

### FE18 — Playwright service startup robustness

- **Files:** `tests/support/process/servers.ts`, `tests/support/fixtures-infrastructure.ts` (worker fixture timeout)
- **What changed:** Startup timeouts raised (backend/gateway 30 s to 120 s, frontend 90 s to 120 s) and the service-manager worker fixture from 120 s to 300 s; readiness poll tracks `lastStatus`/`lastBody` and appends the last response body (first 500 chars) to the timeout error so a failing health check names itself; the poll sleeps only the remainder of the interval after a slow fetch; each service logs its startup time (`ready at ... (1234ms)`) unconditionally. DA's interval change (200 ms to 1 s) is not a clear gain and tracks its heavier stack; keep the baseline 200 ms.
- **Why:** 9655f6ad, 6ec9d26d, 8fc9d331, b7cd22e7, 76b2967d. The `response.status === 503` acceptance (frontend copy only) is DA-specific because DA's `/health/readyz` returns 503 when degraded and RabbitMQ is absent in tests; do not port.
- **Kind:** test infra
- **Applies to:** all apps
- **Port effort:** S.
- **Recommendation:** Port-adapted — timeout bumps (moderate values) and failure diagnostics are generic; leave the poll rate and 503 acceptance behind.

### FE19 — Toast diagnostics copy affordance

- **Files:** `src/components/primitives/toast.tsx`, `src/contexts/toast-context-provider.tsx`, `src/lib/utils/error-diagnostics.ts` (+ `.test.ts`), `src/styles/toast.ts` consumers
- **What changed:** `showException` serialises the error (name, message, stack, HTTP status) via `serializeErrorDiagnostics` into `ToastOptions.diagnostics`; the toast's leading icon turns into a copy-to-clipboard button on hover (check mark on success) that copies `[ERROR] message` plus the diagnostics. The button is shown only when the stage reported by `GET /api/ui-setup` is non-production (`useGetUiSetup`, `staleTime: Infinity`) and the toast carries diagnostics. Portal's `toast-context-provider` inlines the serialiser (frontend extracted it into `error-diagnostics.ts` for testability — use that one). Both copies' button positions use `items-center` alignment.
- **Why:** b55a39b0 / 326c8c83 (overhaul, slice 047), 3df81c77 (diagnostics gate), 6ba22eba / e7d29af0 (move onto the tone icon).
- **Kind:** feature
- **Applies to:** all apps
- **Port effort:** M. Needs a `stage` field and an `ui-setup`-style endpoint (DA backend; check BE section) or a build-time `VITE_*` flag for non-prod; `toast.tsx` imports a generated hook so it cannot be taken verbatim.
- **Recommendation:** Port-adapted — useful for debugging in dev and test; gate on an env flag instead of DA's generated API hook.

### FE20 — `use_app_shell=false` renders shell leftovers (user dropdown, shell-dependent auth tests)

- **Files:** `src/components/layout/user-dropdown.tsx` (portal deleted), `tests/infrastructure/auth/auth.spec.ts`, `tests/infrastructure/auth/AuthPage.ts`, `src/hooks/use-sse-task.ts`, `tests/infrastructure/sse/task-events.spec.ts` (portal deleted)
- **What changed:** In the portal baseline `auth.spec.ts` still has "Authenticated User Display" and "Logout Flow" tests that need the top-bar user dropdown (`AuthPage.waitForAuthenticated` waits on `userDropdownTrigger`), which do not exist without the shell; `user-dropdown.tsx` is generated but unused. DA deleted those tests/files and replaced the positive signal with the `ui_state auth ready` test event (`testEvents.waitForEvent(kind==='ui_state' && scope==='auth' && phase==='ready')`), and keeps the retry test asserting only that the error screen disappears.
- **Why:** 31bc39d2 (trimmed auth tests), 3cd875f7; rationale beyond that not stated. Note the baseline already has `auth-shell.spec.ts` only for the shell variant, so the leak is limited to the files above.
- **Kind:** bug fix (template variant)
- **Applies to:** apps with `use_app_shell=false`
- **Port effort:** S.
- **Recommendation:** Port-adapted — verify against the current template whether the no-shell variant still renders these; fix by flag-gating if so.

### FE21 — `index.css` customisations in a template-owned file

- **Files:** `src/index.css` (both)
- **What changed:** DA edited the template-owned file for: `@source "../../packages/shared-ui/src"` and `@plugin "@tailwindcss/typography"` (DA-specific); `button { cursor: pointer }` in `@layer base` (Tailwind 4 resets buttons to the default cursor); `td { vertical-align: middle }` (frontend only); softer dark-mode tokens (`--primary`, `--ring`, `--link-hover` from `220 90% 56%` to `220 70% 65%`; frontend also `--destructive` from `0 63% 31%` to `0 72% 51%`, where the baseline red is nearly unreadable on dark backgrounds); a `--stage-indicator` token and slide-down keyframes (frontend, DA features).
- **Why:** 050d6ed6 / aaa2db46 (dark mode), fdbfeddd, b702f719 (UI polish).
- **Kind:** refactor / UI polish
- **Applies to:** all apps (dark mode and cursor); the rest DA-only
- **Port effort:** S for the cursor rule and dark-mode contrast; M if moving theme overrides into the app-owned `styles/app-theme.css` so apps stop editing `index.css`.
- **Recommendation:** Port-adapted — take `button { cursor: pointer }` and the dark-mode `--destructive`/`--primary` contrast; the fact that DA had to edit the template file for `@source` / `@plugin` suggests an app-owned hook import.

### FE22 — Istanbul coverage for Playwright runs

- **Files:** `vite.config.ts` (`vite-plugin-istanbul` when `VITE_COVERAGE=true`), `scripts/testing-server.sh`, `tests/support/fixtures-infrastructure.ts` (page fixture flushes `window.__coverage__`), `tests/support/global-teardown.ts` (merge + report), `package.json` (`nyc`, `test:coverage`, `coverage:report`), `.gitignore`, ESLint ignore
- **What changed:** Opt-in coverage: with `VITE_COVERAGE=true` the page fixture writes each test's coverage JSON synchronously into `coverage/.tmp/` (async writes were lost when workers were SIGKILLed; subdirectories break `nyc merge`) and global teardown merges and renders reports.
- **Why:** bb6d7927 (slice 075), 85567883 (sync write, flat dir), 0536570f.
- **Kind:** feature (test infra)
- **Applies to:** apps that want E2E coverage numbers
- **Port effort:** M; needs `vite-plugin-istanbul` and `nyc` devDependencies and a global-teardown file that also hosts the DB cleanup in DA (extract the coverage half).
- **Recommendation:** Optional — no current app needs it; the sync-write lesson is worth keeping if added.

### FE23 — Per-worker PostgreSQL databases cloned from a seed template

- **Files:** `tests/support/helpers/pg-admin.ts` (new), `tests/support/global-setup.ts`, `tests/support/global-teardown.ts` (new), `tests/support/fixtures-infrastructure.ts`, `tests/support/process/servers.ts` (`--database-url` instead of `--sqlite-db`), `package.json` (`pg`, `@types/pg`), `playwright.config.ts` (`globalTeardown`)
- **What changed:** Global setup drops stale `<prefix>_*` databases, creates `<prefix>_seed`, runs `poetry run cli load-test-data` against it; each Playwright worker does `CREATE DATABASE ... TEMPLATE <seed>` and drops it at teardown (`DROP DATABASE ... WITH (FORCE)`). Replaces the baseline's seeded-SQLite-file-copy flow (`initialize-sqlite-database.sh`, `PLAYWRIGHT_SEEDED_SQLITE_DB`, per-worker temp dir). The copies differ only in the default prefix (`test_da_frontend` vs `test_da_portal`), which also prevents cross-app collisions on one Postgres.
- **Why:** 6d739033 (slice 007b, because DA's backend moved to PostgreSQL). `pg-admin.ts` also creates DA-specific ICU collations `app_ci` / `app_ci_ai` on the seed DB.
- **Kind:** feature (test infra)
- **Applies to:** apps with `use_database` if the backend template standardises on PostgreSQL for tests (current baseline uses SQLite)
- **Port effort:** L; coupled to the backend section's database choice, the root template's Postgres sidecar, and `load-test-data` CLI. Parameterise host/credentials/prefix and drop the collations.
- **Recommendation:** Optional — template decision belongs with the backend/root items; port the clone-from-template pattern only if tests move to Postgres.

### FE24 — Vitest unit/component runner

- **Files:** `vitest.config.ts`, `tsconfig.vitest.json` (portal references it from `tsconfig.json`), `src/__tests__/setup-i18n.ts` (portal), `package.json` (`vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `@types/jsdom`), `knip.config.ts` (`vitest.config.ts`, `src/**/__tests__/**/*.test.*` as entries); `test`/`test:unit` script
- **What changed:** Template ships Playwright only. DA added Vitest with `@` aliases, jsdom, and `import.meta.env.DEV=false` for component tests; portal has two tests (e.g. `content-panel`, `help-articles`), frontend a handful of pure-util tests (`error-diagnostics.test.ts`), shared-ui uses it for the markdown/diff logic.
- **Why:** 4a8249b6 "Vitest bootstrap" (slice 024). The template's `testing/no-route-mocks` philosophy keeps behaviour tests in Playwright, so Vitest is for pure functions only.
- **Kind:** tooling
- **Applies to:** apps with non-trivial client-side logic (parsers, formatters, state machines)
- **Port effort:** S-M; needs knip wiring (ignore deps as DA did) and tsconfig reference.
- **Recommendation:** Optional — available as `pnpm test:unit` convention; no current app has pure-logic hotspots.

### FE25 — Localisation with react-i18next (portal)

- **Files:** `src/i18n.ts`, `src/main.tsx` (import), `src/locales/{en,nl}.json`, `schema.json`, `nl.meta.json`, `src/lib/api/accept-language-middleware.ts`, `docs/localization.md`, vitest `setup-i18n.ts`; string extraction in template-owned `auth-gate.tsx`, `deployment-notification-bar.tsx`, `alert.tsx`, `inline-notification.tsx`, `sse-context-provider.tsx` (toast copy), `auth-context.tsx` (language switch)
- **What changed:** Bundled `en.json` is the source of truth, `nl.json` is generated (DA's `canon localize`, not generic), language is server-driven from the profile response (not browser-detected), non-English bundles are `import.meta.glob`-ed eagerly and registered at runtime so `changeLanguage` stays synchronous, an `openapi-fetch` middleware sends `Accept-Language` once the profile is cached. About 6 template-owned components needed `t()` calls.
- **Why:** c03db0d0 (slice 118) plus 153.
- **Kind:** feature
- **Applies to:** apps with non-English users or multi-locale content (a candidate `use_i18n` flag)
- **Port effort:** L; flag-gated edits across many template-owned files, plus a decision on how translations are produced and on the profile-driven language source.
- **Recommendation:** Optional — none of the hobby apps are multilingual; list as a candidate flag, not a default.

### FE26 — Route loaders with `ensureQueryData`, pending UI and navigation progress bar

- **Files:** `src/App.tsx` (`defaultPendingComponent`, `defaultPendingMinMs: 200`), `src/components/common/navigation-progress.tsx`, `src/components/common/route-error.tsx` (`NotFoundRedirect`), `src/lib/api/query-options.ts`, `src/routes/**` loaders (DA-specific entities)
- **What changed:** DA replaced per-page loading spinners with TanStack Router loaders that prefetch via query-option factories whose keys equal the generated hook keys (so components render with data, no refetch). Router shows a pending component after 200 ms plus a thin exponential-decay progress bar for slow transitions. `NotFoundRedirect` toasts and redirects when a loader gets 404. The test-infra implications (FE08 above; a toast-viewport wait in `test-infrastructure.spec.ts` because loaders block the initial render) came with it.
- **Why:** 5cb90818 (slice 054), 3df81c77 (progress bar).
- **Kind:** feature
- **Applies to:** apps with detail pages that benefit from prefetch
- **Port effort:** M for the pattern doc and generic parts (`NavigationProgress`, `NotFoundRedirect`, pending defaults); the query-option factories are hand-written per endpoint and could be generated by `generate-api.js`.
- **Recommendation:** Optional — pattern worth documenting; generating the factories would be the real template value.

### FE27 — Non-blocking `SseGate` (portal)

- **Files:** `src/components/sse/sse-gate.tsx`
- **What changed:** The gate renders children unconditionally instead of a blank div until `isConnected`; hooks buffer events that arrive before their initial fetch completes. The blocking version produced blank pages when the SSE stream was delayed (the Vite proxy buffered the `ready` event) or the gateway was unavailable. Frontend kept the blocking gate and hit the same blank page after `ready` was introduced (facb8c37).
- **Why:** c35c4249 (slice 087b).
- **Kind:** hardening
- **Applies to:** apps with `use_sse` where SSE is not needed for first paint
- **Port effort:** S for the gate; M if the template's SSE-consuming hooks do not already buffer before initial fetch.
- **Recommendation:** Optional — changes a documented template assumption ("SSE is a reliable sidecar"); give apps a choice (gate with timeout, or pass-through).

### FE28 — Dialog `preventOutsideClose` (default true), overlay test id

- **Files:** `src/components/primitives/dialog.tsx` (both)
- **What changed:** New prop `preventOutsideClose` (default `true`) sets `onInteractOutside={e => e.preventDefault()}`, so clicking the backdrop no longer discards a half-filled form. Portal's version defers to `contentProps.onInteractOutside` when false and adds `data-testid="dialog-overlay"`; the frontend version spreads `contentProps` after, so a caller override still wins.
- **Why:** 94c32c13 / ab93768f (slice 051 "form dialog behavior fixes"); rationale: accidental data loss.
- **Kind:** feature (behaviour default change)
- **Applies to:** all apps
- **Port effort:** S; the default flip changes behaviour of every existing dialog.
- **Recommendation:** Optional — a policy default; if adopted take portal's variant.

### FE29 — Button loading overlay and no-wrap

- **Files:** `src/components/primitives/button.tsx`, `src/styles/button.ts` (`whitespace-nowrap`; app-owned)
- **What changed:** While `loading`, the original label and icon stay in the layout (hidden via `invisible`) and the spinner is overlaid, so the button keeps its width (no layout shift), instead of swapping the icon for a spinner. `asChild` renders only `children` (Radix `Slot` requires exactly one child; the first overlay version rendered `false` + children and crashed). The frontend copy (after 09a57a43) is correct; the portal copy wraps content in an `invisible` span even for `asChild`, which would break `Slot` — do not use it. Content wrapped in `inline-flex items-center` to keep icon and text side by side (1c71159f).
- **Why:** b6aa65b9 / d39c6cfe (slice 046), 09a57a43 (asChild crash), 1c71159f.
- **Kind:** feature (UI polish) with a bug fix
- **Applies to:** all apps
- **Port effort:** S.
- **Recommendation:** Optional — visual taste; if taken, use the frontend/ version.

### FE30 — PID-namespace wrapper for Playwright (`unshare`)

- **Files:** `package.json` (`"playwright": "unshare --user --pid --fork playwright"`), `knip.config.ts` (`ignoreBinaries: ['unshare']`)
- **What changed:** Running Playwright in a new PID namespace means that when the runner dies every child (backend, Vite, gateway) dies with it, regardless of process groups. Complements FE04.
- **Why:** c9795e90 "Fixed process tree isolation issues" (first `--pid`, later `--user --pid`).
- **Kind:** hardening
- **Applies to:** Linux dev containers
- **Port effort:** S; fails where unprivileged user namespaces are disabled and does not exist on macOS.
- **Recommendation:** Optional — FE04 covers most cases; add behind a documented script name rather than rebinding `playwright`.

### FE31 — Server-side sort/pagination building blocks

- **Files:** `src/components/ui/data-table.tsx`, `src/hooks/use-server-sort.ts`, `src/hooks/use-pagination.ts`, `scripts/generate-api.js` (`generateTableConfigs` writes `src/lib/api/generated/table-configs.ts`)
- **What changed:** A `@tanstack/react-table` wrapper plus hooks that persist sort/page state; the generator scans GET endpoints with a `sort_by` enum and `sort_dir` parameter and emits camelCase-to-snake_case `TableSortConfig` objects. Requires backend list endpoints following the `sort_by`/`sort_dir`/page convention.
- **Why:** introduced with DA's list screens (table sorting slices); not documented as a single commit.
- **Kind:** feature
- **Applies to:** apps with large lists
- **Port effort:** M-L; depends on a backend convention in the BE section.
- **Recommendation:** Optional — good if a list-heavy app appears; otherwise leave in DA.

### FE32 — Dev health indicator and stage indicator

- **Files:** `src/components/layout/dev-health-indicator.tsx`, `src/components/layout/stage-indicator.tsx`, `src/components/layout/top-bar.tsx`, `src/index.css` (`--stage-indicator`), `vite.config.ts` (`/health` proxy)
- **What changed:** Dev-only (`import.meta.env.DEV`) coloured circles for backend and worker `/health/readyz`, with a hover panel showing the check details; a top-bar text badge for the deployment stage (hidden for PRD, from `GET /api/ui-setup`).
- **Why:** c132e907 (slice 035c).
- **Kind:** feature
- **Applies to:** apps with `use_app_shell`
- **Port effort:** S-M; needs `ui-setup` endpoint with `stage` (also used by FE19) and the `/health` Vite proxy.
- **Recommendation:** Optional — nice for multi-stage deployments; pairs with FE19.

### FE33 — Sidebar: collapse animation and badge render prop

- **Files:** `src/components/layout/sidebar.tsx`, `src/components/layout/top-bar.tsx` (frontend)
- **What changed:** Labels and children animate on collapse via `max-w`/`max-h` and `opacity` transitions instead of conditional rendering (`overflow-hidden`, `shrink-0` on icons); `SidebarItem` gains optional `badge?: () => ReactNode`. DA wires the inbox unread count via a DA-only `SidebarBadgeProvider`.
- **Why:** cfe9297e (slice 065 layout polish), 8571d3a7 (inbox).
- **Kind:** feature
- **Applies to:** apps with `use_app_shell`
- **Port effort:** S for the generic render prop; the provider/inbox parts are DA-specific.
- **Recommendation:** Optional — port only the `badge` prop and animation if desired.

### FE34 — Workspace package shared by two frontends (`packages/shared-ui`)

- **Files (DA root, not in either app):** `packages/shared-ui/{package.json,tsconfig.json,vitest.config.ts,parity-server.ts,test-fixtures/edit-parity.json,src/**}`, `pnpm-workspace.yaml` (`frontend`, `portal`, `packages/*`), root `package.json` (`packageManager: pnpm@11.6.0`); consumer wiring in `frontend/` and `portal/`: `tsconfig.app.json` / `tsconfig.playwright.json` path aliases plus `include`, `vite.config.ts` `server.fs.allow`, `src/index.css` `@source` and CSS imports, `knip.config.ts` `ignoreDependencies`, `package.json` (`"@design-assistant/shared-ui": "workspace:*"`), `Dockerfile` (root build context, copying `pnpm-workspace.yaml` and `packages/shared-ui/package.json` before install)
- **What it holds:** Source-only TypeScript package (`main: src/index.ts`, no build step). Contents are DA-specific: `HelpProvider` / `useHelp` / `HelpPanel` (context-sensitive help drawer: history stack, async `resolveArticle` loader with cache, markdown rendering via `react-markdown`), `DiffSegments` and `rehypeAnnotations` / `applyContentEdit` / `extractMarkdownTitle` (markdown editing, annotation and diff rendering for the AI chat), and shared CSS (`edit-highlight.css`, `diff-segments.css`). The parity server and fixture check that the Python backend and the TS `applyContentEdit` agree. Nothing in it is a de-duplicated primitive; the generic UI primitives (`Button`, `Dialog`, `Toast`, ...) stayed duplicated in both apps by template design, so the pattern was used for domain code.
- **Why:** 50e8714d (slice 070a), 91c6533a (portal rewire), 924e7955, dc39d0a6.
- **Kind:** refactor
- **Applies to:** DA-only today; a repo with two frontends would want the pattern
- **Port effort:** L for a template feature (workspace layout vs the current one-app-per-component copier model; `copier update` would need to manage a package outside `frontend/`, and the Docker context moves to the repo root).
- **Recommendation:** Optional (pattern only, not the contents) — document the wiring in a how-to; no current or planned app has a second frontend. The help system is a candidate on its own only if the operator wants in-app help articles (it is tied to DA's `canon` docs tooling and `/docs/*` nginx routes, so Skip as shipped).

### FE35 — nginx cache-control restructure (`location /` immutable)

- **Files:** `nginx.conf` (both)
- **What changed:** The baseline caches only listed static extensions (`js|css|png|...`) with `expires 1y; immutable` and serves `index.html` with `no-cache`. DA moved `expires 1y; Cache-Control "public, immutable"` into `location /`, so everything except exactly `/index.html` is cached for a year, including non-hashed files such as `/version.json` (the file the backend polls for deployment detection) and `public/` assets.
- **Why:** 2bdd3ba2, rationale not stated (bundled with a canon-docs deployment fix).
- **Kind:** DA-specific
- **Applies to:** DA-only
- **Port effort:** n/a
- **Recommendation:** Skip — worse than baseline (risks stale `version.json` through any HTTP cache); DA's extra proxy locations (`/docs/canon`, `/docs/uat`, `/docs/frontend`, `/docs/portal`) are product-specific.

### FE36 — Global 409 suppression in `query-client.ts`

- **Files:** `src/lib/query-client.ts` (both)
- **What changed:** The global mutation `onError` skips the toast for status 409 because every DA call site shows its own inline conflict message; `error` typed `Error` instead of `any`.
- **Why:** fe82c999 (frontend), portal equivalent; policy specific to DA.
- **Kind:** DA-specific
- **Applies to:** DA-only
- **Port effort:** S
- **Recommendation:** Skip — blanket policy; if wanted, expose a per-mutation opt-out (`meta`) instead. The `any` to `Error` typing is a free tidy-up.

### FE37 — Role enforcement in `useAuth` / `AuthGate` copy

- **Files:** `src/hooks/use-auth.ts`, `src/contexts/auth-context.tsx`, `src/components/auth/auth-gate.tsx`, `tests/infrastructure/auth/auth.spec.ts`, `AuthPage.ts`
- **What changed:** Client-side second layer: authenticated only if `roles` contains `editor` (frontend) or `portal`/`editor` (portal); missing roles show the Forbidden screen. AuthGate wording changed to DA product text (portal: i18n keys).
- **Why:** 2dc04e55, 3cd875f7 (slice 033).
- **Kind:** DA-specific
- **Applies to:** DA-only
- **Port effort:** n/a
- **Recommendation:** Skip — the template has no app role concept on the client; the Forbidden screen already exists for backend 403.

### FE38 — Other DA-specific changes in template-owned files

- **Files:** various
- **What changed:** `file-validation.ts` / `drop-zone.tsx` (removed image/PDF type restrictions; Any file type), `use-copy-to-clipboard.ts` (portal `copyRich` with `marked` / `remove-markdown`), `api-error.ts` (portal `extractLockedBy`), `components/ui/index.ts` / `primitives/index.ts` (exports of DA `Select`, DA-only primitives), `detail-screen-layout.tsx` test-id rename and toolbar padding, `status-badge.tsx` padding, `user-dropdown.tsx` (release notes, notification preferences), `top-bar.tsx` (docs, UAT links), `__root.tsx` (HelpProvider, SidebarBadgeProvider, ReleaseNotesDialog), `main.tsx` / `core-providers.tsx` / `auth-providers.tsx` (i18n, `ProfileGate`), `sse-context-provider.tsx` imports, `Dockerfile` (DA prebuilt base image, root build context, `build-cache-get.sh`), `.env.example` (`VITE_BACKEND_URL`, inconsistent with `vite.config.ts`, which still reads `BACKEND_URL`), `public/favicon.png`, `Jenkinsfile` (deleted; DA root pipelines), `docs/conventions/*` (copied EI-style docs), `.claude/`, `.llmbox/`, `.vscode/`, `.canon-output/`, `scripts/run-server.sh` (DA root `docker-run.sh`), `.codehealthignore` and the `// health: ignore` header in `query-instrumentation.ts`.
- **Why:** various DA product slices.
- **Kind:** DA-specific
- **Applies to:** DA-only
- **Port effort:** n/a
- **Recommendation:** Skip

### FE39 — DA-specific Playwright harness parts

- **Files:** `tests/support/fixtures-infrastructure.ts`, `tests/support/process/servers.ts`, `tests/support/process/backend-logs.ts`, `tests/support/global-setup.ts`, `tests/support/fixtures.ts`, `selectors-domain.ts`, `helpers/api-factories.ts`, `monaco-helpers.ts`, `email-assertions.ts`, `role-parameterization.ts`, `testing-sse.ts`, `workspace-factory.ts`, `page-objects/*`
- **What changed:** Third managed service `startWorker` with `workerLogs` / `PLAYWRIGHT_WORKER_LOG_STREAM` (Celery worker, parallel start with the frontend), `RABBITMQ_ENV_PREFIX=test-<port>` and auto-delete for per-backend queue isolation (gateway gets it too), `OIDC_ENABLED=false` kept, allowlist entries `/health/readyz` and `net::ERR_` (blanket network errors, too loose for a template), `forEachRole` role-parameterised suites and `da_impersonate` cookie helper, all domain page objects, factories and selectors.
- **Why:** 7535201f, 14f4c72f, c132e907, 00fc23ef, 7c218bd3, 4f2d0d5a, 416c822c, 25231e28, 6578f94f.
- **Kind:** DA-specific
- **Applies to:** DA-only (a worker service in the fixture is the only part an app with a Celery worker would want)
- **Port effort:** n/a
- **Recommendation:** Skip — if a future app adds a worker, copy the `startWorker` / `workerLogs` pattern then.

**DA-specific, not candidates:** Customers, projects, documents/context, sessions, inbox and notifications, notification preferences, release notes, LLM configuration, content assets and workspaces (and the whole portal workspace: chat, content panel, annotations/diffs, timeline, search modal, sidebar tree, feedback widget, abuse lockout, brand mark), the Monaco markdown editor, canon/UAT/manual help sites and `help-articles` loaders, JSON tree view, simulation buttons, DA's `tests/domain/**`, `tests/workspace/**`, `tests/help/**`, `tests/sidebar/**`, `tests/localization/**` specs and corresponding page objects and API factories.

## Root — monorepo tooling, CI, dev workflow

Scope: DA's root (everything outside `backend/`, `frontend/`, `portal/` app code). DA's root pre-dates the template root layer, so there is no baseline render. Where a counterpart exists in `/work/ModernAppTemplate/root/template` I only say so (not compared). Paths are relative to the DA repo root.

### RT01 — Counterpart exists: suite runner (local), display and process helpers

- **Files:** `tools/suite_runner/{local,display,process,__init__}.py`, `tools/suite_runner/tests/test_process.py`
- **What changed:** Counterpart exists in root template (`tools/suite_runner/{local.py,display.py,process.py,__init__.py}`) — compare at dedup time. DA-side history worth checking for fixes the template may lack: loud `=== TIMEOUT ... ===` kill line plus a unit test (`325c3bb6`), `--max-failures/--retries/--workers` passthrough to pytest/playwright (`43f08af7`, `6564697e`), vitest run in front/portal suites after a build (`b21f02f5`, `b3057b1c`), readiness waits that fail on 503 (`9655f6ad`), per-step peak-memory tracking via psutil, `poetry lock --no-update` retry on a stale lock.
- **Why:** See SHAs above.
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S-M — diff-driven; the suite list and service waits are DA-specific
- **Recommendation:** Diff at dedup — counterpart exists in the root template; the DA-side changes listed above are what to look for.

### RT02 — Counterpart exists: Jenkinsfile validation pipeline

- **Files:** `Jenkinsfile`
- **What changed:** Counterpart exists in root template (`Jenkinsfile.jinja`) — compare at dedup time. DA-side mechanics to check against it: validation runs as a one-shot k8s Job with sidecars; code is shipped with `kubectl cp` of a context tar plus a `ready` sentinel file; the container writes `exit-code` then `sleep infinity` so results can be copied out; pod log is cleaned and a `===SUITE_RESULT:` summary is built per suite; `try/finally` always deletes the Job; image tag chosen by branch map (`origin/main`->`tst`, `origin/develop`->`dev`, unknown branches rejected, `2621cfe5`); Playwright base image selected from the version in `pnpm-lock.yaml`; kaniko builds tagged `<prefix>-<build>` and `<prefix>-latest`; final `cicd.helmDeploy()` (`61f2d3ab`); `library ... changelog: false` (`4ae681f2`); OpenBao/Vault secrets via `withVault` (`335bb8a0`).
- **Why:** Iterated Mar–Jun 2026 (`3e0ffde0` monorepo build, `46b28df1` parallel suites, later `86b2ea1b` serial again to cap memory).
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S for diff
- **Recommendation:** Diff at dedup — counterpart exists in the root template; the DA-side changes listed above are what to look for.

### RT03 — Counterpart exists: dev orchestration (Procfile.dev, dev.py, dev-sse-gateway.sh, regenerate-openapi.py)

- **Files:** `Procfile.dev`, `scripts/dev.py`, `scripts/dev-sse-gateway.sh`, `scripts/regenerate-openapi.py`
- **What changed:** Counterparts exist in root template (all four) — compare at dedup time. DA notes for the diff: `dev.py` runs honcho in a PTY plus `unshare --user --pid --fork` so every descendant dies with honcho, strips ANSI to per-service `logs/<svc>.log` (`e645f547`, `c9795e90`, `acb26bfd`); `regenerate-openapi.py` picks a free port and polls `/api/docs/openapi.json` instead of `/health/readyz` because readyz can sit at 503 when a non-critical dependency is down (`c0f742db`); SSE gateway gets a RabbitMQ env prefix (`98fb3696`).
- **Why:** See SHAs.
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S
- **Recommendation:** Diff at dedup — counterpart exists in the root template; the DA-side changes listed above are what to look for.

### RT04 — Counterpart exists: root `pyproject.toml`, `.kubecoder/` config, `.vscode/settings.json`, workspace file, root CLAUDE.md

- **Files:** `pyproject.toml`, `.kubecoder/config.yaml`, `.vscode/settings.json`, `DesignAssistant.code-workspace`, `CLAUDE.md`
- **What changed:** Counterparts exist in root template (`pyproject.toml.jinja`, `.kubecoder/{config,project}.yaml.jinja`, `.vscode/settings.json`, `{{ repo_name }}.code-workspace.jinja`, `CLAUDE.md.jinja`) — compare at dedup time. DA's `.kubecoder/config.yaml` has no `project.yaml`; its services/secrets/ports are DA-specific (opensearch, rabbitmq, minio, OPENAI key). Its `pyproject.toml` registers `code-health`, `run-suite`, `run-suite-remote` scripts and has deps portpicker, honcho, pathspec, psutil.
- **Why:** n/a
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S
- **Recommendation:** Diff at dedup — counterpart exists in the root template; the DA-side changes listed above are what to look for.

### RT05 — Pnpm build cache for CI and image builds

- **Files:** `scripts/build-cache-get.sh`, `scripts/build-cache-put.sh`, `tools/suite_runner/local.py` (`_build_cache_get/_put`, `--build-cache`), `frontend/Dockerfile` (cache restore step)
- **What changed:** Two POSIX shell scripts download/upload a tarball of the pnpm store to an in-cluster HTTP `build-cache` service (`BUILD_CACHE_URL`, default `http://build-cache.jenkins-prd.svc.cluster.local`), keyed `<prefix>-sha256(lockfile).tgz`. The suite runner restores before `pnpm install` and uploads on a miss; the frontend Dockerfile restores with `|| true` so a miss is non-fatal, then `pnpm install --frozen-lockfile`.
- **Why:** "Implemented build caching for frontend builds and build speedups" (`aa1907ec`); URL fixed in `f11ad226`.
- **Kind:** tooling
- **Applies to:** all apps with a frontend built in Jenkins/kaniko (and the Poetry equivalent could reuse the same scripts)
- **Port effort:** S — scripts are generic; the cache key `design-assistant` must become a template variable. Depends on the cluster build-cache service being reachable from Jenkins pods and kaniko.
- **Recommendation:** Port-adapted — generic scripts; parameterise key and also consider a Poetry/venv cache

### RT06 — Federated architecture producer pipeline

- **Files:** `Jenkinsfile.architecture`, `scripts/arch-validate.py`, `docs/architecture/architecture.yaml`, CLAUDE.md "Federated architecture model" section
- **What changed:** A tiny Jenkins pipeline runs `scripts/arch-validate.py docs/architecture/*.yaml` (stdlib-only; POSTs each YAML to `https://architecture.webathome.org/api/validate`, exit 0 valid/1 invalid/2 transport) on a `python` container and archives the YAML. The repo carries a hand-authored `architecture.yaml`, and CLAUDE.md nudges the operator to run the `update-architecture` agent on significant changes.
- **Why:** "Add federated architecture producer artifact" (`4e7776c4`, 2026-05-31) — an estate-wide convention, not DA-specific.
- **Kind:** tooling
- **Applies to:** all apps (estate convention)
- **Port effort:** S for the pipeline and script; the `architecture.yaml` is per-app content that must be authored (`/seed-architecture`)
- **Recommendation:** Optional — an estate convention rather than a template fix. If template apps should be architecture producers, the root template carries `Jenkinsfile.architecture` and `scripts/arch-validate.py`, and each app authors its own `architecture.yaml`.

### RT07 — Dependency update checker

- **Files:** `scripts/check_updates.py`
- **What changed:** Walks Poetry projects (`poetry show --outdated`) and pnpm projects (`pnpm outdated --format json`) across root/backend/frontend/portal, classifies each as major/minor/patch from installed vs latest (ignoring range specifiers), prints a report or `--json`.
- **Why:** "Add dependency update checker script" (`d49fb1a4`); used with the minor-version pin normalisation (`07799e8c`).
- **Kind:** tooling
- **Applies to:** all apps
- **Port effort:** S — component list is hard-coded (`backend`, `frontend`, `portal`); switch to discovery
- **Recommendation:** Optional — handy for keeping apps current, but nothing depends on it; make the component list discovered rather than hard-coded if taken.

### RT08 — Cross-cutting convention: status enums are exhaustive end-to-end

- **Files:** `docs/conventions.md` ("Status enum exhaustiveness"), `frontend/src/lib/utils/status-labels.ts` (and portal)
- **What changed:** Rule: backend Pydantic schemas type status fields as `Literal[...]` so OpenAPI emits `enum`; frontend mappers take the generated schema type, not `string`; every `switch` ends with a `const _exhaustive: never = status` default; all status-to-label mappers live in one `status-labels.ts`.
- **Why:** Compile-time failure when a new status appears; stated as binding convention (no SHA found; convention text).
- **Kind:** hardening (convention)
- **Applies to:** all apps
- **Port effort:** S — a doc + template lint-free pattern; the frontend/backend sections cover any code
- **Recommendation:** Port-adapted — no code needed. Destination: the template conventions skill, not template docs.

### RT09 — Cross-cutting convention: toast discipline

- **Files:** `docs/conventions.md` ("Toast discipline")
- **What changed:** No success toast when the outcome is visible (row appears, dialog closes, navigation); error toasts always, using the server's message; mutation errors handled only by the global `onError` in `query-client.ts` via `parseApiError` — no local `showException()` (duplicate toasts) except for status codes the global handler skips.
- **Why:** Convention text; consistent with duplicate-toast bugs (no SHA).
- **Kind:** hardening (convention)
- **Applies to:** all apps
- **Port effort:** S — doc
- **Recommendation:** Port-adapted — verify the template's `query-client.ts` already works that way at dedup. Destination: the template conventions skill, not template docs.

### RT10 — Cross-cutting convention: pagination and sorting contract

Merged into BE-C27 (backend helpers) and FE31 (frontend building blocks).

### RT11 — Cross-cutting convention: UUID path params and long-running-operation rule

- **Files:** `docs/conventions.md` ("API paths", "Long-running operations")
- **What changed:** (a) Resources are addressed in URLs by UUID, never by natural keys (slugs, names, emails). (b) Any operation with estimated p95 over 2 s runs as a background task: API returns 202 with `task_id`, progress/completion over SSE (`useSSETask`), with a queue-tier rule (`task.priority` for immediate-feedback, `task.normal` for ~30 s). The DA queue/worker mechanics are Celery-specific; the generic part is the 2 s rule and 202+SSE contract.
- **Why:** Convention; (b) motivated by the chat/document pipelines.
- **Kind:** feature/convention
- **Applies to:** (a) all apps; (b) apps with `use_sse`
- **Port effort:** S doc
- **Recommendation:** Port-adapted — state (a) and the generic half of (b). Destination: the template conventions skill, not template docs.

### RT12 — Cross-cutting convention: database text collation and keys

Merged into BE-C23 (the convention only makes sense with the collation code).

### RT13 — Cross-cutting convention: tests use real dependencies; testability is a first-class requirement

- **Files:** `docs/conventions.md` ("Testing", "Testability", "Worker in Playwright tests", "Resource-contention test flakes"), `frontend/docs/testing.md`, `frontend/docs/code-style.md`
- **What changed:** Playwright E2E uses real backend, DB, S3, RabbitMQ and IdP; no `page.route`/mock SSE (lint rule `testing/no-route-mocks`); tests wait on emitted instrumentation events (`ListLoading`, `Form`) rather than timeouts; testing-only endpoints live under `/api/testing/` behind a test-mode guard and are a blocking prerequisite for any UI feature that needs them; a UI feature without Playwright coverage is not done. Production-build-only paths (SharedWorker) are tested under `PLAYWRIGHT_PREVIEW_MODE=true` with a bundle built with `VITE_TEST_MODE=true`. Intermittent failures that pass with the configured retries (2) are accepted, not carded; consistently failing tests are real bugs.
- **Why:** Convention distilled from slices; preview-mode section documents a real gotcha (specs silently skip without the env vars).
- **Kind:** test infra (convention)
- **Applies to:** all apps
- **Port effort:** S doc; the preview-mode gotcha belongs next to the frontend testing doc
- **Recommendation:** Port-adapted — keep the generic rules and the preview-mode explanation; drop DA-specific Keycloak `test-da-` prefix. Destination: the template conventions skill, not template docs.

### RT14 — Cross-cutting code-style rules (backend/frontend `code-style.md`)

- **Files:** `backend/docs/code-style.md`, `frontend/docs/code-style.md`, `portal/docs/code-style.md`, `backend/docs/testing.md`, `frontend/docs/testing.md`
- **What changed:** Generic engineering rules beyond what linters enforce: never use `time.time()` for durations (use `time.perf_counter()`); fail fast, custom exceptions from `app.exceptions`, no defensive try/except that continues silently; "guidepost" comments; backend file-creation order (model, service, schema, API, migration); frontend: use generated API hooks and global error handling, instrumentation behind `isTestMode()`, backend-served downloads use `window.open(url)` rather than fetch+blob (cookie BFF auth, `Content-Disposition: attachment`); tests mirror `app/` layout, `test_<module>.py`, `Test<Service>` classes; "no tombstones / no backwards-compat shims" design philosophy.
- **Why:** Agent workflow docs; the rules, not the workflow, are what is generic.
- **Kind:** convention
- **Applies to:** all apps
- **Port effort:** S
- **Recommendation:** Port-adapted — fold the `perf_counter`, fail-fast and `window.open` download rules into the template's code-style docs (check which are already there at dedup). Destination: the template conventions skill, not template docs.

### RT15 — Health checks: registration-driven readiness and per-check reporting

Merged into BE-C13 (the code; the "a new integration needs a probe" rule is listed there).

### RT16 — Code health grader (`code-health`)

- **Files:** `tools/code_health/**` (`__main__.py`, `python_analyzer.py`, `ts_analyzer.py`, `cognitive_analyzer.py`, `config.py`, `suppressions.py`, `gitignore.py`, `formatting.py`), `tools/code_health/cognitive/**` (TypeScript cognitive-complexity analyzer run via `tsx`), `.codehealthignore`, root `pyproject.toml` script entry
- **What changed:** Ranks files by composite score: Python via `ast` + radon (file SLOC > 300, cyclomatic > 8, params > 5 with `__init__` allowed 10, class methods > 12, nesting > 4, inline imports), TS via its own analyzer (SLOC > 200, params, nesting) plus a Python/TS cognitive-complexity port; `# health: ignore <rules> — reason` in the first 10 lines suppresses; exclusions come from `.gitignore` + `.codehealthignore`; JSON output; pager. `.codehealthignore` excludes scripts/docs/support/tools/alembic and testing endpoints.
- **Why:** Created for the `quality-improver` / `refactor-audit` commands (`2d430873`, `7f2102ad`); later tuned for false positives (`ab9cf72b`, `459191c3` dropped function_length).
- **Kind:** tooling
- **Applies to:** all apps; mainly large codebases
- **Port effort:** M-L — hard-coded `backend/app`, `frontend`, `portal` paths; needs radon and a node workspace member for `cognitive/` (tsx)
- **Recommendation:** Optional — good for apps that grow large (DA was ~tens of k LOC); hobby apps have not needed it

### RT17 — Multi-frontend pnpm workspace at the monorepo root

- **Files:** `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, `.dockerignore`, `frontend/Dockerfile` and `portal/Dockerfile` (root as docker context), `Jenkinsfile` (kaniko context `.`), `packages/shared-ui/`
- **What changed:** Root `package.json` (private, `packageManager: pnpm@11.6.0`) and `pnpm-workspace.yaml` list `frontend`, `portal`, `packages/*`, `tools/code_health/cognitive` with an `allowBuilds` allow-list (esbuild, the pinned SSEGateway tarball). Lockfile moves to the root; image builds use the repo root as context and copy workspace manifests first for layer caching; `.dockerignore` keeps `.git`, `node_modules`, `.venv`, `test-results`, `.pnpm-store` out of the root-context upload.
- **Why:** "Update pipeline and scripts for pnpm workspace" (`17d0c079`), "Changed docker context to the project root" (`d592d5ba`).
- **Kind:** refactor
- **Applies to:** apps with a second frontend or shared packages (none today)
- **Port effort:** L — changes lockfile location, Dockerfiles, CI, copier paths; breaks current single-frontend layout
- **Recommendation:** Optional — only for a future app with a second frontend. Note DA convention: never extract template-owned frontend files into `shared-ui` (breaks copier sync).

### RT18 — Playwright memory profiler

- **Files:** `scripts/profile-playwright-memory.py`
- **What changed:** Samples every process on the box (PSS, with RSS for comparison) at an interval, classifies into component buckets (SSE gateway, Flask backend, Celery worker, Vite, Chromium, Postgres, RabbitMQ), prints peak/average per bucket and writes a CSV; can launch the suite or `--watch`.
- **Why:** Created to size CI pod memory when running 3 Playwright workers (`73a1268d`, with `75753725`, `ae6f3be8`).
- **Kind:** tooling
- **Applies to:** apps with a Playwright suite in CI
- **Port effort:** S-M — bucket classifier is DA-specific
- **Recommendation:** Optional — useful only when CI memory is tight

### RT19 — Unified coverage report

- **Files:** `scripts/coverage_report.py`
- **What changed:** Runs pytest with `--cov=app` and frontend/portal Playwright with Istanbul instrumentation and writes a single `coverage_report.md`; per-project flags `--backend-only` etc.
- **Why:** "Slice 075: Istanbul coverage instrumentation for frontend and portal" (`bb6d7927`)
- **Kind:** tooling
- **Applies to:** all apps (needs the frontend template's Istanbul wiring, see frontend section)
- **Port effort:** M — depends on instrumentation items in frontend
- **Recommendation:** Optional

### RT20 — Promote-by-retag deploy pipelines (UAT and PRD)

- **Files:** `Jenkinsfile.deploy-uat`, `Jenkinsfile.deploy-prd`
- **What changed:** Build-Main produces `tst-<n>` images; Deploy-UAT (param `source_build`, default via `utils.lastSuccessfulBuildNumber`) retags them `uat-<n>`/`uat-latest` with `crane --insecure tag` (no rebuild), then Deploy-PRD retags the chosen UAT build to `prd-<n>`/`prd-latest`; each ends with `cicd.helmDeploy()`. Promoted build number is shown in `currentBuild.description`. UAT also regenerates and commits derived docs (DA-specific).
- **Why:** Staging/UAT pipelines (`fbb85d26`, 2026-04-19); `utils.lastSuccessfulBuildNumber` helper (`1263a02e`).
- **Kind:** tooling
- **Applies to:** apps that want a staged release (hobby apps deploy `main` directly)
- **Port effort:** S-M — per-image stage list must be generated from the component list
- **Recommendation:** Optional — immutable-artefact promotion is a good pattern but adds job/Helm environment overhead

### RT21 — Remote suite runner (run tests in a cluster pod)

- **Files:** `tools/suite_runner/remote.py`, `scripts/setup-kube-access.sh`, `.llmbox/docker-compose.yml`
- **What changed:** `run-suite-remote` builds a Job spec (validation image chosen from the Playwright version in the lockfile, sidecars, labels, `ttlSecondsAfterFinished`), tars the working tree (excluding `.git`, `node_modules`, `.venv`, `test-results`, `.pnpm-store`), uploads and signals ready, execs `run-suite` in the pod, copies results back and deletes the Job on exit (`atexit`). `setup-kube-access.sh` creates a namespace-scoped service account kubeconfig for the agent container.
- **Why:** "Allow test runs to be run in the Kubernetes cluster" (`9a46a2e7`), because the llmbox dev container had no database/browser; many follow-up fixes Apr–May 2026.
- **Kind:** tooling
- **Applies to:** environments without local sidecars
- **Port effort:** L
- **Recommendation:** Optional — largely superseded by KubeCoder sidecars and tool containers; keep only if some app cannot run its suite in KubeCoder

### RT22 — Init.d-style build/preflight scripts

- **Files:** `scripts/build-all.py`, `scripts/_initd_log.py`, `scripts/preflight.py`
- **What changed:** Run install/build/test-collection steps silently and print one `[component] action ...... [  OK  ]` line each, dumping captured output only on failure; `preflight.py` bundles `build-all.py`, `pytest --co` and `cli prepare`.
- **Why:** To save agent tokens before slice runs (`96ae4f8f`, `28b83976`)
- **Kind:** tooling
- **Applies to:** DA workflow
- **Port effort:** S
- **Recommendation:** Skip — superseded by `kc project setup|build|test|lint`; the quiet-on-success idea is the only part worth remembering

### RT23 — Agent/dev-workflow tooling

- **Files:** `.claude/{settings.json,agents/*,commands/*}`, `.agents/skills/frontend-ux-designer`, `{backend,frontend,portal}/.claude/{agents,settings.local.json}`, `backend|frontend|portal/docs/{major,minor}_change_workflow.md`, `scripts/claude_session.py`, `scripts/codex_exec.py`, `scripts/send_message.py`, `.llmbox/docker-compose.yml`, `.vscode/tasks.json` ("Claude"/"Build All"/generation tasks)
- **What changed:** Slice workflow (write-slice, run-slice, triage, quality-improver, refactor-audit, arch-design, ux-design), plan/code writer and reviewer agents per component, session/codex wrappers, Home Assistant push notification, llmbox compose file, VS Code tasks.
- **Why:** DA's own pre-plugin orchestration.
- **Kind:** DA-specific
- **Applies to:** DA-only
- **Port effort:** n/a
- **Recommendation:** Skip — replaced by the dev-workflow plugin, KubeCoder, and the `notification` tool

### RT24 — Misc one-off DA scripts

- **Files:** `scripts/sync-env.sh`, `scripts/cleanup-rabbitmq.sh`, `scripts/docker-{build,run,stop}.sh`, `scripts/run-frontend.sh`
- **What changed:** Diff/apply `.env*` between sibling `DesignAssistant*` checkouts; delete RabbitMQ queues/exchanges prefixed `test-` through the management API; generic docker build/run/stop helpers driven by env vars (`DOCKERFILE`, `NAME`, `ARGS`) and a frontend wrapper.
- **Why:** Multi-checkout workflow (`41e09f90`); leaked test queues (`aa913c69`).
- **Kind:** tooling
- **Applies to:** DA-only
- **Port effort:** S
- **Recommendation:** Skip — tied to DA's multi-checkout layout and RabbitMQ test prefix; KubeCoder gives one checkout per environment

### RT25 — Product ADRs and architecture docs

- **Files:** `docs/architecture_decisions.md` (ADR-001..025), `docs/async_work_architecture.md`, `docs/chat_process_architecture.md`, `docs/apply_edits_redesign.md`, `docs/canon/`
- **What changed:** Most ADRs are product (three-model AI, RAG tiers, edit execution, unified inbox, session locking, document processing split, workspace events, Tika sidecar). Generic technical ADRs are folded into items above: RT15 (ADR-022), RT13 (ADR-015/016), RT12 (ADR-016). ADR-019 (SSE gateway RabbitMQ topic exchange, per-connection queue, bindings returned by connect callback) is infrastructure that lives in the SSEGateway repo and backend SSE items. ADR-020/021/025 (database-driven worker, then Celery worker/beat modes) are worker designs; if the template ever adds a worker, the transferable lessons in ADR-025 are: beat is a separate process with `replicas: 1` + `Recreate`, never `-B`; wait on Celery's `worker_shutdown`, not `worker_shutting_down`; set `worker_enable_remote_control = False` because kombu's pidbox queue (`durable=False, auto_delete=True`) loops forever on RabbitMQ 4.3+.
- **Why:** ADR-025 revision dated 2026-05-10 (slice 173).
- **Kind:** DA-specific (with one gotcha worth remembering)
- **Applies to:** DA-only; Celery gotcha applies to any future worker
- **Port effort:** n/a
- **Recommendation:** Skip — record the pidbox/RabbitMQ 4.3 gotcha if a Celery worker item (see backend section) is adopted

DA-specific, not candidates: `canon/` and `docs/canon/`, `scripts/canon-check.py`, `scripts/{generate-locales,generate-manuals,generate-uat,run-canon-docs,run-manuals,serve-canon,serve-uat}.sh`, `support/` (Dockerfile.canon-site, canon-site, uat-site, manuals image and nginx, docs-hosting nginx/auth.lua), canon CI stage and Deploy-UAT canon regeneration/commit, `packages/shared-ui` contents, product principles/AI-provider/content-editing/customer-data-exposure/auth sections of `docs/conventions.md`, Keycloak admin test-user conventions, `.canon-output/`, OpenSearch/document-conversion/MinIO sidecars in the Jenkinsfile validation Job, `frontend/docs/conventions/*` UI pattern docs (button, tooltip, data display; see frontend section).
