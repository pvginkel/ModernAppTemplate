# Template Changelog

This changelog tracks all changes to the template that affect downstream apps. Each entry includes migration instructions for updating apps from the template.

See `CLAUDE.md` for instructions on how to use this changelog when updating apps.

---

<!-- Add new entries at the top, below this line -->

## 2026-10-17 — Root v0.2.0, Backend v0.14.0, Frontend v0.21.0

The DesignAssistant port: the rulings in `docs/da_port_decisions.md`, delivered by `docs/da_port_plan.md` (phases 1–10), plus the move of all three templates to uv. The three releases ship together, and an app takes them in one sync. The first section is the sync's checklist, in the order a sync runs. The sections after it say what changed, and each points back at its steps. The plan's phase log has the long per-app detail (file and line numbers, survey results). Every app is more than one release behind: IoT, EI, DHCPApp and ZigbeeControl are on root v0.1.3, backend v0.13.2 and frontend v0.20.3, FieldnotesApp on v0.1.2, v0.13.2 and v0.20.2, and PilotApp on v0.1.6, v0.13.3 and v0.20.4. So a sync reads every entry after its `_commit`, not this one alone.

### Syncing an app to this release

**What changed:** everything in the sections below. `copier update` brings the template-owned files; steps 5–19 are the app-owned edits. In `backend/` and `frontend/` the update three-way merges the app-owned (`_skip_if_exists`) files too, but only those the app has edited, so some of those edits arrive as hunks or conflicts. An app-owned file the app never edited keeps its old render silently, with no hunk and no conflict: there the step's edit is by hand (DHCPApp's `button.ts` and `vulture_whitelist.py`). At the root the update leaves app-owned files alone. (EI = ElectronicsInventory, IoT = IoTSupport. The database apps are EI, IoT and PilotApp; the S3 apps EI and IoT; the Poetry apps EI, IoT, DHCPApp and ZigbeeControl.)

**Migration steps:**

1. **Start clean.** Every `copier update` needs a clean tree, so commit after each one. Run copier from the component's directory (`/work/<App>`, then `backend/`, then `frontend/`):
   ```bash
   cexec modern-app uv run --project /work/ModernAppTemplate/backend --locked copier update --trust --defaults
   ```
2. **Root `copier update`.** Commit.
   - `Jenkinsfile` conflicts across the whole file, because the old render was the scripted file and every app runs a declarative `modernApp.test` file. Resolve it to the app's file plus the template's new lines: `STAGE: 'tst'` and `BUILD_CACHE: 'true'` in `env:`, with their comments. Per app:
     - The Poetry apps: `install: 'uv sync --locked --no-dev'` and `run: 'uv run --no-sync'`.
     - IoT: add the `postgres` service. Keep the `withVault` wrapper, the OpenSearch service, the Keycloak env and `secrets:`.
     - EI: add the `postgres` service. Keep the docs-image stage and the three-image header. The S3 block already matches.
     - DHCPApp: keep `Job: Dnsmasq/DHCPApp` and its own header wrapping.
     - ZigbeeControl: keep its "No data sidecars" comment.
     - FieldnotesApp: only the `env:` lines change.
     - PilotApp: add the `postgres` service and the comments above `modernApp.test`.
   - `Jenkinsfile.architecture` is app-owned (`_skip_if_exists`), so copier leaves every app's file alone.
   - The root `CLAUDE.md` is app-owned too, so it keeps its old text. Bring over the template's new notes by hand: the two uv projects and their committed locks, `scripts/dev.py stop`, the backend test that fails while the OpenAPI cache is stale, `scripts/check_updates.py`, `Jenkinsfile.architecture`, and the "Architecture model" section (every app already has a model, so leave out the seeding steps).
