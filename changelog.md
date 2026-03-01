# Template Changelog

This changelog tracks all changes to the template that affect downstream apps. Each entry includes migration instructions for updating apps from the template.

See `CLAUDE.md` for instructions on how to use this changelog when updating apps.

---

<!-- Add new entries at the top, below this line -->

## 2026-03-01 — Frontend v0.13.3

### Frontend: Increase nginx upload size limit to 50 MB

**What changed:** Added `client_max_body_size 50M;` to the `http {}` block in `nginx.conf`. The previous default (1 MB) was causing 413 Entity Too Large errors on file uploads. Note: this limit is enforced by nginx independently of `proxy_buffering off` — both must be sufficient for large uploads.

Frontend template files changed:
- `template/nginx.conf.jinja` — added `client_max_body_size 50M;` in the `http {}` block

**Migration steps:**
1. Run `copier update` on the frontend — the only change is in `nginx.conf` (template-maintained).
2. No app-owned file changes required.

## 2026-02-28 — Backend v0.9.1

### Backend: Normalize BASEURL trailing slash

**What changed:** `Settings.load()` now strips any trailing slash from `BASEURL` before storing it. This prevents double-slash URLs (e.g. `https://example.com//api/auth/callback`) when `BASEURL` is configured with a trailing slash.

Backend template files changed:
- `template/app/config.py.jinja` — `baseurl=env.BASEURL.rstrip("/")`

**Migration steps:**
1. Run `copier update` on the backend — the only change is in `app/config.py` (template-maintained).
2. No app-owned file changes required.


## 2026-02-27 — Backend v0.9.0, Frontend v0.13.0

### Backend: Role hierarchy and 403 forbidden handling

**What changed:** Added a full role hierarchy system to `AuthService` with `read_role`, `write_role`, `admin_role`, and `additional_roles` parameters. Method-based access control now automatically infers required role from HTTP method (GET/HEAD → read_role, mutating methods → write_role). The `@allow_roles` decorator overrides method inference. `/api/auth/self` now returns 403 when a user is authenticated but has no recognized hierarchical role. Startup validation (`validate_allow_roles_at_startup`) catches typos in `@allow_roles` decorators at boot time. OpenAPI spec is annotated with per-endpoint security info (`x-required-role`, `x-auth-roles`).

Backend template files changed:
- `template/app/services/auth_service.py` — Role hierarchy: `read_role`, `write_role`, `admin_role`, `additional_roles` params; `expand_roles()`, `resolve_required_role()`, `configured_roles`, `hierarchy_roles`
- `template/app/utils/auth.py` — `@safe_query` decorator; updated `check_authorization()` with `auth_service` + `http_method` params; `validate_allow_roles_at_startup()`
- `template/app/utils/spectree_config.py` — `BearerAuth` JWT security scheme; `annotate_openapi_security()` that injects `x-required-role` into OpenAPI operations
- `template/app/__init__.py.jinja` — Added startup block (within `{% if use_oidc %}`): `validate_allow_roles_at_startup` + `annotate_openapi_security`
- `template/app/api/auth.py` — 403 `AuthorizationException` for users with no recognized hierarchical role; role expansion in test sessions and local user
- `template/app/api/oidc_hooks.py` — Role expansion in test sessions; pass `http_method` to `check_authorization` and `authenticate_request`

**App configuration required:** After running `copier update`, edit `app/services/container.py` and add role parameters to your `AuthService` provider:

```python
auth_service = providers.Singleton(
    AuthService,
    config=config,
    write_role="editor",          # required for POST/PUT/PATCH/DELETE
    # additional_roles=["pipeline"],  # for non-hierarchical roles (e.g. CI/CD)
)
```

**Migration steps:**
1. Run `copier update` on the backend — template-maintained files update automatically.
2. Edit `app/services/container.py`: add `write_role="editor"` (and `additional_roles` if needed) to the `AuthService` provider.
3. If you use `@allow_roles` decorators, review them — startup validation will now raise `ValueError` at boot for any role not in `configured_roles`.

### Frontend: 403 forbidden handling and role constants generation

