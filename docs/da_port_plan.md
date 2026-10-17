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
| 5 | Backend: readiness, SSE, small takes | done 2026-10-17 | backend `f129198`, `b224b4f`, `0fdb1d2`, `b71c1d0`, `22436d4`, `ce1d7d4`, `ac635cb`; parent `d4dc992`, `994c64e`, this entry |
| 6 | Frontend: fixes, Playwright on PostgreSQL | done 2026-10-17 | frontend `23dd7dc`, `c2d9fde`, `9a8e9b6`, `ebb01c1`, `540430c`, `3824500`, `3ac2cdf`, `cbe04b4`, `d2f6ded`, `f9f9a5b`, `9bd07c9`; backend `b9ac732`, `57427d0`; parent `f38d2f8`, `101033b`, `096f326`, this entry |
| 7 | Frontend: stages, SSE, defaults | done 2026-10-17 | frontend `ec93ae9`, `13a4c62`, `fcce4fd`, `98375e0`, `678a52a`; parent `2d351fe`, `323bd88`, this entry |
| 8 | Root: CI, images, dev stack, architecture, tooling | done 2026-10-17 | frontend `f308682`, `b0b1b16`, `0b87bad`; backend `96ee519`, `332a431`, `40cd8da`; parent `07fd094`, `8d28f63`, `0d3f7a7`, `953bbf5`, `67601c2`, `3f43ff2`, `2ea8724`, `33c6bae`, `2d5bfe8`, `13611f4`, this entry; DockerImages clone `7e7c1f7` (not pushed) |
| 9 | Conventions guide and skill | done 2026-10-17 | parent `91f1de1`, `5374474`, this entry; DevGuides clone `92bc97d`; KubeCoderConfig clone `c5db31a`, `ec17ea5`; JenkinsPipelineUtils clone `01bf1fe` (none pushed) |
| 10 | Release | done 2026-10-17 | backend `6976a35`; frontend `5a155fd`, `9828760`, `2ee64bf`; parent `590ca61`, `51d8daa`, `63e1773`, `8b43fc1`, this entry; tags backend `v0.14.0` (`6976a35`), frontend `v0.21.0` (`2ee64bf`), root `v0.2.0` (this entry's commit); none pushed |
| 11 | App: IoTSupport | done 2026-10-17 | IoTSupport `c294800` (root), `c9a67d1` (backend), `21d9d26` (frontend), `c8d48fa` (uv), `a8644f4`, `7481d05`, `db2a3cb`, `49cc3a2`, `6a414da`, `600b8f6`, `b8d3bef`, `b5011b7`, `3efd106`, `e227d07`, `394dde4`, `71d78ea`, `a55c75e`, `e4406be`, `c154080`, `112913f`, `cc5d981`, `7948bf3`, `c6d1337`, `b7741a4`; IotDeploy clone `6f6ea99` (not pushed); parent `3341c75`, `1a7d192`, `3fd9997`, `1ea48c7`, `d237d6c`, `1a1401f`, this entry; none pushed |
| 12 | App: ElectronicsInventory | in progress: changelog steps 1–5 done | ElectronicsInventory `f28c42a9` (root), `ab85dee9` (backend), `58ad6a13` (frontend), `966ab2a2` (uv); parent: this entry; none pushed |
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

### 2026-10-17, phase 5: backend readiness, SSE, small takes

Backend `f129198` (step 1: D5, BE-C13, BE-T13, and BE-T14's S3 check tests), `b224b4f` (BE-T10 and BE-T11 together: the callback decides who is the local admin, and the targets depend on it), `0fdb1d2` (BE-T12), `b71c1d0` (BE-C28), `22436d4` (BE-C29's backend half), `ce1d7d4` (D9a, BE-C27) and `ac635cb` (SSE without OIDC). Corrections 5 (the rest of BE-C29), 6, 7, 9 (BE-C28) and 10 applied. The frontend and root templates are unchanged: no repo holds a readiness probe, and every consumer outside the backend reads only the status code.

- **The readyz format change** (`GET /health/readyz`):
  - Before: `{"status": "ready"|"not ready"|"shutting down", "ready", "stage", "<check>": {..., "ok"}}`, 503 when any check failed.
  - Now: `{"status", "ready", "stage", "checks": {"<check>": {"status": "ok"|"error"|"disabled", "critical": bool, "detail"?: str}}}`. `status` is `ok` (everything passed), `degraded` (a non-critical check failed; 200), `not_ready` (a critical check failed; 503) or `shutting_down` (503, `checks` empty, no check runs). `ready` is false exactly when the answer is 503. `disabled` means "deliberately not configured" and never fails. `detail` is absent when there is nothing to say.
  - The checks: `database` (critical; `detail` is `connection failed`, `N migrations pending`, or the migration lookup's exception text), `s3` (critical, `head_bucket` on the bucket) and `sse_gateway` (not critical; `gateway readyz answered N`, or the request's error).
  - Healthz is `{"status": "alive", "ready": true}`, always 200. `HealthResponse` (healthz, drain) lost `stage`; readyz has its own `ReadyzResponse` and `ReadinessCheckSchema` in the OpenAPI spec.
- **The readiness API** (`app/services/health_service.py`): `register_check(name, check, *, critical, timeout=0.8)`, where `check()` returns `CheckResult(CheckStatus.OK|ERROR|DISABLED, detail=None)` and an exception it raises is the check's error. Registering a name again replaces the check. `clear_cache()` makes the next readyz run every check. `register_readyz` and `register_healthz` are gone; no template code and no app used `register_healthz`.
  - **Who registers what.** `S3Service.startup()` registers `s3`, and `SSEConnectionManager(gateway_url, http_timeout=5.0, health_service=None)` registers `sse_gateway` in its constructor (`check_readiness()` is the check). The container passes `health_service` to the manager only with `use_sse`, because the manager exists without SSE. The database has no service: `create_app()` sets it up and registers `app.database.check_readiness`, which takes over `_check_db_readiness`. The pytest apps skip background services, so their readyz checks only the database; dev, prd and the Playwright backend register all three.
- **The `send_event` signature change** (`app/services/sse_connection_manager.py`):
  - Before: `send_event(request_id: str | None, event_data, event_name, service_type, target_subject: str | None = None)`. `None` broadcast to every connection; `target_subject` narrowed a broadcast to that subject plus every connection bound to the string `"local-user"`.
  - Now: `send_event(target: Target, event_data, event_name, service_type)`. There is no default and no `target_subject`. A request ID or `None` raises `TypeError`, so an old call fails loudly instead of misdelivering, and mypy flags every old call site.
  - The targets: `Target.connection(request_id)` (that connection); `Target.subject(subject)` (connections bound to that subject, plus the local admin's); `LOCAL_ADMIN_TARGET` (the local admin's connections only, so nobody with OIDC on); `BROADCAST_TARGET` (every connection, for infrastructure events only). `Target` is a frozen dataclass `(kind, value)`; the factories refuse an empty value, and there is no `Target.broadcast`.
  - The local admin is a flag on the binding: `bind_identity(request_id, subject, *, local_admin=False)`. The connect callback sets it for the local admin (OIDC off, no test session), and nothing else does. A connection bound to the subject `"local-user"` without the flag (a JWT with that `sub` under OIDC on) is an ordinary subject. This is the SSE form of `_caller_owns` in `api/tasks.py.jinja`.
  - `on_connect` clears the request ID's binding when a connection replaces another; a disconnect and a gateway 404 clear it too (the 404 path used to leave `_identity_map` behind).
- **Task events go to the caller** (`app/services/task_service.py`). `task_event_target(caller_subject)` gives `Target.subject(caller_subject)`, or `LOCAL_ADMIN_TARGET` for a task without a subject (correction 7: nobody with OIDC on, the local admin with OIDC off). `TaskProgressHandle(task_id, manager, target)` takes a required target, and `_broadcast_task_event` is now `_send_task_event(event, target)`. `start_task` still takes only `caller_subject`, so the task's owner (`TaskInfo.subject`) and its event target never differ. `/api/testing/tasks/start` sits outside `api_bp`, so no auth hook runs there and it starts its tasks with `caller_subject=None`: the mother integration tests receive them as the local admin, with OIDC off.
- **The other senders:** `FrontendVersionService` sends `Target.connection(request_id)` on connect and `BROADCAST_TARGET` from `queue_version_event`; `/api/testing/sse/task-event` sends `Target.connection(request_id)`.
- **The connect callback** (`app/api/sse.py.jinja`, started from PilotApp's `3f84260`). Order: callback secret (production), payload and `request_id` checks, then the testing hook, then the identity, then `on_connect` and `bind_identity`. So a refused connect is never registered, never counted in the connection metrics, and never reaches the `on_connect` observers, and an observer can target only the connection, since it runs before the binding.
  - The identity: `resolve_auth_identity(token, auth_service, settings, testing_service)` on the forwarded headers' token (Authorization header first, then the access-token cookie). A missing token under OIDC on, or an `AuthenticationException` (expired, bad signature, issuer, audience), answers 401 `{"error": "Unauthorized"}`. Other exceptions are a 500, as in the API.
  - The role check: `check_authorization(auth_context, auth_service, "GET")`, the rule the API applies to a GET. A caller with none of the configured roles, or one without the read role where the app sets `read_role`, gets 403 `{"error": "Forbidden"}`. The local admin skips the check; a test session is checked under OIDC off too (phase 4's rule).
  - The hook: `POST /api/testing/sse/force-callback-error?status=401|403` answers 204 and makes the next connect callback refuse with that status, whoever connects. It is single-shot, class-level state on `TestingService` (`set_/consume_forced_sse_callback_error`), consumed only when `settings.is_testing`. Any other status answers 400.
  - With `use_oidc=false` (no app has it), every connection is the local admin's.
- **FrontendVersionService (BE-T12).** A failed fetch (a request error, or a body that isn't JSON) sends nothing; the `{"version": "unknown", "error": ...}` payload is gone. A version queued for a request ID through `/api/testing/deployments/version` (the only caller of `queue_version_event`) is dropped when that connection disconnects (`register_on_disconnect`), so `_pending_version` holds live connections only, plus IDs queued but never connected. Kept: the on-connect send, which the stateful manager needs (`integration/test_sse_gateway_version.py::test_pending_events_flushed_on_connect` pins it), and phase 3's local-stage skip (a queued version still goes). Not taken: DA's startup-only broadcast, which needs the stateless manager.
  - Still so: the on-connect observer does a 2 s `requests.get` inside the gateway's connect callback, so outside a local stage a down frontend slows every connect. A gateway 404 clears the mapping without notifying the disconnect observers, so a version queued for that connection stays until shutdown (test-only).
- **`ExternalServiceException` and the error envelope (BE-C28).** The class is in the new template-owned `app/core_exceptions.py` (correction 9: `app/exceptions.py` is app-owned): `ExternalServiceException(operation, cause)`, message `Cannot {operation} because external service failed: {cause}`, code `EXTERNAL_SERVICE_ERROR`. A handler in `register_business_error_handlers` answers 502 with `details.message` "External service request failed". `schemas/common.py` gains `ApiErrorResponseSchema` (`error`, `details`, optional `code`, optional `correlationId`, the alias of `correlation_id`) and `ApiErrorDetailsSchema` (`message`), mirroring `build_error_response()`; a Pydantic `ValidationError` 400 carries `details.errors` instead, as its docstring says. `ErrorResponseSchema` stays, since EI annotates its endpoints with it.
- **`scripts/dev-watch.sh` (BE-C29, backend half).** `dev-watch.sh [command...]` runs the command, `uv run dev` by default, under `uv run -- watchmedo auto-restart`, from the backend directory whatever the caller's working directory.
  - It restarts on changes to `*.py` (outside `tests/` and `alembic/`), `.env*` and `app/assets/`, debounced 1 s, by SIGTERM to the command's process group. The wrapper's `trap` holds watchmedo back until the old server has drained, so the new one never finds the port taken; watchmedo sends SIGKILL after 10 s. A command that exits by itself restarts after 3 s. watchmedo stops the command itself on SIGTERM, SIGINT or SIGHUP.
  - Checked live on test-app: restarts on app code, assets, `.env.test` and `run.py`; none on `tests/` (nested too) or `alembic/`; no port clash; nothing left running after a SIGTERM to the top process; three starts in 7 s for a command that exits at once.
  - `watchdog[watchmedo]>=6.0.0,<7` joins the dev group of `pyproject.toml.jinja` (app-owned). `dev-server.sh` (restart on keypress) is removed: `dev-watch.sh` without arguments does its job. `run.py`'s comment names it. Phase 2 had already taken `use_reloader=False` and dropped the `WERKZEUG_RUN_MAIN` branches (correction 5).
- **Pagination (D9a, BE-C27).** `app/utils/pagination.py` (`use_database` only): `apply_sorting(query, model, sort_by, sort_dir)` orders by the column, then by `id` in the same direction (one clause when `sort_by` is `id`), and raises `ValueError` for an unknown column or direction. `build_pagination_meta(total, page, per_page, sort_by=None, sort_dir=None)` returns a `PaginationMetaSchema`; an empty list has one page. `schemas/common.py` gains `SortDirection` and `PaginationQuerySchema` (`page` ≥ 1, `per_page` 1–100 with default 20, `sort_dir` with default `asc`, an `offset` property; a subclass adds `sort_by` as a `Literal`). `PaginationMetaSchema` gains `sort_by` and `sort_dir` as optional fields, so a caller that builds it without them is unaffected (none does today). `PaginatedResponseSchema` stays.
- **SSE without OIDC fixed** (`ac635cb`). A render with `use_sse=true` and `use_oidc=false` failed at import: `api/testing_sse.py` imported `app.utils.auth`, which that render leaves out, for a `get_auth_context()` that is always `None` there, and `api/sse.py` and `testing_sse.py` use `ServiceContainer.testing_service`, which the container defined only with OIDC or S3. `testing_sse.py` now passes `caller_subject=None`, and `container.py.jinja` defines `testing_service` with `use_sse` too. Checked on two renders, with and without database and S3: `create_app`, ruff, mypy, vulture, a local-admin connect and a forced 403. `container.py` is app-owned, so the fix reaches new apps only; no app has the combination.
- **Deviations:**
  - **Readiness, from DA:**
    - The `critical` flag (D5). DA failed readiness on any error.
    - Timeouts fit the probes. All six apps' prd probes on `/health/readyz` have `timeoutSeconds: 1`, `periodSeconds: 3` and `failureThreshold: 3` (read from the prd cluster), so readyz waits at most 0.8 s per check by default, where DA waited up to 10 s with 5 s HTTP timeouts. A run that outlives its timeout reads `timed out after 0.8 s` and keeps going in its own daemon thread. Later requests wait on that run instead of starting another, and its result is cached when it passes, so a slow first check (a cold pool, Alembic reading its scripts) passes at the next probe. DA started a new pool per request, so a hung dependency added a thread per probe.
    - Only passing results are cached (30 s). A failure re-runs at every probe, so a recovery, the startup one included, shows within one probe period. DA cached failures too.
    - Metrics and logs: one histogram, `readiness_check_duration_seconds{check,status}`, per run and not per cache hit; its `_count` is DA's counter. A check's status change is logged (warning on failure, with the traceback when the check raised), and a repeat is not.
    - `ready` and `stage` stay. No OIDC-issuer check: the worklist drops DA's Keycloak case.
  - **SSE, from DA:** the target is required, where DA took `Target | None` with `None` meaning nobody. `LOCAL_ADMIN_TARGET` replaces DA's `Target.role("editor")` fallback. `Target.role`, `Target.workspace_events`, routing keys and `serialize`/`deserialize` are AMQP-only and not taken.
  - **From the worklist's BE-T11 note** ("replace `editor` with `configured_roles`"): the callback uses `check_authorization` for a GET. That adds the read tier; without a `read_role` it is the same rule.
  - **From PilotApp:** the hook endpoint is in `api/testing_sse.py` (rendered with `use_sse`), with `ForceSSECallbackErrorQuerySchema` in `schemas/testing_sse.py`, and not in `testing_auth.py` (rendered with `use_oidc`). The URL and behaviour are PilotApp's. PilotApp's callback refused a caller with no configured role even when the app configures none; the template's accepts it, as the API does.
  - **BE-C28, from DA:** the signature, message and 502 body are IoTSupport's, not DA's `(service, cause)`, so IoTSupport's call sites stay as they are. `code` is optional in `ApiErrorResponseSchema` (the framework handlers set none), and the schema documents `correlationId`. `UnprocessableEntityException`, `TaskAcceptedSchema`, `WorkspaceLockedError`, `locked_by` and the `ConflictLock*` schemas are not taken.
  - **BE-C29, from DA:** watchdog matches a pattern like `PurePath.match`, from the right and one segment per `*`, and DA's relative `--directory=.` loses the leading segment. So DA's `*/tests/*` and `*/app/assets/*` matched nothing at the top level, and `tests/` edits restarted the server. The script watches the absolute directory, lists one pattern per depth, and adds the debounce and the drain-first `trap`.
  - **D9a, from DA:** the optional meta fields (DA's are required), the `ValueError`s (DA treated any direction but `asc` as `desc`), no duplicate `id` clause, the `offset` property, and a schema instead of a dict from `build_pagination_meta`. DA's removal of `PaginatedResponseSchema` is not copied.
- **MAT-10:** both halves are closed in the template. Under OIDC on, no connection is registered without a valid token and a role, and a task without a subject sends to nobody. The card can close once phase 12 makes EI pass `caller_subject`.
- **What apps must change (phases 11–16):**
  - **Every app:**
    - **App-owned `container.py`:** move `lifecycle_coordinator` and `health_service` above `s3_service`, then pass `health_service=health_service` to `S3Service` (EI, IoTSupport) and to `SSEConnectionManager` (all six use SSE). Without the edit, readyz silently lacks `s3` or `sse_gateway`. `test-app-domain/app/services/container.py` shows the result.
    - **Every direct `send_event` call needs a `Target`.** Choosing `BROADCAST_TARGET` for a domain event is the app's call; it keeps today's behaviour, but the rule (phase 9) is to broadcast only infrastructure events.
    - **App-owned `backend/pyproject.toml`:** add `watchdog[watchmedo]>=6.0.0,<7` to the dev group; `copier update` brings `scripts/dev-watch.sh`, which needs it, and deletes `scripts/dev-server.sh`.
    - **App tests** that assert on the readyz body. A test of an app check must clear the cache or use a fresh `HealthService`.
    - **Deploy repos need nothing:** the probes read the status code only.
  - **IoTSupport (11):**
    - `services/device_log_stream_service.py:297` `send_event(request_id, ...)` → `Target.connection(request_id)`.
    - `services/rotation_nudge_service.py:56` `send_event(None, {}, ...)` → `BROADCAST_TARGET`, or a narrower target.
    - Tests: `tests/services/test_device_log_stream_service.py:156-258` reads the request ID from `call[0][0]` (now a `Target`), and `tests/services/test_rotation_nudge_service.py:34-62` asserts the old call.
    - `tests/api/test_device_log_stream.py` binds `"local-user"` without the flag. That is harmless, since the device log stream compares `get_connection_info().subject`.
    - **`ExternalServiceException`:** its own class in `app/exceptions.py` and its 502 handler in `startup.py:104` match the template's. Delete both and import the class from `app.core_exceptions` in `api/images.py`, `utils/error_handling.py`, `services/{device,elasticsearch,image_proxy,keycloak_admin,rotation}_service.py` and their tests. Don't re-export it at the top of `app/exceptions.py`: `core_exceptions` imports `BusinessLogicException` from there, so that is a circular import. Keeping its own class also works (it has its own handler), but leaves two classes of one name.
    - `.kubecoder/config.yaml:15` says `database.connected`, which is now `checks.database.status`.
  - **ElectronicsInventory (12):**
    - `app/api/ai_parts.py:124,258` must pass `caller_subject` (the caller's `get_auth_context().subject`). Otherwise, with OIDC on, the AI analysis progress and results reach nobody (correction 7).
    - Tests `tests/test_utils_api.py:68-90` and `tests/api/test_testing.py:168-240` assert `args[0] is None` for the version broadcast; that becomes `== BROADCAST_TARGET`.
    - Correction 16: `part_service.py:132` and `inventory_service.py:358` page by `created_at` alone; move them onto `apply_sorting()`, or add the `id` tiebreaker.
    - `frontend/tests/smoke.spec.ts:33-62` builds its failure message from `payload.status` and `payload.migrations.pending`, which were already stale. `.kubecoder/config.yaml:108` says `database.connected`, which is now `checks.database.status`.
  - **DHCPApp (13):** `api/internal.py:50` `send_event(None, event_data, "data_changed", "dhcp")` → `BROADCAST_TARGET`, or a narrower target. Test `tests/test_internal_api.py:26-35` asserts `call_args[0][0] is None`.
  - **ZigbeeControl (14):** `services/tab_status_service.py:34` `send_event(None, ...)` → `BROADCAST_TARGET`, and `:40` `send_event(request_id, ...)` → `Target.connection(request_id)`. Tests: `tests/services/test_tab_status_service.py:42,57,74-81`.
  - **FieldnotesApp (15):**
    - `services/fieldnotes_service.py:78` changes from `register_readyz("store", self._readyz)` to `register_check("store", ..., critical=True)`. `critical=True` keeps today's 503. `_readyz` returns a `CheckResult`: `DISABLED` with no runtime (today's `configured: False`), `OK` when `runtime.ready`, otherwise `ERROR` with the failure in `detail`. In `tests/fieldnotes/test_api.py:37-40,48-51,73-75`, `json()["store"]` becomes `json()["checks"]["store"]` in the new shape. A test that reads a passing store and then expects a failure must call `health_service.clear_cache()` in between, since the passing result is cached for 30 s.
    - The actioner's system task (`fieldnotes/actioner.py:491`, no subject) used to broadcast; now its events go to nobody under OIDC on. Its "explicit target" (correction 7) can only be a subject passed as `caller_subject`, since `start_task` takes no target; or nobody is right for a system task.
    - `inbox.py:522,554,671` already pass subjects.
    - `tests/fieldnotes/test_inbox.py:105` fakes `send_event` with the old signature `(request_id, event_data, event_name, service_type, target_subject=None)`. Its `_send_event_to_token` patches (`:940-960`) still fit, since that signature is unchanged.
    - **The FN-38 binding (correction 10):** `bind_unbound_identity` in FieldnotesApp's copy of `sse_connection_manager.py` and the `X-SSE-Request-Id` binding in `app/api/oidc_hooks.py`, with `tests/test_sse_identity.py`.
      - It bound connections that the old callback left unbound because their token had expired or was missing. The callback now refuses those with 401 instead, and FE16 (phase 7) makes the frontend refresh the session and reconnect. So once FieldnotesApp has FE16, a connection under OIDC on is never unbound, and the binding is redundant: phase 15 drops it.
      - If it is kept, its manager method conflicts with the rewritten manager on `copier update`. It must bind without `local_admin`, and it would rebind a reconnect, because `on_connect` now clears the binding.
    - Its `CLAUDE.md` lists `backend/scripts/dev-server.sh` among its standing edits; the file is gone, so the entry goes.
  - **PilotApp (16):**
    - Take the template's side of `3f84260` in `app/api/sse.py`, `app/services/testing_service.py`, `app/api/testing_auth.py` and `app/schemas/testing_auth.py`. The last two lose PilotApp's hook endpoint and `ForceSSECallbackErrorQuerySchema`, which now live in `testing_sse.py` and `schemas/testing_sse.py` at the same URL.
    - Regenerate the frontend's OpenAPI cache.
    - `tests/test_sse_callback.py` largely duplicates the template's `tests/api/test_sse_callback.py`: drop it, or keep only Pilot-specific role cases.
- **For phase 6:** the comment at `fixtures-infrastructure.ts.jinja:379` ("the gateway must be up before the backend can pass its readiness probe") no longer holds, because `sse_gateway` isn't critical. Starting the gateway first is still right, since it is awaited at its own readyz. The Playwright wait still checks `response.ok`, and readyz is now 503 only for the database or S3.
- **For phase 7 (FE16):**
  - The hook endpoint exists and behaves as PilotApp's frontend spec expects.
  - The Playwright backend runs with OIDC off and no configured roles, so its test sessions are never refused, and its connect path is unchanged.
  - The frontend template's `test-app-domain/openapi-cache/openapi.json` lacks the new endpoint. Regenerate it if a generated hook is wanted.
- **For phase 8 (BE-C29's root half):** `Procfile.dev.jinja`'s backend line becomes `cd backend && env -u VIRTUAL_ENV PORT=... scripts/dev-watch.sh` (no arguments: `uv run dev` is the default), and the "Werkzeug auto-reload" comment goes. Keep `env -u VIRTUAL_ENV`: the script runs `uv run` in `backend/`. Check that stopping `scripts/dev.py` leaves no backend running: honcho's SIGTERM must reach watchmedo, which then drains the server.
- **For phase 9:**
  - **RT15:** a new external integration registers its own check with `register_check`, sets `critical` only when the app cannot serve without it, and keeps its own I/O timeout near the check's timeout.
  - **BE-T17, the targeting rules:** every send names a `Target`; `BROADCAST_TARGET` is for infrastructure events only; task events go to the task's owner, with no fallback chain; a connection sees every subject's events only as the local admin (OIDC off).
  - **BE-C28:** raise `ExternalServiceException` (from `app.core_exceptions`) when an upstream fails, and document error responses with `ApiErrorResponseSchema`.
  - **D9a and RT10:** a paged list endpoint subclasses `PaginationQuerySchema` with `sort_by` as a `Literal`, sorts through `apply_sorting()`, and answers with `build_pagination_meta()`; the rule is that paged lists order stably (the `id` tiebreaker).
  - Nothing is written yet.
- **For phase 10:** the changelog takes the readyz format change, `register_readyz`/`register_healthz` → `register_check`, and the container edit; the `send_event` signature change, `bind_identity`'s `local_admin`, the callback's 401/403, the hook endpoint, and that a task without a subject no longer broadcasts; no `"unknown"` version on a failed fetch; `ExternalServiceException` and `ApiErrorResponseSchema`; `dev-watch.sh`, the `watchdog` dependency and the removal of `dev-server.sh`; the pagination helpers; and the SSE-without-OIDC fix.
- **Noticed, not changed:** `pyproject.toml.jinja` (app-owned) sets `[tool.ruff] exclude = ["vulture_whitelist.py"]`, which replaces ruff's default excludes. Outside a git repository (a fresh render before `git init`), `ruff check .` therefore lints `.venv`; inside one, `.gitignore` hides it. `extend-exclude` would fix it.
- **Tests:**
  - Readiness: `tests/test_health_service.py` is new (24), with DA's registration, caching, isolation, shutdown, metrics, healthz and drain cases, plus critical against non-critical, `disabled`, timeouts, joined runs and uncached failures. `tests/test_health_api.py` is rewritten for the new body: database, SSE gateway and S3 through the session app, behind a fixture that sets aside checks other tests registered and clears the cache. BE-T14's check tests are `TestReadinessCheck` in `tests/test_s3_service.py` (4); the SSE manager's are in `tests/test_sse_connection_manager.py` (4).
  - SSE: `tests/api/test_sse_callback.py` is new (33 with parameters): OIDC on (401 and 403 cases, cookie and bearer, additional role, test sessions, a `local-user` JWT is not the local admin), the read role, OIDC off (the local admin, role-checked test sessions, a stale session token), delivery through the callback's binding (MAT-10), the hook (both statuses, the local admin, single-shot, the endpoint, rejected statuses, ignored outside testing mode), and disconnect. In `tests/test_sse_connection_manager.py`, `TestTarget`, `TestSendEvent` and `TestLocalAdminBinding` replace the broadcast and `target_subject` classes. Correction 6's two tests are inverted as `test_task_events_never_broadcast_when_no_subject` and `test_progress_handle_has_no_default_target`, plus `TestTaskEventTarget`.
  - BE-T12: `tests/services/test_frontend_version_service.py` (6 → 14): failed fetches, `TestQueueVersionEvent` (3), and `TestPendingVersion` (5), with one run on a real manager.
  - BE-C28: `TestExternalServiceException` and `TestApiErrorResponseSchema` in `tests/test_error_handling.py` (5).
  - D9a: `tests/utils/test_pagination.py` is new (16), with paging over duplicate sort values on PostgreSQL in both directions.
- **Gates:** after the last commit, `kc project build`, `test` (mother 656 → 773 over the phase, domain 9, root backend suite) and `lint` are green. Playwright passed at one worker (3,279 MB peak), and `worker-isolation.spec.ts` (`tests/e2e/parallel/`) alone at two workers passed first time (5,402 MB peak). Step 1 and BE-T10/BE-T11 each passed the same gates when they landed: mother 690, then 744; Playwright peaks 3,338 and 5,283 MB, then 3,400 and 5,372 MB.

### 2026-10-17, phase 6: frontend fixes, Playwright on PostgreSQL

Frontend `23dd7dc` (FE02 with FE03), `c2d9fde` (FE04), `9a8e9b6` (FE06), `ebb01c1` (FE01, FE05's error body, FE07, FE08, FE09, phase 5's stale readiness comment), `540430c` (FE11, FE13, FE14), `3824500` (FE12), `3ac2cdf` (FE17), `cbe04b4` (FE18), `d2f6ded` (FE23), `f9f9a5b` (the worker-isolation spec) and `9bd07c9` (knip); backend `b9ac732` (FE23's backend half) and `57427d0` (ruff); parent `f38d2f8` and `101033b` (the chunk entries this one replaces), `096f326` (docs, the root comment), this entry. FE10 and FE20 had landed and were skipped (v0.20.4's placeholder route draws `UserDropdown` under `use_oidc and not use_app_shell`).

- **FE01:** only the enabled-child clone changed. The disabled wrapper's `data-testid={undefined}` already renders no attribute.
- **FE02 (deviation from DA's form):** one `task_event` listener per SSE provider, keyed by its `addEventListener` and reference-counted across the mounted hooks, feeds the replay buffer from mount. DA registered one per hook instance, which buffers and replays each event once per instance. The per-task listener no longer buffers. Nothing in the template or `test-app-domain` mounts `useSSETask`, so the Playwright suite doesn't exercise FE02 or FE03; only typecheck and knip see them.
- **FE03:** `percentage` is `value * 100`, and `SSEProgressEvent.data.value` is now required (`number`), as the backend schema has it. DA's `null` → `-1` mapping is left out.
- **FE04:** DA's patch. Services spawn `detached` and are stopped by `signalProcessGroup()` (`servers.ts`), SIGTERM then SIGKILL to the group; the worker's exit hook SIGKILLs every group. `testing-server.sh` execs `node_modules/.bin/vite`, and its `--preview` branch `node_modules/.bin/vite preview`. Checked: SIGINT to a run's process group during worker startup left no backend, gateway or Vite behind, each service ran as its own group leader, and a clean run left none either. FE23's backend (`uv` and Python) dies with its group.
- **FE05: not needed, confirmed.** The SSE and deployment specs (10 tests) pass without `auth.createSession()`: the Playwright backend runs with OIDC off, and `/api/auth/self` answers with the local admin. No sessions were added. The body-in-error change went into all three `AuthFactory` calls (DA changed `createSession` only).
- **FE06:** DA frontend's `deployment-sse.ts` and `deployment-reset.ts`, and the portal's `test-events.ts` (15 s default waits, `{ cause }` on the one throw that wraps an error). In the banner spec: the bridge re-wait after the reload click, and the portal's 15 → 30 s event waits; FE05's `createSession` there is left out. DA's `disconnect` comment named its auth-recovery path; the template's doesn't.
- **FE07:** the flag. `test-app-domain/src/lib/api/generated/types.ts` is regenerated from the existing `openapi-cache` (not refetched): 13 properties gain `?`, response properties with defaults among them (`status?`, the task event's `data?`, `task_type?`).
- **FE08:** the portal's `mountedRef` version, as is. **FE09:** the global allow. `expectConsoleError`'s added `Toast exception` pattern (`tests/support/helpers.ts:140`) is now redundant; it is left in place.
- **Phase 5's note:** the worker fixture's comments no longer say the backend's readyz waits for the gateway. The gateway still starts first.
- **FE11:** (a) the `src/routes/**` ESLint override; (c) `.env*` with `!.env.example` in `.gitignore`, which made the `.env.test` line redundant, so it went; (d) `build-fast`, with `build` = `build-fast && check`. (b) is not taken, as ruled.
- **FE11, `packageManager` (deviation from the worklist):** it stays `pnpm@9.0.0`. The worklist called it stale, but it decides which pnpm runs. The modern-app container's global pnpm is 12.8.1, yet in a project carrying the field it runs 9.0.0 (pnpm's managed package-manager versions), and the frontend `Dockerfile`'s corepack honours the field too. Dropping it would move every frontend to pnpm 12. pnpm 10 and later hoist nothing to the root `node_modules`, so FE11 (b) would become necessary, and the lockfile and build-script approval would change with it. That is a toolchain upgrade of its own, for the operator; phase 8's move to `modern-app-frontend-build` (corepack `pnpm@latest`) is where it would fit.
- **FE12:** `configureSseProxy` (the portal's copy, which deletes `transfer-encoding` before `writeHead`) is rendered under `use_sse` and sits on `/api/sse` in both `server` and `preview`. `server.strictPort: true`; `preview.strictPort` defaults to it. No `xfwd`, per phase 4. `/api/sse` does not carry `forwardOrigin`.
- **FE14:** `PLAYWRIGHT_RETAIN_VIDEO=true` gives `retain-on-failure`; anything else gives `off`. The name keeps its meaning of "turn video on", but it now has to be exactly `true`, where any non-empty value used to work.
- **FE17:**
  - **`vite.config.ts`:** DA's `define` (`process.env.VITE_TEST_MODE || 'false'`) and `external` (unless `VITE_TEST_MODE === 'true'`), under the `rollupOptions` key (Vite 7 pin).
  - **Preview runs:** `PLAYWRIGHT_PREVIEW_MODE=true` makes `startFrontend` pass `--preview`. `testing-server.sh` then execs `node_modules/.bin/vite preview --strictPort --mode test`.
  - **Addition beyond DA:** the `--preview` branch exits 1 ("--preview needs dist/ from 'VITE_TEST_MODE=true pnpm build'") unless `dist/assets/*.js` contains `__playwright_emitTestEvent`. Without that check, a plain build would time every spec out. A plain build has 0 test markers; `VITE_TEST_MODE=true pnpm build` has 1. Checked: the guard refuses a plain `dist/` and starts on a test build, and the frontend is ready in about 200 ms.
  - **SharedWorker specs:** the two in `sse-connectivity.spec.ts` call `test.skip(PLAYWRIGHT_PREVIEW_MODE !== 'true', …)` first thing in their bodies, so the default dev-server run skips them.
  - **Docs:** the two-step run is in `frontend/CLAUDE.md`'s "Playwright" section, which now also describes FE23's databases. `deployment-reset.ts`'s comment speaks of preview mode.
- **FE18:** each service gets 120 s and the worker fixture 300 s. The last non-OK status and body (500 characters) go into the timeout error. The poll sleeps only what is left of its interval, which stays at 200 ms, and a 503 is still not ready. The `ready at … (N ms)` line now prints with log streaming off too, three lines per worker start.
- **FE23, the frontend:**
  - **Names:** `<project_name>_e2e_<8 hex>_seed` and `…_w<parallel index>`, the project name taken from `PROJECT_NAME` in the app-owned `src/lib/consts.ts`, so `pg-admin.ts` needs no Jinja (all six apps define it). Phase 2's `<database_name>_e2e_` was not possible: the frontend has no `database_name`. pytest's `<database_name>_test_` stays disjoint, so neither sweep touches the other's databases (checked).
  - **`tests/support/helpers/pg-admin.ts`** (new, on `pg`): the admin URL is `TEST_DATABASE_ADMIN_URL` from the Playwright process (the shell, or the frontend's `.env.test`; not the backend's), defaulting to the sidecar, with `+psycopg` stripped for `pg` and kept in the backend's `DATABASE_URL`. Beyond the design, a run holds one admin connection named after its prefix from global setup to teardown, as `RunDatabases` does. The start sweep skips a live run's databases and any in use, and drops without `FORCE`. Checked with planted databases: a dead run's seed went, and a live run's seed, an in-use clone and a `test_app_test_*` stayed.
  - **Global setup:** keyed on `backend/alembic.ini` (plan correction 11); without it, it seeds nothing. It creates the seed from `template0` in production's locale, runs `uv run cli load-test-data --yes-i-am-sure` in the backend with `DATABASE_URL` at the seed and `OIDC_ENABLED=false` (like the old script: no `.env.test`, no `FLASK_ENV`), and publishes the run's prefix in `PLAYWRIGHT_DATABASE_PREFIX`.
  - **Workers** drop any leftover `<run>_w<parallel index>`, clone it from the seed, pass `--database-url`, and drop it at teardown. No `DB_POOL_*`: `testing-server.sh`'s `FLASK_ENV=testing` gives the phase 2 test pool.
  - **`global-teardown.ts`** (new, named in `playwright.config.ts`) drops the run's databases `WITH (FORCE)`, best effort, and closes the run's connection. Playwright 1.60 also runs it after a failed global setup (its task list puts teardowns before setups; read in the source, not seen).
  - `PLAYWRIGHT_SEEDED_SQLITE_DB`, `sqliteDbPath` and `--sqlite-db` are gone; `package.json.jinja` gains `pg` and `@types/pg` (`^8.23.1`).
- **FE23, the backend half (phase 2's deferral):** `initialize-sqlite-database.sh` and its `copier.yml` exclude line, `testing-server.sh --sqlite-db`, and the SQLite branch of `upgrade_database(recreate=True)` are gone. `recreate` now always drops the tables and runs the revisions.
- **The worker-isolation spec (`test-app-domain`):** at one worker both its tests share the worker's database, so once the list refetch lands it holds both items and `getByText(name)` fails strict mode. The dev server was usually slower than the assertion; the first preview pass on PostgreSQL failed it. Each test now looks for its item's description.
- **Ruff (backend, rides along):** `[tool.ruff] exclude` replaced Ruff's default excludes, so `ruff check .` in a fresh render before `git init` linted `.venv`. It is `extend-exclude` now (checked with `--no-respect-gitignore`). The root template's `pyproject.toml.jinja` sets no `exclude`.
- **knip:** `knip-template-ignore.json` gains `tests/support/global-teardown.ts` and `tests/support/helpers/pg-admin.ts`. Phase 6 removed no frontend template file.
- **For phase 7:**
  - FE16's env names: `VITE_TEST_MODE=true` for the build and `PLAYWRIGHT_PREVIEW_MODE=true` for the run; FE16's spec gates on `PLAYWRIGHT_PREVIEW_MODE` the way the SharedWorker specs do. A bridge it adds (`__sseForceWorkerReconnect`) must survive the test-mode build, since only that build reaches the worker. A rename touches `servers.ts`, the spec gates, `testing-server.sh`'s message, the comment in `vite.config.ts.jinja` and `frontend/CLAUDE.md`.
  - `test-app-domain`'s `openapi-cache` is stale: it lacks phase 5's SSE force-callback-error endpoint. Refresh it, and the generated types with it.
- **For phase 8:**
  - `local.py.jinja`: the runner's `pnpm build` is plain and nothing sets `PLAYWRIGHT_PREVIEW_MODE`, so CI skips the preview-only specs. The whole suite passes in preview mode, so one way is DA's: `VITE_TEST_MODE=true` on the runner's build step (which still runs `check`) and Playwright with `PLAYWRIGHT_PREVIEW_MODE=true`, leaving the dev-server path untested in CI. The other is a second, preview-only pass. Either way the image build (`Dockerfile`, `pnpm build`) stays plain. Update the last sentence of `frontend/CLAUDE.md`'s "Playwright" section when the runner changes.
  - CI's frontend suite now needs PostgreSQL too (the validation Job's `postgres` service, at the default `TEST_DATABASE_ADMIN_URL`). The runner already waits for it (`wait-for-services.py`) before both suites.
- **For phase 9 (RT13):** the preview-mode paragraph's source is `frontend/CLAUDE.md`'s "Playwright" section; the env names are final unless phase 7 renames them.
- **For phase 10:** the changelog takes FE03's scale (apps that scaled the percentage themselves), FE07's regenerated types, FE09's console policy, FE04's process groups, FE14's video default and the new meaning of `PLAYWRIGHT_RETAIN_VIDEO`, FE13's `Host $http_host`, FE12's SSE flush and `strictPort`, FE17's test-mode build fix and preview mode, FE18's timeouts, FE11's `.gitignore` and `build-fast`, FE23 (Playwright on PostgreSQL, the `pg` dependency, the SQLite path's removal) and ruff's `extend-exclude`.
- **What apps must change by hand (phases 11–16):**
  - **Every app, `package.json`:** add `pg` and `@types/pg` (`^8.23.1`) to `devDependencies`, apps without a database too: the template-owned global setup, teardown and worker fixture import `pg-admin.ts`, which imports `pg`. FE11's `build-fast`/`build` split reaches new apps only; it is optional, since nothing calls `build-fast`.
  - **Every app, backend `pyproject.toml`:** `exclude = ["vulture_whitelist.py"]` under `[tool.ruff]` becomes `extend-exclude` (all six carry it).
  - **Every app, behaviour:** the build regenerates `src/lib/api/generated/` (gitignored) with FE07's flag, so a property with a default that isn't required becomes optional, in request and response types alike; app code that reads such a response property as always present can fail `tsc`. An unexpected error toast no longer fails a spec (FE09), and a ui-state scope whose data is cached at mount now emits `ready` on mount (FE08); if an app spec changes outcome at the sync, look here first. The two SharedWorker specs skip in the default run. No app sets `PLAYWRIGHT_RETAIN_VIDEO`, and videos are now off unless it is `true`.
  - **Database apps (EI, IoTSupport, PilotApp):** Playwright now runs on the `postgres` sidecar, and `load-test-data` builds the seed through the revisions (no `create_all`), so the app's test data must load on PostgreSQL. `copier update` deletes their `initialize-sqlite-database.sh`. A spec that assumed a fresh SQLite copy per worker still gets a fresh clone per worker.
  - **ElectronicsInventory (12):** `src/components/parts/ai-part-progress-step.tsx:79,81` and `ai-part-cleanup-progress-step.tsx:79,81` multiply `progress.percentage` by 100 themselves. Drop that, or the bars read 100 times too high (FE03); FieldnotesApp's `use-inbox.ts` reads only the message, and no other app uses `useSSETask`. EI tracks `frontend/.env.test.example`: the new `.env*` ignore leaves a tracked file tracked, but a new copy would be ignored.
  - **IoTSupport:** besides dropping `xfwd` (phase 4), its template-owned `vite.config.ts` takes `configureSseProxy` and `strictPort`. Its `define` matched the template's old one, so FE17 merges cleanly.
- **For the operator (FE20, raised by the worklist):** `frontend/regen.sh` generates only `use_app_shell=true`, so the harness never builds or tests the no-shell variant that ZigbeeControl, FieldnotesApp and PilotApp use. Should a second generated variant be added? Likewise, the root test-app has a database, so no harness run covers FE23's no-database skip.
- **Gates (the last, after FE23):** `kc project build`, `test` (mother 773, domain 9, root backend suite) and `lint` are green; lint's one warning, an unused `eslint-disable` at `sse-context-provider.tsx:316`, predates phase 6. Playwright at one worker: 33 passed, 2 skipped (3,227 MB peak). `worker-isolation.spec.ts` alone at two workers passed first time (5,024 MB peak). Preview mode at one worker on the PostgreSQL backends, with the two commands in `frontend/CLAUDE.md`: 35 passed, none skipped. No `test_app_e2e_*` database was left after any run, and the last suite run rebuilt `root/test-app/frontend/dist` plain. The two earlier chunks' gates were green too (one worker: 3,323 and 3,285 MB peak; the isolation spec at two: 5,009 and 4,988 MB; FE17's preview pass on SQLite: 35 passed in 10.5 s).

### 2026-10-17, phase 7: frontend stages, SSE, defaults

Frontend `ec93ae9` (FE19 and FE32, with the OpenAPI refresh and knip), `13a4c62` (FE15, FE16 and FE27, with the spec), `fcce4fd` (FE21, FE28, FE29), `98375e0` (MAT-12 part 1) and `678a52a` (building without OIDC); parent `2d351fe` and `323bd88` (the step entries this one replaces), this entry.

- **`useUiSetup()`** (new, template-owned `src/hooks/use-ui-setup.ts.jinja`) is the one reader of `GET /api/ui-setup`, for FE19 and FE32. It returns `{ stage, exposeInternals }`, or `null` while loading and on any failure, a 403 included; `null` means no badge and no diagnostics. `staleTime: Infinity`, no refetch on focus, the default retry (none on a 4xx).
  - **The sign-in gate:** the toast container renders in `CoreProviders`, outside `AuthProvider`, so the hook can't read the auth context. Under `use_oidc` it watches the `/api/auth/self` query that `AuthProvider` runs, through a disabled `useGetAuthSelf` observer on the same cache key, and enables the ui-setup query once that query has succeeded. Fetching before sign-in would trip the generated client's 401-to-login redirect. A user without the app's roles gets 403 at `/api/auth/self` too, so ui-setup is never asked for. With `use_oidc=false` the query runs at once (checked in a render).
- **FE19:** DA's frontend copy. `showException` puts `serializeErrorDiagnostics(error)` (new `src/lib/utils/error-diagnostics.ts`, DA's; its vitest file left out) into `ToastOptions.diagnostics`. Where `exposeInternals` is true and the toast carries diagnostics, the icon becomes the copy button (copy icon on hover, a check after copying), which copies `[ERROR] <message>`, a `--- Diagnostics ---` line and the diagnostics. The gate is the internals fact, not DA's `stage !== PRD`. Deviations: the test id is `app-shell.toast.copy-button` (DA: `toast.copy-button`), and the button carries `data-copy-state` for the spec. The `items-center` alignment had landed.
- **FE32:** `src/components/layout/stage-indicator.tsx` (new; DA's without the divider, the docs link and the UAT link) sits between the top bar's spacer and the user dropdown, and shows the stage in capitals (`LOCAL-TST`), hidden on `prd`. Test id `app-shell.topbar.stage-indicator`. `copier.yml` excludes it, and its spec, with `use_app_shell=false`. The `--stage-indicator` token is in `index.css` (light `35 80% 45%`, dark `35 70% 60%`, DA's values). No dev-health indicator, no `/health` proxy.
- **OpenAPI refresh:** `test-app-domain/openapi-cache/openapi.json` comes from the backend test-app (Flask test client, `FLASK_ENV=testing`, OIDC off), and the generated `types.ts` and `hooks.ts` are rebuilt from it with `generate:api:build`. It gains `/api/ui-setup`, phase 5's `/api/testing/sse/force-callback-error` (`usePostTestingSseForceCallbackError`, unused: specs post with `page.request`), the readyz schema and `x-auth-roles` (`read` null: no role constants, as before). `useGetHealthReadyz` now returns `ReadyzResponse_…`.
- **FE15:** the worker and the direct EventSource count the stream as connected on the gateway's named `ready` event (no data line), not on `onopen`, which now only resets the worker's retry count. The worker keeps `readyReceived` (reset on close and on every new EventSource) and tells a late-joining tab `connected` only after `ready`, where it used to check `readyState === OPEN`. The direct path sets `requestId` on `ready` too. The `connection_close` listeners are gone: the gateway never sends that event. The pinned gateway (`ssegateway#stable`) sends `ready` as soon as the connect callback accepts, without AMQP (read in its `dist/routes/sse.js`). The `connected` test event moved with it, so a spec waiting for it now waits for `ready`; no spec needed a change.
- **FE16:** PilotApp's `8b8cf41` as the base (DA's behaviour), per correction 10.
  - **Worker:** a `rejected` listener parses `{status, message}` (status 0 when the payload doesn't parse, with the raw payload logged, truncated), sets `rejectedTerminal`, closes the stream and broadcasts `rejected` with a `connection`/`message`/`rejected` test event. `onerror` schedules no reconnect while `rejectedTerminal` is set. The new `reconnect` command closes, clears the flag and opens a stream with a new request ID; `handleConnect` clears the flag when it opens a stream.
  - **Provider:** on `rejected`, `isConnected` goes false and `probeSession()` runs `GET /api/auth/self`, which refreshes the session cookies. On 200 the stream reopens. On 401 nothing happens, since the API client's middleware is already redirecting to login. Anything else, a thrown request included, shows the toast "Connection to the server was lost. Please refresh the page to reconnect." `showError` is read through a ref, so a toast doesn't rebuild the SharedWorker. `reconnect()` now asks a live worker to reconnect, where it used to do nothing when the worker existed; its `isConnected` guard stays.
  - **Deviations from PilotApp and DA:**
    - **The direct path handles `rejected` too.** Both handled it only in the worker. The direct path runs under the dev server, and in production on browsers without SharedWorker, such as Chrome on Android. There the browser's own EventSource retry reopened a refused stream every few seconds without ever refreshing the session, which is the loop D3 rules out. The direct path now closes the stream on `rejected`, emits the same test event and runs the same recovery. It reopens only if nothing replaced or disconnected that stream in the meantime, and goes through a ref, because the React Compiler lint refuses a `useCallback` that names itself.
    - **`sse-context-provider.tsx` is now `.jinja`:** the probe needs `/api/auth/self`, which exists only with `use_oidc`. Without OIDC, `probeSession()` answers `failed`, so a refused stream shows the toast and stays closed: there is no session to refresh, and only the test hook refuses there. `copier.yml`'s `use_sse` exclude matches the rendered path, so it still applies (checked with a `use_sse=false` render).
    - **The bridge is `window.__sseForceReconnect`**, where PilotApp and DA have `__sseForceWorkerReconnect`, and it works on both paths: it posts `reconnect` to the worker or replaces the direct EventSource. It is declared in `playwright-binding.d.ts` and survives the test-mode build; the preview pass uses it.
    - **The SharedWorker decision is made when the module loads** (`USE_SHARED_WORKER`), not when the provider mounts. In test mode the opt-in is the `?__sharedWorker` query parameter, and `test-app-domain`'s index route redirects to `/items` before the provider mounts, which drops it. Until this fix **the two SharedWorker specs in `sse-connectivity.spec.ts` had been passing on the direct connection**; the new spec's path check caught it (DA navigated to a route that doesn't redirect, which the template can't name). The deployment provider's focus handler still reads `__sharedWorker` from the current URL, so in worker test mode it stays off after such a redirect; no spec depends on it.
- **FE27:** the portal's pass-through `SseGate`. Children render at once, `sse.gate.loading` is gone, and the component stays as a placeholder. The deployment bridge (`__deploymentSseControls`) now registers before the stream is ready, so `deploymentSse.ensureConnected()` would call `connect()` and replace the stream that is still connecting. It now waits up to 10 s for the mount connection, and calls `connect()` only if that doesn't arrive. `disconnect()`'s comment no longer says the bridge lives below the gate.
- **Preview-mode env names (correction 12): settled as they are.** `VITE_TEST_MODE=true` on the build and `PLAYWRIGHT_PREVIEW_MODE=true` on the run. They are DA's names, Vite exposes only `VITE_`-prefixed variables to the bundle, and nothing argues for a rename.
- **FE21:** the rest of it. `button:not(:disabled), [role="button"]:not(:disabled) { cursor: pointer }` in `index.css`'s base layer: Tailwind's documented form, where DA's bare `button` also gave disabled buttons the pointer. DA's dark tokens: `--primary`, `--ring` and `--link-hover` at `220 70% 65%`, `--destructive` at `0 72% 51%`. `td { vertical-align: middle }` is left out: the ruling doesn't name it, and it would re-align every app's tables. So are DA's slide-down keyframes, which serve DA features. **Checked: Tailwind 4 honours `@source` and `@plugin` inside the imported, app-owned `app-theme.css`**, with paths relative to that file. A probe class from a directory outside the project and a local plugin's base rule reached the built CSS, and neither did without the two lines. So an app's DA-style `@source` and `@plugin` lines go in `app-theme.css`, not `index.css`.
- **FE28:** the portal's version. `preventOutsideClose` (default true) sets the content's `onInteractOutside` to `preventDefault`. With false, `contentProps.onInteractOutside` applies, or Radix's default, which closes. Escape and the dialog's own buttons still close it. The overlay carries `data-testid="dialog-overlay"`, placed after the `overlayProps` spread, so a caller can't override it. Nothing in the template or `test-app-domain` renders a `Dialog`, so no spec exercises it; typecheck and lint see it.
- **FE29:** DA frontend's copy. While `loading` (and not `asChild`), a spinner is overlaid (`absolute inset-0`) on the button, which gets `relative`, and the label stays in place, `invisible`, wrapped in `inline-flex items-center`. With `asChild` the child renders alone, as `Slot` needs. **Deviation:** DA dropped the icon while loading, so a button with an icon still shrank; the icon stays now, `invisible`. A loading button's label is `visibility: hidden`, so its accessible name is empty while it loads; it is disabled, as before. `whitespace-nowrap` is in both `buttonBaseClasses` of `src/styles/button.ts`, which is app-owned, so it reaches new apps only.
- **MAT-12, part 1:** template-owned `scripts/fetch-openapi.js` now names `scripts/regenerate-openapi.py --frontend` (run from the repository root) and `pnpm generate:api:with-backend` in both its errors: the failed fetch of `pnpm generate:api` and `generate:api:build`'s missing cache. `package.json` (app-owned) gains `"generate:api:with-backend": "python3 ../scripts/regenerate-openapi.py --frontend"`. The root script finds the repository from its own path, so the working directory doesn't matter. Knip fails an unlisted binary, so the template-owned `knip.config.ts` gains `ignoreBinaries: ['python3']`. The standalone frontend test-app has no `../scripts/`, and nothing runs the script there. Checked: with no backend, `pnpm generate:api` prints the pointer (and a refused connection now shows `ECONNREFUSED`, where the message used to be empty), and `pnpm generate:api:with-backend` in the root test-app's `frontend/` started the backend, refreshed the cache and stopped it.
- **Building without OIDC (step 1's finding, fixed):** `top-bar.tsx` is now `.jinja`, and imports and renders `UserDropdown` only under `use_oidc`; the `use_app_shell=false` exclude still matches the rendered path. The render showed a second break: the generated API client (`scripts/generate-api.js`, not Jinja) always imports `buildLoginUrl` from `@/lib/auth-redirect` for its 401 redirect, but `copier.yml` excluded `src/lib/auth-redirect.ts` with `use_oidc=false`. So no `use_oidc=false` app could build, with the shell or without; Vite failed at that import. The exclude is gone: the file is one small function, and a backend without OIDC never answers 401. Checked: renders with `use_oidc=false`, one with `use_app_shell=true` and one with `false`, both pass `pnpm run build` (`build-fast` plus `check`: lint, tsc, knip). No app runs `use_oidc=false`. The default render's `top-bar.tsx` is unchanged.
- **The specs:**
  - `tests/infrastructure/toast/toast-diagnostics.spec.ts` raises an exception toast through the `app:testing:show-exception` hook, clicks the button and reads the clipboard, with `clipboard-read`/`clipboard-write` granted (Chromium only).
  - `tests/infrastructure/shell/stage-indicator.spec.ts` checks that the badge shows the stage the backend reports, uppercased.
  - Both first check `/api/ui-setup` on the backend: `expose_internals` true and a stage other than `prd`, which holds because Playwright's backends run under `FLASK_ENV=testing`. The `prd` path isn't covered: the template's specs don't mock routes.
  - `tests/infrastructure/sse/sse-auth-recovery.spec.ts` replaces DA's spec and PilotApp's `sse-connect-refusal.spec.ts`. Three cases run on each path: a valid session reopens the stream, with a new request ID and a version event delivered on it; a 401 from `/api/auth/self` sends the browser to `/api/auth/login?redirect=…`; a 500 shows the toast, and the stream stays closed (no `connected` within 3 s, and the status stays disconnected). Each case arms the refusal with `POST /api/testing/sse/force-callback-error` (401 twice, 403 once) and the session check with `auth.forceError()`, then opens the next stream with the bridge. The SharedWorker cases skip unless `PLAYWRIGHT_PREVIEW_MODE=true`, as the SharedWorker specs in `sse-connectivity.spec.ts` do; the direct cases run in every run, CI's included. Each case also checks, through CDP's `Target.getTargets` (Chromium), that an `sse-worker` shared worker exists in the SharedWorker cases and in no others.
- **knip:** `knip-template-ignore.json` gains `src/hooks/use-ui-setup.ts` and `src/lib/utils/error-diagnostics.ts`; `stage-indicator.tsx` and the specs fall under `layout/**` and `tests/infrastructure/**`, the provider and the top bar render to their old paths, and `auth-redirect.ts` was listed already. Nothing removed. `knip.config.ts` gains the `ignoreBinaries` above.
- **For phase 8:**
  - **The suite runner (correction 12):** its test-mode build step uses the env names above. Phase 6's note on the two options stands. With the direct path tested in every run, the preview pass adds the SharedWorker cases: 3 in `sse-auth-recovery.spec.ts` and 2 in `sse-connectivity.spec.ts`, which now really run on the worker. The default run skips those 5. The FE19 and FE32 specs need no preview mode.
  - **The no-shell variant (ruling 6):** it renders an empty `tests/infrastructure/shell/` (harmless). `regen.sh`'s domain copies must skip, for that variant, `src/components/layout/sidebar-nav.ts` (copier excludes it, and the domain copy's import of `./sidebar` fails `tsc`) and the `tests/infrastructure/shell/` and `auth-shell-home.spec.ts` specs. With `use_oidc=false` it now builds too.
  - **MAT-12, part 2, the stale-cache test:** the card asks for a test that fails when the committed `frontend/openapi-cache/openapi.json` differs from the backend's document. A per-test app's document is incomplete (Spectree documents only the process's first `create_app`), so the test runs `scripts/regenerate-openapi.py --frontend` in a subprocess and checks `git status`, or builds the app in a subprocess. It belongs to the root suite, and needs a backend that starts (`uv run dev`; a database app's database migrated). The backend registers its testing blueprints whatever the mode, so a dev-mode document carries the `/api/testing/*` paths, like the cache. Checked by hand: in the root test-app, `pnpm generate:api:with-backend` (the dev server) rewrote `frontend/openapi-cache/openapi.json` byte for byte as `test-app-domain` commits it, so such a test would pass on the harness today. Close MAT-12 when part 2 lands.
- **For phase 9:** the SSE client contract. `isConnected` means the gateway accepted the stream (`ready`). The app doesn't wait for SSE before rendering, so a spec that expects an SSE-delivered update first calls `deploymentSse.ensureConnected()` or waits for the `connected` test event. A refused stream recovers through the session, never through a retry loop.
- **For phase 10:** the changelog takes:
  - the copy-diagnostics button (shown where `expose_internals` is true), the stage badge (shell apps), `useUiSetup()`, the `--stage-indicator` token (overridable in `app-theme.css`), and the OpenAPI-cache refresh step below;
  - `connected` on `ready`; the `rejected` recovery on both paths (the toast, the login redirect, no retry loop) and its spec; `reconnect()` reaching a live worker; the non-blocking `SseGate` (no `sse.gate.loading`); `ensureConnected()`'s wait; the `__sseForceReconnect` bridge; and the `?__sharedWorker` fix;
  - **FE28, a behaviour change for every dialog:** a backdrop click no longer closes a `Dialog`; `preventOutsideClose={false}` brings it back; the overlay's `dialog-overlay` test id;
  - FE29's loading overlay (width kept, label hidden while loading) and `whitespace-nowrap` in `src/styles/button.ts` by hand; FE21's button cursor and the dark tokens, and that `@source`/`@plugin` lines belong in `app-theme.css`;
  - MAT-12 part 1: the errors that name `regenerate-openapi.py --frontend`, and `generate:api:with-backend` in `package.json` by hand;
  - `use_oidc=false` builds again, with or without the shell (`auth-redirect.ts` is no longer excluded).
- **What apps must change by hand (phases 11–16):**
  - **Every app: refresh the frontend's OpenAPI cache after the backend update** (`scripts/regenerate-openapi.py --frontend` at the root, or `pnpm generate:api` against a running backend), and commit `frontend/openapi-cache/openapi.json`. No app's cache has `/api/ui-setup` yet, and template-owned `use-ui-setup.ts` imports `useGetUiSetup`, so `tsc` fails until it does.
  - **Every app, `package.json`:** add `"generate:api:with-backend": "python3 ../scripts/regenerate-openapi.py --frontend"` to `scripts` (MAT-12; `knip.config.ts`'s `ignoreBinaries` comes with the update).
  - **Every app, `src/styles/button.ts`:** add `whitespace-nowrap` after `justify-center` in both `buttonBaseClasses` (FE29). No app has it.
  - **Every app, the update:** all six carry the template's `dialog.tsx` and `button.tsx` unedited, and the SSE files unedited too in EI, IoTSupport, DHCPApp and ZigbeeControl, so these merge cleanly. All six carry an older template `deployment-sse.ts`, which the update replaces. No app defines `--stage-indicator` or a `tests/infrastructure/{shell,toast}/` spec, so nothing collides.
  - **Behaviour:**
    - Pages now render before the stream is ready. An app spec that acts right after `page.goto` and expects an SSE-delivered update must call `deploymentSse.ensureConnected()` first. A survey found one candidate: ZigbeeControl `tests/e2e/tab-manager.spec.ts:137-170`, which posts tab status right after `expectLoaded()` and then expects the SSE-driven `data-status`. DHCPApp's "Live"/"Disconnected" dot (`src/routes/index.tsx:8-24`) reads "Disconnected" until `ready`; its spec (`tests/dhcp/leases.spec.ts:165-170`) already waits with `ensureConnected`.
    - A backdrop click no longer closes a `Dialog` (FE28). A survey found no app spec or code that closes a `Dialog` that way or passes `onInteractOutside`. FieldnotesApp's `tests/shell/app-bar.spec.ts:267` clicks outside a hand-rolled portal overlay (`actioner-failure-dialog.tsx`), not a `Dialog`, so it is unaffected. No app spec checks a button's spinner, or its name while it loads (FE29).
    - The dark-mode `--destructive` doesn't reach EI, ZigbeeControl or FieldnotesApp, which set their own in `app-theme.css`.
  - **Shell apps (EI, IoTSupport, DHCPApp):** the badge appears wherever the stage isn't `prd`, which includes the dev stack (`local-dev`) and CI (`tst`). Deployed apps run `prd`, so they show none; the diagnostics button still shows there, because they set `HOMELAB_INTERNAL=true` (operator answer 2).
  - **FieldnotesApp (15):** its FN-38 frontend edits conflict with FE16. They swap the inline `makeUniqueToken` for `@/lib/utils/random` and call `nameSseConnection` in `sse-worker.ts` and `sse-context-provider.tsx`, and `src/lib/api/sse-connection.ts` then adds `X-SSE-Request-Id` to API requests. Phase 15 drops them along with the backend binding (correction 10). If they were kept, the gate no longer holds screens back until the stream is named, so their fetches would go out without the header, and `tests/shell/sse-connection.spec.ts:57-60` would fail.
  - **PilotApp (16):** take the template's side of `8b8cf41` in `sse-worker.ts`, `sse-context-provider.tsx` and `playwright-binding.d.ts`. The bridge is renamed, and PilotApp's specs don't use it. Its `tests/infrastructure/sse/sse-connect-refusal.spec.ts` is not a template file, and copier leaves it alone. It opens a bare EventSource, so FE15 doesn't affect it, and its role cases are Pilot's own: keep it or drop it.
- **Gates:** `kc project build`, `test` (mother 773, domain 9, root backend suite) and `lint` are green. Lint's one warning, the unused `eslint-disable` in the SSE provider, predates phase 6. The Playwright suite at one worker passed 38 with 5 skipped (3,177 MB peak), and `worker-isolation.spec.ts` alone at two workers passed first time (4,540 MB peak). Two edits to the fetch error's text came after `test` and the Playwright runs; `build`, whose frontend `pnpm run build` runs `check`, passed after them. The peaks are sampled from the modern-app container's cgroup each second, because `--output-mode full`, which prints the counts, drops the runner's peak line. Steps 1 and 2 ran the same gates green: Playwright at one worker passed 35 with 2 skipped (3,243 MB) after step 1, and 38 with 5 skipped (3,316 MB) after step 2, and the isolation spec at two workers passed first time (5,081 and 4,691 MB). Step 2's preview pass at one worker, with the two commands in `frontend/CLAUDE.md`, passed 43 with none skipped, and `root/test-app/frontend/dist` was rebuilt plain afterwards; before the `USE_SHARED_WORKER` fix it failed exactly the three SharedWorker cases, at the path check.

### 2026-10-17, phase 8: root CI, images, dev stack, architecture, tooling

Frontend `f308682` (the `@preview` tag), `b0b1b16` (step 2) and `0b87bad` (ruling 6); backend `96ee519` (step 2), `332a431` (the `database_name` fix) and `40cd8da` (MAT-12 part 2); parent `07fd094` (step 1), `8d28f63` (step 3), `0d3f7a7` (step 4), `953bbf5` (step 5), `67601c2` (step 6), `3f43ff2` (MAT-12's docs), `2ea8724` (ruling 6), `33c6bae`, `2d5bfe8` and `13611f4` (the step entries this one replaces), this entry; `/work/scratch/DockerImages` `7e7c1f7` (step 2, committed, **not pushed**).

**Step 1, CI.**

- **`Jenkinsfile.jinja`** is PilotApp's declarative file (correction 2), with:
  - the uv strings: `install: 'uv sync --locked --no-dev'`, `run: 'uv run --no-sync'`;
  - `services:` holding `[name: 'postgres', image: 'postgres:18-trixie', env: [POSTGRES_PASSWORD: 'postgres']]` (no `resources`) under `use_database` and today's RustFS sidecar under `use_s3`, and `services: []` with neither;
  - `env:` holding `STAGE: 'tst'`, `BUILD_CACHE: 'true'` and, under `use_s3`, the four `S3_*` values (bucket `<project_name>-validation`);
  - the comments: the wait for the services, the PostgreSQL sidecar, and ElectronicsInventory's S3 comment, word for word.

  The header's first paragraph goes through Jinja's `wordwrap(97)`, which reproduces the hand-moved headers of PilotApp, FieldnotesApp, IoTSupport and ZigbeeControl exactly.
- **Checked:** the controller's declarative linter (`pipeline-model-converter/validate`, with `JENKINS_TOKEN`) accepted three renders: the root test-app (database and S3), S3 only, and neither. Rendered with PilotApp's answers minus the database, the file differs from PilotApp's only in `env:`. `modernApp.test` stringifies every `env` value and counts a JUnit stem `frontend-*` under the `frontend` suite. No Jenkins run was possible.
- **Build cache (RT05, correction 4):**
  - `run-suite --build-cache` is on by default when `BUILD_CACHE=true`. `scripts/build-cache-get.sh` and `-put.sh` are template-owned copies of `HomelabAppsDeploy/jenkins/chart/scripts/`, byte for byte, run with `sh`.
  - The runner restores the pnpm store (`pnpm store path`, run in `frontend/`) before the install. It uploads after a miss, and only when the `--frozen-lockfile` install succeeded. A failed get or put is not a step result.
  - **Key:** `pnpm-<sha256 of frontend/pnpm-lock.yaml>.tgz`, one fixed prefix for every app. The tarball is relative to the store path (`…/v3` under pnpm 9).
  - **Tested** against a local stand-in server (`BUILD_CACHE_URL`), not the real cache. A miss uploaded 58 MB for the root test-app; the next run restored it in 1 s and installed in 1 s.
- **The preview pass (correction 12): a second, preview-only pass, not DA's single preview run.**
  - **Why:** DA's way would drop the dev-server path from CI, and from every local suite run too. That path is the one developers and `pnpm playwright test` use, and the one FE12's SSE proxy and the `?__sharedWorker` handling live on. A whole second pass would double Playwright time, against `modernApp.test`'s fixed 3,600 s deadline, for apps with large suites. So the second pass runs only the specs that need a production build, and the image build stays plain.
  - **Selection** is by a Playwright tag. The five SharedWorker cases carry `@preview` (frontend `f308682`): a `{ tag }` on the SharedWorker `describe` in `sse-auth-recovery.spec.ts`, and on the two tests in `sse-connectivity.spec.ts`. They keep their skip guard.
  - **The runner,** after the dev-server pass, lists `--grep @preview` within the selected specs (`--list --pass-with-no-tests`). If any are selected, it runs `VITE_TEST_MODE=true pnpm build`, then Playwright with `--grep @preview` and `PLAYWRIGHT_PREVIEW_MODE=true`, into `frontend-preview.xml`. With none selected, as for the worker-isolation spec alone, it skips the pass. It clears both variables for the plain build and the dev-server pass, and leaves `dist/` a test-mode build, which `.dockerignore` keeps out of the image.
  - **Cost** in the root test-app: 16 s of build and 8 s of tests. The JUnit report lists the five twice: skipped in `frontend.xml`, passed in `frontend-preview.xml`.
  - **Deviation:** the plan put the change in `local.py.jinja` alone; the tag is a frontend template change.
- **Docs:** `docs/copier_approach.md` (the `Jenkinsfile` line, the build-cache scripts), `CLAUDE.md`'s `use_database` row, `copier.yml`'s `use_database` help, and the `@preview` convention in `frontend/CLAUDE.md`'s Playwright section.

**Step 2, images (S3).**

- **DockerImages `7e7c1f7`, `modern-app-backend-build` (worklist §6.1):** adds `COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /bin/`, `UV_PYTHON_DOWNLOADS=never` and `UV_LINK_MODE=copy`, and drops `pip install poetry` and the three `POETRY_*` lines; the apt block stays. `modern-app-backend` and `modern-app-frontend-build` are unchanged.
  - **Why 0.13.1:** phase 1 pinned no uv version, and 0.13.1 is what the modern-app toolchain runs and what DevGuides' `Dockerfile` pins. The estate's other images install uv unpinned with the astral installer. This one is pinned per §6.1, so the weekly rebuild doesn't move it.
- **Backend `Dockerfile.jinja` (BE-C17; app-owned, so it reaches new apps only):** the build stage is `FROM registry:5000/modern-app-backend-build AS build`, with no `ENV`, apt or `pip install uv`; the runtime stage is `FROM registry:5000/modern-app-backend`, with no apt; the rest is unchanged. The runtime image carries libmagic, the image codecs and libpq whatever `use_s3` and `use_database` say, so an app without them gets a slightly larger image, all of it in the shared base layer.
- **Frontend `Dockerfile.jinja` (template-owned; RT05's image half):** `FROM registry:5000/modern-app-frontend-build AS build`; the corepack line goes, and `ARG BUILD_CACHE_URL` comes in.
  - After `COPY package.json pnpm-lock.yaml`, one `RUN` restores and then installs: `STORE="$(pnpm store path)"`, `mkdir -p "$STORE"`, then `curl -sSf "${BUILD_CACHE_URL:-http://build-cache.jenkins-prd.svc.cluster.local}/pnpm-$(sha256sum pnpm-lock.yaml | cut -d' ' -f1).tgz" | tar -xzf - -C "$STORE"` (the runner's key) ending in `|| echo "No pnpm store in the build cache"`, then `pnpm install --frozen-lockfile`. One `RUN` puts the store and node_modules' hard links in one layer.
  - **Deviation:** the `mkdir -p`, because `tar -C` needs the directory. DA's `build-cache-get.sh` creates it too.
  - **pnpm (ruling 7):** the image prepared `pnpm@latest`, but corepack runs what `packageManager` names, so the build runs pnpm 9.0.0. Its store is `/root/.local/share/pnpm/store/v3`: the v3 layout the runner's tarball holds.
- **Not verified: no image was built.** This environment has no image builder: `kaniko` answers "pod was composed with no image builder". Building would need `imageBuilder: true` in `.kubecoder/config.yaml` and `kc env restart`, which is the operator's call. So a build of any of the three Dockerfiles, the DockerImages job building the new image, and a kaniko build reaching the build cache are unverified (worklist §6.2's reasoning stands). `/uv` and `/uvx` in `ghcr.io/astral-sh/uv:0.13.1` rest on DevGuides' identical line, which builds.
- **The frontend `RUN`, simulated:** its text, taken from the rendered `Dockerfile`, ran with dash in the modern-app container, with a clean `HOME` and corepack's shim. pnpm was 9.0.0 and the store `…/store/v3`. On a hit (a local stand-in serving a pnpm 9 store tarball for the root test-app's lockfile: 58 MB, key `pnpm-ee6c2573….tgz`), `pnpm install --frozen-lockfile --offline` succeeded. On a miss (a 404, and the real cache's default URL, empty), it printed the miss line and exited 0.
- **The backend, reasoned against §6.1's image contents:** the build image carries every apt package the old build stage installed, under any flags, and the runtime image every old runtime package. Both images are on `python:3.13-slim`, so the venv's `/usr/local/bin/python3.13` link resolves in the runtime stage. `requires-python` is `>=3.13,<4`.

**Step 3, dev stack.**

- **`Procfile.dev.jinja` (BE-C29's root half):** the backend line is `cd backend && env -u VIRTUAL_ENV PORT=<backend_port> scripts/dev-watch.sh`. The header now says the backend restarts on a code change, and "Werkzeug auto-reload" is gone.
- **Checked in the root test-app with `scripts/dev.py`:** readyz answered 200 with `"stage": "local-dev"`. An edit to `backend/app/utils/__init__.py` drained the server (a lifecycle shutdown in `logs/backend.log`) and started a new one under a new PID. On `scripts/dev.py stop`, honcho sent SIGTERM to the three services, watchmedo passed it on, and the server logged a graceful shutdown; no honcho, watchmedo, server, vite or gateway process was left. The setup was by hand, because `regen.sh` leaves no venvs, `.env` or node_modules: `uv sync` (root, backend), the `.env` printf from its `project.yaml`, a dev database, `cli upgrade-db` and `pnpm install`.
- **RT03:** nothing else to take. Per worklist §2, the template's `dev.py`, `dev-sse-gateway.sh` and `regenerate-openapi.py` match or beat DA's, and DA's other scripts are marked leave.
- **`STAGE` and `HOMELAB_INTERNAL` are not seeded.** This follows phase 3 and deviates from the step's text.
  - With `STAGE` unset, the dev stack runs `local-dev`: `FLASK_ENV` is unset there, so it is `development` by default, and `local-dev` is D9b's ruled default for that (readyz confirms it).
  - `HOMELAB_INTERNAL` changes nothing where `STAGE` isn't `prd`.
  - A seeded `STAGE=local-dev` would pin the stage even when a developer sets `FLASK_ENV=production` to try the `prd` path.
  - The seed is written only for apps with a database or S3, and the backend's `.env.example` already documents both settings.

**Step 4, the architecture producer (D8, RT06; correction 1 and operator answer 3 applied).**

- **`Jenkinsfile.architecture.jinja`** (new) is the pipeline guide's app-architecture reference file, with `repo_name` and `github_owner` filled in. Its header goes through `wordwrap(97)` like the `Jenkinsfile`'s. It is `_skip_if_exists` in the root `copier.yml`; all six apps have the file, so `copier update` leaves it alone.
  - **Checked:** the root test-app's render is the guide's reference file and PilotApp's file with the names swapped. Rendered for FieldnotesApp, it matches that app's file byte for byte. The controller's declarative linter accepts it. No Jenkins run was possible.
- **No `scripts/arch-validate.py` and no model.** The validator ships in `aac-tools`, and the template ships no `docs/architecture/` (worklist §6.5).
- **The generated `CLAUDE.md`:** the repo-structure line names `Jenkinsfile.architecture`. A new "Architecture model" section says the model is kept current centrally (`tooling/fleet.py update` in `pvginkel/Architecture`), and that nothing runs from the app after a change. While `docs/architecture/` holds no model, the agent nudges the operator to seed it, in order: `/seed-architecture`, in a clone that `python3 tooling/fleet.py stage <Repo>` stages; push the model; then the operator creates `AaC/<Repo>` from the guide's `config.xml` and adds the `pipeline-producers.yaml` entry.
- **`.kubecoder/config.yaml.jinja`** gains the `aac-tools` toolchain. The root `lint` in **`project.yaml.jinja`** runs `cexec aac-tools arch-validate docs/architecture/*.yaml`, behind an `if ls docs/architecture/*.yaml` guard that prints a pointer to `CLAUDE.md` while there is no model, so a new app's `kc project lint` is green before seeding. The guard was checked by hand both ways; `arch-validate` itself didn't run, because this environment has no `aac-tools`.
- `CLAUDE.md` and `.kubecoder/*` are app-owned, so all of this reaches new apps only.

**Step 5, the dependency checker (RT07):** template-owned `scripts/check_updates.py`, stdlib only, run as `cexec modern-app python3 scripts/check_updates.py [--json]`, with no `pyproject.toml` entry (worklist RT04 row). It keeps DA's file name, unlike the template's hyphenated scripts.

- **Discovery:** a directory with a `uv.lock` (and a `pyproject.toml`) is a Python component; a workspace's members come through its root's lock, labelled `backend (python, <member>)`. A directory with a `package.json` is an npm component. Hidden directories, `node_modules`, `test-app`, `dist`, `build`, `logs` and `test-results` are pruned.
- **Deviation from the worklist's RT07 note:** Python uses `uv tree --outdated --depth 1 --frozen` (text, parsed), not `uv pip list --outdated`. It lists direct dependencies only, with their dependency groups, at their locked versions, and needs no venv. npm stays on DA's `pnpm outdated --format json`, which needs `node_modules`; without them the component is a warning.
- **Output:** a component that fails is a warning on stderr, and the exit is 0. DA's major/minor/patch tables and `--json` are kept.
- **Checked** in the root test-app, and read-only against FieldnotesApp (four workspace members and a frontend; 47 updates).

**Step 6, the rest of the root diff:** nothing more to take. Worklist §2's takes have all landed: RT01's wait helpers are phase 2's `backend/scripts/wait-for-services.py`, the test-mode env is step 1's preview pass, RT02 is step 1, and RT04's RT07 is step 5 and its `CLAUDE.md` section step 4. The commit fixes two comments in `.kubecoder/config.yaml.jinja` that step 1 made stale: the RustFS service runs in the `Jenkinsfile`'s "Test" stage (there is no "Run validation" stage), and the images are built with `helmCharts.kaniko2`. DA's `test_process.py` stays out (worklist: leave, unless the operator wants a root test gate).

**MAT-12, part 2:** template-owned backend `tests/test_openapi_cache.py`. **MAT-12 is closed** (Done, Resolved), citing frontend `98375e0`, backend `40cd8da` and parent `3f43ff2`.

- **How it works:** it builds the app in a subprocess (`create_app(skip_background_services=True)` and the Flask test client), because Spectree documents only a process's first app. It writes the document to a file, compares it with `../frontend/openapi-cache/openapi.json` as parsed JSON, and on a mismatch fails naming the added, removed and changed paths and `scripts/regenerate-openapi.py --frontend`. It skips where no frontend sits beside the backend, as in `backend/test-app`: the domain suite now reports 9 passed and 1 skipped.
- It runs in the suite runner's backend suite, so in CI. **Checked** in the root test-app: it passes on the committed cache, and fails on a doctored one naming all three kinds of change.
- The generated `CLAUDE.md` mentions the test, and `copier_approach.md` lists it.

**The hyphenated-`project_name` setup bug, found in step 3 and fixed at both causes (backend `332a431`).**

- **The bug:** the two templates' `database_name` defaults differed: the root's was `project_name | replace('-', '_')` (`test_app`), the backend's `project_name` (`test-app`). `project.yaml`'s seeded `backend/.env` names the root's, but `scripts/init-dev-database.py` read `DATABASE_URL` from the process environment only, so it created `test-app`, and `cli upgrade-db`, which does read `.env`, failed with `database "test_app" does not exist`. It hit new apps only: the existing apps' `project.yaml` is app-owned.
- **The fix:** the backend's `database_name` now defaults to the root's `project_name | replace('-', '_')`, and `scripts/init-dev-database.py` (template-owned) loads `backend/.env` with `load_dotenv` before it reads `DATABASE_URL`, as `wait-for-services.py` does. The environment still wins.
- **Checked in the root test-app,** after dropping the harness's stale dev databases `test-app` and `test_app`: `kc project setup backend` created `test_app` and `cli upgrade-db` migrated it; a `.env` naming another database made the script create that one; a `DATABASE_URL` in the environment won over `.env`.
- **No app needs a by-hand edit.** Every app's backend answers record `database_name`, so the new default changes no render. The three database apps' two answers already agree (ElectronicsInventory `electronics_inventory`, IoTSupport `iotsupport`, PilotApp `pilot`); DHCPApp, ZigbeeControl and FieldnotesApp have no database. The script change arrives with the update.

**Ruling 6, the no-shell test-app** (frontend `0b87bad`, parent `2ea8724`).

- **`frontend/regen.sh`** renders two test-apps: `test-app` (`use_app_shell=true`) and `test-app-no-shell` (`use_app_shell=false`). Every other answer is the same, so a diff between the two is the flag's effect; `use_oidc` and `use_sse` are true, as in all three no-shell apps (ZigbeeControl and PilotApp checked). `bash regen.sh` renders both; `bash regen.sh <name>…` only those named.
- **The domain copies** for the no-shell render skip `sidebar-nav.ts`, `tests/infrastructure/shell/{navigation,mobile-menu}.spec.ts` and `auth-shell-home.spec.ts`, as phase 7 found; the render keeps an empty `tests/infrastructure/shell/`. **No template fix was needed:** the variant passed `pnpm run build` and `pnpm run check` on its first render.
- **Gitignored, not tracked** (a new `frontend/.gitignore`): nothing copies or runs it, since `root/regen.sh` takes `test-app` alone, and its `package.json` and `pnpm-lock.yaml` are byte-identical to `test-app`'s. Tracking it would add some 200 files and repeat `test-app`'s regen churn on every template commit, with no reader for it.
- **knip and the ignore:** knip reads every `.gitignore` from its directory up to the git root, so under `frontend/.gitignore` it saw no files and reported every dependency unused. So `regen.sh` makes a gitignored test-app a git repo of its own and commits the render before the install. knip then stops at the render's own root and reads only its `.gitignore`, as in an app, and `vite.config.ts` gets the HEAD it stamps into `version.json` (an empty repo printed a `git rev-parse HEAD` stack trace).
- **Cost:** the variant's regen takes about 5 s. Its install links from the environment's shared pnpm store (`pnpm_config_store_dir`, `/work/.pnpm-store`, on the same filesystem as `/work`) in 4 s.
- **`project.yaml`:** `setup` regenerates each frontend test-app that was never generated here (`regen.sh test-app`, `regen.sh test-app-no-shell`, each keyed on its gitignored `routeTree.gen.ts`), so an existing pod gains the variant without churning `test-app`; checked by deleting the variant and running `kc project setup frontend`. `build` and `lint` run `pnpm run build` and `pnpm run check` in both. No Playwright run for the variant (ruling 6).
- **Docs:** `CLAUDE.md` (Quick Start, "Validating both templates"), `frontend/CLAUDE.md` (structure, rules 1–4, a `use_app_shell` row in the flag table), `docs/copier_approach.md` (tree, validation) and the `project.yaml` comments. `docs/change_workflow.md` describes only the backend test-app, so it is unchanged.
- **Seen, not fixed:** both frontend test-apps' `eslint` warn (not error) of an unused `eslint-disable` directive for `react-hooks/set-state-in-effect` at `src/contexts/sse-context-provider.tsx:441`, a template file.

**What apps meet in phases 11–16.**

- **The `Jenkinsfile`.** The old render is the scripted file, so `copier update` conflicts across the file. Resolve to the app's file plus the template's new lines. Every app gains `STAGE: 'tst'` and `BUILD_CACHE: 'true'` with their comments. The four Poetry apps also move to the uv strings.
  - **IoTSupport (11):** gains the postgres service. It keeps its `withVault` wrapper, the opensearch service, the Keycloak env and `secrets:`.
  - **ElectronicsInventory (12):** gains the postgres service. It keeps the docs-image stage and its three-image header. Its S3 block already matches.
  - **DHCPApp (13):** keeps `Job: Dnsmasq/DHCPApp` and its own header wrapping. Its pin key `dhcpapp_ui` is its answer, so it renders.
  - **ZigbeeControl (14):** keeps its "No data sidecars" comment.
  - **FieldnotesApp (15):** gains only the `env:` lines.
  - **PilotApp (16):** gains the postgres service and the comments above `modernApp.test`.
- **The by-hand backend `Dockerfile` edit.** No app's `frontend/Dockerfile` has drifted from the template, so `copier update` replaces it cleanly.
  - **Every app:** the build stage becomes `FROM registry:5000/modern-app-backend-build AS build` and loses its `ENV` lines (`POETRY_*`, `UV_*`, `PYTHON*`), its apt block and `pip install poetry|uv`. The runtime stage becomes `FROM registry:5000/modern-app-backend` and loses its apt block.
  - **The four Poetry apps** take the uv packaging in the same edit: `COPY pyproject.toml uv.lock /app/` and `RUN uv sync --locked --no-dev --no-install-project`.
  - **IoTSupport (11):** rewrite it to the template default. Today it has no build-stage apt, copies `COPY run.py alembic.ini ./` style, has one `COPY --from=build /app /app` and no `DATA_PATH`. Its runtime `ENV` sets `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`; keep them, because the runtime image sets neither.
  - **ElectronicsInventory (12):** a clean swap. Its `frontend/Dockerfile.docs` (app-owned, `node:lts-slim` plus corepack) may move to `modern-app-frontend-build` too; that is optional.
  - **DHCPApp (13), ZigbeeControl (14) and PilotApp (16):** clean swaps.
  - **FieldnotesApp (15):** keep the runtime `apt-get install -y --no-install-recommends git ca-certificates` with its comment; `COPY packages /app/packages`, `COPY mcp-server /app/mcp-server` and `COPY eval/pyproject.toml /app/eval/pyproject.toml`; and `--no-editable` on `uv sync`.
- **`tests/test_openapi_cache.py`** arrives with the backend update and fails until the app's cache is refreshed. Phase 7 already has every app refresh and commit `frontend/openapi-cache/openapi.json` after the backend update, so do that before the gates. The test builds the document under the test settings (`.env`, then `.env.test`), and `regenerate-openapi.py` builds it from the dev server under `.env`; for the template the two are the same. If the test still fails right after a refresh, the app's document depends on its settings, for example a blueprint registered under a flag in `register_blueprints`. Find that before changing the test.
- **The preview pass:** no app has its own spec that gates on `PLAYWRIGHT_PREVIEW_MODE` today. The template's SSE specs arrive tagged.
- **`scripts/check_updates.py`** arrives with the root update; nothing by hand.
- **The architecture files:** nothing required. Optional, and the operator's call, since `.kubecoder/*` is app-owned: the template's `arch-validate` lint step, which today only ElectronicsInventory and PilotApp have. The `aac-tools` toolchain is in EI, DHCPApp, FieldnotesApp and PilotApp, and missing from IoTSupport and ZigbeeControl.
- **The no-shell apps (ZigbeeControl, FieldnotesApp, PilotApp):** their flag combination is now built and checked by the harness; nothing by hand.

**For phase 9:**

- **RT13:** the convention is that a spec needing a production build skips without `PLAYWRIGHT_PREVIEW_MODE=true` and carries `@preview`. `frontend/CLAUDE.md`'s Playwright section says so.
- **Still open, for the operator or phase 9 (worklist §4.3):** after step 1, JenkinsPipelineUtils' `docs/pages/types/modern-app.md`, which says files follow "the reference file below, not the template", and the jenkins-pipelines skill's "two files predate the guide" paragraph (KubeCoderConfig) are stale. Done in phase 9.

**For phase 10, the changelog takes:**

- the new `Jenkinsfile`, with the per-app resolutions above; `scripts/build-cache-*.sh`, `--build-cache` and `BUILD_CACHE`; the preview pass and the `@preview` tag; `STAGE=tst` in CI;
- the backend `Dockerfile` default on the two base images (by hand for existing apps, as above); the frontend `Dockerfile` on `modern-app-frontend-build`, with the build-cache restore and the `BUILD_CACHE_URL` build arg; the DockerImages dependency (correction 13);
- `Procfile.dev` on `dev-watch.sh`;
- `Jenkinsfile.architecture` (new apps only, app-owned), the `CLAUDE.md` architecture section, and `aac-tools` with the lint step;
- `scripts/check_updates.py`;
- the stale-cache test (MAT-12; apps refresh their cache with the update);
- the backend `database_name` default and `init-dev-database.py` reading `.env`.

The no-shell test-app is harness-only and reaches no app.

**For phase 17 (correction 13):** push DockerImages `7e7c1f7` first, let its job rebuild `modern-app-backend-build`, and check that `registry:5000/modern-app-backend-build:latest` has `/bin/uv`. Only then push any app whose backend `Dockerfile` moved. The frontend move needs no image change. None of the three images has been rebuilt since 2026-06-17, so the operator should also confirm that a DockerImages build of them runs.

**For the operator:**

- **No action for the six apps.** Per new app: seed the architecture model, push it, create `AaC/<Repo>`, and add the `pipeline-producers.yaml` entry, as the generated `CLAUDE.md` says.
- **Optional, before phase 17:** an image build here needs `imageBuilder: true` in `.kubecoder/config.yaml` and `kc env restart`.
- **Harness only:** the root test-app's backend answers carry `sse_gateway_port: 3002`, but its gateway runs on 3001. So its dev-stack readyz reports `sse_gateway` as an error, which is non-critical (`degraded`).

**Gates:**

- **Steps 1–6 and MAT-12:** `kc project build`, `test` (mother 773; domain 9, then 9 passed and 1 skipped after MAT-12; root backend suite all passed) and `lint` were green after each step's template edits. After step 6's comment fix and its docs, `kc project build root` and `kc project lint root` were green. The regen churn of a template repo a step didn't change was discarded.
- **Ruling 6:** `kc project build`, `test` (mother 773; domain 9 passed, 1 skipped; root backend suite all passed) and `lint` are green, with `pnpm run build` and `pnpm run check` passing in both frontend test-apps.
- **Playwright, step 1, through the runner:**
  - at one worker, 38 passed and 5 skipped on the dev server, then the preview pass passed 5 (runner peaks 3,254 and 1,297 MB; cgroup peak 3,536 MB);
  - `worker-isolation.spec.ts` alone at two workers passed first time (5,080 MB runner peak), and the preview pass was skipped;
  - one spec file (`sse-connectivity.spec.ts`) ran both passes;
  - a CI-shaped run (`STAGE=tst BUILD_CACHE=true`, `--output-mode full --junitxml-dir … --retries 2`, one worker, a fresh pnpm store and no `node_modules`) was green, with `SUITE_RESULT` backend 9/0/0, frontend 38/0/5 and frontend-preview 5/0/0 (3,650 MB cgroup peak). So `STAGE=tst` changes no outcome of the domain or Playwright suites.
- **Playwright at the close,** with all of phase 8 in: `run-suite --suite frontend` at one worker passed the dev-server pass and the preview pass (runner peaks 3,309 and 1,307 MB).

### 2026-10-17, phase 9: conventions guide and skill

Run in two chunks. Parent `91f1de1` (the guide's source), `5374474`, this entry; DevGuides clone `92bc97d`; KubeCoderConfig clone `c5db31a`, `ec17ea5`; JenkinsPipelineUtils clone `01bf1fe`. None is pushed. DevGuidesPrivate is cloned at `/work/scratch/DevGuidesPrivate` (`9579fbf`, unchanged), for the hub build only.

**The guide (step 1):**

- **Where:** `guide/`, a top-level folder of this repo (`docs/` holds the port's working documents). It holds `mkdocs.yml`, `pyproject.toml` and `uv.lock` (Zensical 0.0.71, as JenkinsPipelineUtils' guide), `check_site.py`, and `pages/` (the `docs_dir`, with `assets/favicon.svg`). `.gitignore` takes `/guide/.venv/` and `/guide/site/`, and `CLAUDE.md`'s repository tree names the folder. The root template is not affected: `copier.yml` renders `root/template` only.
- **How it builds:** `kc project test guide`, the new `guide` component in `.kubecoder/project.yaml`: `cexec modern-app uv run https://raw.githubusercontent.com/pvginkel/DevGuides/main/tools/check_guide.py ..`. Green: "ModernAppTemplate: guide (/modern-app/): pass, 0 warning(s)". `kc project test` now runs it with the backend and root suites. By hand, from `guide/`: `cexec modern-app uv run --locked zensical build --strict`, then `cexec modern-app uv run --locked python check_site.py`. `check_site.py` holds every rule heading to `### ID-n — Title { #id-n }`, ids unique across pages, and a `**Why.**` paragraph under each rule; a broken heading and a missing reason were checked to fail it.
- **Path and title:** `site_url: https://dev-guides.home/modern-app/`, `site_name: Modern apps`. `/modern-app/` rather than the worklist's example `/conventions/`: on the hub, "conventions" names no subject, and "modern app" is the estate's name for the family (the `modern-app` toolchain, the `modern-app-*` images, the pipelines guide's "Modern app build" type). Taken paths on the hub: `data-modelling`, `pipelines`.
- **Rule ids:** a prefix per page, as the pipelines guide does (`POD-`, `TIME-`), not the worklist's flat `CONV-n`. A page's Markdown copy is `https://dev-guides.home/modern-app/<page>/index.md`; a rule's anchor is its id in lower case. The pages, in nav order, and their rules (the skill's list):
  - `index.md`, Home: how the rules read, the page table. No rules.
  - `api.md`, API: API-1 a path identifies a resource by its UUID (no natural keys; a table that already keys on an integer keeps its integer paths); API-2 work that can take over 2 s (p95) runs as a task (`start_task()`, `202` with `task_id`, `useSSETask`); API-3 a paged list orders stably (`id` last); API-4 a paged list endpoint pages with the template's helpers (`PaginationQuerySchema` subclass with `sort_by` a `Literal`, `apply_sorting()`, `data` + `build_pagination_meta()`); API-5 error responses are documented with `ApiErrorResponseSchema`.
  - `status.md`, Status values: STATUS-1 a status field is a `Literal` or `StrEnum`, never `str`; STATUS-2 the frontend types a status by its generated schema; STATUS-3 a switch over a status ends in a `never` guard; STATUS-4 status labels live in `src/lib/utils/status-labels.ts` (the template ships none).
  - `backend.md`, Backend code: BE-1 durations with `time.perf_counter()`; BE-2 an error is raised, never swallowed (no hand-built error responses, no log-and-continue); BE-3 a failing upstream raises `ExternalServiceException` (`502`).
  - `readiness.md`, Readiness: READY-1 a service registers the check of the system it depends on (`register_check()`, in the constructor of a `Singleton`, from the startup hook of a `Factory`); READY-2 `critical` only when the app cannot serve without the system; READY-3 a check is one quick call, and its I/O times out.
  - `sse.md`, Server-sent events (with the target table and the local-admin fact): SSE-1 every event names its target; SSE-2 broadcast is for infrastructure events only; SSE-3 a task's events go to the user who started it (`caller_subject`, no fallback); SSE-4 the UI renders without the stream (`isConnected` means `ready`); SSE-5 the SSE provider owns the connection (no own `EventSource`, no retry; recovery through the session).
  - `frontend.md`, Frontend code: UI-1 no success toast for an outcome the user sees; UI-2 a mutation's error is toasted once, by the global handler (no hook-level `onError`); UI-3 a file the backend serves downloads through `window.open()`.
  - `testing.md`, Testing: TEST-1 tests run against the real infrastructure (the template's token fixtures and test sessions stand in for the IdP); TEST-2 a missing system stops the run (`pytest.exit`, never `skipif`); TEST-3 a failing test is a regression (CI's `--retries 2` for Playwright absorbs flakes; no retries in test code); TEST-4 a backend test module mirrors the module it tests (`test_<module>.py`, `Test<Name>`); TEST-5 a service and an endpoint are tested in full; TEST-6 a testing endpoint comes before the UI that needs it (`/api/testing/`, `reject_if_not_testing()`).
  - `playwright.md`, Playwright: PW-1 a UI feature ships with its specs; PW-2 a spec mocks no request (`testing/no-route-mocks`); PW-3 a spec waits on test events, never on time (instrumentation in the same change); PW-4 a spec that needs a production build carries `@preview` and skips without `PLAYWRIGHT_PREVIEW_MODE=true`; PW-5 a spec that expects an SSE event waits for the stream first (`deploymentSse.ensureConnected()`).
- **The items, mapped:** RT08 → STATUS-1..4; RT09 → UI-1, UI-2; RT11 → API-1, API-2; RT13 → TEST-1, TEST-2, TEST-6, PW-1..4; RT14 → BE-1, BE-2, UI-3; BE-T17 → TEST-3..5, SSE-1..3; D9a → API-3; RT10 → API-4; RT15 → READY-1..3; phase 5's BE-C28 note → BE-3, API-5; phase 7's SSE client contract → SSE-4, SSE-5, PW-5; phase 8's `@preview` → PW-4. Not taken, per the worklist and D9a: DA's worker tier, `/api/portal/`, "paginate past 50 items", server-side sorting on every list, `DataTable`, guidepost comments, file-creation order, the Keycloak `test-da-` prefix.
- **Checked against the template, and where the template differs from DA or the earlier notes:**
  - **RT09:** `src/lib/query-client.ts`'s default mutation `onError` toasts every mutation error through `parseApiError()`, skips no status and has no opt-out. A hook-level `onError` replaces it (TanStack Query lays a mutation's options over the defaults), which UI-2 states. DA's "the portal skips 409" exception has no counterpart.
  - **RT13:** the template has no pytest retries (DA had two); CI retries Playwright only, through `run-suite --retries 2`. The template does not test against a real IdP, unlike DA's Keycloak; TEST-1 says what stands in for it.
  - **RT15:** the phase 5 note's "I/O timeout near the check's timeout" is not what the template's checks do: S3 relies on boto3's default timeouts (60 s), the SSE gateway check on its 5 s `http_timeout`, against the checks' 0.8 s. READY-3 requires an I/O timeout of its own and explains the cost of a long one, without "near".
  - **TEST-2's recipe:** `tests/conftest.py` star-imports `conftest_infrastructure.py`, so an app's own `pytest_configure` there replaces the template's pre-flight. The recipe uses `pytest_sessionstart`; `pytest.exit` there was checked to stop the run with its return code, after the template's `pytest_configure` ran.

**The hub (step 2):**

- **DevGuides `92bc97d`** is the contract's two edits, and nothing else registers a source (the `Dockerfile` and `build_hub.py` read `sources.txt`): `ModernAppTemplate` in `sources.txt`, and a `dir('ModernAppTemplate') { git url: 'https://github.com/pvginkel/ModernAppTemplate.git', branch: 'main', credentialsId: … }` clone in the `Jenkinsfile`'s `Checkout`. The controller's declarative linter validated the `Jenkinsfile`. The Jenkins clone of this repo has no `backend/` or `frontend/`, which the guide does not need.
- **The check:** DevGuides' `kc project test` (`cexec python uv run tools/build_hub.py /work`) expects the four source repos side by side under `/work`, and this environment has neither that layout nor a `python` container. `/work/scratch/dev-guides-root` holds symlinks to `/work/scratch/DevGuides`, `/work/scratch/DevGuidesPrivate`, `/work/scratch/JenkinsPipelineUtils` and `/work/ModernAppTemplate`; from `/work/scratch/DevGuides`, `cexec modern-app uv run tools/build_hub.py /work/scratch/dev-guides-root` is green: "out/ holds 3 guide(s) …: Data modelling (/data-modelling/), Jenkins pipelines (/pipelines/), Modern apps (/modern-app/)", with the card on the index and the line in the root `llms.txt`. Green again after the stale-doc fix. This is the hub check to re-run before phase 17.

**The skill (step 3):** KubeCoderConfig `c5db31a`, plugin 0.13.2 → 0.14.0 (a new skill is a minor bump).

- `kubecoder/skills/modern-app/SKILL.md`, named after the guide's path as `data-modelling` is. Its description triggers on writing, changing or reviewing code in a modern app (endpoints, paged lists, status values, errors, services and their readiness checks, SSE, toasts and downloads, backend tests, Playwright specs).
- The body: the intro; what a modern app is, the template's code as a rule's definition, and that a template-owned file that breaks a rule is fixed in the template, never in the app; reading the guide (`llms.txt`, `llms-full.txt`, `<page>/index.md`, `#test-2`); checking code (the app's gates catch PW-2 through ESLint, STATUS-3 through `tsc` and TEST-2 through the pre-flight, and the rest is read); then the 34 rules under their eight pages, each a brief with its id.
- In the same commit, the dev-guides skill's "the Jenkins guide is the one guide whose source lives in a library repo", false now, names both guides that live in the repo of the code they rule.
- Gate: `npm run format:check` (KubeCoderConfig's `kc project lint`), through `cexec modern-app`, since there is no `frontend` container here. Green.

**The stale pipeline docs (phase 8's note, worklist §4.3):**

- **JenkinsPipelineUtils `01bf1fe`:** `docs/pages/types/modern-app.md` no longer says a file "follows the reference file below, not the template". It says the root template renders the reference file with the app's Copier answers, and that a change to the type is made in the template too. It also adds PilotApp to the type's apps: its `PilotApp` job runs `modernApp.test` (last build 11, green). The guide check, `check_guide.py ..` from `docs/` through `cexec modern-app` (no `iac` here), passes with 0 warnings. `lint_examples.py` was not run, since no example changed.
- **KubeCoderConfig `ec17ea5`** (0.14.1): the jenkins-pipelines skill's "Two files predate the guide" paragraph becomes "ModernAppTemplate renders a type", as on the page, and "One file predates the guide", KitchenDisplay's, unchanged.

**Findings for the operator, from step 1 (nothing waits on them):**

- **API-1 against the apps:** the apps address resources by integer (ElectronicsInventory 72 `<int:…>` routes, IoTSupport 21, ZigbeeControl 2) and by natural keys (EI's `part_key`, IoTSupport's `code` and `model_code`), and the template's own `test-app-domain` has `<int:item_id>` on an integer key. API-1 exempts a table that already keys on an integer, which is my reading of RT11 for a guide stated as the world is. The operator may want to confirm the exemption, or rule natural keys too.
- **Template code that breaks a rule:** three fixed waits (PW-3) in the frontend template, `tests/support/helpers/toast-helpers.ts:155` and `:276` and `tests/infrastructure/deployment/deployment-banner.spec.ts:64`; the backend's `app/api/tasks.py.jinja` answers 404 with a hand-built `{"error": "Task not found"}` outside the envelope (BE-2, API-5). Candidates for a template change, not taken here.
- **Two paging shapes:** the frontend's `src/hooks/use-paginated-fetch-all.ts` pages by `offset`/`limit` at 1,000 a page, while the backend's `PaginationQuerySchema` takes `page`/`per_page` with `per_page` at most 100. API-4 rules the backend endpoint only.

**For phases 10–16:**

- **Phase 10:** the guide and the skill change no template and give the apps no migration step. The coordinated changelog may name them: `guide/`, https://dev-guides.home/modern-app/ and `kubecoder:modern-app`.
- **Phases 11–16:** the skill reaches no session until KubeCoderConfig is pushed and the plugin updates (this environment runs 0.13.1). Until then, the rules are in `guide/pages/`. The apps' `CLAUDE.md` do not link the guide: the skill carries it.
- **Any phase that changes a rule** changes it in the skill in the same sitting, and `kc project test guide` is its gate.

**For phase 17:**

- **The first push group** is DevGuides, KubeCoderConfig, JenkinsPipelineUtils and DockerImages. Phase 17's step 2 now names JenkinsPipelineUtils. DevGuidesPrivate is unchanged.
- **The `DevGuides` job** (last build 5) starts on every push to DevGuides or JenkinsPipelineUtils. A build before this repo is pushed finds no guide in ModernAppTemplate, which `check_guide.py` accepts ("no guides"), so it stays green.
- **This repo has no GitHub push hook.** `gh api repos/pvginkel/ModernAppTemplate/hooks` is empty, while DevGuidesPrivate and JenkinsPipelineUtils have Jenkins' hook. So pushing this repo does not start `DevGuides`, and /modern-app/ does not publish by itself. The pipelines guide's new-repo page says Jenkins installs a repo's hook when a job's configuration arrives with the push trigger; not seen working here. So, after a `DevGuides` build has cloned ModernAppTemplate, a `GET` and then a `POST` of `/job/DevGuides/config.xml` should install it. Then push this repo. Without the hook, start a `DevGuides` build by hand. Either way it is a write to Jenkins, so it is the operator's call. Done when https://dev-guides.home/modern-app/ serves and the root `llms.txt` lists it.

**Operator actions:** ModernAppTemplate's push hook, or a hand-started `DevGuides` build, at phase 17 (above). The three findings above, at any time.

### 2026-10-17, phase 10: release

Run in two chunks. Backend `6976a35`; frontend `5a155fd`, `9828760`, `2ee64bf`; parent `590ca61` (the first chunk's entry, folded in here), `51d8daa` (the changelog), `63e1773` and `8b43fc1` (its corrections), this entry.

**The tags,** lightweight like the earlier ones, none pushed: backend **`v0.14.0`** on `6976a35`, frontend **`v0.21.0`** on `2ee64bf`, root **`v0.2.0`** on this entry's commit. The status row can't name that commit, because the row is part of it. For the tag check below, `v0.2.0` stood on `51d8daa` first, and was moved here once the check had passed. `copier.yml` and `root/template/` are the same in both commits, so the check holds for the final tag.

**The pre-release fixes** (the first chunk; no by-hand edit to any app, and none needed):

- **The unused `eslint-disable` (frontend `5a155fd`):** `react-hooks/set-state-in-effect` on the SSE provider's mount effect (phase 6 saw it at `:316`, phase 7 at `:441`). `pnpm run check` gives no warnings in either test-app.
- **Fixed waits (PW-3, frontend `9828760`):** phase 9's three and two more.
  - `waitForToastViewportDismissed()` closes every toast and waits until none is left, instead of sleeping 1 s. EI calls it in `boxes-list.spec.ts`, three times.
  - `assertToastSequence()` closes each matched toast and waits for it to leave. Nothing calls it.
  - `deployment-banner.spec.ts` waits with `deploymentSse.waitForCurrentVersion(baselineVersion)`, which is new, as is the bridge's `getCurrentVersion()`.
  - `sse-connectivity.spec.ts`'s two 500 ms in-browser waits are gone: `open` already means the callback registered the connection.
- **The task endpoints raise (backend `6976a35`):** `RecordNotFoundException` instead of a hand-built `{"error": …}`. The status stays 404, and the body becomes the envelope (`code: RECORD_NOT_FOUND`). The messages are in the changelog. A task the caller doesn't own reads exactly like an unknown id. No app reads the body.
- **Left open, for the operator:** API-5 on the three task endpoints (they have no `@api.validate`, and adding one changes every app's generated types), and the other hand-built error bodies in `api/testing_sse.py` and `api/sse.py.jinja` (BE-2 candidates).

**`dismissToast()` (frontend `2ee64bf`).** Both branches now find the close button through `getCloseButton()`, by role and name. The all-toasts loop closes the first toast until none is left, because a closed toast leaves the DOM at once and `nth(i)` would skip every other one. I fixed the selector rather than the button: the button isn't unlabelled, since its `sr-only` "Close" text names it. An `aria-label` would only duplicate that name, and it would leave the loop's skip in place. `sse-auth-recovery.spec.ts`'s 500 case calls `expectErrorToast()`, so both Playwright passes run the fix.

**The changelog.** Neither template repo has a changelog of its own (`backend/` and `frontend/` hold only `CLAUDE.md`, plus the frontend's `README.md`). So the one coordinated entry in `changelog.md`, "2026-10-17 — Root v0.2.0, Backend v0.14.0, Frontend v0.21.0", covers all three.
- **Its first section, "Syncing an app to this release", is the checklist for phases 11–16.** It has 19 steps in sync order, with per-app marks: the three updates and their conflicts, then packaging, pins, `container.py`, `app_config.py`, app code, tests, `.env*`, `package.json`, `button.ts`, the `Dockerfile`, the OpenAPI cache, gates, the deploy repo, the IdP redirect URIs, and the architecture YAML. The last says there is nothing to do, per correction 1.
- The sections after it say what changed, by subject, and point back at the steps. One lists the behaviour users and tests will notice. The guide and the skill are named, with no migration step.
- The per-app file and line detail stays in this log; the changelog points here.

**Gates:** `kc project build`, `test` (mother 773, domain 9 passed and 1 skipped, root backend suite, guide) and `lint` (no warnings) are green.
- Playwright through the runner at one worker passed both passes, the dev server and preview (peaks 3,337 and 1,316 MB).
- `tests/e2e/parallel/worker-isolation.spec.ts` alone at two workers passed on the first run (5,065 MB peak), with the preview pass skipped.
- The first chunk's gates were green the same way.

**The tag check.** I ran it in a scratch clone of IoTSupport, beside a symlink to this repo, because the apps' `_src_path` is relative. The clone is deleted, and `/work/IoTSupport` was not touched. Run from each component's directory, the sync command printed "Updating to template version 0.2.0", then 0.14.0 in `backend/` and 0.21.0 in `frontend/`, and each `_commit` read the new tag. Conflicts were seen, not resolved:
- root: `Jenkinsfile`;
- backend: `Dockerfile`, `app/app_config.py`, `app/services/container.py`, `pyproject.toml` and `scripts/wait-for-services.py`;
- frontend: `package.json`, `src/routes/index.tsx` and `vite.config.ts`.

**For phases 11–16, beyond the changelog:**

- **`copier update` merges app-owned files in `backend/` and `frontend/`.** In the components, `_skip_if_exists` files whose template render changed are three-way merged: the conflicts above, clean hunks in `tests/conftest.py` and `vulture_whitelist.py`, and `tests/test_smoke.py` added. At the root, the app-owned files were left alone (`pyproject.toml`, `.kubecoder/*`, `CLAUDE.md` and `scripts/regenerate-openapi.py` changed in the template since v0.1.3, and none was touched).
  - So correction 9's "a template change reaches new apps only" does not hold for the components, and neither does `downstream_sync_process.md`'s "never overwritten". The changelog's steps 3 and 4 say how to resolve: keep the app's file plus what the steps name, and check `git diff` on app-owned files, since a clean hunk raises nothing.
  - The likely cause, read but not confirmed: copier matches `_skip_if_exists` against paths that carry the component's `backend/`/`frontend/` prefix under the monorepo's git root.
  - This is not a ruling. Whether to fix it is the operator's call.
- **IoTSupport's `backend/scripts/wait-for-services.py` (phase 11).** IoT has its own copy (an OpenSearch wait, and S3 bucket creation), and the file is template-owned now. The template's `S3Service.startup()` creates the bucket, so only the OpenSearch wait lacks a home. Phase 11 settles it, as a standing edit listed in IoT's `CLAUDE.md` or as a template hook. If neither fits the rulings, it is a stop.
- **The toast helpers (phase 12).** `dismissToast()`, `waitForToastsToDisappear()` and `expect*Toast()` now close toasts at EI's ~50 call sites (17 `dismissToast`, 33 `expect*Toast`), plus the three `waitForToastViewportDismissed()` calls. `expect*Toast()` closes the *first* toast, not necessarily the one it matched. That was always so, and it is only visible now. Run EI's suite, and look here first when a spec that touches toasts changes outcome.
- **Phase 17:** push this repo's tags with it, `backend/`'s and `frontend/`'s with theirs.

### 2026-10-17, phase 11: IoTSupport

Changelog steps 1–19 in `/work/IoTSupport`, one commit per step or fix (the status row lists them), plus the deploy clone. Nothing is pushed. No template change was needed, and no app bug turned up.

**Sync (steps 1–4).** `c294800` root v0.2.0, `c9a67d1` backend v0.14.0, `21d9d26` frontend v0.21.0. The conflicts were the ones the tag check saw, and the rulings settled each.

- **Root:** only `Jenkinsfile` conflicted. Resolved to IoT's file (the `withVault` wrapper, the opensearch service, the Keycloak env, `secrets:`) plus the `postgres` service (first in `services:`), `STAGE: 'tst'` and `BUILD_CACHE: 'true'` with their comments, and the uv `install`/`run` pair. The template's comment block above `modernApp.test` was not taken (PilotApp only). The root's app-owned files were left alone.
- **Backend app-owned files,** resolved per step 3 (check `git diff` on them: clean hunks raise nothing):
  - `container.py`: step 7 arrived whole. The merge also added a second `testing_service = providers.Factory(TestingService)`; dropped it, kept IoT's `Singleton` (the template has always used `Factory`), and reverted the template's reworded health-service comment.
  - `Dockerfile`: both conflict hunks were step 14's, so the rewrite was finished there: the template's default plus `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`. Step 14's precondition stands: DockerImages `7e7c1f7` pushed and the images rebuilt before CI builds it.
  - `app_config.py`: the hunk brings `dump_for_logging` **without** the `Sensitive` marks, so taking it as merged would log every secret at boot. Step 8 finished it (below).
  - `pyproject.toml`: the merge is a hybrid (the template's `[project]` without the app's dependencies); keep the app's file and convert it in step 5.
  - `tests/conftest.py`: dropped the docstring hunk. `vulture_whitelist.py`: kept the `uv run` comment. `tests/test_smoke.py` (new, app-owned): kept.
  - `.env.example.rej` (backend, once) and `frontend/.env.example.rej` (every frontend update) are copier's rejected hunks on app-owned `.env.example`, gitignored by `.env*`. Delete them.
- **IoT's `scripts/wait-for-services.py`** (OpenSearch wait, S3 bucket creation) gave way to the template's. The bucket needs no home (`S3Service.startup()` creates it). The OpenSearch wait became a `pytest_sessionstart` pre-flight in app-owned `tests/conftest.py`: no standing edit, no template change. It polls `ELASTICSEARCH_URL/_cluster/health?wait_for_status=yellow` for up to 180 s (the old budget) and `pytest.exit`s if OpenSearch never comes up, **only when `STAGE == "tst"` and `ELASTICSEARCH_URL` is set**, which is Jenkins. In CI, `run-suite` runs the template's wait (PostgreSQL, S3), then pytest, where the hook waits, then Playwright, whose backend is the one that reads the sidecar (the backend tests point at `elasticsearch.test` and mock `httpx`). Ungated, it would wait locally too, since `conftest_infrastructure` loads `.env`'s `ELASTICSEARCH_URL=http://localhost:9200` and this environment has no opensearch: 180 s, then a failure. Checked against a fake health endpoint both ways.
- **Frontend:** `package.json` brought step 12 (kept IoT's `split2`/`ssegateway` and the optional `build-fast`/`build` split; `pnpm install` in the commit), `button.ts` step 13, `src/routes/index.tsx` kept IoT's redirect to `/devices`, and `vite.config.ts` took the template's side of all four hunks (no `xfwd`; `forwardOrigin`/`configureSseProxy`), keeping the esptool alias and `optimizeDeps`; against the frontend test-app's render, only those two blocks and the ports differ.
- The violation finder shows no post-adoption drift. Pre-existing divergence: backend `.gitignore` +4, frontend `.gitignore` +2, `knip.config.ts` +2.

**Packaging (step 5, `c8d48fa`).** Root and backend `pyproject.toml` are PEP 621 with hatchling, one for one per worklist §3 (constraints, scripts, dev group, the PilotApp comment above `[build-system]`). `requires-python` stays `>=3.11,<4` and the root project's name `iot-support` (the template says `>=3.13,<4` and `<project_name>-workspace`; harmless). **The lock method, for EI, DHCPApp and ZigbeeControl:** append every `poetry.lock` package as `name==version` to `[tool.uv] constraint-dependencies`, `uv lock`, restore `pyproject.toml`, `uv lock` again. uv keeps the locked versions and the final lock carries no constraints; the diff against `poetry.lock` was empty at the root, and the backend gained only `tomli`. Delete `poetry.lock` at both levels. `.dockerignore`'s comment lists `uv.lock, *.py`. Also on uv: `.kubecoder/project.yaml` and its comments, root app-owned `scripts/regenerate-openapi.py` (`uv run dev`: copier leaves it on `poetry run dev`, which breaks step 15), `CLAUDE.md`, `backend/CLAUDE.md`, `backend/README.md` and `docs/slice-test-plan.md`. No `poetry` mention is left outside the frozen `docs/features/`.

**Steps 6–9, 11, 15** (`a8644f4`, `7481d05`, `db2a3cb`–`b8d3bef`, `b5011b7`, `3efd106`). Steps 7, 12, 13 and 14 were checked against the steps, not redone; the `Dockerfile` differs from the backend test-app's render only in its port and the two `PYTHON*` lines.

- **6:** the pins, `uv lock` in both projects, then `uv lock --upgrade-package mypy` (1.19.1 → 1.20.2), which clears template-owned `app/config.py:81` (`Stage.__init__` narrows by `value not in STAGES`, which only mypy 1.20 does). Ruff 0.15's `--fix` changed nothing in IoT: the I001s that ruff 0.11 raised before step 6, in template-owned `app/database.py` and `tests/test_database_schema.py`, don't fire under 0.15. Pillow 12 needed nothing (the `.convert()` sites already annotate `Image.Image`).
- **8, taken:** `Sensitive` on `mqtt_password`, `keycloak_admin_client_secret`, `wifi_password`, `elasticsearch_password`, `fernet_key` and `architecture_pipeline_trigger_url` (a Jenkins webhook URL whose token is secret); each dumps as `***`. `secret_key` is the template's, marked already.
- **9:** `device_log_stream_service.py` sends `Target.connection(request_id)`, and `rotation_nudge_service.py` `BROADCAST_TARGET` (app-wide dashboard state), with their test asserts. IoT's `ExternalServiceException` and its 502 handler are deleted, and seven app and five test modules import it from `app.core_exceptions`. `coredump_service._update_parse_status` runs in `scoped_session(...)`, with the container check moved to a new `_require_container()`. The readyz wording in `.kubecoder/config.yaml` and `docs/slice-test-plan.md:90` now reads `checks.*.status`.
- **11:** `backend/.env.example` gains the four settings in the template's words. IoT's 50 MB nginx limit matches the default.
- **15:** `python3 scripts/regenerate-openapi.py --frontend` against the dev database. The cache gains `/api/ui-setup`, `/api/testing/sse/force-callback-error`, the readyz schemas, `x-auth-roles.hierarchy` and `/api/pipeline/fleet-projection` (missing before). The "`x-auth-roles.read` not found" warning predates the sync.
- **Two frontend gaps, now in the changelog's steps 12 and 15** (`e227d07`, `394dde4`, `71d78ea`): IoT's lock held `eslint-plugin-react-hooks` 7.0.1, under which template-owned `sse-context-provider.tsx:441` fails `react-hooks/set-state-in-effect`; `pnpm update eslint-plugin-react-hooks` (to `^7.1.1`) fixes it, and 7.1 then flagged `use-device-logs.ts:192`'s deliberate reset, which got a reasoned disable comment. After the refresh, `--default-non-nullable false` gave 13 `tsc` errors in 4 hooks and 2 test factories that typed a defaulted response field as always present: those became `?:`, mapped with `?? null`. Plus one pre-existing unused disable directive dropped.

**Backend tests on PostgreSQL (step 10,** `a55c75e` fixtures, `e4406be` models, `c154080` metrics registry, `112913f` session-app state, `cc5d981` roles). Before: 95 failed, 621 passed, in five groups. After: 716 passed in 36 s, stable, also in reverse order (a throwaway `-p` plugin reversing `items`), and a throwaway last test counting rows in `<run>_main` from its own connection found none, so no test commits past its savepoints. No template fixture changed; `StubLifecycleCoordinator` gained `unregister_lifecycle_notification`, and `tests/test_openapi_cache.py` passes. In the order the next database apps meet it:

- **The overrides:** `test_settings` and `test_app_settings` are `scope="session"`, with `tmp_path_factory.mktemp(...)` and no `database_url`. IoT builds its own `Settings(...)` (`flask_env="development"`, keeping the testing endpoints gated), and **a hand-built `Settings` must take the template's small pool itself**: `db_pool_size`/`db_pool_max_overflow` from `TEST_DB_POOL_SIZE`/`TEST_DB_POOL_MAX_OVERFLOW`, and the whole `sqlalchemy_engine_options` dict (otherwise SQLAlchemy's 5 + 10). Don't derive it with `_build_test_settings().model_copy(update={"flask_env": ...})`: `stage` resolves from `flask_env` at construction, and `model_copy` doesn't redo it.
- **A second app with other settings** (IoT's `testing_app`, `FLASK_ENV=testing`, which replaced the SQLite `testing_template_connection`): per test, `url = run_databases.clone()`, `_create_test_app(settings.model_copy(update={"database_url": url}), app_settings)`, then `_dispose_app(app)` and `run_databases.drop(url)`, `committed_app`'s shape. Import the private helpers by name from `tests.conftest_infrastructure` (the star import skips them), and use `_create_test_app`, not `create_app`, which fails at its first metric-registering service (`Duplicated timeseries in CollectorRegistry`). 59 tests on fresh clones take about 9 s. A module re-importing those fixtures from another (`test_testing_device_sse.py`) drops the removed one from its import list.
- **Hand-built metric-registering services** (`MqttService`, `LogSinkService`): `pytestmark = pytest.mark.usefixtures("clear_prometheus_registry")` per module. 81 of the 95 failures.
- **State on the session app,** each now restored: `app.container = mock_container` (`test_startup.py`; passed only because the file sorts late) became `monkeypatch.setattr`; attribute flips on container singletons (`keycloak_service.enabled`, `es_service.enabled`/`config`, about 30 sites) are snapshotted and restored by an autouse fixture per module; a test asserting the now session-wide thumbnail directory gets created builds the `Factory` with a call-time `app_settings=` on its own `tmp_path`.
- **Roles in test sessions** (now in the changelog's step 10): sessions from `/api/testing/auth/session` with no role or `["admin"]` get 403 everywhere, `/api/auth/self` included; they hold `editor` now.
- **The drift test** found models and revisions apart: revisions 002/005/006 index four columns the models don't mark (`devices.device_model_id`, `devices.rotation_state`, `coredumps.device_id`, `firmware_versions.device_model_id`), and build `devices.key` and `device_models.code` as a unique constraint plus a plain `ix_` index. **Fixed on the model side,** so production's schema is unchanged: `index=True` on the four, and `unique=True` plus `__table_args__ = (Index("ix_..._key|code", ...),)` on the two. A revision dropping the redundant constraints is cleaner but a production migration: the operator's call. Read the drift from the alembic `Detected ...` INFO lines in the test's captured log.
- **Nothing needed `committed_app`.** Coredump tests calling `_parse_coredump_thread` in the test thread pass on `container`: `scoped_session(container)` gets the test's `_KeptOpenSession`, so its commit releases a savepoint and its close is a no-op. Same for the `container.db_session().commit()` sites. IoT has no `db.session` writes and no literal-ID asserts.

**Gates (step 16).** `kc project setup`, `build` and `lint` are green (root ruff; backend ruff, mypy over 184 files, vulture; frontend `pnpm check`), and `kc project test backend` passes 716 in 36 s. Playwright through `uv run run-suite --suite frontend --workers 1`, after the fix and with the stand-ins below: the dev-server pass 133 passed and 5 skipped (the `@preview` SharedWorker cases), the preview pass 5 passed (`SUITE_RESULT` frontend 133/0/5, frontend-preview 5/0/0; 2,096 MB cgroup peak, runner peaks about 2,050 MB). At the config's 2 workers, the shape `kc project test frontend` runs, it is green too (runner peaks 3,562 and 2,391 MB). `kc project test frontend` as such can't pass in this environment (below), so it was run in that equivalent form.

- **Fix: `ssegateway` in the lock (`c6d1337`).** IoT's `pnpm-lock.yaml` held SSEGateway `dea28a1`, older than the gateway's `ready` event (`c136d9c`/`02ebe75`, 2026-04-05). The v0.21.0 client counts a stream connected only on `ready`, so it never connected and reopened the stream every 10 s. 14 specs timed out in `deploymentSse.ensureConnected()`: `sse-connectivity`, `sse-auth-recovery`, `task-events` and `deployment-banner`, 9 in the dev-server pass and 5 in the preview pass. `pnpm update ssegateway` re-resolves `#stable` to `3f6199d`, the commit the template test-app locks. The deployed gateways are new enough: the six deploy repos pin `registry:5000/ssegateway` `:56` to `:65`, and SSEGateway build 56 is from 2026-09-24, after `ready` and the in-stream `rejected` (`fc5124d`, 2026-05-08).
- **Environment, not code: IoT's Keycloak admin secrets and OpenSearch.** Neither exists in this environment. IoT's own environment projects `KEYCLOAK_ADMIN_CLIENT_ID`/`_SECRET` through `secrets:` and runs the `opensearch` service, and CI has both (`withVault`, the opensearch sidecar). Without them, 70 of the 138 tests fail with `502 … Keycloak admin API not configured`, because creating a device creates a Keycloak client, and 7 device specs get 503 from `GET /api/devices/<id>/logs`, the log viewer's history query. The green runs used a throwaway stand-in for both, `/work/scratch/iot-pw-tools/fake_keycloak.py` (not committed). It serves the token endpoint, the admin-client endpoints and an empty `_search`. The runner's environment exported `KEYCLOAK_BASE_URL`, `KEYCLOAK_REALM`, `OIDC_TOKEN_URL`, `KEYCLOAK_ADMIN_CLIENT_ID`, `KEYCLOAK_ADMIN_CLIENT_SECRET` and `ELASTICSEARCH_URL` to point at it, and process env beats `backend/.env`. **So IoT's real Keycloak path first runs in CI at the push (phase 17).** `b7741a4` corrects IoT's `.kubecoder/config.yaml` comment, which said that neither suite needs OpenSearch.
- No other spec changed outcome. The other behaviour changes flipped nothing: IoT's Playwright sessions already carry `editor`.
- **Upkeep:** `7948bf3` rewrites the two Playwright-on-SQLite passages in `frontend/docs/contribute/testing/`, including the stale `initialize-sqlite-database.sh` mention the sync left. Vulture and knip are green with no change, and IoT has no `.codehealthignore`.
- **Noise, not a failure, and a possible template take:** at teardown, the template's `lifecycle_coordinator` logs `Received signal 15` from its signal handler. A backend that is mid-write to stderr then prints `RuntimeError: reentrant call inside <_io.BufferedWriter name='<stderr>'>` (a few backends per run, not every run).

**Deploy repo (step 17).** `/work/scratch/deploy/IotDeploy` (pulled, at `2c129d3`) commit `6f6ea99`, **not pushed**: `STAGE=prd` and `HOMELAB_INTERNAL=true` (literal, with a comment) in the `iotsupport.env` helper in `chart/templates/_iotsupport.tpl`, which the init container `iotsupport-setup` (whose `FLASK_ENV=db` no longer decides the stage), the app container and the rotation cronjob all include. `BASEURL` kept. The repo has no render or lint check, and this environment has no `helm`; the edit follows the helper's existing `{{- /* */}}` comment pattern.

**Operator actions.**

- **Step 18:** in Keycloak, IoTSupport's client gets `https://iot.ginbov.nl/api/auth/callback` as a valid redirect URI and `https://iot.ginbov.nl/*` as valid post-logout redirect URIs. After deploying, check that the login's `redirect_uri` reads `https://iot.ginbov.nl/...`.
- **Before CI builds IoT:** DockerImages `7e7c1f7` pushed and `modern-app-backend-build` rebuilt (step 14).
- Optional: the drift fix's revision alternative (above).
- **For phase 17:** IoT's Playwright stage in Jenkins is the first run against a real Keycloak admin client and OpenSearch since the sync; read its result before calling IoT green.

**Step 19:** nothing; IoT already produces its architecture model.

**For the next apps.**

- Copier merges the components' app-owned files: read `git diff` on them before each commit, delete the `.env.example.rej` files, and watch for a duplicated provider in `container.py` and an unmarked `dump_for_logging` in `app_config.py`.
- The Poetry apps: the lock method above, then step 6's `uv lock --upgrade-package mypy`. Fix the app-owned scripts copier leaves on `poetry run` (`scripts/regenerate-openapi.py`).
- Expect the frontend lock gaps: `eslint-plugin-react-hooks` 7.0.x and an SSEGateway older than `ready` (`pnpm update eslint-plugin-react-hooks ssegateway`), and `tsc` errors on defaulted fields after the OpenAPI refresh.
- Playwright runs at one worker here are cheap for IoT's suite (about 2 GB), and 2 workers fit too (3.6 GB). Check the app's `.kubecoder/config.yaml` for `secrets:` and services this environment lacks before reading failures as regressions.
- EI and PilotApp, step 10: run the suite once and sort the failures into the groups above; hand a sub-agent a survey for `app.<attr> =`, singleton attribute writes, hand-built metric-registering services, `db.session` and literal IDs; finish with a reversed-order run and the row-count probe, which catch the state leaks a forward run hides. EI's `sse_server` is the same "second app" shape as IoT's `testing_app`.
- **A possible template take (not a stop):** a public helper in `conftest_infrastructure.py` (say `clone_app(settings, app_settings)` as a context manager) would give IoT's `testing_app` and EI's `sse_server` one supported shape instead of private imports.

### 2026-10-17, phase 12, steps 1–5: ElectronicsInventory sync and uv

Changelog steps 1–5 in `/work/ElectronicsInventory`: `f28c42a9` root v0.2.0, `ab85dee9` backend v0.14.0, `58ad6a13` frontend v0.21.0, `966ab2a2` uv. Nothing is pushed. No template change was needed, and no conflict needed a ruling beyond those IoT used.

**Root (`f28c42a9`).** Only `Jenkinsfile` conflicted, in two hunks. The header keeps EI's three-image wording. The Test stage takes the `postgres` service (first in `services:`), `STAGE: 'tst'` and `BUILD_CACHE: 'true'` with their comments, and the uv `install`/`run` pair; the template's five-line services/PostgreSQL comment above `modernApp.test` was not taken (as IoT; the checklist gives it to PilotApp only). The docs-image stage, the S3 block and the pins stage are EI's. The rest arrived clean (`Procfile.dev`, `scripts/dev.py`, the suite runner, the build-cache scripts, `check_updates.py`). Violation finder: no post-adoption drift; pre-existing `.gitignore` +2.

**Backend (`ab85dee9`).** Conflicts in `Dockerfile`, `app/app_config.py`, `app/services/container.py`, `pyproject.toml` and `tests/conftest.py`; a clean hunk in `vulture_whitelist.py`; new app-owned `tests/test_smoke.py` kept; `.env.example.rej` deleted. Deleted by the update: `scripts/dev-server.sh`, `scripts/initialize-sqlite-database.sh`.

- `Dockerfile`: the template's side is **step 14 whole**: it equals the backend test-app's render but for `EXPOSE 3001`. Step 14's precondition stands (DockerImages `7e7c1f7` pushed, `modern-app-backend-build` rebuilt before CI builds EI).
- `container.py`: **step 7 done**: EI's file with `lifecycle_coordinator` and `health_service` moved above `s3_service`, and `health_service=health_service` on `S3Service` and `SSEConnectionManager`. The merge's second `testing_service = providers.Factory(TestingService)` was dropped (EI has its own, also `Factory`), as were the template's reworded comments. One conflict hunk's "after" side would have deleted EI's kit, inventory and document providers: resolve this file by hand, never by taking a side.
- `app_config.py`: kept as EI's. The hunk brought `dump_for_logging()` without `Sensitive` marks on `openai_api_key` and `mouser_search_api_key`; **step 8 is still open** (optional; without the method nothing is dumped).
- `pyproject.toml`: kept, then converted in step 5. `tests/conftest.py`: kept as EI's (docstring hunk dropped); step 10 untouched. `vulture_whitelist.py`: the `uv run` comment taken.
- Violation finder: no post-adoption drift; pre-existing `app/schemas/upload_document.py` +3/-1.

**Frontend (`58ad6a13`).** Conflicts in `eslint.config.js`, `package.json` and `src/routes/index.tsx`; `src/styles/button.ts` took a clean hunk; `.env.example.rej` deleted.

- **`eslint.config.js` is template-owned, and EI carries a standing edit in it** that neither its `CLAUDE.md` nor worklist §5 lists: the `role-gating` plugin (imports of `scripts/eslint-rules/role-import-enforcement.js` and `gate-usage-enforcement.js`, and two config blocks). The template's new TanStack-routes block (`react-refresh/only-export-components` off under `src/routes/`) landed at the same spot. Kept both: the template's block, then EI's two. The finder reports it as pre-existing divergence (+27), so the next update conflicts again unless EI lists it or the template gains a hook for app rules.
- `package.json`: the hunks are **step 12's `package.json` part** (`pg`, `@types/pg`, `generate:api:with-backend`, the optional `build-fast`/`build` split); kept EI's `split2` and `ssegateway`. `pnpm install` synced the lock (adds only `pg`, `@types/pg`). **Step 12's `pnpm update eslint-plugin-react-hooks ssegateway` is not done.**
- `src/routes/index.tsx`: kept EI's redirect to `/parts`. `button.ts`: **step 13 done** (`whitespace-nowrap` in both).
- `vite.config.ts` (template-owned) equals the test-app's render but for its ports; EI had no `xfwd`.
- Violation finder: no post-adoption drift; pre-existing divergence in `.gitignore`, `eslint.config.js` (above), `knip.config.ts`, `scripts/generate-api.js` (an example comment), `alert.tsx`, `list-section-header.tsx`, `status-badge.tsx`, `api-error.ts`, all present before the sync.

**Packaging (step 5, `966ab2a2`).** Root and backend `pyproject.toml` are PEP 621 with hatchling, one for one per worklist §3: names `electronics-inventory` and `electronics-inventory-backend` kept, the backend's placeholder author (`Your Name <your.email@example.com>`) converted as is, `requires-python` `>=3.13,<4` (root) and `>=3.11,<4` (backend) as Poetry had them, the PilotApp comment above the backend's `[build-system]`. Phase 11's lock method (`/work/scratch/iot-uv/lockpins.py`; EI's pin lists in `/work/scratch/ei-uv/`): the root lock equals `poetry.lock` exactly, and the backend's adds only `tomli` 2.5.0. Both `poetry.lock` files are deleted. On uv as well: `.kubecoder/project.yaml` (commands and comments), the `.kubecoder/config.yaml` comments, root app-owned `scripts/regenerate-openapi.py` (`uv run dev`), `CLAUDE.md`, `backend/CLAUDE.md`, `backend/README.md`, `frontend/CLAUDE.md`, `docs/commands.md`, `docs/slice-test-plan.md`, `docs/slice-doc-plan.md`, the code-workspace comment, and `frontend/docs/contribute/testing/ci_and_execution.md` (Jenkins runs `uv run --no-sync run-suite`). Left: `backend/docs/ei_copier_refactoring.md:346` (`[tool.poetry.scripts]` in a historical refactoring plan) and the frozen `docs/features/`. `backend/.dockerignore` names no lock file.

**Gates.** `kc project setup` is green on uv (root and backend `uv sync --locked`, `init-dev-database.py`, `upgrade-db` at revision 023, the frontend's install and generators). Root ruff and backend vulture are green. Red, both fixed by **step 6**:

- backend `uv run ruff check .`: two I001 in template-owned `app/database.py` and `tests/test_database_schema.py` (ruff 0.11; IoT's cleared under 0.15);
- backend `uv run mypy .`: `app/config.py:81` (`Stage` literal; needs `uv lock --upgrade-package mypy` to 1.20).

**For the next chunks.**

- Done whole: steps 7, 13, 14. Partly: step 12 (`pnpm update eslint-plugin-react-hooks ssegateway` left). Open: 6, 8, 9, 10, 11, 15–19.
- Step 16 upkeep: `frontend/docs/contribute/testing/playwright_developer_guide.md:72` and `docs/architecture.md:56` still describe the Playwright SQLite seed through the deleted `initialize-sqlite-database.sh`. `.kubecoder/config.yaml` still says both suites run on SQLite (lines 13–14, 85, 109) and readyz reports `database.connected` (line 108; step 9).
- Expect `tsc` to fail until step 15's OpenAPI refresh (`use-ui-setup.ts`), as in IoT.

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
   1. DevGuides, KubeCoderConfig, JenkinsPipelineUtils and DockerImages (if changed);
   2. this repo, `backend/` and `frontend/`, with tags;
   3. the six deploy repos;
   4. the six apps, whose pushes start their Jenkins builds.
3. **Watch:** follow the builds to green through Jenkins, `DevGuides` included (phase 9's log: this repo's push hook), and the Argo CD syncs after them.
4. **Report:** report the result, and list what's left for the operator: the per-app architecture Jenkins jobs, and any architecture YAMLs not seeded.

**Done when:** every app is built and synced, and the report is sent.