3. **Backend `copier update`.** Commit. The update deletes `scripts/dev-server.sh` and `scripts/initialize-sqlite-database.sh`.
   - App-owned files get merged as well. IoT, the release's trial run, conflicts in `Dockerfile`, `app/app_config.py`, `app/services/container.py` and `pyproject.toml`, and takes clean hunks into `tests/conftest.py` and `vulture_whitelist.py`. Resolve an app-owned file to the app's own content, keeping only what steps 5–15 name for it (they say what the file must end with, whatever a hunk brought). Check `git diff` on the app-owned files before committing, since a clean hunk raises nothing. Two hunks the apps met are wrong to take: `container.py` gains a second `testing_service` provider or moves the existing one (keep the app's), and `app_config.py` gains `dump_for_logging` without the `Sensitive` marks step 8 asks for. Delete the `.env.example.rej` files copier leaves (gitignored, rewritten on every update).
   - FieldnotesApp and PilotApp: where their own uv edits to template-owned files differ from the template, take the template's. Then drop uv, `scripts/dev-server.sh` and any other edit the template now covers from their `CLAUDE.md`'s list of standing template edits.
   - IoT: its own `scripts/wait-for-services.py` (OpenSearch wait, S3 bucket creation) meets the template's, which is template-owned now. Settle where the OpenSearch wait and the bucket creation go before resolving.
   - FieldnotesApp: `app/api/oidc_hooks.py` and `app/services/sse_connection_manager.py` conflict. Drop the FN-38 binding (`bind_unbound_identity`, the `X-SSE-Request-Id` binding, `tests/test_sse_identity.py`), and with it its `authenticate()` copy of the old hook body. An old body kept by mistake fails at its first request, because `throw_on_error` is now required. Its own `tests/test_smoke.py` meets the template's new one: keep the app's. App-owned FN-38 leftovers go too: the header in `tests/fieldnotes/test_inbox.py` (bind each test connection on connect instead; the unbound-page case can no longer happen) and the binding's description in `docs/rest-api.md` and `docs/design.md`.
   - PilotApp: take the template's side of `3f84260` in `app/api/sse.py`, `app/services/testing_service.py`, `app/api/testing_auth.py` and `app/schemas/testing_auth.py`. The SSE force-callback-error hook now lives in `api/testing_sse.py`, at the same URL. The two `testing_auth.py` files merge without a conflict and keep Pilot's hook, and `sse.py` keeps two lines outside its conflict hunks: compare all four with a fresh render. `alembic/env.py` and `app/cli.py` conflict too; take the template's side.
4. **Frontend `copier update`.** Commit.
   - App-owned files get merged here too (IoT: `package.json` and `src/routes/index.tsx` conflict). Resolve them as in step 3, and keep the app's own `src/routes/index.tsx`, not the template's placeholder.
   - EI: its own role-gating rules in template-owned `eslint.config.js` meet the template's new block at the same spot; keep both.
   - IoT: drop `xfwd: true` from the `vite.config.ts` proxies. On `/api` it puts `https,http` in `X-Forwarded-Proto` and breaks the dev login's redirect URI. Keep the esptool alias and `optimizeDeps`.
   - FieldnotesApp: drop its FN-38 edits to `sse-worker.ts`, `sse-context-provider.tsx` and `src/lib/utils/random.ts` (the merge keeps the last silently), and delete `src/lib/api/sse-connection.ts` (only the `X-SSE-Request-Id` header) and `tests/shell/sse-connection.spec.ts`; drop the header checks in `tests/inbox/inbox.spec.ts`.
   - PilotApp: take the template's side of `8b8cf41` in `sse-worker.ts`, `sse-context-provider.tsx` and `playwright-binding.d.ts`.
   - DHCPApp: delete the re-created `public/favicon.png` again.
5. **Packaging to uv** (the Poetry apps). Convert the root and `backend/` `pyproject.toml` to PEP 621 with uv, following `docs/da_port_worklist.md` §3, "App-owned packaging". Lock so that uv keeps Poetry's versions: add every `poetry.lock` package as `name==version` to `[tool.uv] constraint-dependencies`, run `uv lock`, remove the constraints and run `uv lock` again (a plain `uv lock` resolves to the newest versions). Check the locked versions against `poetry.lock` package by package, then delete `poetry.lock`. The root's own `scripts/regenerate-openapi.py` is app-owned, so copier leaves its `poetry run dev`: make it `uv run dev`, or step 15 fails. If the app's copy is a trimmed one without the template's `--frontend` flag (EI's was), replace it with the template's version: steps 12 and 15 call `--frontend`. In `.kubecoder/project.yaml`, `poetry install --no-interaction` becomes `uv sync --locked` and `poetry run X` becomes `uv run X`. Reword every Poetry mention outside the frozen `docs/features/`: comments (EI's `.kubecoder/config.yaml`; IoT's and ZigbeeControl's `project.yaml`), both `CLAUDE.md` files, `backend/README.md`, `backend/.dockerignore` and `docs/slice-test-plan.md` where the app has them.
6. **Dependency pins**, in app-owned `backend/pyproject.toml`:
   - `spectree>=2.0.0,<3`, `flask-cors>=6.0.0,<7`, `pillow>=12.0.0,<13` (S3 apps);
   - in the dev group: `ruff>=0.15.0,<0.16`, `pytest>=9.0.0,<10`, `pytest-cov>=7.0.0,<8`, `types-flask-cors>=6.0.0,<7`, and the new `watchdog[watchmedo]>=6.0.0,<7` (the dev stack's backend runs under `scripts/dev-watch.sh` and doesn't start without it); drop `types-pillow`;
   - mypy 1.20 or later: the template's stage code fails type-checking on 1.19 (`app/config.py`). The `mypy>=1.8.0,<2` range allows it, but `uv lock` keeps an older locked version, so run `uv lock --upgrade-package mypy`;
   - under `[tool.ruff]`, `exclude = ["vulture_whitelist.py"]` becomes `extend-exclude`.

   Pin `ruff==0.15.22` in the root `pyproject.toml`. Run `uv lock`, then `uv run ruff check --fix`: ruff 0.15 re-sorts some imports, and reports an app enum declared `str, Enum` (UP042), which `--fix` leaves: make it a `StrEnum`, as the template's are (ZigbeeControl's `StatusState`). An app that runs `ruff format --check` finds that 0.15 reformats its multi-line lambdas and template-owned files (FieldnotesApp: `testing_guard.py`, `health_service.py`, `http_metrics.py`, `log_formatter.py`; the database apps also `scripts/init-dev-database.py`): format its own, and add the template's to its format `exclude`, since the template doesn't run `ruff format`. App code that reassigns `img = img.convert(...)` needs the Pillow typing fix the template's own code got.
7. **`backend/app/services/container.py`:** move `lifecycle_coordinator` and `health_service` above `s3_service`. Pass `health_service=health_service` to `S3Service` (S3 apps) and to `SSEConnectionManager` (all six). Without it, readyz silently lacks `s3` or `sse_gateway`. `test-app-domain/app/services/container.py` in the backend repo shows the result. Roles need no edit: every app has an `editor` client role (EI also `reader`), and the operator ruled no lockout to handle. `role_hierarchy` is opt-in, and no app needs it.
8. **`backend/app/app_config.py`** (optional): to have the boot log dump `AppSettings` too, add `def dump_for_logging(self): return dump_config_for_logging(self)`, and mark every secret `Annotated[str, Sensitive]` (EI: `OPENAI_API_KEY`, `MOUSER_SEARCH_API_KEY`). Without the method nothing is dumped, so nothing leaks.
9. **App code** (the phase log has the lines):
   - Every direct `send_event` call takes a `Target` first: IoT `device_log_stream_service.py` → `Target.connection(request_id)` and `rotation_nudge_service.py` → `BROADCAST_TARGET`; DHCPApp `api/internal.py` → `BROADCAST_TARGET`; ZigbeeControl `tab_status_service.py` → `BROADCAST_TARGET` and `Target.connection(request_id)`. A narrower target than `BROADCAST_TARGET` is the app's call; the convention is broadcast for infrastructure events only.
   - EI: `api/ai_parts.py` passes `caller_subject` to its two `start_task` calls, or their progress reaches nobody under OIDC. `part_service.py` and `inventory_service.py` page by `created_at` alone: move them onto `apply_sorting()`, or add the `id` tiebreaker. `services/metrics/dashboard_metrics.py` moves to `app.database.scoped_session`. Its two progress components (`ai-part-progress-step.tsx`, `ai-part-cleanup-progress-step.tsx`) stop multiplying `progress.percentage` by 100.
   - IoT: delete its own `ExternalServiceException` and 502 handler, and import the class from `app.core_exceptions` (not re-exported from `app/exceptions.py`: that import is circular). `services/coredump_service.py` moves to `scoped_session`.
   - FieldnotesApp: `register_readyz("store", ...)` becomes `register_check("store", ..., critical=True)`, with `_readyz` returning a `CheckResult`. Reconcile its own `FIELDNOTES_LOG_LEVEL` with the template's `LOG_LEVEL`. The actioner's system task (no subject) now sends its events to nobody under OIDC: pass a subject, or accept it.
   - The comments in IoT's and EI's `.kubecoder/config.yaml` that say readyz reports `database.connected` now mean `checks.database.status`. App docs and scripts that read the readyz body change too (FieldnotesApp's `docs/slice-test-plan.md` waited for the old body text and would hang). Without the SSE gateway readyz now answers 200 `degraded`, where it answered 503.
10. **`backend/tests/conftest.py` and the app's tests.** An app without a database has only the call-shape and session-role items below to check (DHCPApp: one `send_event` assert).
    - The database apps' tests now run on PostgreSQL, through the template's fixtures. Overrides of `test_settings` and `test_app_settings` become `scope="session"` (`tmp_path_factory`, no `database_url="sqlite..."`). `template_connection` is gone: rebuild on `run_databases.clone()` or `committed_app`. Writes through `db.session` move to the `session` fixture (EI's `test_database_constraints.py`). Literal sequence IDs in asserts fail (EI). Tests that leave in-memory state on the session app undo it. Tests that build services with their own metrics request `clear_prometheus_registry`. The schema drift test must pass, so models and revisions must match (EI's `with_variant(..., "sqlite")` columns).
    - The test template database runs the app's `post_migration_hook`, so seed data it inserts (EI's 100 part types) is present in every test, where the SQLite database was empty: tests that assume an empty table clear it inside their own transaction (EI's `without_seeded_types` fixture).
    - PostgreSQL enforces column lengths, which SQLite ignored: test data longer than its column fails (EI's part keys).
    - Tests that add routes to an app need an app of their own: Flask refuses new routes on the session app once it has served a request.
    - Test sessions (the testing endpoints' fake sign-in) must hold one of the app's roles, `editor` for most: a session with none gets 403 everywhere, `/api/auth/self` included.
    - EI's and IoT's `StubLifecycleCoordinator` (`tests/testing_utils.py`) gains `unregister_lifecycle_notification`.
    - Tests that assert the old call shapes change: `send_event`'s first argument is a `Target` (`== BROADCAST_TARGET`, not `is None`); readyz bodies (FieldnotesApp `json()["checks"]["store"]`, and `health_service.clear_cache()` between a passing and a failing check); a version event read on connect without queueing one first now gets none in a local stage; `Settings(flask_env="production")` gives `stage == "prd"` and no exception text in a 500.
    - Readyz tests check the status code too: 200 when only a non-critical check fails (the SSE gateway's), 503 when a critical one does. `clear_cache()` matters only where tests share one app.
    - Tests that start a task as one subject and call `/api/tasks/*` as another, or start one without a subject under OIDC, get 404.
    - PilotApp: `tests/test_sse_callback.py` largely duplicates the template's `tests/api/test_sse_callback.py`: drop it, or keep only Pilot's role cases.
11. **`.env*`.** App-owned `backend/.env.example` gains `STAGE` (commented out), `HOMELAB_INTERNAL`, `LOG_LEVEL` and `MAX_UPLOAD_SIZE_MB` (see the template's), and the `BASEURL` comment no longer says it sets the redirect URI: it infers `OIDC_COOKIE_SECURE`, and the redirect URIs come from the request's origin. App docs that say the login and logout `redirect` is validated against `BASEURL` change too: it must be a path on the site (ZigbeeControl's `backend/README.md`). The dev `.env` and `.env.test` need nothing: `FLASK_ENV` gives the local stage, and `TEST_DATABASE_ADMIN_URL` defaults to the `postgres` sidecar. EI sets `MAX_UPLOAD_SIZE_MB` above 50 only if it raises nginx's 50 MB limit too.
12. **`frontend/package.json`:** add `pg` and `@types/pg` (`^8.23.1`) to `devDependencies`, in every app (the Playwright global setup imports them, database or not), and `"generate:api:with-backend": "python3 ../scripts/regenerate-openapi.py --frontend"` to `scripts`. The `build-fast`/`build` split is optional. Run `pnpm install`, then `pnpm update eslint-plugin-react-hooks ssegateway` (it re-sorts `package.json`; put the template's order back where the app keeps it). SSEGateway: a lock older than `c136d9c` (2026-04-05) holds a gateway that never sends `ready`, which the SSE client now waits for, so every SSE spec times out (IoT held `dea28a1`); the deployed gateway images are newer. eslint-plugin-react-hooks: the template's `sse-context-provider.tsx` fails lint under 7.0.x, which an existing lock may hold, and passes under 7.1.1 or later. 7.1 may also flag the app's own code (IoT one site, EI 21 across three rules); where the pattern is deliberate, give it a disable comment that says why. It can also move an existing `set-state-in-effect` error to another `setState` in the same effect and report the old disable comment as unused (DHCPApp's `lease-table.tsx`).
13. **`frontend/src/styles/button.ts`:** add `whitespace-nowrap` after `justify-center` in both `buttonBaseClasses`. The frontend update merges it in only where the app had edited the file (IoT, EI); check rather than assume.
14. **`backend/Dockerfile`** (needs DockerImages `7e7c1f7` pushed and `modern-app-backend-build` rebuilt first, or the build fails with `uv: not found`). The build stage becomes `FROM registry:5000/modern-app-backend-build AS build` and loses its `ENV` lines, apt block and `pip install`. The runtime stage becomes `FROM registry:5000/modern-app-backend` and loses its apt block. The Poetry apps also take `COPY pyproject.toml uv.lock /app/` and `RUN uv sync --locked --no-dev --no-install-project`. IoT rewrites its short file to the template's default, keeping `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` in the runtime `ENV`. FieldnotesApp keeps its runtime `git ca-certificates` install, its extra `COPY` lines and `--no-editable`. The frontend `Dockerfile` is template-owned and arrives with step 4.
15. **Refresh the frontend's OpenAPI cache** after the backend edits: `python3 scripts/regenerate-openapi.py --frontend` at the root (or `pnpm generate:api:with-backend`), and commit `frontend/openapi-cache/openapi.json`. Until then, `tsc` fails (`use-ui-setup.ts` imports `useGetUiSetup`) and so does the new `tests/test_openapi_cache.py`. Run `tsc` after `pnpm generate:api:build && pnpm generate:routes` (or `pnpm build`): the refresh doesn't generate the routes, and in a tree never built most errors are only missing generated files. If that test still fails right after a refresh, the app's document depends on its settings (a blueprint registered under a flag, for example); find that before changing the test. The generator now leaves a response field with a default optional (`--default-non-nullable false`), so `tsc` may then flag app code and test factories that read such a field as always present: handle the missing value (IoT mapped it to `null`).
16. **Gates:** the app's `kc project setup`, `build`, `test` and `lint`, and its Playwright suite through `uv run run-suite --suite frontend`. Before reading a Playwright failure as a regression, check the app's `.kubecoder/config.yaml` and `Jenkinsfile` for secrets and services this environment lacks (IoT's Keycloak admin API and OpenSearch exist only in CI). Look at the behaviour changes below when a test changes outcome; two of them failed EI specs: the mount-time `ready` of action scopes, and the toast helpers that now close the toast. Keep `vulture_whitelist.py`, `knip` and `.codehealthignore` current. Vulture never reports a whitelist entry that names nothing: drop the entries for template code the release removed (ZigbeeControl's `generate_authorization_url`).
17. **The deploy repo** (`/work/scratch/deploy/<repo>`): set `STAGE=prd` and `HOMELAB_INTERNAL=true` in all six, in the backend container's `env:` in the chart templates and on the backend's own init container where it has one (DnsmasqDeploy's pod also runs dnsmasq's init containers: leave those) (the values files set no env; `docs/da_port_worklist.md` §5 names each repo's file). PilotApp's `tests/render-chart.py` checks the env, so update it with the change. Keep `BASEURL`: it still sets the cookie's `Secure` flag.
18. **The IdP client** (Keycloak, an operator action): add `https://<host>/api/auth/callback` as a valid redirect URI and `https://<host>/*` as valid post-logout redirect URIs for every hostname a browser signs in on. Hosts: IoT `iot.ginbov.nl`, EI `parts.ginbov.nl`, DHCPApp `dhcp.home`, ZigbeeControl `z2m.webathome.org`, FieldnotesApp `fieldnotes` and `fieldnotes.home` (its `-api`, `-mcp` and `-hooks` hosts serve no UI), PilotApp `pilot.ginbov.nl`. A dev environment with OIDC on signs in on `https://frontend.<env-id>.home`. After deploying, check that the login's `redirect_uri` reads `https://<host>/...`.
19. **The architecture YAML: nothing to do.** All six apps already produce their model on the library's `architectureProducer` (plan correction 1), so only new apps seed one. The `aac-tools` toolchain and `arch-validate` lint step in `.kubecoder/*` are optional, and the operator's call.

### uv replaces Poetry; dependency bumps

**What changed:**
- Backend: `pyproject.toml` is PEP 621 (`[project]`, `[dependency-groups]`, `[project.scripts]`, hatchling), with a `uv.lock`. Every `poetry run` in template-owned files is `uv run`. Bumps: spectree 2, flask-cors 6, Pillow 12 (with the typing fix), pytest 9, pytest-cov 7, ruff 0.15, types-flask-cors 6; types-pillow is gone. The `Dockerfile` default installs with `uv sync`.
- Frontend: Playwright's global setup runs the backend CLI with `uv run`.
- Root: the suite runner, `Procfile.dev`, `scripts/dev.py`, `scripts/regenerate-openapi.py`, the generated `project.yaml` and `CLAUDE.md` run on uv; `pyproject.toml` pins `ruff==0.15.22`. A new app's `project.yaml` runs `uv sync` without `--locked`, since it has no `uv.lock` until its first setup.

**Migration steps:** sync steps 5, 6 and 14.

### Backend tests and Playwright run on PostgreSQL

**What changed:**
- Backend: `tests/conftest_infrastructure.py` builds one template database per run from the revisions (`upgrade_database()` and the post-migration hook) in production's locale, and serves a session-scoped `app` on a clone of it. `session` is a savepoint session rolled back after each test; `committed_app` gets a clone with real commits. Leftovers from dead runs are swept. Test pools are small (`TEST_DB_POOL_SIZE = 2`, `TEST_DB_POOL_MAX_OVERFLOW = 3`, unless `DB_POOL_*` is set). New template-owned `tests/test_database_schema.py` (the database is at the head, and the models match it) and `scripts/wait-for-services.py` (waits for `TEST_DATABASE_ADMIN_URL`, and `S3_ENDPOINT_URL` when set). `testing-server.sh` takes `--database-url` and runs `uv run dev`. SQLite is gone: `initialize-sqlite-database.sh`, `--sqlite-db`, the SQLite branch of `upgrade_database(recreate=True)` and `Settings.set_engine_options_override()`.
- Frontend: Playwright's global setup builds a seed database (`<project_name>_e2e_<run>_seed`) with the backend's `load-test-data` when the backend has `alembic.ini`, each worker's backend serves its own clone, and the new `global-teardown.ts` drops them (`tests/support/helpers/pg-admin.ts`, on `pg`). The `postgres` sidecar is the default server.
- Root: CI's validation Job runs a `postgres:18-trixie` service under `use_database`.

**Migration steps:** sync steps 2, 10, 11 and 12. The database apps' test data must load on PostgreSQL through the revisions.

### Stages and the internals fact

**What changed:**
- Backend: `STAGE` (`local-dev`, `local-tst`, `dev`, `tst`, `uat`, `prd`; `Settings.stage`) defaults to `local-tst` under testing, `local-dev` under development and `prd` for any other `FLASK_ENV`. `HOMELAB_INTERNAL` (default false) is a deploy setting. `Settings.expose_internals` is true when the stage isn't `prd` or the app is internal. The 500 catch-all shows the exception text only when it is true. New `GET /api/ui-setup` returns `stage` and `expose_internals` to a signed-in user. On `prd`, `upgrade-db --recreate`, `load-test-data` and the testing endpoints refuse. The boot log dumps every setting, with `Sensitive` ones masked. `LOG_LEVEL` sets the root logger's level, and `MAX_UPLOAD_SIZE_MB` (default 50) sets `MAX_CONTENT_LENGTH`.
- Frontend: `useUiSetup()` reads `/api/ui-setup` once signed in (`null` on any failure, a 403 included). Where `expose_internals` is true, an error toast's icon becomes a button that copies the message and its diagnostics. Shell apps show the stage badge in the top bar, hidden on `prd`; its colour is the `--stage-indicator` token, which `app-theme.css` can override.
- Root: CI runs `STAGE=tst`. The dev stack seeds no `STAGE`.

**Migration steps:** sync steps 8, 11 and 17.

### Auth: roles, one identity path, the redirect origin, task owners

**What changed:** backend, and the frontend's dev proxy.
- **Roles.** A signed-in caller holding none of the app's configured roles gets 403 on every `/api` endpoint, before the per-tier check, `@public` ones included. `@no_role_check` exempts login, callback and logout. With OIDC off, every request runs as the local admin (`local-user`), exempt from role checks. Opt-in `role_hierarchy` on `AuthService`, with cycle detection over the tiers and the hierarchy; the OpenAPI spec gains `x-auth-roles.hierarchy` (`{}` when off).
- **Identity.** `resolve_auth_identity()` is the one identity path (test session, local admin, JWT). Tolerant mode (`@public`) reads the access token from the cookie only, never the Authorization header, so device and client bearer tokens stay the endpoint's business, and `/api/auth/self` no longer accepts a bearer token. `authenticate_request(..., *, throw_on_error)` requires the flag. Logout sets `g.clear_auth_cookies`.
- **Redirect origin.** Login builds the OIDC `redirect_uri` from the request's origin (behind `ProxyFix`) and keeps it in the encrypted state, where it used to use `BASEURL`. A `redirect` parameter must be a path on this origin; an absolute URL gets 400. The Vite dev proxy forwards `X-Forwarded-Host` and `X-Forwarded-Proto` (`forwardOrigin`), and must not use `xfwd`.
- **Task owners.** `GET /api/tasks/<id>/status`, `POST …/cancel` and `DELETE /api/tasks/<id>` serve only the task's subject; anyone else gets the unknown-id 404. With OIDC on, a task without a subject belongs to nobody. The 404 is now the error envelope (`code: RECORD_NOT_FOUND`), with the messages "Task <id> was not found", "Cancellable task <id> was not found" and "Finished task <id> was not found".

**Migration steps:** sync steps 4 (IoT's `xfwd`), 7, 10 and 18.

### Readiness checks and the readyz format

**What changed:** backend.
- `GET /health/readyz` answers `{"status", "ready", "stage", "checks": {"<name>": {"status": "ok"|"error"|"disabled", "critical", "detail"?}}}`. `status` is `ok`, `degraded` (a non-critical check failed; 200), `not_ready` (a critical one failed; 503) or `shutting_down` (503). The old body had a top-level key per check with an `ok` flag. Healthz answers `{"status": "alive", "ready": true}`.
- Services register their own checks: `HealthService.register_check(name, check, *, critical, timeout=0.8)`, with `check()` returning a `CheckResult`. `register_readyz` and `register_healthz` are gone. The checks are `database` and `s3` (critical) and `sse_gateway` (not critical). They run concurrently, each within its timeout, and a passing result is cached for 30 s.
- The probes read the status code only, so the deploy repos need nothing.

**Migration steps:** sync steps 7, 9 (FieldnotesApp, the `.kubecoder` comments) and 10.

### SSE: typed targets, refused connects, the client's recovery

**What changed:**
- Backend: `send_event(target, event_data, event_name, service_type)` takes a required `Target`: `Target.connection(request_id)`, `Target.subject(subject)`, `LOCAL_ADMIN_TARGET` or `BROADCAST_TARGET`. A request ID or `None` raises `TypeError`, and `target_subject` is gone. A task's events go to its owner, and to nobody under OIDC when it has no subject (they used to broadcast). The local admin is a flag on the binding (`bind_identity(..., local_admin=False)`). The gateway's connect callback answers 401 to a missing or invalid token and 403 to a caller without the read role. `POST /api/testing/sse/force-callback-error?status=401|403` makes the next connect refuse. The version service sends nothing on a failed fetch (no `"unknown"` version), and nothing on connect in a local stage unless a version was queued. `use_sse` without `use_oidc`, which failed at import, now renders and runs (new apps only: the fix is in app-owned `container.py`).
- Frontend: the stream counts as connected on the gateway's `ready` event, not on open. On `rejected`, the client refreshes the session through `/api/auth/self` and reconnects; a 401 sends the user to login, and anything else shows "Connection to the server was lost. Please refresh the page to reconnect." There is no retry loop, on the SharedWorker and the direct path alike. `SseGate` no longer holds the page back (no `sse.gate.loading`), and `deploymentSse.ensureConnected()` waits for the mount connection. `reconnect()` reaches a live worker, the test bridge is `window.__sseForceReconnect`, and the SharedWorker opt-in (`?__sharedWorker`) survives a redirect. FE03: `percentage` is `value * 100`.

**Migration steps:** sync steps 3, 4, 9 and 10.

### Backend fixes and additions

**What changed:**
- Werkzeug HTTP errors without a handler of their own (413, 415, …) answer their own status instead of 500. Requests that match no route are labelled `endpoint="unknown"` in the request histogram, where they used to carry the path; `DiagnosticsService.request_duration_seconds` is gone.
- `scoped_session` and `scoped_savepoint` in `app/database.py`; `after_commit()` runs after a scoped session's commit too. Alembic's `fileConfig` no longer silences the app's loggers, and `drop_all_tables()` no longer empties `db.metadata`.
- `LifecycleCoordinatorProtocol.unregister_lifecycle_notification` is a new abstract method, and the log stream's `connection_close` event is gone. `allow_empty` column info opts a column out of empty-string normalization. The CLI's "Using database" line masks the password.
- New template-owned `app/core_exceptions.py` with `ExternalServiceException(operation, cause)` (502, `EXTERNAL_SERVICE_ERROR`). `schemas/common.py` gains `ApiErrorResponseSchema` and, for paged lists, `PaginationQuerySchema` and `SortDirection`, with `apply_sorting()` (`id` tiebreaker) and `build_pagination_meta()` in `app/utils/pagination.py`.
- `scripts/dev-watch.sh` runs `uv run dev` under `watchmedo auto-restart`, replacing `dev-server.sh`; `run.py` runs without the Werkzeug reloader.
- New template-owned `tests/test_openapi_cache.py` fails when `frontend/openapi-cache/openapi.json` differs from the backend's document (MAT-12).
- `database_name` defaults to `project_name` with underscores, as the root's does, and `scripts/init-dev-database.py` reads `backend/.env`. No app's render changes.

**Migration steps:** sync steps 3, 6, 9, 10 and 15.

### Frontend fixes and defaults

**What changed:**
- **Dialogs:** a backdrop click no longer closes a `Dialog` (`preventOutsideClose`, default true; `false` restores it). The overlay carries `data-testid="dialog-overlay"`.
- **Buttons:** a loading button keeps its width (a spinner overlaid, the label and icon hidden). Enabled buttons get the pointer cursor; the dark theme's `--primary`, `--ring`, `--link-hover` and `--destructive` changed. An app's Tailwind `@source` and `@plugin` lines go in `app-theme.css`.
- **Generated API types** mark a property with a default as optional, in requests and responses alike, so app code that reads such a response property as always present can fail `tsc`. `scripts/fetch-openapi.js`'s errors name `regenerate-openapi.py --frontend` and `generate:api:with-backend`. `use_oidc=false` builds again, with or without the shell (`auth-redirect.ts` is no longer excluded).
- **Vite and nginx:** an SSE proxy that flushes (`configureSseProxy`, under `use_sse`), `strictPort`, the test-mode build's `define`/`external` fix, and nginx's `Host $http_host`. `.gitignore` ignores `.env*` except `.env.example`.
- **Playwright:** preview mode (`VITE_TEST_MODE=true pnpm build`, then `PLAYWRIGHT_PREVIEW_MODE=true`), with the `@preview` tag on specs that need it. Services run in their own process groups, so an interrupted run leaves nothing behind. Readiness waits are 120 s per service and 300 s per worker. Video is off unless `PLAYWRIGHT_RETAIN_VIDEO=true` (any value used to turn it on). An unexpected error toast no longer fails a spec, and a ui-state scope whose data is cached at mount emits `ready` on mount.
- **The toast helpers now close toasts.** `dismissToast()` matched no element (`button[aria-label="Close"]`; the close button is named by its screen-reader text), so it and the dismissal in `expectSuccessToast()`, `expectErrorToast()`, `expectInfoToast()` and `waitForToastsToDisappear()` were no-ops. They now close the first toast, or every toast. `waitForToastViewportDismissed()` closes every toast and waits for none to be left, instead of sleeping 1 s. `assertToastSequence()` closes each matched toast.
- **Test bridges:** `__deploymentSseControls.getCurrentVersion()` and `DeploymentSseHelper.waitForCurrentVersion()`; specs wait on conditions, not fixed sleeps.

**Migration steps:** sync steps 4, 12, 13 and 16.

### CI, images, dev stack and tooling

**What changed:** root, unless noted.
- `Jenkinsfile` is the declarative `modernApp.test` file: `services:` for `postgres` (`use_database`) and RustFS (`use_s3`), `env:` with `STAGE: 'tst'` and `BUILD_CACHE: 'true'`, and the uv `install`/`run` strings.
- The suite runner restores and saves the pnpm store through the build cache (`--build-cache`, on when `BUILD_CACHE=true`; `scripts/build-cache-get.sh` and `-put.sh`). After the dev-server pass, it runs the `@preview` specs against a test-mode build (`frontend-preview.xml`), and leaves `dist/` a test-mode build.
- Frontend: `Dockerfile` builds on `registry:5000/modern-app-frontend-build` and restores the pnpm store from the build cache (`ARG BUILD_CACHE_URL`). Backend: the `Dockerfile` default builds on `modern-app-backend-build` and runs on `modern-app-backend` (new apps only; app-owned).
- `Procfile.dev` runs the backend through `scripts/dev-watch.sh`, so it restarts on a code change.
- `Jenkinsfile.architecture` (new, `_skip_if_exists`) and a generated `CLAUDE.md` section on the architecture model; new apps get the `aac-tools` toolchain and an `arch-validate` lint step.
- New `scripts/check_updates.py` lists outdated direct dependencies per component (`cexec modern-app python3 scripts/check_updates.py [--json]`).

**Migration steps:** sync steps 2, 14 and 19.

### Behaviour users and tests will notice

**What changed:**
- A signed-in user with none of the app's roles gets 403 everywhere, `@public` endpoints called with the session cookie and the SSE connect included. No current user is locked out (operator ruling).
- With OIDC on, a refused SSE connect shows the "Connection to the server was lost" toast or sends the user to login, and never retries in a loop.
- A backdrop click no longer closes a dialog.
- Pages render before the SSE stream is ready. A spec that expects an SSE-delivered update right after `page.goto` calls `deploymentSse.ensureConnected()` first (ZigbeeControl's `tab-manager.spec.ts` was the one candidate found, and passes unchanged: its backend resends each tab's status to every new connection).
- Shell apps show the stage badge wherever the stage isn't `prd`, the dev stack and CI included. With `HOMELAB_INTERNAL=true`, deployed apps show the copy-diagnostics button and the exception text in 500 responses.
- An oversized body answers 413, not 500.
- Readyz has the new body, and can answer 200 `degraded`.
- Unmatched requests are labelled `endpoint="unknown"` in the request metrics.
- The task endpoints answer 404 to anyone but the task's owner, with the error envelope as the body.
- A request that fails schema validation gets its errors as a JSON list in the 400 body; under spectree 1.x they came as one JSON-encoded string. Tests that substring-matched the old body change (EI's seller tests).
- A ui-state scope that mounts idle emits `ready` at once, with no metadata. Action scopes do too (EI's pick-list pick/undo and quantity edit), so a spec waiting on an action's `ready` must match the action's metadata, or it takes the mount-time one.
- Playwright: the toast helpers really close toasts (EI calls them at about 50 sites), so a spec that clicks a toast's action button after `expectSuccessToast()` finds it gone: wait with `waitForToastWithText()` instead (EI's archive-undo spec). The two SharedWorker specs skip in the dev-server pass and run in the preview pass, and video is off by default.

**Migration steps:** sync step 16. A test that changes outcome at the sync starts here.

### The modern-app conventions guide

**What changed:** the conventions (API, status values, backend code, readiness, SSE, frontend code, testing, Playwright) are a guide, sourced in this repo's `guide/` for https://dev-guides.home/modern-app/, and the `kubecoder:modern-app` skill carries its rules. The guide and the skill change no template.

**Migration steps:** none.

## 2026-10-07 — Root v0.1.6

### The validation Job books a CPU request again

**What changed:** `Jenkinsfile`'s validation container requests `cpu: "1"` again, as before v0.1.5. Without a CPU request a validation pod starves on a busy node, and timing-sensitive tests fail (argo-cd D65 as amended 2026-10-07). The memory request stays Kyverno's, set at pod creation.

**Migration steps:**
1. `copier update --trust --defaults` at the app root. An app whose `Jenkinsfile` runs its validation through the library's `modernApp.test` gets the same CPU request from the library; the update changes nothing there.

## 2026-10-06 — Root v0.1.5

### The validation Job books no requests

**What changed:** `Jenkinsfile`'s validation container no longer requests `cpu: "1"` and `memory: 3584Mi`. On prd, Kyverno sets each pod's memory request at creation from a daily snapshot of measured usage (Ansible slice 053, argo-cd D65 as amended 2026-10-06).

**Migration steps:**
1. `copier update --trust --defaults` at the app root. An app whose `Jenkinsfile` runs its validation through the library's `modernApp.test` books no request of its own; the update changes nothing there.

## 2026-09-30 — Frontend v0.20.5

### `pnpm generate:api` falls back to the cached spec when the backend is down

**What changed:** `scripts/fetch-openapi.js` read `timestamp`, `hash` and `spec` fields from a cache that holds only the spec itself. With a cached spec and an unreachable backend, `fetchAndCache()` returned `undefined`, and `pnpm generate:api` crashed while generating hooks. It now returns the cached spec. It also compares the fetched spec with the cached one, so an unchanged spec is no longer rewritten on every run. `pnpm build` (`--cache-only`) was not affected.

**Migration steps:**
1. `copier update --trust --defaults` in `frontend/`. The file is template-owned.

## 2026-09-30 — Root v0.1.4, Backend v0.13.3, Frontend v0.20.4

### A fresh instance passes its own gates

**What changed:** a newly generated app (seen with `use_database=false`, `use_app_shell=false`) failed its gates until the app added code of its own.
- Backend v0.13.3: new app-owned `tests/test_smoke.py` (`_skip_if_exists`), one test that the app answers `/health/healthz`. With no tests at all, `pytest` exits 5 and `poetry run check` fails.
- Frontend v0.20.4: new app-owned `src/routes/index.tsx` (`_skip_if_exists`), a placeholder home page. With `__root` as the only route, the router's types collapse to `never` and `tsc` fails. With `use_oidc` and without `use_app_shell`, the page draws a header with the `UserDropdown`, which the template's auth specs look for.
- Frontend v0.20.4: `scripts/fetch-openapi.js` creates `openapi-cache/` before it writes the spec, so the first `pnpm generate:api` in a fresh app no longer fails with ENOENT.
- Root v0.1.4: the generated `CLAUDE.md` lists `after_commit()` and post-migration logic as extension points only with `use_database`.

**Migration steps:**
1. `copier update --trust --defaults` in `backend/` and `frontend/`. The update adds `backend/tests/test_smoke.py` to an app that has none; keep it or delete it. `src/routes/index.tsx` is skipped, since every app has one.

### `scripts/dev.py` stops on a signal, and the validation Job's tar extraction is clean

**What changed:**
- `scripts/dev.py` forwards SIGINT and SIGTERM to honcho as a Ctrl-C through its PTY instead of ignoring them, so a signal from another shell stops every service. Before, the only way to stop a backgrounded stack was to kill the cexec client, and that left the backend and the SSE gateway running as orphans in the `modern-app` sidecar. New `scripts/dev.py stop` signals the running stack through `logs/dev.pid` and waits for it to exit. A stop that comes in before honcho has started every service is held until then, because honcho crashes on a SIGINT during startup.
- `Jenkinsfile`: the validation Job extracts the context archive with `--strip-components=1`. That skips the archive's `./` entry, whose mode and mtime uid 1000 cannot set on the root-owned `/work` emptyDir. The old command printed "Cannot utime" / "Cannot change mode" and exited 2 on every run; the files were extracted anyway, so builds stayed green.

**Migration steps:**
1. `copier update --trust --defaults` at the app root. App additions to the validation Job spec go through the three-way merge; check them in the diff.

## 2026-09-30 — Root v0.1.3, Frontend v0.20.3

### S3 sidecar is `s3storage`, and Playwright is pinned to 1.60.0

**What changed:**
- Root v0.1.3: KubeCoder's catalog replaced the `minio` service with `s3storage`, a RustFS sidecar on the same `localhost:9000` with credentials `s3storage`/`s3storage`, and storage cleared on every start. An environment whose `config.yaml` names `minio` is refused on restart. The generated `.kubecoder/config.yaml` selects `s3storage`, and `.kubecoder/project.yaml` seeds `backend/.env` and `backend/.env.test` with the new credentials. CI's validation Job already ran RustFS with these credentials.
- Frontend v0.20.3: `package.json` pins `@playwright/test` to `1.60.0` instead of `^1.60.0`. 1.63.0's browser download times out in KubeCoder pods and in CI, while 1.60.0 downloads fine. This is a hold until a Playwright release fixes it, not a floor.

**Migration steps:** both files are generated once (`_skip_if_exists`), so `copier update` does not change them.
1. `copier update --trust --defaults` at the app root and in `frontend/`.
2. With `use_s3`: in `.kubecoder/config.yaml`, replace `- minio` under `services:` with `- s3storage`. In `.kubecoder/project.yaml`, replace `minioadmin` with `s3storage` in the `.env` and `.env.test` seeds. Also update any app-owned script that seeds the same credentials.
3. With `use_s3`, in each existing environment: the seeds never overwrite a file, so fix the S3 credentials in `backend/.env` and `backend/.env.test`, or delete the files and run `kc project setup`. Then `kc env restart`.
4. In `frontend/package.json`, change `"@playwright/test": "^1.60.0"` to `"1.60.0"`, and run `pnpm install` to update the lockfile's specifier.

## 2026-09-26 — Root v0.1.2

### Validation Job runs in the KubeCoder modern-app toolchain image

**What changed:** The `Jenkinsfile` validation Job runs in `registry:5000/kube-coder-modern-app-toolchain:node-24`, the image of the dev environment's `modern-app` sidecar, instead of `modern-app-dev-playwright:playwright-<version>`, which is retired; the lockfile lookup that picked that tag is gone. The image carries Chromium's OS dependencies but no browser, so the suite runner's `pnpm playwright install chromium` downloads Chromium on every run. It has no `/work`, so the Job mounts an emptyDir there.

**Migration steps:**
1. `copier update --trust --defaults` at the app root. App additions to the validation Job spec (extra env, sidecars) go through the three-way merge; check them in the diff.

## 2026-09-26 — Frontend v0.20.2

### Auth redirect test goes back to `/items`

**What changed:**
- `tests/infrastructure/auth/auth.spec.ts`: "preserves full path including query params in redirect" navigates to `/items?filter=active&sort=name` again. v0.20.0 had switched it to `/` (from DHCPApp), but apps whose index route redirects (EI to `/parts`, IoTSupport to `/devices`) drop the query string before the 401, so the test failed in their CI. `/items` is not a route in the apps, so nothing redirects it.

**Migration steps:**
1. `copier update --trust --defaults` in `frontend/`.

## 2026-09-26 — Root v0.1.1

### Suite runner timeouts sized for the largest suite

**What changed:** `scripts/dev.py`'s usage no longer suggests `-e gateway` to skip a service (honcho's `-e` is `--env`); a subset is started with positional names, e.g. `./scripts/dev.py backend frontend`. `tools/suite_runner/local.py` allows ElectronicsInventory's timeouts: backend install 600s, backend pytest 1800s, pnpm install 600s, frontend build 900s, Playwright browser install 900s, Playwright 3600s (were 300/900/300/600/300/1800).

**Migration steps:**
1. `copier update --trust --defaults` at the app root.

## 2026-09-26 — Backend v0.13.1, v0.13.2, Frontend v0.20.1

### Patch releases found while updating the apps

**What changed:**
- Backend v0.13.1: the `use_s3`/`use_oidc` gates in `testing_service.py` and `spectree_config.py` no longer leave doubled blank lines when the flag is off.
- Backend v0.13.2: `truncate_with_ellipsis` loses its unused `encoding` parameter (from EI), and the scaffold `vulture_whitelist.py` drops the matching `encoding` entry and no longer leaves doubled blank lines around its `use_database` blocks.
- Frontend v0.20.1: `routed-tabs.tsx` carries a file-level `react-refresh/only-export-components` disable, like `auth-context.tsx`.

**Migration steps:**
1. `copier update --trust --defaults` in `backend/` and `frontend/`.
2. Optional: remove `encoding  # unused variable` from the app's `vulture_whitelist.py` (app-owned).

## 2026-09-26 — Root v0.1.0, Backend v0.13.0, Frontend v0.20.0

### Monorepo: a root template, and per-repo CI leaves the component templates

**What changed:** The apps are monorepos (backend and frontend in one repo, one CI pipeline). A third template now generates the root layer, and the backend and frontend templates stop generating the per-repo CI and Docker-era scripts that the conversion made dead.

**Root template (new, v0.1.0).** Lives in this repo: `copier.yml` at the root, the template in `root/template/`, versioned by this repo's tags. Generates:
- Template-owned: `Jenkinsfile` (validation Job on `modern-app-dev-playwright:playwright-<version>` running `run-suite`, RustFS S3 sidecar when `use_s3`, kaniko builds of both images, `cicd.writeVersionPins` into the Argo CD deploy repo), `tools/suite_runner/` (`run-suite`), `Procfile.dev`, `scripts/dev.py`, `scripts/dev-sse-gateway.sh` (`use_sse`), `.gitignore`, `.vscode/settings.json`.
- Generated once (`_skip_if_exists`): `pyproject.toml` (with the pinned `[tool.ruff]` and ruff dev group), `CLAUDE.md`, `<repo_name>.code-workspace`, `scripts/regenerate-openapi.py`, `.kubecoder/config.yaml`, `.kubecoder/project.yaml`.
- The suite runner runs `backend/scripts/wait-for-services.py` after the backend install when that file exists — the hook for CI sidecars that are slow to come up.

**Backend v0.13.0:**
- Removed: `Jenkinsfile`, `scripts/{args,build,push,run,stop}.sh`, `scripts/dev-sse-gateway.sh` (now root), and the `repo_url`, `image_name`, `validation_jenkins_job` questions.
- `scripts/testing-server.sh` has its own default port instead of sourcing `args.sh`.
- Flask 3 typing: `types-flask` dropped from the scaffold `pyproject.toml`; `app/app.py` gains `current_container()` (and declares `diagnostics_service` with `use_database`); `dict[str, Any]` health checks; App-typed CLI handlers; `BaseException` in `close_session`; `ProxyFix` assignment marked `method-assign`.
- New `app/utils/after_commit.py` (`use_database`): `after_commit(callback)` runs the callback only after the request's transaction commits; `close_session` runs or drops them.
- S3 preflight in `tests/conftest_infrastructure.py` treats any HTTP response as reachable (MinIO answers `GET /` with 403).
- New `scripts/init-dev-database.py` (`use_database`): creates the dev database on the Postgres sidecar.
- Flag fixes: `testing_service.py`, `spectree_config.py`, `vulture_whitelist.py` and `flask_error_handlers.py` docstrings are feature-gated; `app/models` is excluded without `use_database`.
- Scaffold fixes for new apps: `README.md` (poetry install needs it), `.dockerignore`, `app_config.py` defines `thumbnail_storage_path` for `use_s3`, `Dockerfile` installs `--only main`, the SQLAlchemy mypy plugin is gone (removed in SQLAlchemy 2.1).

**Frontend v0.20.0:**
- Removed: `Jenkinsfile`, `Jenkinsfile.validation`, `scripts/validation-entrypoint.sh`, and the `repo_url`, `image_name`, `backend_repo_url`, `backend_image_name`, `backend_jenkins_job`, `frontend_jenkins_job`, `validation_jenkins_job`, `generate_validation_pipeline` questions.
- `knip.config.ts` no longer ignores `@tanstack/router-devtools` and `class-variance-authority` (unused); the scaffold `package.json` drops them, requires `@playwright/test ^1.60.0` and uses `github:pvginkel/SSEGateway#stable`.
- `DebouncedSearchInput` syncs the URL term during render (eslint-plugin-react-hooks 7.1 rejects setState in effects).
- New `RoutedTabs` primitive (from IoTSupport). `DialogContent` accepts `data-testid`. Vite ignores `.pnpm-store`. SegmentedTabs indicator contrast and toast alignment (from EI).
- `global-setup.ts` runs the seed script with `OIDC_ENABLED=false`; `auth.spec.ts` redirect test uses `/` instead of `/items`.
- `.dockerignore` scaffold.

**Migration steps:**
1. On a clean tree: `cd backend && copier update --trust --defaults`, then `cd ../frontend && copier update --trust --defaults`. Deleted template files that the app still has (e.g. `backend/scripts/build.sh`) are removed; resolve any conflicts.
2. Adopt the root template (once): from the repo root, `copier copy --trust --defaults <path-to>/ModernAppTemplate . --vcs-ref v0.1.0` with the app's answers (`-d project_name=… -d repo_name=… -d backend_image=… -d frontend_image=… -d deploy_repo=… -d backend_image_pin_key=… -d frontend_image_pin_key=…` plus ports and flags), then review `git diff`: keep genuine app additions in the template-owned files (extra Jenkinsfile stages, extra `.gitignore` lines); the `_skip_if_exists` files are left untouched. Commit; from then on `copier update` at the root.
3. `backend/pyproject.toml`: remove `types-flask`; remove the `sqlalchemy.ext.mypy.plugin` line if the app moves to SQLAlchemy 2.1.
4. `frontend/package.json`: remove `@tanstack/router-devtools` and `class-variance-authority`, then `pnpm install` — knip flags them otherwise.
5. Replace hand-edits of `close_session` in `app/__init__.py` with `after_commit()` calls from the service code.
6. Move any sidecar wait the app does in the suite runner into `backend/scripts/wait-for-services.py`.

## 2026-06-05 — Frontend v0.19.1

### Fix: validation extracts source to /work/backend and /work/frontend

**What changed:** The v0.19.0 streaming validation extracted the source to `/work/backend-src` and `/work/frontend-src`. That broke the Playwright test harness: `tests/support/process/servers.ts` resolves the backend repo root as `<frontendRoot>/../backend`, so it spawns `/work/backend/scripts/testing-server.sh` — which didn't exist (`spawn … ENOENT`). The Job now renames the extracted dirs to `/work/backend` and `/work/frontend` (the same sibling layout the old `Dockerfile.validation` produced via `COPY`), and `validation-entrypoint.sh` `cd`s into those paths.

Frontend template files changed:
- `template/Jenkinsfile.validation.jinja` (`mv /work/backend-src /work/backend` + `mv /work/frontend-src /work/frontend` after extract)
- `template/scripts/validation-entrypoint.sh` (`cd /work/backend` and `cd /work/frontend`)

**Migration steps:**
1. `copier update --trust` on the frontend — picks up the rename and the entrypoint paths.

## 2026-06-05 — Frontend v0.19.0

### Validation runs on the prebaked Playwright image; no per-build validation image

**What changed:** The validation pipeline no longer builds a `Dockerfile.validation` image with kaniko. Instead, `Jenkinsfile.validation` resolves the Playwright version from `frontend-src/pnpm-lock.yaml`, runs the validation Job directly on `registry:5000/modern-app-dev-playwright:playwright-<version>` (browsers prebaked), and streams the source into the Job via `tar` + `kubectl cp`.

This fixes validation jobs hanging after `playwright install` downloaded Chromium on the plain `modern-app-dev` base image. The Job runs as `runAsUser: 1000` so the prebaked browser cache (owned by `ubuntu`) is found, and results are copied out of the still-running pod via `kubectl cp` instead of the base64-in-logs hack. The source now extracts to `/work/backend-src` and `/work/frontend-src`.

This requires the `modern-app-dev-playwright` image to be published for the Playwright version pinned in the app's lockfile (currently `1.58.2`).

Frontend template files changed:
- `template/Jenkinsfile.validation.jinja` (rewrote the `Run validation` stage; dropped the `Build validation image` kaniko stage)
- `template/scripts/validation-entrypoint.sh` (reads `/work/backend-src` and `/work/frontend-src`; dropped the base64 JUnit export trap — results now leave via `kubectl cp`)
- `template/Dockerfile.validation` (removed)
- `copier.yml` (removed `Dockerfile.validation` from `_skip_if_exists` and `_exclude`; removed the now-unused `validation_image_name` variable; updated `generate_validation_pipeline` help text)

**Migration steps:**
1. `copier update --trust` on the frontend — `Jenkinsfile.validation` and `scripts/validation-entrypoint.sh` update and `Dockerfile.validation` is deleted. The `validation_image_name` answer is dropped automatically.
2. Ensure `registry:5000/modern-app-dev-playwright` is published for the Playwright version in your `pnpm-lock.yaml`. If your app pins a version with no published image, bump to a published one or have the image built for it.
3. If your app's validation Job injects extra env/secrets (e.g. S3, Keycloak, Elasticsearch), re-add them to the new Job spec — the template's validation Job ships no app-specific env by default.

## 2026-03-15 — Frontend v0.18.0

### UI components now template-owned

**What changed:** The `src/components/ui/` directory is no longer fully `_skip_if_exists`. Only `src/components/ui/index.ts` remains app-owned (for managing re-exports of app-specific additions). All other template UI components (badge, skeleton, empty-state, key-value-badge, etc.) are now template-owned and will be updated by `copier update`.

Additionally:
- **Skeleton**: Now accepts optional `className` prop for additional styling (margin, etc.)
- **EmptyState**: `action` prop now accepts `ReactNode` in addition to `ActionConfig`, supporting custom action elements like `<Link><Button>...</Button></Link>`

Frontend template files changed:
- `copier.yml` (`_skip_if_exists` changed from `src/components/ui` to `src/components/ui/index.ts`)
- `src/components/ui/skeleton.tsx` (added `className` prop)
- `src/components/ui/empty-state.tsx` (action accepts `ReactNode | ActionConfig`)

**Migration steps:**
1. `copier update --trust` on frontend — skeleton.tsx and empty-state.tsx will be updated automatically.
2. If your app has **customized any template ui component** (other than index.ts), the three-way merge will attempt to reconcile. Review merge results carefully.
3. If your app uses Skeleton with `className` for sizing (e.g. `className="h-12 w-full"`), refactor to `height="h-12" width="w-full"`. Use `className` only for non-size styling like margins.
4. If your app uses EmptyState with `data-testid`, change to `testId`.
5. Apps can still **add their own components** to `src/components/ui/` — copier only manages the files defined in the template. Update `index.ts` to export your additions.

## 2026-03-15 — Frontend v0.17.1

### fetch-openapi.js BACKEND_PORT env var override

**What changed:** `scripts/fetch-openapi.js` now reads `process.env.PORT` as a fallback before the copier-rendered `backend_port`. This allows overriding the backend port at runtime without editing the file. Extracted from DesignAssistant.

Frontend template files changed:
- `scripts/fetch-openapi.js.jinja` (template-owned, auto-updated by copier)

**Migration steps:**
1. `copier update --trust` on frontend — `fetch-openapi.js` is template-owned (Jinja-rendered) and will be updated automatically.

## 2026-03-15 — Frontend v0.17.0

### useCopyToClipboard hook, KeyValueBadge copy support, grouped sidebar navigation

**What changed:**

1. **New `useCopyToClipboard` hook** (`src/hooks/use-copy-to-clipboard.ts`) — Reusable hook for clipboard copy with visual feedback. Returns `{ copyState, copy, reset }` where `copyState` cycles through `'idle' → 'success'/'error' → 'idle'` with a configurable reset delay (default 1500ms). Eliminates duplicated clipboard logic across components.

2. **`KeyValueBadge` copy support** (`src/components/ui/key-value-badge.tsx`) — New optional `copyValue` prop. When provided, hovering the badge reveals a copy icon; clicking copies the value to clipboard with success/error feedback. Uses the new `useCopyToClipboard` hook. (Note: `src/components/ui/` is `_skip_if_exists` — existing apps must manually update their copies.)

3. **Grouped sidebar navigation** (`src/components/layout/sidebar.tsx`) — `SidebarItem` now supports an optional `children` array for grouped navigation. Child items render indented below the parent, hidden when sidebar is collapsed. Parent highlights when any child route is active. Backward-compatible — items without `children` render identically to before.

Frontend template files changed:
- `src/hooks/use-copy-to-clipboard.ts` (new)
- `src/components/ui/key-value-badge.tsx` (updated — `_skip_if_exists`, won't auto-update)
- `src/components/layout/sidebar.tsx` (updated — template-owned, will auto-update)
- `knip-template-ignore.json` (updated)

**Migration steps:**
1. `copier update --trust` on frontend — updates sidebar.tsx (template-owned) and knip-template-ignore.json automatically.
2. **KeyValueBadge**: If your app uses `key-value-badge.tsx` with inline clipboard logic (like EI), refactor to use `useCopyToClipboard` hook. The template version is `_skip_if_exists` so won't overwrite your copy.
3. **Grouped sidebar**: No action needed unless your app has customized `sidebar.tsx` — copier's three-way merge will apply the changes. If you have grouped nav items, add `children` arrays to your `sidebar-nav.ts`.
4. Any component with duplicated clipboard logic can now use `import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'` instead.

## 2026-03-09 — Frontend v0.16.0

### Validation pipeline improvements

**What changed:** Several improvements to the validation pipeline in the frontend template:
- Removed `validation_credential_id` from `copier.yml` — credentials are now fully app-customized in the `Jenkinsfile.validation` (which is `_skip_if_exists`)
- Added resource requests (1 CPU, 3.5Gi memory) to the validation K8s Job
- Enabled backend log streaming in validation entrypoint for better diagnostics
- Added `--retries=2` to Playwright in validation entrypoint
- Fixed Groovy parse error in validation log cleanup
- Used `utils.cleanLog()` for validation log cleanup instead of shell sed/tr
- Strip ANSI codes and Unicode emoji from validation.log

Frontend template files changed:
- `copier.yml` (removed `validation_credential_id` variable)
- `template/Jenkinsfile.validation.jinja` (simplified, credentials removed from template)
- `template/scripts/validation-entrypoint.sh` (retries, log streaming, cleanup improvements)

**Migration steps:**
1. `copier update --trust` on frontend — only updates `.copier-answers.yml` (removes `validation_credential_id`).
2. `Jenkinsfile.validation` and `scripts/validation-entrypoint.sh` are `_skip_if_exists` — existing files won't be overwritten. If you want the new entrypoint improvements, manually update your copies from the template's `test-app/` versions.

## 2026-03-09 — Backend v0.12.0, Frontend v0.15.0

### Jenkins validation pipeline support

**What changed:** Both templates now support a Jenkins validation pipeline that runs test suites before promoting images to `:latest`. When `validation_jenkins_job` is set, the Jenkinsfile builds without tagging `:latest`, archives build metadata as a JSON artifact, and triggers a validation job. The validation job (in the frontend template) resolves the image pair, clones source repos, builds a validation Docker image, runs backend + frontend tests in a K8s Job, then promotes images and deploys Helm on success.

New backend variables:
- `validation_jenkins_job` — validation job name (empty = old build+deploy flow)

New frontend variables:
- `validation_jenkins_job` — validation job name (empty = old build+deploy flow)
- `backend_repo_url` — backend git URL for cloning in validation
- `backend_image_name` — backend Docker image for crane tag promotion
- `backend_jenkins_job` — backend Jenkins job name for copyArtifacts
- `frontend_jenkins_job` — frontend Jenkins job name for copyArtifacts
- `validation_image_name` — validation Docker image name
- `validation_credential_id` — Jenkins secret file credential ID for test env vars

New frontend template files (all `_skip_if_exists`, excluded when `validation_jenkins_job` is empty):
- `Jenkinsfile.validation.jinja`
- `Dockerfile.validation`
- `scripts/validation-entrypoint.sh`

**Migration steps:**
1. `copier update --trust` on backend — adds `validation_jenkins_job` variable. Set to your validation job name or leave empty.
2. `copier update --trust` on frontend — adds all new variables. Provide values for your app.
3. For apps not yet using validation: existing Jenkinsfiles are `_skip_if_exists` and won't change.
4. For apps adopting validation: after `copier update`, manually update the existing Jenkinsfile to the new flow (or delete it and re-run `copier update` to get the template version).
5. Create the validation Jenkins pipeline job pointing to `Jenkinsfile.validation` in the frontend repo.
6. If the app needs test secrets (S3, OIDC, etc.), set `validation_credential_id` and create the corresponding Jenkins secret file credential.

## 2026-03-09 — Frontend v0.14.3

### Frontend: Fix useListLoadingInstrumentation not emitting ready when query data is cached on mount

**What changed:** When a component mounted with query data already in the TanStack Query cache (`isLoading=false`, `isFetching=false` from the start), the `useListLoadingInstrumentation` hook never entered the loading state and therefore never transitioned to `ready`. This caused `waitForListLoading()` calls in Playwright tests to time out. The fix emits `ready` immediately on first render when data is already available.

Frontend template files changed:
- `template/src/lib/test/query-instrumentation.ts`

**Migration steps:**
1. Run `copier update` on the frontend — the file is template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Frontend v0.14.2

### Frontend: Whitelist 400 errors in Playwright console handler

**What changed:** The console error handler in `fixtures-infrastructure.ts` now whitelists HTTP 400 (BAD REQUEST) responses. When OIDC is disabled in test mode, navigating to `/api/auth/login` returns 400, and the browser's error message doesn't include the URL path — so the existing `/api/auth/` filter didn't catch it.

### Frontend: Make auth-shell tests conditional on SIDEBAR_VISIBLE

**What changed:** `auth-shell.spec.ts` now imports `SIDEBAR_VISIBLE` from `consts.ts` and skips sidebar/hamburger tests when it's `false`. Apps with `use_app_shell=true` but `SIDEBAR_VISIBLE=false` (top bar only, no sidebar) were failing because the test assumed a hamburger button always exists.

Frontend template files changed:
- `template/tests/support/fixtures-infrastructure.ts.jinja`
- `template/tests/infrastructure/auth/auth-shell.spec.ts`

**Migration steps:**
1. Run `copier update` on the frontend — both files are template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Frontend v0.14.1

### Frontend: Templatize backend-url.ts with backend_port variable

**What changed:** `tests/support/backend-url.ts` is now a Jinja template (`backend-url.ts.jinja`) that renders the `DEFAULT_BACKEND_URL` using the `backend_port` copier variable instead of hardcoding port 5000. This matches how `vite.config.ts`, `nginx.conf`, and `consts.ts` already work.

Frontend template files changed:
- `template/tests/support/backend-url.ts` → `template/tests/support/backend-url.ts.jinja`

**Migration steps:**
1. Run `copier update` on the frontend — the file is template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Frontend v0.14.0

### Frontend: SseGate component, SSE auto-connect fix, test improvements

**What changed:** Four related improvements to SSE and test infrastructure:

1. **New `SseGate` component** (`src/components/sse/sse-gate.tsx`). Blocks rendering of children until the SSE connection is established. Used in `SseProviders` to ensure the app only renders once SSE is ready.

2. **SSE auto-connect in all modes.** Removed the `hasSharedWorkerParam`/`shouldAutoConnect` guard in `sse-context-provider.tsx` that was preventing SSE from auto-connecting in test mode. SSE now connects unconditionally on mount.

3. **Infrastructure tests use `fixtures-infrastructure` directly.** `tests/infrastructure/auth/auth.spec.ts` and `tests/infrastructure/test-infrastructure.spec.ts` now import from `fixtures-infrastructure` instead of `fixtures`. Infrastructure tests should not depend on app-specific domain fixtures.

4. **Auth tests use `roles: ['editor']` and 401 tests re-enabled.** All `auth.createSession()` calls in infrastructure auth tests now pass `roles: ['editor']` to match role-gated backends. The two previously-skipped 401 redirect tests are now enabled using `auth.forceError(401)` to reliably trigger the redirect flow.

Frontend template files changed:
- `template/src/components/sse/sse-gate.tsx` — new file
- `template/src/providers/sse-providers.tsx` — wraps `DeploymentProvider` in `SseGate`
- `template/src/contexts/sse-context-provider.tsx` — removed `shouldAutoConnect` guard
- `template/tests/infrastructure/auth/auth.spec.ts` — `fixtures-infrastructure` import, `roles: ['editor']`, re-enabled 401 tests
- `template/tests/infrastructure/auth/auth-shell.spec.ts` — `roles: ['editor']` on all sessions
- `template/tests/infrastructure/test-infrastructure.spec.ts` — `fixtures-infrastructure` import
- `copier.yml` — exclude `src/components/sse` when `use_sse=false`
- `template/knip-template-ignore.json` — added `src/components/sse/**`

**Migration steps:**
1. Run `copier update` on the frontend — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Backend v0.11.0

### Backend: Reverse proxy support (ProxyFix + Waitress trusted_proxy)

**What changed:** The backend now correctly handles `X-Forwarded-*` headers from reverse proxies (nginx, ingress controllers, etc.):

1. **`ProxyFix` middleware** added at the end of `create_app()`. Rewrites `request.remote_addr`, `request.url_root`, and `request.scheme` from `X-Forwarded-For`, `X-Forwarded-Host`, and `X-Forwarded-Proto` headers respectively. Configured with `x_for=1, x_host=1, x_proto=1`.

2. **Waitress `trusted_proxy` settings** added to production server startup. Configures Waitress to trust proxy headers from any upstream (`trusted_proxy="*"`, `trusted_proxy_count=1`) and passes `x-forwarded-for`, `x-forwarded-proto`, and `x-forwarded-host`.

3. **Debug logging in `check_authorization()`** — when a 403 is raised (no recognized role, or insufficient permissions), the user's roles, configured roles, and required roles are now logged at DEBUG level for easier diagnosis.

Backend template files changed:
- `template/app/__init__.py.jinja` — added `ProxyFix` import and middleware setup before `return app`
- `template/run.py` — added `trusted_proxy`, `trusted_proxy_count`, `trusted_proxy_headers` to Waitress `serve()` call
- `template/app/utils/auth.py` — added `logger.debug()` calls before both `AuthorizationException` raises in `check_authorization()`

**Migration steps:**
1. Run `copier update` on the backend — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-01 — Backend v0.10.0

### Backend: OIDC state in URL parameter + partitioned cookies (iframe support)

**What changed:** Two related improvements that allow the OIDC login flow to work inside cross-origin iframes (e.g. Home Assistant):

1. **State moved from cookie to encrypted URL parameter.** The PKCE auth state (code_verifier, redirect URL, nonce) is now encrypted with Fernet and carried as the OAuth `state` query parameter instead of a short-lived `auth_state` cookie. Third-party cookie blocking in cross-origin iframes would have silently dropped that cookie, breaking the callback.

2. **Partitioned (CHIPS) cookie support.** A new `OIDC_COOKIE_PARTITIONED` env var (default `False`) sets the `Partitioned` attribute on all auth cookies. When set alongside `SameSite=None; Secure`, this allows cookies to work in cross-origin iframes without being treated as third-party cookies.

3. **`get_cookie_kwargs()` replaces `get_cookie_secure()`.** A single helper now returns all common `set_cookie()` keyword arguments (httponly, secure, samesite, partitioned), keeping every call-site consistent.

4. **`itsdangerous` dependency removed.** Auth state is now encrypted with `cryptography.fernet` (already a dependency). `itsdangerous` is no longer in the OIDC dependency block.

Backend template files changed:
- `template/app/config.py.jinja` — added `OIDC_COOKIE_PARTITIONED` env var and `oidc_cookie_partitioned` setting
- `template/app/utils/auth.py` — `serialize_auth_state`/`deserialize_auth_state` use Fernet; `get_cookie_secure()` replaced by `get_cookie_kwargs()`
- `template/app/services/oidc_client_service.py` — added `create_auth_state()` and `build_authorization_url()` methods; `generate_authorization_url()` is now a convenience wrapper
- `template/app/api/auth.py` — login endpoint no longer sets `auth_state` cookie; callback reads encrypted state from `state` param; logout uses `get_cookie_kwargs()`
- `template/app/api/oidc_hooks.py` — uses `get_cookie_kwargs()`
- `template/app/api/testing_auth.py` — uses `get_cookie_kwargs()`
- `template/pyproject.toml.jinja` — removed `itsdangerous` from OIDC dependencies

**Migration steps:**
1. Run `copier update` on the backend — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes required.
3. **Optional:** To enable iframe embedding, set `OIDC_COOKIE_PARTITIONED=True`, `OIDC_COOKIE_SAMESITE=None`, and ensure your deployment uses HTTPS (`OIDC_COOKIE_SECURE=True` or `BASEURL=https://...`).
4. If your app has `itsdangerous` pinned in its `pyproject.toml` for other purposes, leave it. If it was only there for OIDC, you may remove it and run `poetry lock`.

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