**What changed:** Added 403 detection throughout the auth stack. `isForbiddenError()` predicate added to `api-error.ts`. `isForbidden` flag added to `useAuth`, `AuthContext`, and `AuthGate`. `AuthGate` now shows a "No Access" screen with a logout button when the backend returns 403 from `/api/auth/self`. `generate-api.js` now generates `roles.ts` and `role-map.json` from `x-required-role` annotations in the OpenAPI spec (used with `Gate` components to enforce role checks in the UI).

Frontend template files changed:
- `template/src/lib/api/api-error.ts` — Added `isForbiddenError()` predicate for 403 detection
- `template/src/hooks/use-auth.ts` — Added `isForbidden` flag; 403 excluded from `effectiveError`
- `template/src/contexts/auth-context.tsx` — Added `isForbidden` to `AuthContextValue`; emits `'forbidden'` test event phase
- `template/src/components/auth/auth-gate.tsx` — Added `AuthForbidden` component (lock icon, "No Access" message, logout button)
- `template/src/lib/test/test-events.ts` — Added `'forbidden'` to `UiStateTestEvent.phase` union
- `template/scripts/generate-api.js` — Added `generateRoles()` producing `roles.ts` (typed role constants) and `role-map.json` (hook→constant mapping) from OpenAPI `x-required-role` annotations

**Migration steps:**
1. Run `copier update` on the frontend — all changed files are template-maintained.
2. No app-owned file changes required.
3. After running `generate-api` with a backend that has the role system configured, `roles.ts` will contain typed constants for each non-reader role endpoint. Use these with `Gate` components to enforce access in the UI (app-specific work, no template changes needed).

## 2026-02-25 — Backend v0.8 / v0.8.1, Frontend v0.12 / v0.12.1

### Backend: Unified check script and vulture dead code detection

**What changed:** Added `scripts/check.py` — a unified code quality runner that executes ruff, mypy, vulture, and pytest in sequence. Added vulture as a dev dependency with `vulture_whitelist.py` for false positives (callback signatures, TYPE_CHECKING patterns). Tightened ruff config: added ERA (commented-out code) and RUF100 (unused noqa) rules, per-file-ignores for alembic and tools directories.

Backend template files changed:
- `template/scripts/check.py` — **New:** unified check runner
- `template/vulture_whitelist.py` — **New:** vulture false-positive whitelist (app-owned via `_skip_if_exists`)
- `template/pyproject.toml.jinja` — Added vulture dep, `check` script entry point, ERA/RUF100 rules, per-file-ignores, mypy override for vulture_whitelist
- `template/app/__init__.py.jinja` — Removed now-unnecessary `# noqa: F401` comments
- `template/app/database.py` — Fixed import sort order
- `template/app/config.py.jinja` — Used `_options` for unused param in non-database path (v0.8.1)
- `template/alembic/env.py` — Removed unnecessary `# noqa: E402`
- `template/tests/conftest.py` — Removed unnecessary F401 from noqa directive
- `copier.yml` — Added `vulture_whitelist.py` to `_skip_if_exists`

### Frontend: Knip dead code analysis

**What changed:** Added knip for detecting unused files, exports, types, and dependencies. Template-owned files are excluded via `knip-template-ignore.json` (template-maintained). Template-provided dependencies that are only used in ignored files are listed in `ignoreDependencies`.

Frontend template files changed:
- `template/knip.config.ts` — **New:** knip configuration loading template-ignore list
- `template/knip-template-ignore.json` — **New:** template-owned file exclusions (~60 paths)
- `template/package.json.jinja` — Added `knip` devDependency, `check:knip` script, updated `check` to include knip

**Migration steps:**
1. Run `copier update` for both backend and frontend — template-maintained files update automatically.
2. Backend: Run `poetry lock && poetry install` to install vulture. Run `ruff check --fix .` to auto-fix RUF100/ERA findings in app-owned files. Review and extend `vulture_whitelist.py` for any app-specific false positives.
3. Frontend: Run `pnpm install` to install knip. Run `pnpm run check:knip` and fix any findings in app-owned code (remove unused exports, delete unused files, unexport types only used locally).
4. Use `poetry run check` (backend) or `pnpm run check` (frontend) as the single command for all code quality checks.

