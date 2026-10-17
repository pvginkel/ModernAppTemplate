# DesignAssistant port: delivery plan

This plan delivers every ruling in [`da_port_decisions.md`](da_port_decisions.md), and moves the templates and all six apps from Poetry to uv on the way. It ships as **one push**: every phase commits locally, and nothing leaves this environment until phase 17. That works because each app's `.copier-answers.yml` points `_src_path` at the local template checkouts, so the apps update to template tags that haven't been pushed.

The six apps are ElectronicsInventory, IoTSupport, DHCPApp, ZigbeeControl, FieldnotesApp and PilotApp (see `CLAUDE.md`). DesignAssistant is archived and is **not** synced; its clone is reference material only.

The plan is written to be run **one phase per chat**. An agent asked to "make progress on the DA port plan" starts at "How to run a phase".

## How to run a phase

**Which phase.** The operator may name one. Otherwise take the first phase in the status table that isn't `done`, and check that every phase before it is `done`.

**Read before working:**

- `CLAUDE.md` and `docs/change_workflow.md` (the template change workflow).
- `docs/da_port_decisions.md`: the rulings, which are binding. Where this plan and a ruling disagree, the ruling wins; say so in the phase log.
- Each inventory item your phase names, in `docs/da_port_inventory.md` (search by ID). Each item cites DA files and commits.
- `docs/da_port_worklist.md` (phase 0's output). Skip items it marks as landed; for items marked partial, finish only the missing part.
- The phase log below. Earlier phases leave facts and deviations there.

**Reference material:**

- **DA clone:** `/work/scratch/DesignAssistant`, branch `main`. If it's missing, re-clone `https://github.com/pvginkel/DesignAssistant.git` into `/work/scratch/`.
- **Baseline renders:** `/work/scratch/da-base/{backend,frontend,portal}`. These are the template at DA's versions (backend v0.12.0, frontend v0.18.1), rendered with DA's answers. Their only use is diffing a DA change.
- **PilotApp's database-testing design:** `docs/pilotapp_database_testing_design.md`.

**Rules:**

- **Never push.** Phase 17 alone pushes, after the operator's go.
- **No tags** until phase 10.
- **Commit early, one commit per step,** in the repo you change (`backend/`, `frontend/`, this repo, an app, or a clone under `/work/scratch/`). A template commit includes the regen churn of the `test-app/` lockfiles and `.copier-answers.yml`.
- **Template changes go through `template/` → regen → gates.** Apps change only in phases 11–16, through `copier update` plus app-owned edits. Never apply a template change by editing an app's template-owned file. The one exception is resolving a conflict that `copier update` raises.
- **Gates:** after a template edit, run `kc project build`, then `kc project test` and `kc project lint`. Whenever a phase touches Playwright code or what it starts (backend test server, SSE gateway, frontend), also run the Playwright suite by hand:
  - `cexec modern-app sh -c 'cd root/test-app && <runner> run-suite --suite frontend'`, where `<runner>` is `poetry run`, or `uv run` from phase 1 on.
  - It can push the modern-app container to its 5 GiB limit, so cap the workers if it struggles.
- **Sub-agents:** use them for wide reading, per the environment's `CLAUDE.md`. Do the implementation yourself, and review every diff a sub-agent makes.

**Stop and notify the operator** (with the `notification` tool) when:

- a finding contradicts a ruling;
- a gate fails and the fix lies outside the phase's scope;
- the phase would need something only the operator can do.

Record the stop in the phase log, and leave the phase `blocked`.

**Close the phase:**

1. Set its status row to `done`, with the date and the commits per repo.
2. Add a phase log entry with anything later phases need: facts, deviations, deferred bits and changed commands.
3. Commit this file in the parent repo.
4. Notify the operator in one line.

## Status

| # | Phase | Status | Commits |
|---|---|---|---|
| 0 | Dedup and facts | done 2026-10-17 | parent `7cb4426` |
| 1 | uv everywhere, dependency bumps | done 2026-10-17 | backend `5cbec2a`, `7353261`; frontend `f3dfb72`; parent `7b06a55`, `23459f1` |
| 2 | Backend: PostgreSQL testing | done 2026-10-17 | backend `6a2d04e`, `a29fd98`, `c9fba33`; parent `241d216` |
| 3 | Backend: fixes, stages, internals fact | done 2026-10-17 | backend `5e7552c`, `c5e3c97`, `a6537f5`, `0f25bc3`, `fd86f68`, `fa492c6`, `76ece1f` (reverted by `625c644`), `d70dfe9`, `6c4de17`, `15621ef`, `a77da81`, `dccf055`, `1f2df1f`; parent: this entry |
| 4 | Backend: auth | done 2026-10-17 | backend `7db254c`, `997ea1f`, `c3b8607`, `a84795a`; frontend `fbf00f9`; parent `e2064d4`, `670d8d8`, this entry |
| 5 | Backend: readiness, SSE, small takes | in progress: step 1 and BE-T10, BE-T11 done | backend `f129198`, `b224b4f`; parent `d4dc992`, this entry |
| 6 | Frontend: fixes, Playwright on PostgreSQL | todo | |
| 7 | Frontend: stages, SSE, defaults | todo | |
| 8 | Root: CI, images, dev stack, architecture, tooling | todo | |
| 9 | Conventions guide and skill | todo | |
| 10 | Release | todo | |
| 11 | App: IoTSupport | todo | |
| 12 | App: ElectronicsInventory | todo | |
| 13 | App: DHCPApp | todo | |
| 14 | App: ZigbeeControl | todo | |
| 15 | App: FieldnotesApp | todo | |
| 16 | App: PilotApp | todo | |
| 17 | The push | todo | |

## Phase log

*(Phases append here: date, phase, then the facts, deviations and commands later phases need.)*

### 2026-10-17, phase 0: dedup and facts

- **Output:** [`da_port_worklist.md`](da_port_worklist.md). Every later phase reads its "Plan corrections" (16 items) as well as its own §1 rows. The corrections change these phases' steps: 2, 3, 5, 6, 7, 8, 12, 15, 16 and 17.
- **Deviation:** phase 8 step 4 takes the estate's `Jenkinsfile.architecture` on `architectureProducer`, not DA's files, and ships no `scripts/arch-validate.py` (correction 1, operator question 3). Phases 11–16 drop their architecture-YAML step, because all six apps are already producers.
- **Gap filled:** phase 2 ships `backend/scripts/wait-for-services.py` (correction 3).
- **For phase 1:**
  - The proposed copier command for syncing an app is `cexec modern-app uv run --project /work/ModernAppTemplate/backend copier update --trust --defaults`, run from the component's directory. Confirm it on a real update and record the result here.
  - Pin `copier==9.11.3` before the bumps.
  - The CI toolchain image already has uv.
  - §3 lists every Poetry use.
- **Open for the operator:** D2 lockouts in IoTSupport, DHCPApp and ZigbeeControl; `HOMELAB_INTERNAL` on the public hosts; D8's means; PilotApp slice 002; MAT-12. None blocks phases 1–10.
- **Read-only clones in `/work/scratch/`,** untouched: `JenkinsPipelineUtils`, `DockerImages`, `HomelabAppsDeploy`, `DevGuides`, `KubeCoderConfig`, `Architecture`, and the six deploy repos under `deploy/`. Phases 8, 9 and 11–16 can commit in them. Pull each one first.
- **kubectl:** this environment has no `iac` tool container, so no `kubectl`. Phase 17 watches Argo CD syncs, so add `iac` to `.kubecoder/config.yaml` before it and use `cexec iac kubectl --context prd …`.

### 2026-10-17, phase 1: uv everywhere, dependency bumps

- **The copier command for syncing an app,** run from the component's directory (`/work/<App>`, `backend/`, `frontend/`):

  ```bash
  cexec modern-app uv run --project /work/ModernAppTemplate/backend --locked copier update --trust --defaults
  ```

  Verified on a scratch clone of IoTSupport: run from its `backend/`, a directory with its own Poetry `pyproject.toml`, it updated v0.13.2 to v0.13.3. `CLAUDE.md`, `change_workflow.md` and `downstream_sync_process.md` carry it.
- **copier** is pinned `==9.11.3` in `backend/pyproject.toml`, the backend repo's own uv project. The frontend repo and this repo no longer have a Python project: `frontend/regen.sh` runs `uv run --project ../backend --locked copier`. The apps' own dev groups still list `copier>=9,<10` (9.19.1 today), which no sync uses.
- **Gate commands:** `kc project build|test|lint` are unchanged and run `uv run` underneath. Playwright, by hand:
  - `cexec modern-app sh -c 'cd root/test-app && uv run run-suite --suite frontend --frontend-args="--workers=1"'`. At the default 2 workers the full run took the modern-app container down (`cexec: could not reach the modern-app tool (EOF)`).
  - `worker-isolation.spec.ts` assumes two backends. At 1 worker it failed in one of two runs. Run it alone at 2 workers as well: `… run-suite --suite frontend --frontend-args="tests/e2e/parallel/worker-isolation.spec.ts"`.
- **Bumps (BE-C08), ruled majors only:** spectree 2.0.3, flask-cors 6.0.5, Pillow 12.3.0, pytest 9.1.1, pytest-cov 7.1.0, ruff 0.15.22, types-flask-cors 6; types-pillow dropped. Newer majors exist (spectree 3, Pillow 13, ruff 0.17) and were not taken. Spectree 2 and flask-cors 6 needed no code change. pytest 9 needed no `pythonpath`. Ruff 0.15 re-sorted `alembic.config`/`alembic.script` in `database.py`, as in DA. The root template pins `ruff==0.15.22`.
- **For phases 11–16 (app-owned, by hand):**
  - `backend/pyproject.toml`: `spectree>=2.0.0,<3`, `flask-cors>=6.0.0,<7`, `pillow>=12.0.0,<13` (S3 apps), `ruff>=0.15.0,<0.16`, `pytest>=9.0.0,<10`, `pytest-cov>=7.0.0,<8`, `types-flask-cors>=6.0.0,<7`; drop `types-pillow`.
  - Root `pyproject.toml`: `ruff==0.15.22`.
  - Ruff 0.15 may re-sort imports in app-owned files (`uv run ruff check --fix`). The Pillow typing fix arrives with `copier update`; app-owned code that reassigns `img = img.convert(...)` needs the same change.
  - The template's `project.yaml.jinja` runs `uv sync` without `--locked`, because a new app has no `uv.lock` until its first setup. The existing apps' `project.yaml` is app-owned, so PilotApp's `--locked` form is fine for them.
- **Deferred:**
  - The changelog entries: phase 10 writes them. The migration steps are worklist §3 "App-owned packaging" plus the bump list above.
  - `Jenkinsfile.jinja` only swapped its install and run lines; phase 8 replaces the file.
  - `CLAUDE.md` (the downstream-apps table) and `downstream_sync_process.md` (the sync-status rows) still call FieldnotesApp and PilotApp "on uv, not Poetry". The FieldnotesApp row also says to move the template to uv at its first sync. Phases 15 and 16 rewrite those rows.
- **Small choices:** `regen.sh` (backend, root) exports `UV_LINK_MODE=copy`, and the backend repo sets `link-mode = "copy"`, because the sidecar's uv cache and `/work` are different mounts. `scripts/test_all.py` runs `uv sync` without `--locked`, so a stale lock is re-locked, as Poetry's retry did.

### 2026-10-17, phase 2: backend PostgreSQL testing

- **Deviation: the Playwright SQLite seed stays until phase 6.** `initialize-sqlite-database.sh`, `testing-server.sh --sqlite-db` and the SQLite branch of `upgrade_database(recreate=True)` are still in the template, used only by Playwright's global setup. Removing them now would leave the Playwright suite red until phase 6, and phases 3–5 (auth, SSE) need it as a gate. Phase 6 removes all three with FE23, plus `copier.yml`'s exclude line for the script. pytest uses no SQLite.
- **What the fixtures are now** (`tests/conftest_infrastructure.py`, `use_database`):
  - `run_databases` (class `RunDatabases`), session-scoped: sweeps, then builds `<database_name>_test_<8 hex>_tpl` from `template0` in production's locale, with `upgrade_database()` and `post_migration_hook`. `clone(name)` and `drop(url)` serve the other fixtures. A run holds one admin connection named after its prefix (`application_name`); the sweep skips live runs and any database with connections, and drops without `FORCE`. The run drops its own databases `WITH (FORCE)` at the end.
  - `app`, session-scoped, on `<run>_main`. `session`: savepoints in a transaction rolled back at teardown; only `close()` is a no-op. `container` makes `session_maker` return it; `client` depends on `container`; `oidc_app` (same database, OIDC on) gets the test session too.
  - `committed_app`: a clone of its own with real commits, dropped afterwards.
  - The autouse `session_app_isolation` re-wires `app.api` to the session app when another app took the wiring (checked through dependency-injector's registry, so a re-wire, ~15 ms, happens only when needed), and undoes provider overrides a test leaves on the container.
  - `test_settings` and `test_app_settings` are session-scoped with a database. `clear_prometheus_registry` is opt-in with a database; every app the fixtures build clears the registry first. pytest loads `.env`, then `.env.test` over it.
  - No-database apps keep the function-scoped app and the autouse registry clear.
- **New template-owned files:** `tests/test_database_schema.py` (the database is at the Alembic head; `compare_metadata` finds no drift; passes on an app without revisions) and `scripts/wait-for-services.py` (correction 3: a login on `TEST_DATABASE_ADMIN_URL`, its default if unset, and an HTTP answer from `S3_ENDPOINT_URL` if set; 60 s). The root suite runner already calls the script; phase 8 needs no change for it.
- **BE-C18 (correction 14):** `TEST_DB_POOL_SIZE = 2` and `TEST_DB_POOL_MAX_OVERFLOW = 3` in `app/config.py`. `Settings.load()` takes them under `FLASK_ENV=testing` unless `DB_POOL_SIZE` or `DB_POOL_MAX_OVERFLOW` is set (each on its own, via `model_fields_set`). The Playwright backends therefore get the small pool without any `DB_POOL_*` in `servers.ts` (phase 6). The pool tests (`TestTestModePool` in mother `test_config.py`) were written now: **phase 3's BE-T15 skips its pool part.**
- **BE-C09 and correction 5:** `testing-server.sh` takes `--database-url`, sources `.env.test` (the app reads `.env` itself), lets the flag win over `.env.test`, and execs `uv run dev`. `run.py` runs `app.run(..., use_reloader=False)` and has no `WERKZEUG_RUN_MAIN` branches, so **the dev stack has no auto-reload until phase 5's `watchmedo` and phase 8's `Procfile.dev`.** `Settings.set_engine_options_override()` is gone; no app calls it.
- **Mother suite:** `backend/tests/conftest_infrastructure.py` is a symlink to `test-app/tests/conftest_infrastructure.py`, so the mother suite runs on the rendered template fixtures and `tests/conftest.py` holds only the SSE fixtures (`sse_server` on its own clone; `tests/integration/conftest.py` wires the SSE app during those tests). New: `test_database_fixtures.py` (savepoint semantics, isolation, `committed_app`, the sweep) and `test_database.py` (`upgrade_database`, including `recreate=True`, on PostgreSQL). Counts: mother 357, domain 9; Playwright green at one worker, and `worker-isolation.spec.ts` alone at two (peak 5,368 MB, at the container's limit).
- **For phase 3:** BE-C05 changes `DiagnosticsService`'s metrics, which register in its constructor; its mother tests request `clear_prometheus_registry`. `drop_all_tables()` empties `db.metadata` (harmless in the CLI's one-shot process; `test_database.py` stubs it). BE-C02 may want to stop that too.
- **For phase 6:** use a prefix of its own (for example `<database_name>_e2e_`): the pytest sweep only touches `<database_name>_test_`. Start from `testing-server.sh --database-url`; the template DB clone and locale are in `RunDatabases` as a model.
- **For phases 11, 12 and 16 (the database apps), in `tests/conftest.py` and app-owned tests:**
  - Overrides of `test_settings` and `test_app_settings` must be `scope="session"` (pytest raises `ScopeMismatch` otherwise): `tmp_path` becomes `tmp_path_factory` (IoTSupport's `test_app_settings`), and `database_url="sqlite..."` goes (IoTSupport's `test_settings`). `_build_test_settings` stays importable by name (EI).
  - `template_connection` is gone. EI's `sse_server` and IoTSupport's `testing_template_connection` rebuild on `run_databases.clone()` or `committed_app`; tests that call `create_app()` themselves get the wiring restored at the next test, but need a database from those fixtures.
  - The session app keeps in-memory state across tests: a test that sets a lifecycle flag, config value or service state undoes it (`monkeypatch`). Overrides on the container are undone automatically.
  - Tests that construct services registering their own metrics request `clear_prometheus_registry`.
  - Writes through Flask-SQLAlchemy's `db.session` are not on the test's session and commit for real into `<run>_main`: move them to `session` (EI's `test_database_constraints.py`, 143 uses).
  - Sequences are not rolled back, so literal IDs in asserts fail (EI's `box_no` asserts, worklist §5).
  - Every database app now runs the drift test; models and revisions must match (EI's `with_variant(..., "sqlite")` columns).
  - Nothing to set in `.env.test`: the default `TEST_DATABASE_ADMIN_URL` is the sidecar. CI needs the `postgres` service (phase 8).

### 2026-10-17, phase 3: backend fixes, stages, the internals fact

- **Deviations:**
  - **BE-C10 skipped (reverted, `625c644`).** The root `.gitignore` already ignores `.env*` under `backend/`, so the change did nothing in a monorepo. In this repo, `template/.gitignore`'s `.env*` also matched `template/.env.example.jinja`. A dirty regen re-adds the template with `git add -A`, so it silently dropped the file. Keep patterns in `template/.gitignore` from matching template source names.
  - **BE-C03:** the template's `after_commit()` stays the only mechanism; DA's `session_hooks.py` was not taken. `app.database.scoped_session` runs the callbacks after its own commit and always clears them, and `BaseSessionTask` runs on it.
  - **BE-C04:** `scoped_session` and `scoped_savepoint` live in template-owned `app/database.py`, not in `container.py` (app-owned), because template code calls them.
  - **BE-C05:** a request that matched no route is labelled `endpoint="unknown"`. `DiagnosticsService` used `request.path`, which let scans grow the label set. The histogram keeps its name, labels and buckets. `DiagnosticsService.request_duration_seconds` is gone (no app references it).
  - **BE-C16 brought a fix:** the `Exception` catch-all turned every Werkzeug HTTP error without its own handler (413, 415 and so on) into a 500. A new `HTTPException` handler returns their own status.
  - **Two fixes outside the items:** `alembic/env.py` calls `fileConfig(..., disable_existing_loggers=False)`, because every in-process migration (pytest's included) silenced the app's existing loggers. `drop_all_tables()` no longer empties `db.metadata` (phase 2's note).
  - **S6's open question, settled:** `HOMELAB_INTERNAL` is a deploy setting (env var, default false), not a copier answer.
- **What phase 3 added** (backend template):
  - `Stage` (`is_local()`, `is_env()`, `.value`), `STAGES`, `default_stage()` and `Settings.stage` in `config.py`. Unset, `STAGE` is `local-tst` under testing, `local-dev` under development, and `prd` for any other `FLASK_ENV` (correction 8). `Settings(...)` built directly gets the same default from its `flask_env`.
  - `Settings.homelab_internal`, and `Settings.expose_internals` (true when `STAGE` is not `prd`, or when `HOMELAB_INTERNAL` is set).
  - The 500 catch-all shows `str(error)` only when `expose_internals` is true; otherwise "An unexpected error occurred". The correlation ID and the log keep the detail.
  - `GET /api/ui-setup` returns `{"stage": ..., "expose_internals": ...}` in snake_case (`app/api/ui_setup.py`, `app/schemas/ui_setup_schema.py`). It sits under `api_bp`, so the OIDC hooks apply: it needs a signed-in user, at the read tier.
  - Readyz carries `"stage"`. `HealthResponse.stage` is optional, because healthz has none.
  - `FrontendVersionService._on_connect_callback` sends no fetched version in a local stage; a queued (pending) one still goes. The template sends on connect, where DA broadcast at startup.
  - The `prd` guards: `upgrade-db --recreate` and `load-test-data` refuse with exit 1, and `reject_if_not_testing()` refuses on `STAGE=prd` even under `FLASK_ENV=testing`. A plain `upgrade-db`, which every deploy repo's init container runs, is unaffected.
  - The settings dump: `Sensitive` marks (`secret_key`, `drain_auth_key`, `database_url`, `oidc_client_secret`, `s3_access_key_id`, `s3_secret_access_key`, `sse_callback_secret`), `dump_config_for_logging()` and `Settings.dump_for_logging()`; the latter shows the database URL with only its password masked. `run.py` logs every setting at boot. It dumps `AppSettings` only when the app's class has `dump_for_logging()`.
  - Logging: `LOG_LEVEL` sets the root level (unknown names mean INFO), and `app/utils/log_formatter.py` holds `ExtraFieldFormatter` and `resolve_log_level()`.
  - `MAX_UPLOAD_SIZE_MB` (default 50) becomes `MAX_CONTENT_LENGTH`. `allow_empty` column info opts a column out of empty-string normalization.
  - `LifecycleCoordinatorProtocol.unregister_lifecycle_notification` is a new abstract method. The log stream's `connection_close` event is gone.
  - MAT-13: the CLI's "Using database" line masks the password.
  - Mother suite: 357 → 459 tests. BE-T04 is in `tests/test_task_service_internals.py`; BE-T05 and BE-T14 are appended to the existing files; BE-T15's pool part was phase 2's.
- **Settings and edits the apps need (phases 11–16), all by hand:**
  - **Deploy repos:** `STAGE=prd` (unset already means `prd`, but state it), and `HOMELAB_INTERNAL=true` where operator question 2 says.
  - **App-owned `.env.example`:** add `STAGE` (commented), `HOMELAB_INTERNAL`, `LOG_LEVEL` and `MAX_UPLOAD_SIZE_MB`. The dev `.env` needs no `STAGE`, because `FLASK_ENV=development` gives `local-dev`.
  - **Upload limit:** EI's `MAX_FILE_SIZE` is 100 MB, but nginx already caps bodies at 50 MB. EI sets `MAX_UPLOAD_SIZE_MB` only if it raises both.
  - **App-owned `app_config.py`:** to get the `AppSettings` dump, add `dump_for_logging()` (`return dump_config_for_logging(self)`) and mark secrets `Annotated[str, Sensitive]`. EI's `OPENAI_API_KEY` and `MOUSER_SEARCH_API_KEY` are examples. Without the method there is no dump, so no secret leaks.
  - **EI and IoTSupport's own `tests/testing_utils.py`:** `StubLifecycleCoordinator` needs `unregister_lifecycle_notification`.
  - **EI `services/metrics/dashboard_metrics.py:124` and IoTSupport `services/coredump_service.py:443`:** they reset without closing; move them to `app.database.scoped_session`.
  - **FieldnotesApp:** it reads its own `FIELDNOTES_LOG_LEVEL`/`LOG_LEVEL` (`app/fieldnotes/config.py:319`), and `run.py` now applies `LOG_LEVEL` to the root logger. Phase 15 reconciles the two.
  - **App tests:**
    - On `local-tst` the 500 body still carries the exception text, so tests asserting on it pass.
    - A test that builds `Settings(flask_env="production")` now gets `stage == "prd"` and no exception text.
    - Tests that read a version event on connect without queueing one first get nothing in a local stage.
- **For phase 4:** the 403 from D2 will also hit `/api/ui-setup` for a role-less user, and phase 7 must treat it as "no badge, no diagnostics".
- **For phase 5:**
  - `_check_db_readiness` (`app/__init__.py.jinja`) now catches a failing `get_pending_migrations()` and reports `{"connected": true, "error": ..., "ok": false}`. D5's database check takes that over.
  - Keep `stage` in the reworked readyz, and keep the local-stage skip in BE-T12's version-service rewrite.
  - The two broadcast tests that correction 6 inverts are still in `tests/test_task_service.py`.
  - BE-T14's S3 health-check tests come with D5's S3 check.
- **For phase 7:** FE19 and FE32 read `GET /api/ui-setup` (`stage`, `expose_internals`) once the user is signed in.
- **For phase 8:** the dev stack needs no `STAGE`; seed `HOMELAB_INTERNAL` only if wanted. CI sets `STAGE=tst`, whose `expose_internals` is true.
- **For phase 10:** the changelog's migration steps are the list above, plus the readyz `stage` field, the `endpoint="unknown"` label, and 413 instead of 500 for oversized bodies.
- **Gates:** `kc project build`, `test` (mother 518, domain 9, root backend suite) and `lint` are green. Playwright at one worker passed twice (35 tests, a few skip outside preview mode).
  - `worker-isolation.spec.ts` alone at two workers failed once: worker 0's Vite process exited with code 1 before it was ready, and its backend was fine. It passed on the re-run at a 5,297 MB peak, against the container's 5 GiB limit.
  - The runner writes `test_results.md` details only for a failed step, so a green run shows no counts. `pnpm exec playwright test --list` gives the inventory.
- **Test gotcha:** don't assert on `spectree_config.api.spec` in the mother suite. Each `create_app()` makes a new SpecTree, and a spec lists only the routes its own instance decorated, which happened at the first app's import. So a later app's spec misses template routes.

### 2026-10-17, phase 4: backend auth

Backend `7db254c` (steps 1–2: BE-C01 and BE-C12 with BE-T09, plus BE-T05's `resolve_required_role` tests, which waited for BE-C01), `997ea1f` (step 3, BE-T16), `c3b8607` (step 5, BE-C25) and `a84795a` (step 4, BE-C15); frontend `fbf00f9` (step 4's dev proxy).

- **What the template has now** (`app/utils/auth.py`, `app/api/oidc_hooks.py`, `app/api/auth.py`, `app/api/tasks.py.jinja`, `app/services/oidc_client_service.py`):
  - **Roles.** `check_authorization` refuses a caller holding none of `configured_roles` before the per-tier lookup, so also on a GET when `read_role` is unset ("No recognized role -- access denied", 403). `@no_role_check` (attribute `is_no_role_check`) skips every role check; login, callback and logout carry it.
  - **Identity.** `resolve_auth_identity(token, auth_service, config, testing_service=None)` is the one identity path: a test session (testing mode, `test-session-` prefix, live session), else the local admin when OIDC is off, else the validated JWT, else `None`. It reads neither the request nor `g`. `authenticate_request(..., *, throw_on_error, testing_service=None)`: `throw_on_error` is keyword-only and required. Tolerant mode (`@public`) returns on an authentication failure without `g.auth_context`. An authorization failure raises in both modes, so a signed-in caller with no role gets 403 on a `@public` endpoint too. `g.clear_auth_cookies` is set only after a failed refresh. The hook body is the module-level `authenticate_api_request(auth_service, oidc_client_service, testing_service, config)` in `oidc_hooks.py`, which returns `None` or the 401/403 tuple. Constants `LOCAL_USER_SUBJECT` and `TEST_SESSION_PREFIX` are in `app/utils/auth.py`.
  - **Auth endpoints.** `/api/auth/logout` sets `g.clear_auth_cookies`; `after_request_set_cookies` alone clears the cookies, so a refresh made on the way in can't put them back. `/api/auth/self` reads `g.auth_context` and keeps the forced-error hook.
  - **Task owners (BE-T16).** `GET /api/tasks/<id>/status`, `POST .../cancel` and `DELETE /api/tasks/<id>` serve only the caller whose subject equals `TaskInfo.subject`; anyone else gets the unknown-id 404 body, and nothing is cancelled or removed. The role tiers apply first (status at read, cancel and delete at write). With OIDC off, the local admin (`local-user`) owns every task, those without a subject included. With OIDC on, a task without a subject belongs to nobody, admins included, matching correction 7. A test session under OIDC off owns only its own tasks, and a JWT with `sub=local-user` owns nothing. `tasks.py` became `tasks.py.jinja` (helpers `_caller_owns`, `_find_caller_task`); with `use_oidc=false` the render is unchanged.
  - **Role hierarchy (BE-C25).** `AuthService(..., role_hierarchy=None)`, a `role_hierarchy` property (a copy of the input), and `x-auth-roles.hierarchy` in the OpenAPI spec, `{}` when off. The frontend's `generate-api.js` reads only `x-auth-roles.read`. The app-owned `container.py.jinja` is unchanged; an app that wants a hierarchy passes it to `AuthService` in its own container.
  - **Redirect origin (BE-C15).** Login builds `redirect_uri` from `get_request_origin()` (`request.scheme://request.host`, after `ProxyFix(x_proto=1, x_host=1)`) and stores the origin in the encrypted state as `AuthState.origin`; the callback's token request uses the stored one, or `BASEURL` for a state without it (made by the old code, which used `BASEURL`; states expire after 10 minutes). Logout's `post_logout_redirect_uri` is the request origin plus the path. `validate_redirect_url(redirect_url)` accepts only a path on this origin: it must start with one `/`, and backslashes and control characters are refused, because browsers turn both into `//host`. Signatures: `create_auth_state(redirect_url, origin)`, `build_authorization_url(auth_state, state_value, origin)`, `exchange_code_for_tokens(code, code_verifier, origin)`, module-level `callback_uri(origin)`. `generate_authorization_url` is gone (nothing called it). `BASEURL` now only infers `OIDC_COOKIE_SECURE`, plus that fallback.
  - **Dev proxy (frontend).** `vite.config.ts.jinja`'s `/api` proxy, in `server` and `preview`, has `configure: forwardOrigin`: it sends `X-Forwarded-Host` (the browser's `Host`) and `X-Forwarded-Proto: http` unless a proxy in front already set them, the rule nginx's `proxy.conf` follows. Checked against an echo backend through the Vite dev server: direct, the backend sees `X-Forwarded-Host: 127.0.0.1:3998` and `http`; with an upstream `X-Forwarded-Proto: https`, that value is kept.
- **Deviations from DA:**
  - **Tolerant mode reads the access token from the cookie only,** never the Authorization header. IoTSupport's `/api/iot/*` endpoints are `@public` and validate device JWTs with the same `AuthService` (`app/utils/device_auth.py:94`); in DA's form the hook would validate the device token itself and answer 403 to every device, since devices hold none of the app's roles. FieldnotesApp's client bearer tokens stay the endpoint's business the same way. Throwing mode still reads the header (IoTSupport's `pipeline` tokens). So `/api/auth/self` no longer accepts a bearer token.
  - **With OIDC off, every `/api` request carries the local admin in `g.auth_context`** (subject `local-user`), exempt from role checks. DA, like the template before, set it only for its `seed_user`. Test sessions under OIDC off are still role-checked.
  - `/api/auth/self` lost its `hierarchy_roles` check; the hoisted check covers it, with `configured_roles`. A caller holding only an additional role (IoTSupport's `pipeline`) now gets 200 there instead of 403. It could already read every GET.
  - **BE-C25:** the tier chain and the hierarchy form one graph, and cycle detection and the closure run over both. So `{"editor": ["portal"]}` gives an admin `portal` too, where DA's one-step lookup left admins without it, and `{"reader": ["editor"]}` is rejected as a cycle, where DA accepted it and let every reader write. The cycle error names the path.
  - **BE-C15:** DA's check let `/\evil.com` through and accepted a path without a leading slash, which its logout glued onto the origin (`https://app.example.com` + `.evil.com`). The template refuses both.
  - **The dev proxy takes FE12's forwarded-headers part now, in another form.** DA and IoTSupport set `xfwd: true`, which appends this hop's `http` to `X-Forwarded-Proto`; ProxyFix reads the last value, so behind the KubeCoder front door (`sslOffload`, TLS at the edge) the backend would build `http://` redirect URIs.
- **Production path, checked; FE13 stays in phase 6.** The prd edge's shared snippet (`nginx-prd`, configmap `nginx-configmap-snippets`, `proxy.conf`) sends `Host $host` and `X-Forwarded-Proto $scheme`, and no `X-Forwarded-Host`. The app's nginx keeps that `X-Forwarded-Proto` and sends `Host $host`, so the backend sees `https://<public host>`: right on port 443. FE13 (`$http_host`) wouldn't change that, and couldn't restore a port the edge already stripped. That the KubeCoder front door sends `X-Forwarded-Proto` as well is assumed, not seen.
- **Tests:** BE-T09 in `tests/utils/test_resolve_auth_identity.py` and `test_authenticate_request.py` (DA's tolerant, throwing and helper cases, plus cookie-only and OIDC-off ones), with end-to-end cases appended to `tests/api/test_auth_middleware.py` and `test_auth_endpoints.py`, and hoist and `@no_role_check` cases in `tests/utils/test_auth_utils.py`. `tests/api/conftest.py` adds `roles_oidc_app`/`roles_oidc_client` (`write_role="editor"`, `additional_roles=["pipeline"]`, no `read_role`). BE-T05: the seven `resolve_required_role` cases in `tests/services/test_auth_service.py`; the redirect tests as `TestRedirectOrigin` in `test_auth_endpoints.py`, `TestValidateRedirectUrl` and origin round-trips in `test_auth_utils.py`, and `TestBuildAuthorizationUrl` in `test_oidc_client_service.py`. BE-T16: `TestTaskOwnership` in `tests/test_task_api.py` (9). BE-C25: `tests/services/test_auth_role_hierarchy.py` (31: DA's expansion, validation, cycle and property cases, plus the tier chain, role checks, `x-auth-roles` and `/api/auth/self`; DA's portal-endpoint and role-map cases are DA-specific).
- **Gates:** `kc project build`, `test` (mother 518 → 656, domain 9, root backend suite) and `lint` are green after the last step. Playwright ran after steps 1–2 and after step 4, green both times: at one worker (peaks 3,302 and 3,374 MB), and `worker-isolation.spec.ts` alone at two workers, first time (5,343 and 5,345 MB). Steps 3 and 5 skipped it: nothing in the frontend calls `/api/tasks/*` or reads `x-auth-roles.hierarchy`.
- **For phase 5:**
  - The SSE connect callback (`app/api/sse.py.jinja` `_bind_identity`) still validates the forwarded token by itself and sees no test sessions. BE-T11 can call `resolve_auth_identity` with the token from the forwarded headers.
  - Keep the SSE rule and the REST rule the same: a task's events go to its subject, plus `local-user` with OIDC off (the subject an endpoint passes to `start_task` there, and correction 7's sentinel), and to nobody when there is no subject with OIDC on.
  - `/api/testing/tasks/start` (`api/testing_sse.py`) sits on its own blueprint outside `api_bp`, so the OIDC hooks never run there: `get_auth_context()` is always `None` and its tasks have no subject. Under OIDC on their events go to nobody once correction 7 lands, and the task endpoints already refuse them.
  - `start_task`'s docstring still says a `None` subject broadcasts; BE-T10 rewrites that.
- **For phase 6:** FE12 must not add `xfwd: true` to the `/api` proxy; `forwardOrigin` is that part. `/api/sse` can take `configure: forwardOrigin` too, if the gateway's callbacks ever need the origin (they don't today), but then `configureSseProxy` and it share the one `configure`.
- **What apps must check (phases 11–16):**
  - **Role configuration (D2).** The lockouts in worklist §5: IoTSupport, DHCPApp, ZigbeeControl, and FieldnotesApp's `GET /api/tasks/<id>/status`. A signed-in user with none of the app's roles gets 403 everywhere, app-owned `@public` endpoints called from the browser with the session cookie included. Endpoints called with a bearer token only (IoTSupport's devices, FieldnotesApp's clients) are unaffected, and IoTSupport's `device_log_stream.py` already ignores the caller with OIDC off. EI's `tests/test_role_based_access.py` calls `check_authorization` directly: a caller with none of the configured roles now gets "No recognized role" before any per-tier check. `role_hierarchy` is opt-in and no app needs it; each app's OpenAPI spec gains `x-auth-roles.hierarchy: {}`.
  - **IdP redirect URIs per hostname.** Each hostname a browser signs in on needs `https://<host>/api/auth/callback` as a valid redirect URI and its paths (`https://<host>/*`) as valid post-logout redirect URIs on the app's IdP client; before, both came from `BASEURL`. The deploy hosts: IoTSupport `iot.ginbov.nl`, EI `parts.ginbov.nl`, DHCPApp `dhcp.home`, ZigbeeControl `z2m.webathome.org`, FieldnotesApp `fieldnotes.home` (check whether `fieldnotes-api.home` or the others serve the UI), PilotApp `pilot.ginbov.nl`. A dev environment with OIDC on signs in on its frontend port's front door, `https://frontend.<env-id>.home` where that port is named `frontend`. After deploying, check that the login's `redirect_uri` reads `https://<host>/...`. Keep `BASEURL` set: it still infers the cookie's `Secure` flag.
  - **Redirect parameters:** `redirect` on login and logout must now be a path; an absolute URL, even on the app's own origin, gets 400. All six frontends send `pathname + search` to login and nothing to logout, so nothing changes for them.
  - **IoTSupport's `vite.config.ts`** (template-owned) has `xfwd: true` on `/api` and `/api/sse`. Drop it at the sync: on `/api` it would put `https,http` in `X-Forwarded-Proto` and break the dev login's redirect URI.
  - **Task endpoints** serve only the task's owner. No app frontend and no Playwright spec calls them; they appear only in generated hooks. The worklist's note that FieldnotesApp's UI polls `GET /api/tasks/<id>/status` does not hold: its frontend has no such call, and the actioner's task id (`actioner.py:491`) never reaches a client. EI's `ai_parts.py:124,258` tasks have no subject, so under OIDC on their task endpoints answer 404 to everyone until phase 12 passes `caller_subject`. App tests that start a task as one subject and call the endpoints as another, or start one without a subject under OIDC on, now get 404. FieldnotesApp's `tests/test_sse_identity.py` uses a task id that doesn't exist, so it is unaffected.
  - **FieldnotesApp's `app/api/oidc_hooks.py` conflicts** (phase 15). Its `authenticate()` copy of the old hook body goes. If the FN-38 binding stays, its hook calls `authenticate_api_request(...)` and then binds. An old body kept by mistake fails at its first request, because `throw_on_error` is required. Its `_editor()` (`api/inbox.py:49`) now gets `local-user` with OIDC off instead of `None`.

### 2026-10-17, phase 5, step 1: readiness

Backend `f129198` (D5: BE-C13, BE-T13, and BE-T14's S3 check tests). The root and frontend templates are unchanged: no repo holds a probe, and every consumer outside the backend reads only the status code.

- **The readyz format change** (`GET /health/readyz`):
  - Before: `{"status": "ready"|"not ready"|"shutting down", "ready", "stage", "<check>": {..., "ok"}}`, 503 when any check failed.
  - Now: `{"status", "ready", "stage", "checks": {"<check>": {"status": "ok"|"error"|"disabled", "critical": bool, "detail"?: str}}}`. `status` is `ok` (everything passed), `degraded` (a non-critical check failed; 200), `not_ready` (a critical check failed; 503) or `shutting_down` (503, `checks` empty, no check runs). `ready` is false exactly when the answer is 503. `disabled` means "deliberately not configured" and never fails. `detail` is absent when there is nothing to say.
  - The checks: `database` (critical; `detail` is `connection failed`, `N migrations pending`, or the migration lookup's exception text), `s3` (critical, `head_bucket` on the bucket) and `sse_gateway` (not critical; `gateway readyz answered N`, or the request's error).
  - Healthz is `{"status": "alive", "ready": true}`, always 200. `HealthResponse` (healthz, drain) lost `stage`; readyz has its own `ReadyzResponse` and `ReadinessCheckSchema` in the OpenAPI spec.
- **The API** (`app/services/health_service.py`): `register_check(name, check, *, critical, timeout=0.8)`, where `check()` returns `CheckResult(CheckStatus.OK|ERROR|DISABLED, detail=None)` and an exception it raises is the check's error. Registering a name again replaces the check. `clear_cache()` makes the next readyz run every check. `register_readyz` and `register_healthz` are gone; no template code and no app used `register_healthz`.
- **Who registers what.** `S3Service.startup()` registers `s3` and `SSEConnectionManager.__init__` registers `sse_gateway`, each given an optional `health_service` that the container passes. The container passes it to the manager only with `use_sse`, because the manager exists without SSE. The database has no service: `create_app()` sets it up and registers `app.database.check_readiness`, which takes over `_check_db_readiness`. The pytest apps skip background services, so their readyz checks only the database; dev, prd and the Playwright backend register all three.
- **Deviations from DA:**
  - **The `critical` flag** (D5). DA failed readiness on any error.
  - **Timeouts fit the probes.** All six apps' prd probes on `/health/readyz` have `timeoutSeconds: 1`, `periodSeconds: 3` and `failureThreshold: 3` (read from the prd cluster), so readyz waits at most 0.8 s per check by default, where DA waited up to 10 s with 5 s HTTP timeouts. A run that outlives its timeout reads `timed out after 0.8 s` and keeps going in its own daemon thread. Later requests wait on that run instead of starting another, and its result is cached when it passes, so a slow first check (a cold pool, Alembic reading its scripts) passes at the next probe. DA started a new pool per request, so a hung dependency added a thread per probe.
  - **Only passing results are cached** (30 s). A failure re-runs at every probe, so a recovery, the startup one included, shows within one probe period. DA cached failures too.
  - **Metrics and logs.** There is one histogram, `readiness_check_duration_seconds{check,status}`, per run and not per cache hit; its `_count` is DA's counter. A check's status change is logged (warning on failure, with the traceback when the check raised), and a repeat is not.
  - `ready` and `stage` stay. No OIDC-issuer check: the worklist drops DA's Keycloak case.
- **What apps must change (phases 11–16):**
  - **App-owned `container.py`:** move `lifecycle_coordinator` and `health_service` above `s3_service`, then pass `health_service=health_service` to `S3Service` (EI, IoTSupport) and to `SSEConnectionManager` (all six use SSE). Without the edit, readyz silently lacks `s3` or `sse_gateway`. `test-app-domain/app/services/container.py` shows the result.
  - **FieldnotesApp (phase 15)** changes `services/fieldnotes_service.py:78` from `register_readyz("store", self._readyz)` to `register_check("store", ..., critical=True)`. `critical=True` keeps today's 503. `_readyz` returns a `CheckResult`: `DISABLED` with no runtime (today's `configured: False`), `OK` when `runtime.ready`, otherwise `ERROR` with the failure in `detail`. In `tests/fieldnotes/test_api.py:37-40,48-51,73-75`, `json()["store"]` becomes `json()["checks"]["store"]` in the new shape. A test that reads a passing store and then expects a failure must call `health_service.clear_cache()` in between, since the passing result is cached for 30 s.
  - **Prose and messages that name the old body:**
    - EI `frontend/tests/smoke.spec.ts:33-62` builds its failure message from `payload.status` and `payload.migrations.pending`, which were already stale.
    - EI `.kubecoder/config.yaml:108` and IoTSupport `.kubecoder/config.yaml:15` say `database.connected`, which is now `checks.database.status`.
  - **App tests** that assert on the readyz body. A test of an app check must clear the cache or use a fresh `HealthService`.
  - Deploy repos need nothing: the probes read the status code only.
- **For the SSE chunk (step 2):** `SSEConnectionManager.__init__(gateway_url, http_timeout=5.0, health_service=None)` now registers the check, and `check_readiness()` is new. Keep both through BE-T10 and BE-T12. Their tests are `TestReadinessCheck` in `tests/test_sse_connection_manager.py`; `tests/test_health_api.py` builds managers with a `health_service`.
- **For phase 6:** the comment at `fixtures-infrastructure.ts.jinja:379` ("the gateway must be up before the backend can pass its readiness probe") no longer holds, because `sse_gateway` isn't critical. Starting the gateway first is still right, since it is awaited at its own readyz. The Playwright wait still checks `response.ok`, and readyz is now 503 only for the database or S3.
- **For phase 9 (RT15):** the rule for the skill is that a new external integration registers its own check with `register_check`, sets `critical` only when the app cannot serve without it, and keeps its own I/O timeout near the check's timeout. Nothing is written yet.
- **For phase 10:** the changelog takes the format change above, `register_readyz`/`register_healthz` → `register_check`, and the container edit.
- **Tests:** `tests/test_health_service.py` is new (24), with DA's registration, caching, isolation, shutdown, metrics, healthz and drain cases, plus critical against non-critical, `disabled`, timeouts, joined runs and uncached failures. `tests/test_health_api.py` is rewritten for the new body: database, SSE gateway and S3 through the session app, behind a fixture that sets aside checks other tests registered and clears the cache. BE-T14's check tests are `TestReadinessCheck` in `tests/test_s3_service.py` (4); the SSE manager's are in `tests/test_sse_connection_manager.py` (4).
- **Gates:** `kc project build`, `test` (mother 656 → 690, domain 9, root backend suite) and `lint` are green. Playwright passed at one worker (3,338 MB peak), and `worker-isolation.spec.ts` alone at two workers passed first time (5,283 MB peak).

### 2026-10-17, phase 5, BE-T10 and BE-T11: SSE targets, connect callback

Backend `b224b4f` (BE-T10 and BE-T11 together: the callback decides who is the local admin, and the targets depend on it). Corrections 6, 7 and 10 applied. The frontend and root templates are unchanged.

- **The `send_event` signature change** (`app/services/sse_connection_manager.py`):
  - Before: `send_event(request_id: str | None, event_data, event_name, service_type, target_subject: str | None = None)`. `None` broadcast to every connection; `target_subject` narrowed a broadcast to that subject plus every connection bound to the string `"local-user"`.
  - Now: `send_event(target: Target, event_data, event_name, service_type)`. There is no default and no `target_subject`. A request ID or `None` raises `TypeError`, so an old call fails loudly instead of misdelivering, and mypy flags every old call site.
  - The targets: `Target.connection(request_id)` (that connection); `Target.subject(subject)` (connections bound to that subject, plus the local admin's); `LOCAL_ADMIN_TARGET` (the local admin's connections only, so nobody with OIDC on); `BROADCAST_TARGET` (every connection, for infrastructure events only). `Target` is a frozen dataclass `(kind, value)`; the factories refuse an empty value, and there is no `Target.broadcast`.
  - The local admin is a flag on the binding: `bind_identity(request_id, subject, *, local_admin=False)`. The connect callback sets it for the local admin (OIDC off, no test session), and nothing else does. A connection bound to the subject `"local-user"` without the flag (a JWT with that `sub` under OIDC on) is an ordinary subject. This is the SSE form of `_caller_owns` in `api/tasks.py.jinja`.
  - `on_connect` clears the request ID's binding when a connection replaces another; a disconnect and a gateway 404 clear it too (the 404 path used to leave `_identity_map` behind).
- **Task events go to the caller** (`app/services/task_service.py`). `task_event_target(caller_subject)` gives `Target.subject(caller_subject)`, or `LOCAL_ADMIN_TARGET` for a task without a subject (correction 7: nobody with OIDC on, the local admin with OIDC off). `TaskProgressHandle(task_id, manager, target)` takes a required target, and `_broadcast_task_event` is now `_send_task_event(event, target)`. `start_task` still takes only `caller_subject`, so the task's owner (`TaskInfo.subject`) and its event target never differ. `/api/testing/tasks/start` sits outside `api_bp`, so its tasks have no subject: the mother integration tests receive them as the local admin, with OIDC off.
- **The other senders:** `FrontendVersionService` sends `Target.connection(request_id)` on connect and `BROADCAST_TARGET` from `queue_version_event`; `/api/testing/sse/task-event` sends `Target.connection(request_id)`.
- **The connect callback** (`app/api/sse.py.jinja`, started from PilotApp's `3f84260`). Order: callback secret (production), payload and `request_id` checks, then the testing hook, then the identity, then `on_connect` and `bind_identity`. So a refused connect is never registered, never counted in the connection metrics, and never reaches the `on_connect` observers.
  - The identity: `resolve_auth_identity(token, auth_service, settings, testing_service)` on the forwarded headers' token (Authorization header first, then the access-token cookie). A missing token under OIDC on, or an `AuthenticationException` (expired, bad signature, issuer, audience), answers 401 `{"error": "Unauthorized"}`. Other exceptions are a 500, as in the API.
  - The role check: `check_authorization(auth_context, auth_service, "GET")`, the rule the API applies to a GET. A caller with none of the configured roles, or one without the read role where the app sets `read_role`, gets 403 `{"error": "Forbidden"}`. The local admin skips the check; a test session is checked under OIDC off too (phase 4's rule).
  - The hook: `POST /api/testing/sse/force-callback-error?status=401|403` answers 204 and makes the next connect callback refuse with that status, whoever connects. It is single-shot, class-level state on `TestingService` (`set_/consume_forced_sse_callback_error`), consumed only when `settings.is_testing`. Any other status answers 400.
  - With `use_oidc=false` (no app has it), every connection is the local admin's.
- **Deviations:**
  - **From DA:** the target is required, where DA took `Target | None` with `None` meaning nobody. `LOCAL_ADMIN_TARGET` replaces DA's `Target.role("editor")` fallback. `Target.role`, `Target.workspace_events`, routing keys and `serialize`/`deserialize` are AMQP-only and not taken.
  - **From the worklist's BE-T11 note** ("replace `editor` with `configured_roles`"): the callback uses `check_authorization` for a GET. That adds the read tier; without a `read_role` it is the same rule.
  - **From PilotApp:** the hook endpoint is in `api/testing_sse.py` (rendered with `use_sse`), with `ForceSSECallbackErrorQuerySchema` in `schemas/testing_sse.py`, and not in `testing_auth.py` (rendered with `use_oidc`). The URL and behaviour are PilotApp's. PilotApp's callback refused a caller with no configured role even when the app configures none; the template's accepts it, as the API does.
  - **Pre-existing, left alone:** `api/testing_sse.py` imports `app.utils.auth`, which `use_oidc=false` excludes, so `use_sse` without `use_oidc` doesn't import. No app has that combination.
- **MAT-10:** both halves are closed in the template. Under OIDC on, no connection is registered without a valid token and a role, and a task without a subject sends to nobody. The card can close once phase 12 makes EI pass `caller_subject`.
- **What each app must change (phases 11–16):**
  - **Every app:** every direct `send_event` call needs a `Target`. Choosing `BROADCAST_TARGET` for a domain event is the app's call; it keeps today's behaviour, but the rule (phase 9) is to broadcast only infrastructure events.
  - **IoTSupport (11):**
    - `services/device_log_stream_service.py:297` `send_event(request_id, ...)` → `Target.connection(request_id)`.
    - `services/rotation_nudge_service.py:56` `send_event(None, {}, ...)` → `BROADCAST_TARGET`, or a narrower target.
    - Tests: `tests/services/test_device_log_stream_service.py:156-258` reads the request ID from `call[0][0]` (now a `Target`), and `tests/services/test_rotation_nudge_service.py:34-62` asserts the old call.
    - `tests/api/test_device_log_stream.py` binds `"local-user"` without the flag. That is harmless, since the device log stream compares `get_connection_info().subject`.
  - **ElectronicsInventory (12):**
    - `app/api/ai_parts.py:124,258` must pass `caller_subject` (the caller's `get_auth_context().subject`). Otherwise, with OIDC on, the AI analysis progress and results reach nobody (correction 7).
    - Tests `tests/test_utils_api.py:68-90` and `tests/api/test_testing.py:168-240` assert `args[0] is None` for the version broadcast; that becomes `== BROADCAST_TARGET`.
  - **DHCPApp (13):** `api/internal.py:50` `send_event(None, event_data, "data_changed", "dhcp")` → `BROADCAST_TARGET`, or a narrower target. Test `tests/test_internal_api.py:26-35` asserts `call_args[0][0] is None`.
  - **ZigbeeControl (14):** `services/tab_status_service.py:34` `send_event(None, ...)` → `BROADCAST_TARGET`, and `:40` `send_event(request_id, ...)` → `Target.connection(request_id)`. Tests: `tests/services/test_tab_status_service.py:42,57,74-81`.
  - **FieldnotesApp (15):**
    - The actioner's system task (`fieldnotes/actioner.py:491`, no subject) used to broadcast; now its events go to nobody under OIDC on. Its "explicit target" (correction 7) can only be a subject passed as `caller_subject`, since `start_task` takes no target; or nobody is right for a system task.
    - `inbox.py:522,554,671` already pass subjects.
    - `tests/fieldnotes/test_inbox.py:105` fakes `send_event` with the old signature `(request_id, event_data, event_name, service_type, target_subject=None)`. Its `_send_event_to_token` patches (`:940-960`) still fit, since that signature is unchanged.
    - **The FN-38 binding (correction 10):** `bind_unbound_identity` in FieldnotesApp's copy of `sse_connection_manager.py` and the `X-SSE-Request-Id` binding in `app/api/oidc_hooks.py`, with `tests/test_sse_identity.py`.
      - It bound connections that the old callback left unbound because their token had expired or was missing. The callback now refuses those with 401 instead, and FE16 (phase 7) makes the frontend refresh the session and reconnect. So once FieldnotesApp has FE16, a connection under OIDC on is never unbound, and the binding is redundant: phase 15 drops it.
      - If it is kept, its manager method conflicts with the rewritten manager on `copier update`. It must bind without `local_admin`, and it would rebind a reconnect, because `on_connect` now clears the binding.
  - **PilotApp (16):**
    - Take the template's side of `3f84260` in `app/api/sse.py`, `app/services/testing_service.py`, `app/api/testing_auth.py` and `app/schemas/testing_auth.py`. The last two lose PilotApp's hook endpoint and `ForceSSECallbackErrorQuerySchema`, which now live in `testing_sse.py` and `schemas/testing_sse.py` at the same URL.
    - Regenerate the frontend's OpenAPI cache.
    - `tests/test_sse_callback.py` largely duplicates the template's `tests/api/test_sse_callback.py`: drop it, or keep only Pilot-specific role cases.
- **For phase 7 (FE16):**
  - The hook endpoint exists and behaves as PilotApp's frontend spec expects.
  - The Playwright backend runs with OIDC off and no configured roles, so its test sessions are never refused, and its connect path is unchanged.
  - The frontend template's `test-app-domain/openapi-cache/openapi.json` lacks the new endpoint. Regenerate it if a generated hook is wanted.
- **For phase 9 (BE-T17):** the targeting rules to write:
  - every send names a `Target`;
  - `BROADCAST_TARGET` is for infrastructure events only;
  - task events go to the task's owner, with no fallback chain;
  - a connection sees every subject's events only as the local admin (OIDC off).
- **For the BE-T12 chunk:**
  - Keep `Target.connection(request_id)` for the on-connect send and `BROADCAST_TARGET` for `queue_version_event`. `tests/services/test_frontend_version_service.py` gained `TestQueueVersionEvent` (1 test).
  - The callback runs the `on_connect` observers before `bind_identity`, so an observer can target only the connection.
  - `check_readiness()` and the `sse_gateway` check registration are untouched.
- **For phase 10:** the changelog takes the signature change, `bind_identity`'s `local_admin`, the callback's 401/403, the hook endpoint, and that a task without a subject no longer broadcasts.
- **Tests:**
  - `tests/api/test_sse_callback.py` is new (33 with parameters): OIDC on (401 and 403 cases, cookie and bearer, additional role, test sessions, a `local-user` JWT is not the local admin), the read role, OIDC off (the local admin, role-checked test sessions, a stale session token), delivery through the callback's binding (MAT-10), the hook (both statuses, the local admin, single-shot, the endpoint, rejected statuses, ignored outside testing mode), and disconnect.
  - `tests/test_sse_connection_manager.py`: `TestTarget`, `TestSendEvent` and `TestLocalAdminBinding` replace the broadcast and `target_subject` classes; `TestReadinessCheck` is unchanged.
  - Correction 6's two tests are inverted as `test_task_events_never_broadcast_when_no_subject` and `test_progress_handle_has_no_default_target`, plus `TestTaskEventTarget`.
- **Gates:** `kc project build`, `test` (mother 690 → 744, domain 9, root backend suite) and `lint` are green. Playwright passed at one worker (3,400 MB peak), and `worker-isolation.spec.ts` (`tests/e2e/parallel/`) alone at two workers passed first time (5,372 MB peak).

## Phases

### Phase 0: dedup and facts

**Goal:** produce `docs/da_port_worklist.md`, the ground truth the later phases build on. This phase is read-only, apart from that file and this plan. Fan the reading out to parallel sub-agents.

**The worklist holds:**

1. **Item status.** One row per taken item, with ID, status (missing / partial / landed), where it stands now, and notes. The taken items are every item that the mapping in `da_port_decisions.md` assigns to S1–S6 or D1–D9 and that its ruling takes. Check each against the current templates (`backend/`, `frontend/`, `root/template/`) and note any app that already carries its own version. For example, `after_commit()` is already in the template.
2. **The root diff** (RT01–RT04): what DA's suite runner, `dev.py`, dev scripts, `Jenkinsfile`, `pyproject.toml` and `.kubecoder` have that the root template lacks. Each entry gets a take/leave recommendation in the spirit of the rulings.
3. **The uv reference.** List every edit FieldnotesApp and PilotApp made to template-owned files to move to uv (their `CLAUDE.md`s list the files), plus their app-owned packaging (`pyproject.toml` layout, `uv.lock`, scripts and entry points, `.kubecoder/project.yaml`). Then list every Poetry use in the three templates, in this repo's harness (`.kubecoder/project.yaml`, the `regen.sh` scripts, `scripts/`, `CLAUDE.md`, `docs/`) and in the template repos' own `pyproject.toml`s.
4. **The CI pipeline.** Compare the template's scripted `Jenkinsfile` with the estate pipeline guide (`kubecoder:jenkins-pipelines` skill) and with PilotApp's `modernApp.test` version, and say what the template should become. PostgreSQL in CI comes through `modernApp.test`'s `services:`.
5. **Per app:**
   - the configured roles, and whether any user who should read holds none of them (D2 would lock that user out);
   - every `send_event` call site (D3);
   - the app-owned tests that depend on SQLite or a per-test app (S1);
   - the backend `Dockerfile`;
   - the deploy repo, and where its values file sets environment variables;
   - the app's own gates (`.kubecoder/project.yaml`).
6. **Infrastructure:**
   - what `registry:5000/modern-app-backend`, `modern-app-backend-build` and `modern-app-frontend-build` contain (Poetry or uv, tini, libmagic, libpq), and where they're built (`pvginkel/DockerImages`);
   - the build cache's in-cluster URL (HomelabAppsDeploy's Jenkins chart);
   - how DevGuides (`pvginkel/DevGuides`) merges a guide whose source lives in another repo (the JenkinsPipelineUtils precedent; `kubecoder:dev-guides` skill), and the shape of KubeCoderConfig's pipelines skill;
   - how a Jenkins job gets created for an app's `Jenkinsfile.architecture`;
   - whether the `/seed-architecture` skill can run here.
7. **Overlapping MAT cards** in YouTrack that this work closes (MAT-13 looks like one).

**Done when:** the worklist is committed. It must answer every question above, or say who can (the operator, or a later phase).

### Phase 1: uv everywhere, dependency bumps

**Goal:** the three templates generate uv projects, the template repos and this repo's harness run on uv, and no `poetry` is left. FieldnotesApp's and PilotApp's edits (worklist §3) are the reference.

**Steps:**

1. **Backend template:**
   - `pyproject.toml.jinja` becomes PEP 621 with uv: `[project]`, `[dependency-groups]`, and the scripts as `[project.scripts]`.
   - Every `poetry run` in template-owned files becomes `uv run`.
   - The default `Dockerfile` installs with uv.
   - The test-app gets a `uv.lock`.
2. **Frontend template:** every Poetry call (for example, Playwright's global setup running the backend CLI) moves to uv.
3. **Root template:** `pyproject.toml.jinja`, the suite runner, `Procfile.dev`, `scripts/dev.py`, `scripts/regenerate-openapi.py`, `.kubecoder/project.yaml.jinja`, `CLAUDE.md.jinja` and the `Jenkinsfile`.
4. **Harness:**
   - the `backend/` and `frontend/` repos' own `pyproject.toml` (copier comes from there) and `regen.sh`;
   - this repo's `.kubecoder/project.yaml`, `root/regen.sh`, `scripts/`, `CLAUDE.md` (including the copier command for syncing an app), `docs/change_workflow.md` and `docs/downstream_sync_process.md`.
5. **Dependency bumps** (BE-C08): Pillow 12 (with the typing fix), spectree 2, flask-cors 6, pytest 9 and ruff 0.15, plus their fallout.

**Done when:**

- a grep for `poetry` over the templates, the harness and the docs finds only history;
- all gates are green on uv;
- the phase log records the new copier command and gate commands.

### Phase 2: backend, PostgreSQL testing (S1)

**Goal:** the backend suites run on PostgreSQL, and SQLite is gone. Follow `docs/pilotapp_database_testing_design.md` §3.4 and §4, built into the **template-owned** `tests/conftest_infrastructure.py` rather than an app's override. The items are BE-T06, BE-T07, BE-C18 and BE-C09.

**Steps:**

1. **Template database:** one per run, built by the revisions with `upgrade_database()` and the post-migration hook, in production's locale (ICU `und`, `C`). The admin URL comes from `TEST_DATABASE_ADMIN_URL`. The sweep drops leftovers without `FORCE` and skips databases in use.
2. **Session-scoped app** on a clone of the template database. The `session` fixture binds a savepoint session: `commit()` and `rollback()` stay real, and only `close()` is a no-op. The `container` fixture makes `session_maker` return that session.
3. **Tier-2 `committed_app`:** its own cloned database, for tests that need commits seen by a second connection.
4. **Prometheus:** the registry is cleared once per session and before each extra app. `oidc_app` uses the same URL and re-wires the main container afterwards.
5. **Pools:** small ones, via the shared constants of BE-C18.
6. **Schema tests:** a drift test (`compare_metadata` returns nothing), and migration tests running against the run's database.
7. **Remove SQLite:** the recreate branch of `upgrade_database()`, `initialize-sqlite-database.sh`, the engine-options override "for testing with SQLite", and the SQLite imports.
8. **`testing-server.sh`** takes `--database-url`, loads `.env` then `.env.test`, and runs through the project's `dev` entry point (BE-C09).
9. **App defaults:** the default `tests/conftest.py` for new apps follows. The mother suite moves to PostgreSQL. The dev environment's `postgres` sidecar serves it.

**Done when:** both backend suites are green on PostgreSQL, nothing builds a SQLite database, and the phase log records what apps' `tests/conftest.py` must change.

### Phase 3: backend fixes, stages, the internals fact

**Goal:** D1's backend part, plus D9b, S6 and S4.

**Steps:**

1. **Fixes:**
   - BE-C02, BE-C04, BE-C05 (keep the current metric label set), BE-C06, BE-C10 and BE-C11;
   - BE-C03, only if the worklist shows a gap;
   - BE-T01 (it covers BE-C07) and BE-C16.
2. **Tests for template code:** BE-T04, BE-T05, BE-T14 and BE-T15, adapted to the template as it is now.
3. **Stages** (D9b, as ruled):
   - DA's six-value `STAGE` and the `Stage` wrapper;
   - the default (`prd` under a production `FLASK_ENV`, `local-tst` under testing, `local-dev` in development);
   - readyz reporting the stage;
   - the local-stage skip of the version broadcast;
   - guards on destructive CLI commands and test-only endpoints on `prd`.
4. **The internals fact** (S6): `HOMELAB_INTERNAL`, and one fact meaning "`STAGE` is not `prd`, or `HOMELAB_INTERNAL`". The generic 500 handler shows exception text only when the fact is true (S4). `GET /api/ui-setup` returns the stage and the fact.

**Done when:** the gates are green, and the phase log records the new settings apps must set.

### Phase 4: backend auth

**Goal:** D2, D4, S2 and D9c.

**Steps:**

1. **BE-C01:** a user with none of the app's roles gets 403 everywhere.
2. **BE-C12 with its tests BE-T09:**
   - one identity-resolution path;
   - tolerant `@public` with refresh;
   - `g.clear_auth_cookies` on logout;
   - `@no_role_check` for login, callback and logout.

   Leave out DA's user-seeding glue.
3. **BE-T16:** task endpoints check the caller.
4. **BE-C15:**
   - the OIDC `redirect_uri` comes from the request origin and travels in the encrypted state;
   - redirect parameters must be relative;
   - BE-T05's redirect tests follow.
5. **BE-C25:** `role_hierarchy` with cycle detection, off by default, with its tests.

**Done when:** the gates are green, and the phase log records what apps must check (role configuration, IdP redirect URIs per hostname).

### Phase 5: backend readiness, SSE, small takes

**Goal:** D5, D3's backend part, and D9's backend takes.

**Steps:**

1. **Readiness** (BE-C13, BE-T13):
   - services register their own checks;
   - checks run concurrently, each with a timeout, with a 30 s cache;
   - each check carries a `critical` flag, and readyz returns 503 only when a critical check fails (the database; S3 where `use_s3`);
   - the response reports every check.
2. **SSE:**
   - BE-T10: a typed `Target`, with no implicit broadcast. Task events go to the caller.
   - BE-T11: the connect callback answers 401 or 403, plus the single-shot forced-rejection test hook.
   - BE-T12: the parts that don't depend on DA's stateless manager.
3. **Small takes:**
   - BE-C28: `ExternalServiceException` as a 502, and the error-envelope schemas.
   - BE-C29: run under `watchmedo` without the Werkzeug reloader. The root half is in phase 8.
   - D9a: `apply_sorting()` with its `id` tiebreaker, and the pagination schemas.

**Done when:** the gates are green, and the phase log records the readyz format change and the `send_event` signature change.

### Phase 6: frontend fixes, Playwright on PostgreSQL

**Goal:** D1's frontend part, and S1 for Playwright.

**Steps:**

1. **Fixes:** FE01–FE14, FE17, FE18 and FE20. For FE14, video is off by default, and an env var turns `retain-on-failure` back on.
2. **Playwright on PostgreSQL** (PilotApp design §4.6, FE23):
   - Global setup creates a seed database in production's locale and seeds it with the backend's `load-test-data`.
   - Each worker clones the seed (`CREATE DATABASE … TEMPLATE`) through a `pg-admin.ts` on the `pg` client.
   - A global teardown drops the run's databases.
   - `servers.ts` passes `--database-url`, and the backends get small pools.
   - The SQLite seed path goes.
3. **knip:** update `knip-template-ignore.json` for every template-owned file added or removed.

**Done when:** the frontend gates and the Playwright suite are green.

### Phase 7: frontend stages, SSE, defaults

**Goal:** the UI side of S6 and D9b, D3's frontend part, and D6.

**Steps:**

1. **The `ui-setup` client:**
   - FE19: a copy-diagnostics button on error toasts, shown when the internals fact is true;
   - FE32: the stage badge, hidden on `prd`.
2. **SSE:**
   - FE15: `connected` means `ready` was received;
   - FE16: on `rejected`, refresh the session and reconnect, or send the user to login; the spec runs in preview mode;
   - FE27: a non-blocking SSE gate.
3. **Defaults:** FE21, FE28 and FE29 (take the frontend copy of the button).
4. **knip:** keep `knip-template-ignore.json` current.

**Done when:** the frontend gates and the Playwright suite are green.

### Phase 8: root CI, images, dev stack, architecture, tooling

**Goal:** the root template side of S1, S3, BE-C29, D8, RT07 and the root diff.

**Steps:**

1. **CI:**
   - the `Jenkinsfile` takes the shape worklist §4 decided;
   - PostgreSQL in the validation Job, with a wait for it;
   - `STAGE=tst`;
   - the build cache (RT05).
2. **Images** (S3):
   - the frontend `Dockerfile` (template-owned) moves to `modern-app-frontend-build`;
   - the backend `Dockerfile` default moves to the backend base images.

   If worklist §6 says the images aren't uv-ready, add the change in a `/work/scratch/DockerImages` clone, committed, not pushed.
3. **Dev stack:**
   - `watchmedo` restarts (BE-C29);
   - what the worklist takes from DA's `dev.py` and scripts (RT03);
   - `STAGE=local-dev` and `HOMELAB_INTERNAL` in the seeded `.env`.
4. **Architecture producer** (D8):
   - `Jenkinsfile.architecture` and `scripts/arch-validate.py`, taken from DA and parameterised;
   - the nudge section in the generated `CLAUDE.md`.
5. **Dependency checker** (RT07): `scripts/check_updates.py`, discovering components rather than listing them.
6. **Rest of the root diff:** what the worklist takes from RT01, RT02 and RT04.

**Done when:** the root gates and the Playwright suite are green.

### Phase 9: conventions guide and skill (S5)

**Goal:** the conventions become a guide on dev-guides.home, and a KubeCoderConfig skill points at it. Load the `kubecoder:dev-guides` skill first.

**Steps:**

1. **The guide's source** goes in this repo, laid out per the dev-guides contract. It holds:
   - RT08: exhaustive status enums;
   - RT09: when to toast;
   - RT11: UUID paths and the 2-second rule;
   - RT13: testing against real dependencies, with the preview-mode gotcha;
   - RT14: `perf_counter`, failing fast, and `window.open` downloads;
   - BE-T17: test conventions and SSE targeting;
   - D9a: paged lists order stably.
2. **Merge it into the site:** in a `/work/scratch/DevGuides` clone, as the worklist describes. Commit, don't push.
3. **The skill:** in a `/work/scratch/KubeCoderConfig` clone, modelled on the pipelines skill. Commit, don't push.

**Done when:** the guide builds by the contract's check, and both clones are committed.

### Phase 10: release

**Steps:**

1. **Changelogs:**
   - each template repo's own;
   - one coordinated entry in this repo's `changelog.md`, with the migration steps an app follows. These are the checklist for phases 11–16: uv, PostgreSQL tests, `STAGE`/`HOMELAB_INTERNAL`, roles, typed SSE targets, the readyz format, the backend `Dockerfile`, IdP redirect URIs and the architecture YAML.
2. **Gates:** all green.
3. **Tags:** backend v0.14.0, frontend v0.21.0, root v0.2.0.

**Done when:** the tags exist locally, and the phase log names them.

### Phases 11–16: the apps, one per phase

**Order:** IoTSupport (11), ElectronicsInventory (12), DHCPApp (13), ZigbeeControl (14), FieldnotesApp (15), PilotApp (16). The app is at `/work/<App>`. Read its `CLAUDE.md` first.

**Steps:**

1. **Start clean:** `git status` must be clean.
2. **Root:** `copier update` from the app's root, using the command in the phase log, with `--trust --defaults`. Commit.
3. **Backend:** the same from `backend/`. Commit.
4. **Frontend:** the same from `frontend/`. Commit.
5. **Conflicts:** resolve each within the rulings.

   FieldnotesApp and PilotApp: their uv edits to template-owned files are now the template's own. Where they differ, take the template's version. Then remove uv from their `CLAUDE.md`'s list of standing template-owned edits, and remove any other standing edit the template now covers.
6. **Packaging** (Poetry apps only: IoTSupport, ElectronicsInventory, DHCPApp, ZigbeeControl): convert the app-owned packaging to uv, following worklist §3. That means `pyproject.toml`, `uv.lock` in place of `poetry.lock`, and `.kubecoder/project.yaml`. Commit.
7. **App-owned follow-ups,** following the changelog's migration steps. Commit each.
   - the database apps' `tests/conftest.py` on PostgreSQL;
   - `STAGE` and `HOMELAB_INTERNAL` in `.env`, `.env.test` and `.env.example`;
   - the `send_event` call sites on typed targets;
   - the roles check;
   - the backend `Dockerfile` on the base images;
   - vulture and knip upkeep;
   - the architecture YAML, if `/seed-architecture` can run. Otherwise log it as an operator action.
8. **Deploy repo:** clone it into `/work/scratch/deploy/<repo>`, and set `STAGE=prd` and `HOMELAB_INTERNAL=true` where the worklist says. Commit, don't push.
9. **Gates:** the app's `kc project` setup, build, test and lint, plus its Playwright suite. All green.

**Stops:**

- users who would be locked out by D2;
- a real bug that PostgreSQL exposes and that is too large to fix in the phase;
- a conflict the rulings don't settle.

**PilotApp (phase 16):** its planning (slice 002) is paused until the apps are updated, and then reviews where things stand. Give it a hand-off section in the phase log covering what the sync brought: PostgreSQL testing from the template, stages and the internals fact, uv as template-native, and the auth, SSE and readiness changes.

### Phase 17: the push

**Steps:**

1. **Summary:** give the operator a per-repo summary: commits, tags, gate results, and the operator actions logged. Wait for the go-ahead.
2. **Push in dependency order:**
   1. DevGuides, KubeCoderConfig and DockerImages (if changed);
   2. this repo, `backend/` and `frontend/`, with tags;
   3. the six deploy repos;
   4. the six apps, whose pushes start their Jenkins builds.
3. **Watch:** follow the builds to green through Jenkins, and the Argo CD syncs after them.
4. **Report:** report the result, and list what's left for the operator: the per-app architecture Jenkins jobs, and any architecture YAMLs not seeded.

**Done when:** every app is built and synced, and the report is sent.