## 2026-02-21 — Frontend v0.9

### SSE: switch from named events to {type, payload} envelope format

**What changed:** The SSE Gateway now sends all events as unnamed data-only messages with a `{type, payload}` envelope instead of named SSE events. This eliminates a race condition where events were silently dropped before per-event-type `addEventListener` calls could be attached (especially on fast backend responses).

Frontend template files changed:
- `src/workers/sse-worker.ts` — Replaced per-event subscriptions with single `onmessage` handler; removed `subscribe` command from worker protocol; added version payload caching for late-joining tabs
- `src/contexts/sse-context-provider.tsx` — Replaced per-event `addEventListener`/subscription logic with single `onmessage` envelope unwrapping; removed `attachedEventsRef`, `workerSubscribedEventsRef`, `ensureDirectEventSourceListener`, `ensureWorkerSubscription`
- `tests/infrastructure/sse/sse-connectivity.spec.ts` — Updated task event tests to use envelope format; added 2 SharedWorker tests
- `tests/infrastructure/deployment/deployment-banner.spec.ts` — Removed `correlation_id` matching (not in version payloads)
- `tests/infrastructure/sse/task-events.spec.ts` — **New:** generic task event infrastructure tests (receive, payload structure, sequencing)

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained and will be updated automatically.
2. Run `pnpm update ssegateway` to pick up the new SSE Gateway `#stable` commit.
3. If your app has custom code that uses `es.addEventListener('eventName', ...)` to listen for SSE events, switch to `es.onmessage` and unwrap the `{type, payload}` envelope.
4. If your app sends `subscribe` commands to the SharedWorker, remove them — the worker no longer needs per-event subscriptions.

## 2026-02-20 (v0.7.2)

### Stderr logging in testing mode for Playwright visibility

**What changed:** All apps now get stderr logging enabled when `FLASK_ENV=testing`, so request logs and exception tracebacks appear in the process output captured by Playwright.

Files changed:
- `template/app/__init__.py.jinja` — Adds a `StreamHandler(sys.stderr)` block before the log capture handler. The `root_logger.setLevel(logging.INFO)` call moves into this block so it's set regardless of SSE feature flag. The `import logging` is no longer conditional on `use_sse`.

### dev-sse-gateway.sh uses backend_port variable

**What changed:** The dev SSE gateway script now uses the `backend_port` Copier variable instead of hardcoded port 5000. Also excluded from non-SSE apps via `_exclude`.

Files changed:
- `template/scripts/dev-sse-gateway.sh` → `template/scripts/dev-sse-gateway.sh.jinja` — Uses `{{ backend_port }}`
- `copier.yml` — Added `scripts/dev-sse-gateway.sh` to SSE exclude list

### Import ordering fix in testing_sse.py

**What changed:** Fixed ruff I001 import sorting violation in `testing_sse.py`.

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes needed.

## 2026-02-19 (v0.7.0)

### Subject-based task event filtering

**What changed:** Task events (started, progress, completed, failed) are no longer broadcast to all SSE connections. They are now filtered by the subject of the user who started the task. Version events remain broadcast to everyone.

Files changed:
- `template/app/services/sse_connection_manager.py` — `send_event()` accepts optional `target_subject` parameter; in broadcast mode, restricts delivery to connections with matching subject or the `"local-user"` sentinel
- `template/app/services/task_service.py` — `start_task()` accepts `caller_subject`; threads it through `_execute_task()`, `TaskProgressHandle`, and `_broadcast_task_event()` to reach `send_event(target_subject=...)`
- `template/app/schemas/task_schema.py` — `TaskInfo` gains `subject: str | None` field
- `template/app/api/testing_sse.py` — `start_test_task()` derives `caller_subject` from `get_auth_context()` and passes it to `start_task()`
- `template/regen.sh` — Added `--vcs-ref HEAD` so copier picks up uncommitted template changes

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained and will be updated automatically.
2. If your app calls `task_service.start_task(task, ...)` directly, add `caller_subject=<subject>` to filter task events to that user's SSE connections. Pass `None` to broadcast to all (backward-compatible default).
3. If your app has custom identity verification on SSE task subscriptions (e.g., IoTSupport's `_verify_identity()`), the template now handles subject filtering at the event delivery layer. The app-level check may still be needed for subscription authorization but is no longer the only line of defense.

## 2026-02-16 (v0.6.3)

### Background service startup registry and register_root_blueprints hook

**What changed:**

1. **`container.py` scaffold** — Adopted the `register_for_background_startup` pattern. Infrastructure service startup is now declared co-located with provider definitions, and `start_background_services(container)` runs them all. App-specific services register their starters the same way.

2. **`__init__.py`** — Inline startup calls (`temp_file_manager().start_cleanup_thread()`, `task_service().startup()`, `s3_service().startup()`, `frontend_version_service()`) replaced with a single call to `start_background_services(container)`.

3. **`startup.py` scaffold** — New hook: `register_root_blueprints(app)` for registering blueprints directly on the Flask app (not under `/api`). Called after template blueprints (health, metrics) and before feature-gated blueprints (SSE, OIDC, S3).

**Migration steps:**
1. Run `copier update` — `__init__.py` is template-maintained and will be updated automatically.
2. Add to your `app/startup.py` (app-owned):
   ```python
   def register_root_blueprints(app: Flask) -> None:
       """Register app-specific blueprints directly on the app."""
       pass
   ```
3. Add the startup registry to your `app/services/container.py` (app-owned):
   ```python
   from collections.abc import Callable
   from typing import Any

   _background_starters: list[Callable[[Any], None]] = []

   def register_for_background_startup(fn: Callable[[Any], None]) -> None:
       _background_starters.append(fn)

   # After each provider that needs startup:
   register_for_background_startup(lambda c: c.temp_file_manager().start_cleanup_thread())
   register_for_background_startup(lambda c: c.task_service().startup())
   # etc.

   def start_background_services(container: Any) -> None:
       for starter in _background_starters:
           starter(container)
   ```
4. Move any root-level blueprint registrations from `__init__.py` overrides into `register_root_blueprints()`.

## 2026-02-16 (v0.6.2)

### SSE OIDC identity auto-binding in connect callback

**What changed:** `app/api/sse.py` is now a Jinja template (`sse.py.jinja`) that conditionally includes OIDC identity binding when `use_oidc=true`.

When both `use_sse` and `use_oidc` are enabled:
- `_extract_token_from_headers(headers, cookie_name)` — extracts Bearer token or cookie from forwarded SSE Gateway headers
- `_bind_identity(request_id, headers, sse_connection_manager, auth_service, settings)` — validates OIDC token and binds identity to the SSE connection (falls back to sentinel subject when OIDC is disabled at runtime)
- `handle_callback()` injects `AuthService` and calls `_bind_identity()` after `on_connect()`

When `use_oidc=false`: no OIDC imports, no identity binding code — identical to the previous `sse.py`.

**Migration steps:**
1. Run `copier update` — `sse.py` is template-maintained and will be updated automatically.
2. No breaking changes. Identity binding is additive and only active when OIDC is enabled.
3. If your app has custom code in `sse.py`, move it to a separate module — `sse.py` will be overwritten by copier.

## 2026-02-16 (v0.6.1)

### SSE connection manager: identity binding and disconnect observers

**What changed:** `sse_connection_manager.py` now supports:
- `bind_identity(request_id, subject)` — associate an OIDC subject with an SSE connection
- `get_connection_info(request_id)` — retrieve connection info including bound identity
- `register_on_disconnect(callback)` — observe disconnect events (symmetric with existing `register_on_connect`)
- `ConnectionInfo` dataclass — returned by `get_connection_info()`
- `SSE_IDENTITY_BINDING_TOTAL` Prometheus counter

Identity map is cleaned up automatically on disconnect. Disconnect observers are notified outside the lock, matching the existing on_connect pattern.

**Migration steps:**
1. Run `copier update` — `sse_connection_manager.py` is template-maintained.
2. No breaking changes. New features are additive.

## 2026-02-16 (v0.6.0)

### Background service lifecycle improvements

**What changed:**

1. **`run.py`** — Werkzeug reloader parent detection. In debug mode, background services are now skipped in the reloader parent process to avoid duplicate threads, MQTT connections, etc.

2. **`task_service.py`** — Cleanup thread start is deferred to a new `startup()` method instead of running in `__init__()`. This improves test isolation (no daemon threads spawned during container construction).

3. **`s3_service.py`** — Added `startup()` (wraps `ensure_bucket_exists()` with warning-only error handling), `list_objects(prefix)` (paginated listing), and `delete_prefix(prefix)` (best-effort bulk delete). Also moved `mypy_boto3_s3` imports under `TYPE_CHECKING` and added a module logger.

4. **`__init__.py`** — Background service startup block now calls `task_service.startup()` and `s3_service.startup()` instead of inline code.

5. **`conftest_infrastructure.py`** — Test fixtures (`app`, `oidc_app`) now pass `skip_background_services=True` to `create_app()`. Background cleanup threads and S3 bucket checks are no longer started during tests.

6. **`testing_service.py`** — Added `clear_all_sessions()` method for test isolation.

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained.
2. If your app starts background services in `__init__.py` (e.g., `s3_service.ensure_bucket_exists()`), remove that code — the template now handles it via `s3_service.startup()`.
3. If your tests relied on background services starting during `create_app()`, they now need explicit startup calls or the services must register for lifecycle STARTUP events.

## 2026-02-16

### Add SpectTree validation and send_task_event endpoint to testing SSE endpoints

**What changed:** The testing SSE endpoints (`app/api/testing_sse.py`) now use SpectTree schema validation, matching the pattern used by `testing_content.py` and other template endpoints. A new endpoint `POST /api/testing/sse/task-event` allows integration tests to inject fake task events directly into SSE connections without running actual background tasks.

New files:
- `template/app/schemas/testing_sse.py` — Pydantic request/response schemas for all testing SSE endpoints

Files changed:
- `template/app/api/testing_sse.py` — Added `@api.validate()` decorators, added `send_task_event` endpoint, switched to lazy `reject_if_not_testing` import pattern; declared `HTTP_400=TestErrorResponseSchema` on `send_task_event` so SpectTree doesn't reject error responses
- `copier.yml` — Added `app/schemas/testing_sse.py` to SSE feature-flag exclusion list

**Migration steps:**
1. Run `copier update` — both files are template-maintained and will be created/updated automatically
2. If your app has a custom `app/schemas/testing_sse.py`, it will be overwritten by the template version. Move any app-specific schemas to a different file name
3. If your app's integration tests reference `resp.json()["task_id"]` from the start-task endpoint, no change needed — the response format uses snake_case field names
4. If your app's tests assert camelCase keys in testing SSE responses (e.g., `requestId`, `taskId`, `eventType`), update to snake_case (`request_id`, `task_id`, `event_type`)

## 2026-02-14

### Fix auth/self endpoint not extracting token from request

**What changed:** The `/api/auth/self` endpoint is decorated with `@public` (to handle its own auth logic), but this meant the `before_request` OIDC hook skipped it entirely. When OIDC is enabled and a user has a valid token cookie, the endpoint would fail with "No valid token provided" because `get_auth_context()` returned `None`.

Fixed by injecting `AuthService` and falling back to manually extracting and validating the token from the request when `auth_context` is not set by the hook.

Files changed:
- `template/app/api/auth.py` — Added `auth_service` DI parameter; added fallback token extraction via `extract_token_from_request()`

**Migration steps:**
1. Run `copier update` — this file is template-maintained and will be updated automatically

### Upgrade ruff to 0.11+ and modernize Python syntax

**What changed:** Upgraded ruff from `^0.1.0` to `^0.11.0` to support `py313` target version. Fixed all new lint findings:

- Moved ruff config to `[tool.ruff.lint]` section (old top-level format deprecated)
- `str, Enum` → `StrEnum` (UP042) in `task_schema.py`, `lifecycle_coordinator.py`
- `Generator[X, None, None]` → `Generator[X]` (UP043) in `conftest_infrastructure.py`, `sse_utils.py`
- `TypeVar` → PEP 695 type parameters (UP047) in `request_parsing.py`
- Quoted type annotations → unquoted (UP037) in `alembic/env.py`
- Import sorting fixes (I001) in `database.py`

Files changed:
- `template/pyproject.toml.jinja` — ruff `^0.11.0`, `[tool.ruff.lint]` config format
- `template/app/schemas/task_schema.py` — `StrEnum`
- `template/app/utils/lifecycle_coordinator.py` — `StrEnum`
- `template/app/utils/request_parsing.py` — PEP 695 type params
- `template/app/utils/sse_utils.py` — simplified `Generator` type
- `template/app/database.py` — import order
- `template/alembic/env.py` — unquoted annotation
- `template/tests/conftest_infrastructure.py.jinja` — simplified `Generator` types

**Migration steps:**
1. Run `copier update` — template-maintained files will be updated automatically
2. After update, run `ruff check --fix .` to auto-fix any remaining issues in app-owned files
3. Manually fix any `str, Enum` → `StrEnum` classes in app-owned code

## 2026-02-13

### Add service layer files (infrastructure services and DI container scaffold)

**What changed:** Added the service layer files extracted from Electronics Inventory. These provide the infrastructure services that all generated apps share, plus a scaffold DI container for app-specific customization.

Template-maintained service files (overwritten on `copier update`):
- `template/app/services/__init__.py` - Empty services package
- `template/app/services/health_service.py` - Health check callback registry (healthz/readyz/drain)
- `template/app/services/metrics_service.py` - Background polling service for Prometheus metrics
- `template/app/services/task_service.py` - Background task management with SSE progress updates
- `template/app/services/base_task.py` - Abstract base classes for background tasks (BaseTask, BaseSessionTask)
- `template/app/services/sse_connection_manager.py` - SSE Gateway token mapping and event delivery (always included)
- `template/app/services/auth_service.py` - JWT validation with JWKS discovery (use_oidc)
- `template/app/services/oidc_client_service.py` - OIDC authorization code flow with PKCE (use_oidc)
- `template/app/services/s3_service.py` - S3-compatible storage operations (use_s3)
- `template/app/services/cas_image_service.py` - CAS thumbnail generation and image processing (use_s3)
- `template/app/services/frontend_version_service.py` - Frontend version SSE notifications (use_sse)
- `template/app/services/diagnostics_service.py` - Request/query performance profiling (use_database)

App-maintained scaffold (skip_if_exists, generated once):
- `template/app/services/container.py.jinja` - DI container with infrastructure providers; app adds domain providers

Also changed:
- `template/app/utils/temp_file_manager.py` - Reordered constructor params to put `lifecycle_coordinator` first; added defaults for `base_path` ("/tmp/app-temp") and `cleanup_age_hours` (24.0) so the scaffold container works without app-specific config

**Migration steps:**
1. Copy all new service files from template into your app's `app/services/` directory
2. Review your existing `app/services/container.py` - the scaffold is a starting point; your container should already have these infrastructure providers plus your domain-specific ones
3. If your `TempFileManager` usage passes `base_path` and `cleanup_age_hours` as positional args, update to use keyword arguments since the parameter order changed (lifecycle_coordinator is now first)
4. The `sse_connection_manager.py` and `base_task.py` are always included regardless of feature flags (TaskService depends on them)

## 2026-02-13

### Add schemas, build/deploy, alembic, scripts, and test infrastructure files

**What changed:** Added the remaining template files extracted from Electronics Inventory:

Schema files:
- `template/app/schemas/__init__.py` - Schema package init
- `template/app/schemas/health_schema.py` - Health check response schema (Pydantic)
- `template/app/schemas/task_schema.py` - Task status, events, progress schemas (Pydantic)
- `template/app/schemas/sse_gateway_schema.py` - SSE Gateway callback/send schemas (Pydantic)
- `template/app/schemas/upload_document.py` - Document upload schemas (use_s3, generic - no EI model dependency)

Build/deploy files:
- `template/run.py` - Development/production server entry point (Waitress + Flask debug)
- `template/.gitignore` - Standard Python/Flask gitignore
- `template/Dockerfile.jinja` - Multi-stage Docker build with feature-flagged system deps
- `template/Jenkinsfile.jinja` - Jenkins CI/CD pipeline with template variables
- `template/pyproject.toml.jinja` - Poetry project config with feature-flagged dependencies (skip_if_exists)
- `template/.env.example.jinja` - Environment variable documentation grouped by feature flag (skip_if_exists)

Alembic files (use_database only):
- `template/alembic.ini.jinja` - Alembic configuration with templated DB URL
- `template/alembic/env.py` - Alembic environment (offline/online migrations, test connection reuse)
- `template/alembic/script.py.mako` - Migration script template
- `template/alembic/versions/.gitkeep` - Empty versions directory

Scripts:
- `template/scripts/args.sh.jinja` - Shared variables (project name, ports) with template variables
- `template/scripts/build.sh` - Docker build script
- `template/scripts/dev-server.sh` - Development server restart loop
- `template/scripts/dev-sse-gateway.sh` - SSE Gateway development restart loop
- `template/scripts/initialize-sqlite-database.sh` - SQLite database initialization
- `template/scripts/push.sh` - Docker push to registry
- `template/scripts/run.sh` - Docker run script
- `template/scripts/stop.sh` - Docker stop script
- `template/scripts/testing-server.sh` - Testing server (generic, no EI references)

Test infrastructure:
- `template/tests/__init__.py` - Test package init
- `template/tests/conftest_infrastructure.py.jinja` - Infrastructure fixtures with feature-flagged sections (database clone pattern, OIDC mocks, SSE server, S3 checks)
- `template/tests/conftest.py` - Scaffold that imports infrastructure fixtures (skip_if_exists)

EI-specific code removed:
- `upload_document.py`: Replaced `AttachmentType` model import with generic `str | None`
- `pyproject.toml`: Removed openai, anthropic, celery, beautifulsoup4, validators, reportlab, types-beautifulsoup4 dependencies
- `conftest_infrastructure.py`: Removed AI/Mouser/document settings from `_build_test_app_settings`
- `testing-server.sh`: Replaced "Electronics Inventory" with generic "backend"
- `Dockerfile`: Changed from PyPy to CPython 3.12, removed jiter/openai patches

**Migration steps:**
1. These are new files - no migration needed for existing downstream apps
2. For new apps generated from the template, all files are created automatically
3. Existing apps should:
   - Compare their `pyproject.toml` against the template and ensure infrastructure dependencies match
   - Adopt `conftest_infrastructure.py` pattern: import infrastructure fixtures in `conftest.py`
   - Move from custom Dockerfile to the template Dockerfile pattern if not already using it
   - Replace EI-specific `upload_document.py` imports with generic types if using S3

## 2026-02-13

### Add core application files (app factory, config, CLI, exceptions, database)

**What changed:** Added the core application layer files extracted from Electronics Inventory:

- `template/app/__init__.py.jinja` - Flask application factory with feature-flagged sections for database, OIDC, S3, and SSE
- `template/app/app.py` - Custom Flask App class with typed container attribute
- `template/app/config.py.jinja` - Two-layer configuration (Environment + Settings) with feature-flagged field groups
- `template/app/cli.py.jinja` - CLI commands (upgrade-db, load-test-data) with feature-flagged database sections
- `template/app/consts.py.jinja` - Project constants scaffold (skip_if_exists)
- `template/app/app_config.py` - App-specific settings scaffold (skip_if_exists)
- `template/app/startup.py` - Hook functions scaffold (skip_if_exists)
- `template/app/exceptions.py` - Base exception classes scaffold (skip_if_exists)
- `template/app/extensions.py` - Flask-SQLAlchemy initialization (use_database only)
- `template/app/database.py` - Database operations: migrations, health checks, upgrade (use_database only)
- `template/app/models/__init__.py` - Empty models scaffold (skip_if_exists, use_database only)

EI-specific code removed: dashboard_metrics, sync_master_data_from_setup, SetupService import, InsufficientQuantityException, CapacityExceededException, DependencyException.

**Migration steps:**
1. These are new files - no migration needed for existing downstream apps
2. For new apps generated from the template, all files are created automatically
3. Existing apps should compare their `app/__init__.py`, `app/config.py`, `app/cli.py` against these templates and adopt the hook-based pattern if not already using it
