# DesignAssistant port: worklist

This is phase 0's output, and the ground truth for phases 1–16 of [`da_port_plan.md`](da_port_plan.md). It was checked on 2026-10-17 against backend template v0.13.3, frontend template v0.20.5, the root template at `a9db8ab` (v0.1.6 plus docs), and the six apps at their HEADs that day. IDs refer to [`da_port_inventory.md`](da_port_inventory.md), and rulings to [`da_port_decisions.md`](da_port_decisions.md).

A phase reads its own rows in §1 and skips the items marked **landed**. For a **partial** item, it does only the part the row names. §2–§7 answer the plan's phase 0 questions, in the plan's order.

## Summary

- **Nearly everything taken is missing from the templates.**
  - Landed: BE-T02 (`after_commit()`, v0.13.0), FE10 (`.dockerignore`), and FE20 (solved differently in v0.20.4).
  - Partial: BE-C03, BE-C10, BE-T04, BE-T05, BE-T13, BE-T14, FE21, RT02, RT06, RT13, RT14 and BE-T17.
- **The apps are ahead of the template in three places:**
  - All six apps run declarative `Jenkinsfile`s on the library's `modernApp.test`. They also publish architecture models through `architectureProducer`, each with an `AaC/<Repo>` job. The root template's `Jenkinsfile.jinja` is still the old scripted file, and it calls library functions that no longer exist, so a newly generated app doesn't build.
  - PilotApp carries BE-T11 and FE16 (the connect callback refuses, and the frontend handles `rejected`) in seven template-owned files. They're a better base than DA's.
  - FieldnotesApp carries an SSE identity binding (FN-38) in five template-owned files.

  Neither app lists its SSE edits in its `CLAUDE.md`.
- **PilotApp doesn't run its tests on PostgreSQL.** [`pilotapp_database_testing_design.md`](pilotapp_database_testing_design.md) is advice for its slice 002, and none of it is built. Phase 2 builds S1 from the design alone.
- **No finding contradicts a ruling.** Plan correction 1 departs from D8's wording, but not from its decision.

## Questions for the operator

None of these blocks phases 1–10. Each names the phase that needs the answer.

1. **D2 lockouts.** Phase 4 needs this for the design; phases 11, 13 and 14 apply it.
   - IoTSupport, DHCPApp and ZigbeeControl leave `read_role` unset, so any signed-in account in realm `homelab` can read them today. After D2, an account with none of the app's roles gets 403.
   - The role assignments live only in Keycloak's database. For each of the three apps: who signs in without `editor`? And do you grant them `editor`, add a `reader` role, or accept the lockout?
   - Is `editor` a realm role or a client role? Granting a realm role for one app grants it for all of them.
   - ElectronicsInventory, PilotApp and FieldnotesApp are unaffected (§5).
2. **`HOMELAB_INTERNAL=true` on public hosts.** This affects phases 11, 12 and 14–16.
   - Under S6, an app marked internal shows exception text in its 500 responses.
   - Four apps serve public hostnames: IoTSupport (`iot.ginbov.nl`), ElectronicsInventory (`parts.ginbov.nl`), ZigbeeControl (`z2m.webathome.org`) and PilotApp (`pilot.ginbov.nl`). So does FieldnotesApp's webhook host (`fieldnotes-hooks.webathome.org`). DHCPApp is internal only.
   - Confirm that this is intended, or name the apps that stay unmarked.
3. **D8's means (phase 8).** D8 says the root template carries `scripts/arch-validate.py`. Since then, the estate has moved validation into the library's `architectureProducer` and the `aac-tools` image, so the template needs no script (plan correction 1). Phase 8 follows the estate form unless you object.
4. **PilotApp slice 002 (phase 16).** Confirm that no model or revision is in flight before phase 16 replaces PilotApp's test conftest. Its spec repo isn't checked out here.
5. **MAT-12 (optional).** No ruling takes it. It could ride along in phases 7 and 8, or stay a card (§7).

**The operator's answers (2026-10-17):**

1. Every one of these apps has an `editor` role; ElectronicsInventory also has a `reader` role. They are **client roles**, so a grant reaches one app only. No lockout to handle: phases 11, 13 and 14 apply D2 as built.
2. **Yes:** set `HOMELAB_INTERNAL=true` on all of them, the public hosts included.
3. **Agreed:** phase 8 follows the estate form (plan correction 1).
4. PilotApp's planning is paused until the whole port is done, so nothing is in flight: phase 16 replaces its test conftest.
5. **Take MAT-12** where it fits: part 1 (the error text and `package.json`) in phase 7, part 2 (the stale-cache test) in phase 8. Close the card when both land.

## Plan corrections

These facts change what a later phase does. Each phase logs the correction when it applies it.

1. **Phase 8 step 4 (D8, RT06): don't take DA's files.**
   - The estate's form is PilotApp's `Jenkinsfile.architecture` on the library's `architectureProducer`. `arch-validate` ships in the `aac-tools` image, so the template needs no `scripts/arch-validate.py`.
   - Make `Jenkinsfile.architecture` `_skip_if_exists`: four of the apps have two models and two stages.
   - All six apps are already producers, so phases 11–16 drop their "architecture YAML" step. Only new apps run `/seed-architecture` (§6.4, §6.5).
2. **Phase 8 step 1 (RT02): the template `Jenkinsfile` becomes PilotApp's declarative shape.** It gets `services:` for PostgreSQL and S3, `env: [STAGE: 'tst', …]`, and uv `install`/`run` strings (§4.3). Each app's `copier update` then meets a small diff instead of a rewrite.
3. **No phase owns `backend/scripts/wait-for-services.py`.** The root suite runner calls it if it exists, and the library doesn't wait for services. Phase 2 ships it, template-owned, waiting for `TEST_DATABASE_ADMIN_URL` and `S3_ENDPOINT_URL`. Phase 8 relies on it. DA's `_wait_for_tcp` and `_wait_for_http` are the model (§2, RT01).
4. **Phase 8 turns on the build cache (RT05) with an env var in `modernApp.test`'s `env:`.** `modernApp.test` fixes the `run-suite` flags, so `--build-cache` can't be passed. The alternative is a library argument, which would need the operator (§4.3).
5. **Phase 2 takes part of BE-C29.** BE-C09 routes the testing server through `uv run dev`, and in testing mode that starts the Werkzeug reloader. So phase 2 takes `use_reloader=False` and drops the `WERKZEUG_RUN_MAIN` branches from `run.py`. Phase 5 does the rest.
6. **Phase 3 leaves BE-T10's assertions to phase 5.** BE-T04's port leaves out DA's `Target` assertions. Phase 5 inverts the two template tests that pin today's broadcast: `test_task_events_broadcast_when_no_subject` and `test_progress_handle_none_subject_broadcasts`.
7. **BE-T10's fallback for a task without a subject follows D3's "no implicit broadcast".**
   - With OIDC on, the task's events go to nobody. With OIDC off, they go to the `local-user` sentinel. DA's `Target.role("editor")` has no meaning in the template.
   - ElectronicsInventory's two `start_task` calls (`ai_parts.py:124,258`) must pass `caller_subject` in phase 12.
   - FieldnotesApp's actioner (`actioner.py:491`) gets an explicit target in phase 15.
8. **D9b's default covers any `FLASK_ENV`.** IoTSupport's init container runs with `FLASK_ENV=db`. `STAGE` defaults to `local-tst` under testing, `local-dev` under development, and `prd` for anything else.
9. **Ownership.** Some files are app-owned (`_skip_if_exists`): a template change to them reaches new apps only, and phases 11–16 make it by hand.
   - **The files.** In the backend: `pyproject.toml`, `Dockerfile`, `.env.example`, `app/exceptions.py`, `app/app_config.py`, `app/startup.py`, `app/services/container.py` and `tests/conftest.py`. At the root: `pyproject.toml`, `.kubecoder/*`, `CLAUDE.md` and `scripts/regenerate-openapi.py`.
   - **Hand edits in phases 11–16.** The dependency bumps (BE-C08), the move to the base images (BE-C17) and the uv packaging.
   - **New exception classes (BE-C28).** Template-owned code that imports a new name from `app/exceptions.py` breaks every existing app on update, so put new exception classes in a template-owned module.
   - **The boot-time settings dump (BE-C06).** It must not dump `AppSettings`. In existing apps that class has no `Sensitive` marks, and ElectronicsInventory's holds API keys.
10. **The SSE edits in FieldnotesApp and PilotApp.**
    - PilotApp's edits are BE-T11 and FE16, which D3 takes. Phases 5 and 7 start from PilotApp's code, and phase 16 drops the edits.
    - FieldnotesApp's FN-38 binding handles connections that are left unbound under OIDC, and BE-T11 refuses such connections. Phase 15 checks that the binding is redundant and drops it. If it's still needed, phase 15 keeps it and lists it as a standing edit.
11. **FE23 needs a new "has a database" marker.** Playwright's global setup currently keys on `initialize-sqlite-database.sh`, which phase 2 deletes. Phase 6 keys on `backend/alembic.ini` instead. The backend template renders that file only with `use_database`, so the frontend template needs no new question.
12. **Preview mode never runs in CI.** Nothing sets `PLAYWRIGHT_PREVIEW_MODE`, and the suite runner builds with plain `pnpm build`. So FE16's spec, and the SharedWorker specs that need a production build, would always skip. Phase 7 settles the env names, and phase 8 adds a test-mode build step to `local.py.jinja`.
13. **Phase 17's push order.** Push DockerImages, and let it rebuild `modern-app-backend-build` with uv, before any app's `Dockerfile` moves onto that image. Otherwise every app's first build fails with `uv: not found`. The images were last built on 2026-06-17.
14. **BE-C18's pool size: take the design doc's 2+3,** which is S1's basis, not DA's 5+5.
15. **MAT-13 rides along in phase 3 with BE-C06,** using PilotApp's `make_url(...).render_as_string(hide_password=True)`. MAT-10 closes in phase 5 (§7).
16. **ElectronicsInventory's paged lists sort by `created_at` alone** (`part_service.py:132`, `inventory_service.py:358`), which is the bug D9a describes. Phase 12 adds the `id` tiebreaker once `apply_sorting()` lands in phase 5.

## 1. Item status

Status is **missing**, **partial** (the row says which part is missing) or **landed**. The "Apps" column names an app that carries its own version. Otherwise every app's copy matches the template.

### Backend core (BE-C)

Template paths are under `/work/ModernAppTemplate/backend/template/`. "Apps carry nothing" means no app has its own version. All six apps' template-owned files match the template apart from the divergences named below.

Ownership matters for the rows: `copier.yml` `_skip_if_exists` makes `pyproject.toml`, `Dockerfile`, `.env.example`, `app/exceptions.py`, `app/app_config.py`, `app/startup.py`, `app/services/container.py` and `tests/conftest.py` app-owned. A template change to those reaches new apps only; the six apps take it by hand in phases 11-16.

| ID | Ruling | Phase | Status | Where it stands now | Apps with their own version | Notes for the phase |
|---|---|---|---|---|---|---|
| BE-C01 | D2 | 4 | missing | `app/utils/auth.py:156-165` `check_authorization` still returns early when `resolve_required_role` is None; the "no recognized role" 403 (l.185) sits after it | none | Do before BE-C12. DA's hoist: `configured_roles` non-empty and no role overlap raises. Four apps have no `read_role` and are exposed today: IoTSupport (`write_role=editor`, `additional_roles=[pipeline]`), DHCPApp, ZigbeeControl and FieldnotesApp (`write_role=editor`). PilotApp sets `read=write=editor`; EI sets all three tiers. The per-app role audit is §5 |
| BE-C02 | D1 | 3 | missing | `app/database.py:121` `get_pending_migrations` wraps everything in `except Exception: return []` | none (EI, IoTSupport, PilotApp `database.py` are identical to the template) | See Details: callers need a catch |
| BE-C03 | D1 (only if gap) | 3 | partial | `app/utils/after_commit.py` (v0.13.0, `629ec60`): `after_commit(cb)`, a ContextVar queue run by `close_session` in `app/__init__.py.jinja:277-286`; tests in `backend/tests/test_after_commit.py` (5) | IoTSupport uses it (`architecture_pipeline_trigger_service.py:64`); EI and PilotApp only carry the template's `close_session` | Request path landed; background commits are the gap. See Details |
| BE-C04 | D1 | 3 | missing | No `scoped_session` or `scoped_savepoint` in `app/services/container.py.jinja` | none. Reset-without-close sites exist: template `base_task.py.jinja:123` (all apps), EI `services/metrics/dashboard_metrics.py:124`, IoTSupport `services/coredump_service.py:443` | Apply it to `BaseTask.execute` too (the leak DA fixed). Two app sites are for the apps' phase |
| BE-C05 | D1: keep `{method,endpoint,status}` | 3 | missing | No `app/utils/http_metrics.py`. The duration histogram `http_request_duration_seconds{method,endpoint,status}` exists only in `diagnostics_service.py:91` (`use_database`, `DIAGNOSTICS_ENABLED`) | FieldnotesApp has `fieldnotes_http_request_duration_seconds` (`app/fieldnotes/metrics.py:181`, no clash). No other app | See Details: name clash with DiagnosticsService, and the test registry |
| BE-C06 | D1 | 3 | missing | No `Sensitive`, `dump_for_logging`, `LOG_LEVEL` or `log_formatter.py`. `run.py` hard-codes `logging.INFO`; `create_app` testing handler uses a plain `Formatter` and `setLevel(INFO)` (`app/__init__.py.jinja:109-120`) | FieldnotesApp reads its own `FIELDNOTES_LOG_LEVEL`/`LOG_LEVEL` in `app/fieldnotes/config.py:319` | See Details: do not dump `AppSettings`. Does not cover MAT-13 |
| BE-C07 | (merged into BE-T01) | 3 | missing | `lifecycle_coordinator.py:195-202` still iterates the live list; no `unregister_lifecycle_notification` | none | Taken through BE-T01 (plan phase 3 step 1). Listed so it is not lost |
| BE-C08 | D1 | 1 | missing | `pyproject.toml.jinja` pins: pillow `^10.2.0`, spectree `^1.2.0`, flask-cors `^4.0.0`, pytest `^7.4.0`, pytest-cov `^4.1.0`, ruff `^0.11.0`, `types-flask-cors ^4.0.0`, `types-pillow ^10.2.0`. `types-flask` and the mypy sqlalchemy plugin are already gone (since v0.12.0). The `.convert()` reassignment is still in `utils/image_processing.py` (l.71, 102, 181) and `cas_image_service.py` (l.74, 104) | IoTSupport pillow `^11.0.0`; all other apps carry the old pins; FieldnotesApp and PilotApp are on spectree `<2`, flask-cors `<5`, ruff `<0.12`; FieldnotesApp pytest `>=8,<9`, PilotApp pytest `<8` | See Details: pins are app-owned |
| BE-C09 (+BE-T03) | D1 | 2 | missing | `scripts/testing-server.sh.jinja`: no `.env.test` source, no `--database-url`, ends in `exec poetry run python -m flask run`. `tests/conftest_infrastructure.py.jinja:45-48` loads `.env.test` only | none beyond uv (FieldnotesApp and PilotApp swap `poetry run` for `uv run` in this script) | See Details: reloader ordering with BE-C29 |
| BE-C10 | D1 | 3 | partial | Root layer landed: `root/template/.gitignore` has `.env*` and `!.env.example` (since root v0.1.0). Backend `template/.gitignore` still lists `.env` and `.env.test`; no `coverage/` | none; all six apps' root `.gitignore` has `.env*` | In a monorepo the root pattern already covers `backend/`, so DA's change has no effect. Either align the backend file or skip; `coverage/` belongs to BE-C30 (not taken) |
| BE-C11 | D1 | 3 | missing | `app/utils/empty_string_normalization.py:36-47` has no opt-out | none | Three lines: skip a column when `column.info.get("allow_empty")`. Add a test |
| BE-C12 (+BE-T09) | D4 | 4 | missing | `app/utils/auth.py` `authenticate_request` has no tolerant mode, no `resolve_auth_identity`, no `no_role_check`; `@public` endpoints skip the hook; `/api/auth/self` and `oidc_hooks.py` each hold a copy of the test-session lookup (`api/auth.py:67-75`, `oidc_hooks.py:70`) | FieldnotesApp restructured `app/api/oidc_hooks.py` (`authenticate()` plus a wrapper that binds the SSE connection to the user via `X-SSE-Request-Id`); a `copier update` conflicts there | Needs BE-C01 first. Leave out `seed_user`/tenant glue. Mind the FieldnotesApp conflict in phase 15 and BE-T10/T11's SSE binding |
| BE-C13 (+RT15 rule) | D5 | 5 | missing | `services/health_service.py`: `register_healthz`/`register_readyz` sequential, uncached, dict with `ok`; `status` strings `ready`/`not ready`/`shutting down`. Checks are registered inline in `app/__init__.py.jinja:152-188` (database, sse_gateway); `S3Service.startup()` registers none | FieldnotesApp registers `store` through `register_readyz` (`services/fieldnotes_service.py:78`) | Needs BE-C02. The format change reaches the probes and anything that parses the body. Add a `critical` flag per D5. The RT15 rule ("a new integration registers its own probe") has no phase; phase 9 should take it |
| BE-C14 (+BE-T19) | S4 | 3 | missing | `flask_error_handlers.py.jinja:276-279` `handle_generic_exception` returns `{"message": str(error)}`. The separate 500 handler (l.133-141) is already generic | none | Gate on the S6 internals fact, which phase 3 builds in step 4. DA's portal-blueprint test does not carry over; write a new one |
| BE-C15 | S2 | 4 | missing | `oidc_client_service.py:227,282` build `redirect_uri` from `config.baseurl`; `api/auth.py:325` builds the logout URI from `baseurl`; `utils/auth.py:427` `validate_redirect_url(url, base_url)` accepts same-origin absolute URLs; `AuthState` has no `origin` | none; all six apps are template-identical | See Details: dev proxy and FE13 |
| BE-C16 | D1, default 50 MB | 3 | missing | No `MAX_CONTENT_LENGTH` anywhere in the template. Frontend `nginx.conf.jinja:21` already sets `client_max_body_size 50M` | none. EI's own limits: `MAX_FILE_SIZE` 100 MB, `MAX_IMAGE_SIZE` 10 MB (`app_config.py:37-44`) | Put `MAX_UPLOAD_SIZE_MB` in `Settings` (`config.py.jinja`, template-owned) and set the config in `create_app`, not `startup.py` (app-owned, DA's spot). EI's 100 MB is already cut to 50 MB by nginx; EI must set the setting if it wants more |
| BE-C17 | S3 | 8 | missing | `Dockerfile.jinja`: `python:3.13-slim` both stages, `pip install poetry`, inline apt block. `Jenkinsfile.jinja` is already deleted (since v0.12.0) | none uses `modern-app-backend*`. PilotApp keeps `python:3.13-slim` with `pip install uv` | `Dockerfile` is app-owned, so apps change it by hand. §6.1 lists what the images carry; `modern-app-backend-build` needs uv first |
| BE-C18 (+BE-T08) | S1 | 2 | missing | No `TEST_DB_POOL_*`; `Settings.load` builds the engine options from `DB_POOL_*` only (`config.py.jinja:430-437`); test settings use pool 20/30 on SQLite (`conftest_infrastructure.py.jinja:123-124`) | none | See Details: pool sizes disagree |
| BE-C24 | S6/D9b | 3 | missing | No `STAGE`. `FLASK_ENV` drives `is_testing`/`is_production`; `sse.py.jinja:37` and `load()` (`sse_heartbeat_interval`) test `flask_env == "production"`. Frontend version broadcast has no local skip | none (no app mentions `STAGE`; `HOMELAB_INTERNAL` appears only in the plan docs) | See Details: DA has no CLI guard to copy; its default differs from the ruling |
| BE-C25 | D9c | 4 | missing | `auth_service.py` has no `role_hierarchy`; `spectree_config.py.jinja` writes `x-auth-roles` without `hierarchy` | none | `AuthService` and `spectree_config` are template-owned; `container.py` is app-owned but needs no change (default None). DA's 24 tests come with it |
| BE-C27 | D9a, backend only | 5 | missing | `schemas/common.py:43-60` has `PaginationMetaSchema` and `PaginatedResponseSchema`; no `app/utils/pagination.py` | none. No app paginates (no `per_page`/`sort_by` in any `backend/app`); six apps carry the unused `PaginatedResponseSchema` | Do not copy DA's removal of `PaginatedResponseSchema`. Adding `sort_by`/`sort_dir` to `PaginationMetaSchema` makes them required, which breaks any app that builds it; none does today. The convention (RT10) goes to the phase 9 skill |
| BE-C28 | D9 | 5 | missing | `app/exceptions.py` (app-owned) has no `ExternalServiceException`; `common.py` has `ErrorResponseSchema`, no `ApiErrorResponseSchema` | IoTSupport: own `ExternalServiceException(operation, cause)` with a 502 handler in its `startup.py:104` | See Details: ownership and signature clash |
| BE-C29 | D9 | 5 (root half 8) | missing | `run.py` still uses `WERKZEUG_RUN_MAIN` and `app.run(debug=True)`; `scripts/dev-server.sh` is a restart-on-keypress loop; no `watchdog` dependency. Root `Procfile.dev.jinja:3,14` says "Werkzeug auto-reload" and runs `poetry run dev` | FieldnotesApp and PilotApp changed the dev scripts for uv only | See Details: ordering with BE-C09; DA's script needs uv edits |
| MAT-13 | (card, not in rulings) | 3 | missing | `app/cli.py.jinja:70` and `:135` print `app.config['SQLALCHEMY_DATABASE_URI']` unmasked. Card MAT-13 is State New, tag Solution Known | PilotApp masks it in its template-owned `cli.py:67-68,134-135` (and has `tests/test_cli.py` asserting the password is absent); EI and IoTSupport print it raw (`cli.py:65`, `:130`); the no-database apps have no `cli.py` print | DA did not fix it: its `cli.py:179,313` print the raw URI. BE-C06 does not cover it: redaction is for the `Settings` dump. Take PilotApp's `make_url(...).render_as_string(hide_password=True)` in phase 3 and close the card; the template's `tests/test_cli.py` asserts on "Using database", so check it. `scripts/init-dev-database.py.jinja:37` also prints the full URL when it has no database name (minor). Apps that logged a password should rotate it |

#### Details (BE-C)

- **BE-C01.** `AuthService` with `read_role=None` returns `None` from `resolve_required_role` for GETs, so today any authenticated user passes. DA's change is one hoisted check at the top of `check_authorization`. Logout and callback stay reachable only once BE-C12's `@no_role_check` exists, so land the two together.
- **BE-C02.** Callers that relied on the swallow: `_check_db_readiness` (`app/__init__.py.jinja:162`) has no try/except and readyz would answer 500, so catch there (DA's `HealthService` does). `get_current_revision` (l.66-75) also swallows and DA left it; with the DB down, `get_pending_migrations` then returns every revision, not an error. `cli upgrade-db` (l.90) and `upgrade_database` (l.221) now surface errors.
- **BE-C03.** The template's `after_commit()` is a ContextVar queue drained only by `close_session`. Nothing drains it for commits outside a request: `BaseTask.execute` (`base_task.py.jinja:111-123`), the BE-C04 `scoped_session`, CLI and polling callbacks. A callback registered in a task thread is never run and stays in that thread's context. DA's `add_after_commit(session, cb)` hangs on SQLAlchemy's `after_commit` and handles all of those, but it keeps duplicates, where the template's version coalesces them. Recommendation: keep the template API and have `scoped_session` and `BaseTask.execute` call `run_after_commit_callbacks()` and `clear_after_commit_callbacks()`; do not add a second mechanism. S1 already assumes `after_commit()` stays. Phase 3 picks; DA's listener is the alternative, and both are within D1. DA's 6 tests in `tests/test_session_hooks.py` then become extra cases in `test_after_commit.py`.
- **BE-C05.** Two histograms called `http_request_duration_seconds` cannot both register. DA dropped the `DiagnosticsService` copy; to keep the label set, make the new module own the three-label histogram and remove the one in `DiagnosticsService._init_metrics` (and its `.observe` at the response hook). Non-database apps get no request metrics today, so this is also their first. The tests' autouse `clear_prometheus_registry` unregisters module-level metrics after the first test; phase 2 changes that to once per session, so check the metrics test after both.
- **BE-C06.** `app_config.py` is app-owned, so existing apps' `AppSettings` has no `dump_for_logging` and no `Sensitive` marks (EI holds `OPENAI_API_KEY`, `MOUSER_SEARCH_API_KEY`). Dump `Settings` only, or `AppSettings` only when it has the method and marks. `run.py` is edited by BE-C06, BE-C29 and BE-C09, and DA's `run.py` is restructured for worker modes, so port by hand and do the three in one pass. Do not copy DA's `Sensitive` on `sqlalchemy_engine_options`. The testing-mode `setLevel(INFO)` in `create_app` should follow `LOG_LEVEL`.
- **BE-C08.** The pins in `pyproject.toml` are app-owned: template pins reach new apps only; the six apps bump in phases 11-16. Phase 1 moves to uv, so the bump rides on a rewritten file. Pillow 12 needs the `processed: Image.Image` change in the five sites and drops `types-pillow`; mypy decides about spectree 2 and flask-cors 6. `types-flask-cors` goes to `^6` in DA. DA's `pythonpath = ["."]` for pytest 9 was for its own plugin; the template needs it only if rootdir detection breaks in the monorepo, which phase 1's test run shows.
- **BE-C09.** `poetry run dev` goes through `run.py`, where `debug_mode` is true for `FLASK_ENV=testing`, so `app.run(debug=True)` starts the Werkzeug reloader. Without BE-C29's `use_reloader=False` and removal of the `WERKZEUG_RUN_MAIN` branches, the Playwright backend would run as parent plus child and skip background services in the parent. Phase 2 must take that part of `run.py` too, or phase 5's work must come first. The pytest side: load `.env` then `.env.test` with `override=True` (the template loads `.env.test` only). The command becomes `uv run dev` after phase 1. DA's `--database-url` takes precedence over `--sqlite-db`; SQLite goes in phase 2, so drop `--sqlite-db`.
- **BE-C15.** Behind the template's frontend nginx, `proxy.conf` sets `Host $host` (no port) and no `X-Forwarded-Host`; `create_app` already uses `ProxyFix(x_host=1)`. The origin that results is right in prod only with FE13 (Host with port) or an ingress that sends `X-Forwarded-Host`. In dev and the Playwright run, `vite.config.ts.jinja` proxies `/api` with `changeOrigin: true`, which rewrites Host to the backend (`localhost:3401`), so `redirect_uri` would point at the backend. Phase 4 must check this and fix the proxy (forwarded host) before the change works in dev. The IdP needs each hostname's redirect URI registered; that is phases 11-16. `validate_redirect_url` must also reject `//host` forms (relative-only).
- **BE-C18.** DA uses 5+5 for `FLASK_ENV=testing` with explicit env winning (`model_fields_set`); PilotApp's design doc says 2+3 for pytest and `DB_POOL_SIZE=2`/`DB_POOL_MAX_OVERFLOW=3` set in the Playwright backend's environment. Phase 2 picks one set of constants. The pytest settings must set the whole `sqlalchemy_engine_options` dict (BE-T08), which the template's `_build_test_settings` does not do now.
- **BE-C24.** (a) The inventory says DA stage-gates destructive CLI commands. It does not: DA's `cli.py` has no stage check. DA's real uses are `simulation_guard.py` (blocks on `prd`) and Keycloak user recreate. The destructive-command guard (`upgrade-db --recreate`, `load-test-data`) is new work for phase 3, as is the guard on the template's testing blueprints (`testing_guard.py`, today `is_testing` only). (b) DA's `STAGE` default is `local-dev` always; the ruling's default (`prd` under production `FLASK_ENV`, `local-tst` under testing, `local-dev` in development) is new. Pydantic cannot derive it in the field default, so resolve it in `Settings.load()`, and `Settings(...)` built directly in tests needs a default too. (c) Leave out DA's stage-derived S3 bucket and queue prefix. (d) `GET /api/ui-setup` and `schemas/ui_setup_schema.py` (stage and release notes) are DA files not itemised under BE-C24; the S6 fact needs a template version. (e) The version-broadcast skip is `frontend_version_service.py:104-110` in DA; the template's service differs (BE-T12 changes it too). (f) The CI Job sets `tst`; the dev stack sets `local-dev` (phase 8).
- **BE-C28.** `app/exceptions.py` is app-owned, so a template-owned handler that imports `ExternalServiceException` from it breaks every app that lacks the class after `copier update`. Either put the class in a new template-owned module or have each app add it before the update (phases 11-16). IoTSupport's class takes `(operation, cause)`, DA's `(service, cause)`; adopting DA's signature changes IoTSupport's call sites (`device_service.py`, `rotation_service.py`, `error_handling.py`), or the template class keeps IoTSupport's shape. `UnprocessableEntityException`, `WorkspaceLockedError`, `locked_by` and `ConflictLock*` schemas stay out. `TaskAcceptedSchema` is not in the ruling.
- **BE-C29.** DA's `scripts/dev-watch.sh` runs `poetry run -- watchmedo auto-restart ...` with `--pattern='*.py;*.env*;*/app/assets/*'`; under uv it becomes `uv run -- watchmedo`, and `watchdog[watchmedo]` goes into the dev dependencies (app-owned `pyproject.toml`). The root `Procfile.dev` backend line changes to call it, and the Procfile comment saying "Werkzeug auto-reload" goes. The template's `dev-server.sh` (restart on keypress) overlaps: decide whether it stays.

#### Merged items (BE-C)

- BE-C03 absorbs BE-T02 (tests, covered above). BE-C09 absorbs BE-T03. BE-C14 absorbs BE-T19. BE-C18 absorbs BE-T08. BE-C13 absorbs RT15 (rule needs a home in phase 9). BE-C27 absorbs RT10 (convention for the phase 9 skill). BE-C23 absorbs RT12 (not taken, with ICU collations left in DA).
- Merged away from the BE-C range: BE-C07 into BE-T01 (taken in phase 3, status above); BE-C31 into RT14 (S5, phase 9).

#### DA dependencies the inventory doesn't itemise

- `GET /api/ui-setup` with `schemas/ui_setup_schema.py` (S6's hand-off to the frontend); also the `stage` field in `portal_schema.py` (DA-specific, leave).
- `app/api/simulation_guard.py` is the pattern for the `prd` guard on test endpoints.
- DA's `run.py` restructure into modes (BE-C19) intermixes with BE-C06, BE-C09 and BE-C29; no patch applies as is.
- `Stage` is injected into `KeycloakAdminService` and read by `HealthService`; only the `HealthService` use is in scope.
- DA's `container.py` passes `role_hierarchy={"editor": ["portal"]}`; the template needs only the parameter.

### Backend SSE, tasks and tests (BE-T)

Read at backend template v0.13.3 (`/work/ModernAppTemplate/backend/`), apps as checked out. "Mother" means the mother suite `backend/tests/`. "Tmpl" paths are under `backend/template/`. Template-owned SSE and task files (`sse_connection_manager.py`, `task_service.py`, `frontend_version_service.py`, `api/tasks.py`, `lifecycle_coordinator.py`, `testing_logs.py`, `log_capture.py`, `auth_service.py`, `oidc_client_service.py`) are byte-identical to the v0.12.0 baseline render, so DA's patches to them apply as written. Counts: 1 landed, 4 partial, 13 missing, plus MAT-10 open.

| ID | Ruling | Phase | Status | Where it stands now | Apps with their own version | Notes for the phase |
|---|---|---|---|---|---|---|
| BE-T01 (+BE-C07) | D1 | 3 | missing | `tmpl/app/utils/lifecycle_coordinator.py` has no `unregister_lifecycle_notification`; `_raise_lifecycle_event` iterates the live list. `tmpl/app/api/testing_logs.py` and `tmpl/app/utils/log_capture.py` are the baseline (shared `connection_close` broadcast). Mother `tests/test_lifecycle_coordinator.py` (18 tests) has none for unregister. | None. No app has `unregister_lifecycle_notification`; none edited these files. | Four template files: the three above plus `tmpl/app/__init__.py.jinja:124-128` (drop `set_lifecycle_coordinator`). The new abstract method breaks `StubLifecycleCoordinator` in mother `tests/testing_utils.py` and in EI's and IoTSupport's own `tests/testing_utils.py` copy (phases 11, 12). DA's `test_testing_logs_stream.py` (8) ports as is; its coordinator tests belong in `test_lifecycle_coordinator.py`. No Playwright or root code reads the log stream's `connection_close`; the `connection_close` listeners in `sse-worker.ts:212` and `sse-context-provider.tsx:249` are on the gateway stream. |
| BE-T02 | merged into BE-C03 | none | landed | Template has its own design: `tmpl/app/utils/after_commit.py` (ContextVar callbacks, dedup), run from `teardown_request` in `tmpl/app/__init__.py.jinja:255-286` after a successful commit and dropped on rollback. Mother `tests/test_after_commit.py` (5 tests). Landed v0.13.0 (backend `629ec60`, 2026-09-26). | EI, IoTSupport (`architecture_pipeline_trigger_service.py`) and PilotApp use it. | Do not port DA's `session_hooks.py` or its 6 tests; the template's version covers the same ground. The S1 session must keep `commit()` real so this hook fires under test (design doc §3.4). |
| BE-T03 | merged into BE-C09 | 2 | missing | `tmpl/scripts/testing-server.sh.jinja` has `--sqlite-db` only, does not source `.env.test`, ends in `poetry run python -m flask run`. `tmpl/tests/conftest_infrastructure.py.jinja` loads `.env.test` only. | None. | Ships with S1 (plan phase 2 step 8). The `poetry run` becomes `uv run` in phase 1. |
| BE-T04 | D1 | 3 | partial | Mother `tests/test_task_service.py` has 17 tests (DA: 38), plus `test_task_api.py` 8, `test_base_task.py` 6, `test_task_schemas.py` 17. Covered: start, status, failure, cancel, remove, events, concurrency, shutdown, cleanup, progress handle. Missing: monotonic progress, text-only/value-only updates, SSE send exception swallowed, start during shutdown raises, cancelled stays cancelled, `mode='json'`, remove of failed/cancelled, recent and running tasks survive cleanup, lifecycle (flag, gauge, `wait_for_tasks` timeouts, `_check_tasks_complete`, `SHUTDOWN` clears state). | None own tests. | Template tests `test_task_events_broadcast_when_no_subject` and `test_progress_handle_none_subject_broadcasts` pin today's broadcast; BE-T10 (phase 5) must invert them. Phase 3 should port DA's lifecycle, progress and cleanup tests now and leave DA's Target assertions (`Target.subject`, `Target.role`) for phase 5. |
| BE-T05 | D1 | 3 (redirect tests: 4) | partial | The template already has about 114 auth tests: `tests/services/test_auth_service.py` 15, `test_oidc_client_service.py` 38 (DA: 19, so a superset), `tests/api/test_auth_endpoints.py` 11, `test_auth_middleware.py` 14, `tests/utils/test_auth_utils.py` 36 (includes `validate_redirect_url`). DA's three files total 65. Missing from `AuthService`: missing `sub`, malformed token, generic error records the metric, duration histogram, claim-shape cases (`realm_access` not a dict, no `resource_access`, `aud` None, both lists empty), OIDC-enabled init failures (missing issuer or client id, JWKS client failure), JWKS discovery (HTTP error, missing `jwks_uri`), and `resolve_required_role` (7). | None own tests. | Take only the missing cases into `tests/services/test_auth_service.py`; do not overwrite. Hold DA's `resolve_required_role` tests until BE-C01 (phase 4), which changes its fallback. DA's `test_auth_redirect.py` (14): the origin-from-request tests need BE-C15 (phase 4); about 3 template equivalents already exist. The inventory's "least-tested area" premise is out of date. |
| BE-T06 | S1 | 2 | missing | See Details (S1). Template is per-test app on an in-memory SQLite clone; `session` commits at teardown. | None. No app has a session-scoped app, savepoints or `begin_nested`. | See Details (S1). PilotApp hasn't built the design. |
| BE-T07 | S1 | 2 | missing | See Details (S1). Nothing creates a PostgreSQL test database; `TEST_DATABASE_ADMIN_URL` appears nowhere in any template. | None. EI, IoTSupport, PilotApp: SQLite fixtures from the template. | See Details (S1). |
| BE-T08 | merged into BE-C18 | 2 | missing | `tmpl/app/config.py.jinja` has no `TEST_DB_POOL_*`; `_build_test_settings()` uses pool 20/30 and no `sqlalchemy_engine_options`; `Settings.load` builds the options at `config.py.jinja:422`. | None. | Design doc §4.2 sets pytest's pool to 2+3 through `sqlalchemy_engine_options`, so set the whole options dict (DA's trap: a partial dict silently ignores the pool). |
| BE-T09 | D4 | 4 | missing | Mother has 14 middleware tests (`tests/api/test_auth_middleware.py`) and 11 endpoint tests, all against today's strict `authenticate_request` (`tmpl/app/utils/auth.py:219`). No `@no_role_check`, tolerant mode or `resolve_auth_identity` anywhere in the template. | None. No app has any of them. | Port with BE-C12. Of DA's six files, `test_auth_role_hierarchy.py` (25) goes with D9c, not D4: the basic hierarchy (`expand_roles`, `configured_roles`) is already in the template (since `d615c72`); BE-C25 adds validation and cycle detection, so only the tests for those are new. |
| BE-T10 | D3 | 5 | missing | `tmpl/app/services/sse_connection_manager.py:send_event(request_id \| None, ..., target_subject=None)`: `None` is broadcast, a subject filters on the identity map plus the `local-user` sentinel. `TaskService`/`TaskProgressHandle` pass `target_subject`. Mother `test_sse_connection_manager.py` (9) pins this. | None has `Target`. App call sites in Details (BE-T10). FieldnotesApp added `bind_unbound_identity` to the manager. | DA's `Target` is an AMQP routing-key object; on the HTTP transport it must resolve to tokens in memory (connection to `_connections`, subject to `_identity_map`, broadcast to all). `Target.role` cannot be delivered, because the identity map holds subjects only; DA's `editor` fallback is DA-specific. Keep `get_connection_info`, `has_connection`, `register_on_connect`/`register_on_disconnect` and `bind_identity`: apps call them (Details). Signature change touches `task_service.py`, `frontend_version_service.py`, `api/testing_sse.py:181`. Mother `integration/test_sse_gateway_tasks.py` docstring says task events are broadcast to all connections. |
| BE-T11 | D3 | 5 | missing | `tmpl/app/api/sse.py.jinja`: `on_connect` registers the connection first, then `_bind_identity` only logs a warning on a missing or invalid token. No 401/403, no forced-rejection hook (`tmpl/app/services/testing_service.py.jinja` and `api/testing_auth.py` have `forced_auth_error` only). Mother `tests/test_sse_api.py` (11) has no OIDC-on callback test. | PilotApp has it: commit `3f84260` (ported from DA `b4997d6`), `backend/app/api/sse.py` (401, 403, forced hook consumed before identity), `testing_service.py:127-143`, `testing_auth.py:150` (`POST /api/testing/sse/force-callback-error`), `schemas/testing_auth.py:53`, `tests/test_sse_callback.py` (14). Other apps: none. | Start from PilotApp's version, not DA's: it is already on the HTTP manager and the template's `_extract_token_from_headers`. Replace the literal `editor` with `auth_service.configured_roles`. PilotApp's commit message says to take the template's side on `copier update` (phase 16), and the edit is not in its `CLAUDE.md` list of standing edits. The frontend needs FE16 or the stream loops (phase 7), and the Playwright spec needs the hook endpoint. The gateway `stable` branch is already pinned (`ssegateway#stable`). |
| BE-T12 | D3 | 5 | missing | `tmpl/app/services/frontend_version_service.py` is the baseline: `_pending_version` dict (cleared only at `SHUTDOWN`), on-connect observer, `{"version": "unknown", "error": ...}` on fetch failure. No mother test file for it (DA: 9). | None edited it; every SSE app carries the template copy. | Parts and dependencies in Details (BE-T12). Mother `integration/test_sse_gateway_version.py::test_pending_events_flushed_on_connect` pins the on-connect send. |
| BE-T13 | D5 | 5 | partial | Landed: `register_healthz`/`register_readyz` (`tmpl/app/services/health_service.py`), checks registered in `tmpl/app/__init__.py.jinja:169,187` (database, SSE gateway), any failing check gives 503, 503 while shutting down. Mother `tests/test_health_api.py` (15). Missing: self-registration by services, `register_check`, concurrency, per-check timeout, 30 s cache, `critical` flag, metrics, and any S3 check (none exists, so D5's "S3 where use_s3" is new). DA: 29 + 5 tests. | FieldnotesApp registers its own check: `services/fieldnotes_service.py:78` (`register_readyz("store", ...)`). The other five register only the template's database and `sse_gateway` checks. | The registration API changes shape (`register_readyz` to the new one), so FieldnotesApp's call moves in phase 15. Port DA's tests minus the Keycloak, RabbitMQ, OpenAI and OpenSearch cases; add critical-versus-non-critical cases (D5), which DA lacks. Needs BE-C02 first (`get_pending_migrations` swallows errors, `database.py:78-121`). |
| BE-T14 | D1 | 3 | partial | Mother `tests/test_s3_service.py` has 12 mocked-boto3 tests (DA: 47). Covered: client init, upload, download, delete, `file_exists`. Missing: `copy_file`, `get_file_metadata`, `list_objects`, `delete_prefix`, `ensure_bucket_exists` branches, hash and CAS key, `startup()` swallowing failures, error mapping on download and delete. | None. EI and IoTSupport test S3 only through their own services. | Extend the file; do not replace it. Drop DA's presigned, `get_object_stream` and `list_objects_with_metadata` tests (BE-C26 not taken) and the health-check registration tests (the template's `startup()` registers none; add them if D5 adds an S3 check). |
| BE-T15 | D1 | 3 | missing | `Sensitive`, `dump_for_logging`, `LOG_LEVEL` and `TEST_DB_POOL_*` appear nowhere in `backend/template` (grep). Mother `tests/test_config.py` has 6 unrelated tests (Environment and production validation). | None. | Blocked on BE-C06 (phase 3) for the redaction, dump and log-level tests, and on BE-C18 (phase 2) for the pool tests. Merge into the existing `test_config.py`; DA's file has a different scope. |
| BE-T16 | D4 | 4 | missing | `tmpl/app/api/tasks.py` has no authorisation on status, cancel or delete: any authenticated caller can act on any task id. `TaskInfo.subject` is recorded (`task_service.py:171`). Mother `tests/test_task_api.py` (8). | None. | DA's `@allow_roles("editor")` is DA-specific. D4 says "check the caller": an owner-subject check against `TaskInfo.subject` is possible today. The rule for tasks with no subject (OIDC off, system tasks) needs deciding in phase 4. |
| BE-T17 | S5 | 9 | missing | No SSE-targeting doc and no conventions skill exist. Neighbours: `backend/CLAUDE.md` (running the two suites, SQLite section 5, conftest gotcha), `docs/backend_porting_guide.md` section 2.6 (test fixtures), every app's `docs/slice-test-plan.md` (how a slice is verified, not coding conventions). KubeCoderConfig `kubecoder/skills/` has seven skills, none on conventions. | None has DA's `testing.md` or `sse-event-targeting.md`. | Pure docs. `backend/CLAUDE.md` section 5 and `docs/copier_approach.md:342` need rewording when S1 lands (phase 2). The six SSE targeting rules are written in BE-T10's inventory entry. |
| BE-T19 | merged into BE-C14 | 3 | missing | `tmpl/app/utils/flask_error_handlers.py.jinja:276-284` returns `{"message": str(error)}` on every 500. No sanitisation test. | None. | S4/S6 shape it; DA's two tests need adapting to the `STAGE`-based fact. |
| MAT-10 | D3, D4 (card) | 5 (BE-T16: 4) | open | Not closed in the template. See Details (MAT-10). | PilotApp closes the anonymous-connection half through its own BE-T11. EI starts tasks with no subject today. | See Details (MAT-10). |

#### Details (BE-T)

**BE-T06 / BE-T07, S1: what the template's test infrastructure is today, and the distance to design doc §3.4 and §4**

PilotApp has not done this. `/work/PilotApp/backend/tests/conftest.py` is the 9-line star import, `tests/conftest_infrastructure.py` is still the template's SQLite file, and PilotApp's `.kubecoder/config.yaml:39` says the suite runs on in-memory SQLite. The design doc is advice for its slice 002. No file in any of the six apps has `begin_nested`, `create_savepoint` or `TEST_DATABASE`. There is no reference implementation to copy; DA's and the design doc are all there is.

Today, in `tmpl/tests/conftest_infrastructure.py.jinja` (`use_database` branch) and, as a separate full copy, mother `tests/conftest.py`:

- `pytest_configure` (line 52) checks S3 only (`use_s3`); there is no PostgreSQL preflight.
- Autouse function-scoped `clear_prometheus_registry` (line 92) strips the registry before and after every test.
- `_build_test_settings()` (line 118) sets `database_url="sqlite:///:memory:"`, pool 20/30, no `sqlalchemy_engine_options`.
- `template_connection` (session scope, line 215) builds one in-memory SQLite connection on a `StaticPool` and calls `upgrade_database(recreate=True)`. On SQLite that is `create_all` plus `stamp head`, so no Alembic revision runs in any test.
- `app` (function scope, line 244) copies the template with `sqlite3.backup` and runs `create_app()` per test.
- `session` (line 280) takes `container.db_session()` and commits at teardown. `container` (line 329) overrides `session_maker` with a plain `sessionmaker`.
- `oidc_app` (line 463) clones the template per test.
- Mother only: `sse_server` (session scope, line 451, a real threaded Flask server with its own SQLite clone), `sse_gateway_server`, and tests that build `sqlite://` settings themselves: `test_app_factory.py`, `test_sse_api.py:97,108`, `services/test_diagnostics_service.py`, `test_cli.py` (file databases `cli-test.db`, `upgrade-test.db`).
- `test-app-domain/tests/test_items.py` uses only `client` and commits through request teardown.

Design doc §3.4/§4 asks for the following; every item is new:

1. A run prefix, a sweep that drops stale databases without `FORCE` and skips those in use, `TEST_DATABASE_ADMIN_URL`, ICU `und` / `C` locale, an Alembic-built `<run>_tpl` followed by `post_migration_hook`, then the engine disposed so the database can be cloned.
2. A session-scoped `app` on `<run>_main`, cloned from `<run>_tpl`.
3. A savepoint-bound `session` where only `close()` is a no-op and `commit()`/`rollback()` stay real, and a `container` that makes `session_maker` return it.
4. `client` must depend on `container`. DA's `client` depends on `app` only, so a test that uses just `client` commits for real into the shared database. The domain tests do exactly that.
5. A tier-2 `committed_app` with its own cloned database. Mother `sse_server` is a natural user (real threads, real commits).
6. Prometheus cleared once per session and before each extra app. `oidc_app` shares the main URL (`render_as_string(hide_password=False)`) and re-wires the main container (`app.container.wire(packages=['app.api'])`) afterwards.
7. Small pools (BE-T08), a drift test (`compare_metadata`), migration tests, and a clear `pytest.exit` when the admin URL is unreachable.
8. The mother suite's own `conftest.py` needs the same rewrite, since it is a full copy and not a star import. The mother domain suite builds its schema from `test-app-domain/alembic/versions/001_create_items.py`; a freshly generated app has no revision, which must still work.

Things that depend on ordering:

- The design's drift test relies on `get_pending_migrations()` not swallowing errors. BE-C02 is in phase 3, after S1. Phase 2 should assert the database revision equals head itself.
- SQLite leftovers in the template, for plan phase 2 step 7: `tmpl/app/database.py:182-206` (recreate branch), `tmpl/scripts/initialize-sqlite-database.sh`, `tmpl/scripts/testing-server.sh.jinja` (`--sqlite-db`, lines 26-77), `tmpl/app/config.py.jinja:12,324-329` (docstring and `set_engine_options_override`; the latter is called only by mother `test_app_factory.py:19,30`), `tmpl/app/services/metrics_service.py:102` (comment), `tmpl/scripts/init-dev-database.py.jinja:9` (docstring "they run on SQLite"), `backend/CLAUDE.md` section 5, `docs/copier_approach.md:342`, `docs/backend_porting_guide.md:266`. Elsewhere (other phases): `root/template/.kubecoder/config.yaml.jinja:11-15`, this repo's `.kubecoder/config.yaml` ("No suite uses it"), and the frontend's `global-setup.ts`, `fixtures-infrastructure.ts.jinja` (`sqliteDbPath`), `process/servers.ts` (phase 6).
- Apps' own SQLite-bound tests (for phases 11, 12, 16): EI `tests/conftest.py` (`sse_server` on `template_connection`), `tests/api/test_testing.py:389`, `tests/test_role_based_access.py:13`, `tests/test_startup.py` (dialect stubs, harmless); IoTSupport `tests/conftest.py:41`, `tests/api/test_testing.py` (own `testing_template_connection`, `_override_settings_for_sqlite`) and `test_testing_device_sse.py`. PilotApp: only template-owned files. DHCPApp, ZigbeeControl and FieldnotesApp have no `use_database`, so S1 does not touch their pytest. §5 has the full list.

**BE-T10 call sites in apps (phases 11-16)**

- Task starts without a subject: EI `app/api/ai_parts.py:124,258` (see MAT-10); FieldnotesApp `fieldnotes/actioner.py:491` (system task). With a subject: FieldnotesApp `fieldnotes/inbox.py:522,554,671`. Template `api/testing_sse.py:116` in all six.
- Direct `send_event`: IoTSupport `services/device_log_stream_service.py:297` (by request id) and `rotation_nudge_service.py:56` (broadcast); DHCPApp `api/internal.py:50` (broadcast `data_changed`); ZigbeeControl `services/tab_status_service.py:34` (broadcast) and `:40` (by request id). EI, IoTSupport, DHCPApp, ZigbeeControl and FieldnotesApp register `register_on_connect` observers through the template's version service; ZigbeeControl also through `tab_status_service`. IoTSupport uses `get_connection_info` and `register_on_disconnect`; every app's `testing_sse.py` uses `has_connection`. So DA's stateless manager (BE-T20, not taken) cannot be adopted; keep the stateful HTTP manager and add `Target` on top.
- FieldnotesApp carries two template-owned edits not in its `CLAUDE.md` list: `bind_unbound_identity` in `sse_connection_manager.py` and the `X-SSE-Request-Id` binding in `api/oidc_hooks.py` (commit `34f6d65`, P3), with `tests/test_sse_identity.py`. Once BE-T11 rejects unauthenticated connects and FE16 reconnects after a refresh, a connection can no longer sit unbound under OIDC; the phase 15 owner (with the operator) decides whether to drop it. The manager rewrite will conflict with it.

**BE-T12: which parts depend on DA's stateless manager**

- Independent, port in phase 5: `_fetch_frontend_version` returns `None` on failure and nothing is sent in place of the `"unknown"` payload; the unbounded `_pending_version` goes (drop it on disconnect through `register_on_disconnect`, or delete the dict); `queue_version_event` sends with `BROADCAST_TARGET` (rides with BE-T10); the local-stage skip needs `settings.stage`, which BE-C24 adds in phase 3.
- Dependent on the stateless manager: removing the on-connect observer and sending the version only on `STARTUP`. With the stateful manager a client that connects after startup would never get a version, and mother `integration/test_sse_gateway_version.py::test_pending_events_flushed_on_connect` would fail. Keep the on-connect send. DA's startup-broadcast tests (`TestStartupBroadcast`) need rewriting as on-connect tests; the `queue_version_event` and shutdown tests port as is.
- Cost to note: the on-connect observer runs inside the gateway's connect callback and does a 2 s `requests.get`, so a down frontend slows every connect.

**MAT-10: does BE-T10 plus BE-T11 close it, and what the template does today**

Today, both halves of the card are true in the template:

- `api/sse.py.jinja` calls `on_connect` before `_bind_identity`; a missing or invalid token only logs, so an anonymous connection stays registered with no identity.
- `TaskService.start_task(caller_subject=None)` calls `send_event(None, ..., target_subject=None)`, which sends to every registered connection. With a subject set, the manager sends only to connections bound to that subject or to `local-user`, which excludes anonymous ones.
- Live exposure: EI's two `start_task` calls in `ai_parts.py` pass no subject, so its AI analysis progress and results go to every connection. Mother tests `test_task_events_broadcast_when_no_subject` and `test_progress_handle_none_subject_broadcasts` pin the behaviour.

What closes it:

- BE-T11 as PilotApp built it closes the card's stated proposal (OIDC on: no registered connection without a valid token and a configured role), because the 401/403 comes before `on_connect`. It does not stop one signed-in user from receiving another's unscoped task events.
- BE-T10 as DA built it closes that, but DA's fallback for "no subject" is `Target.role("editor")`, which has no meaning on the HTTP transport (no role is tracked) and no meaning in the template. The fallback that follows D3's "no implicit broadcast" (plan correction 7): with OIDC on and no subject, deliver nothing and log at debug; with OIDC off, target the `local-user` sentinel. EI's `ai_parts.py` must then pass `caller_subject` in phase 12, or its AI progress stops arriving.
- Together, with the fallback chosen and EI's call sites fixed, the card is closed. BE-T16 (task endpoints check the caller, phase 4) covers the REST side of the same leak, which the card does not mention.

### Frontend (FE)

Checked against frontend template v0.20.5 (`/work/ModernAppTemplate/frontend/template/`) and the six apps' `frontend/`. Every template file an item touches is byte-identical to DA's v0.18.1 baseline, except `dialog.tsx` (a type added), `toast.tsx` (`items-center` already landed), `knip.config.ts`, `global-setup.ts` (`OIDC_ENABLED=false` for the seed script) and `auth.spec.ts` (a comment). DA's patches therefore apply as they are, except where a cell says otherwise. App frontends are on v0.20.2 (FieldnotesApp), v0.20.3 (EI, IoTSupport, DHCPApp, ZigbeeControl) and v0.20.4 (PilotApp). Apart from the cases named in the "Apps" column, every app's copy of every file listed is identical to the template's.

| ID | Ruling | Phase | Status | Where it stands now | Apps with their own version | Notes for the phase |
|---|---|---|---|---|---|---|
| FE01 | D1 | 6 | missing | `src/components/primitives/tooltip.tsx` title mode still clones with `'data-testid': testId` (undefined clobbers the child's id). Content mode already guards with `childHasTestId`. | none | DA's patch applies. Only the enabled-child clone matters. |
| FE02 | D1 | 6 | missing | `src/hooks/use-sse-task.ts` buffers only inside the per-task listener. | none | DA's mount-effect buffers once per mounted hook instance, so two instances double-buffer and replay twice. Buffer from one place (module-level listener) or dedupe. Pair with FE03. |
| FE03 | D1 | 6 | missing | `use-sse-task.ts` passes `data.value` straight to `percentage`. Backend `TaskProgressUpdate.value` is still 0.0 to 1.0 (`backend/template/app/schemas/task_schema.py:28`). | none | Multiply by 100. Leave out DA's `null` to `-1` mapping (the schema makes `value` required). |
| FE04 | D1 | 6 | missing | `tests/support/process/servers.ts` spawns without `detached`, kills with `child.kill`, and the exit hook sends SIGTERM to the leader. `scripts/testing-server.sh` ends in `exec pnpm exec vite`. | none | DA's patch applies. Use `node_modules/.bin/vite` in both branches of the script (see FE17). |
| FE05 | D1 | 6 | missing, probably not needed | The three specs (`sse-connectivity`, `task-events`, `deployment-banner`) never call `auth.createSession()`. `AuthFactory.createSession` error omits the response body. | none | DA's backend failed without a session. The template backend's `/api/auth/self` returns a local admin when OIDC is off and no test session exists (`backend/template/app/api/auth.py`), so the specs probably pass today. Not run in phase 0. Phase 6: run the SSE specs after phases 4 and 5 land. Add sessions only if they fail, and pass `{ roles: ['editor'] }`, not DA's `?? ['editor']` default (D2 denies a user with no roles). Take the body-in-error change anyway. |
| FE06 | D1 | 6 | missing | `deployment-sse.ts`: bridge wait 5 s, connect wait 20 s, `ensureConnected` waits separately, `disconnect` blocks on a missing bridge. `deployment-reset.ts` does not wait for the bridge. `test-events.ts`: default waits 5 s, no `{ cause }`. | none | Take the union: the frontend copy's helper changes plus the portal's 15 s default waits (`test-events.ts` lines 292 and 408) and `{ cause }`. The banner-spec re-wait after the reload click goes in too. |
| FE07 | D1 | 6 | missing | `scripts/generate-api.js` runs `npx openapi-typescript <spec> --output <file>`. | none (EI differs by a comment only) | One flag. Leave out DA's `shouldSkipPath`, `generateTableConfigs`. Regenerating changes `frontend/test-app-domain/src/lib/api/generated/types.ts`, which `regen.sh` copies in by hand: refresh it. |
| FE08 | D1 | 6 | missing | `src/lib/test/ui-state.ts` has no first-run branch. v0.14.2 (`a84b3dc`) fixed the same bug in `useListLoadingInstrumentation` only. | none | Take the portal's `mountedRef` version. |
| FE09 | D1 | 6 | missing | `fixtures-infrastructure.ts.jinja` console allowlist has `Form submission error` but not `Toast exception`. | none | One condition. Existing `expectConsoleError` already registers a `Toast exception` prefix per test (`tests/support/helpers.ts:140`), so it becomes redundant. A global allow also stops an unexpected error toast from failing a test. |
| FE10 | D1 | 6 | landed | `frontend/template/.dockerignore` (v0.20.0, `032f366`) excludes `.git .pnpm-store node_modules test-results playwright-report dist .claude logs`. | EI, IoTSupport, DHCPApp, ZigbeeControl edit the comment or the list | Nothing to do. DA's `.venv`/`__pycache__` lines do not apply to a frontend-only context. |
| FE11 | D1 | 6 | missing | (a) `eslint.config.js` has no `src/routes/**` rule. (b) `package.json.jinja` lacks `@typescript-eslint/parser` and `/utils`. (c) `.gitignore` has `.env`, `.env.local`. (d) No `build-fast`. | none | (a), (d) and the `.env*` / `!.env.example` form of (c): take. (b): DA needed it under pnpm 11; pnpm 9's default `*eslint*` hoist covers it, so skip unless the template moves to pnpm 11. `coverage` ignore lines belong to FE22, which is not taken. `"packageManager": "pnpm@9.0.0"` is in the template and all six apps. DA dropped it; it is stale. Phase 6 drops it or sets the real version. |
| FE12 | D1 | 6 | missing | `vite.config.ts.jinja`: no `xfwd`, no `configureSseProxy`, no `server.strictPort` (only the CLI flag in `testing-server.sh`). | IoTSupport has `xfwd: true` on its `/api` proxies (`vite.config.ts`). | Take the portal's `configureSseProxy` (deletes `transfer-encoding` before `writeHead`), under `use_sse`, in both `server.proxy` and `preview.proxy`. IoTSupport's `xfwd` matches, so no conflict. |
| FE13 | D1 | 6 | missing | `snippets/proxy.conf` line 3: `proxy_set_header Host $host;` | none | One line to `$http_host`. |
| FE14 | D1 | 6 | missing | `playwright.config.ts` line 31: `video: process.env.PLAYWRIGHT_RETAIN_VIDEO ? 'on' : 'retain-on-failure'`. | none (all six carry the template line) | Ruling: off by default, the env var gives `retain-on-failure`. `PLAYWRIGHT_RETAIN_VIDEO` exists already and means "always on". Reuse the name with the new meaning (no app sets it) or pick a new one. |
| FE15 | D3 | 7 | missing | `src/workers/sse-worker.ts` and `sse-context-provider.tsx` set `connected` on `EventSource.onopen`. A late tab gets `connected` when `readyState === OPEN`. | none | DA's patch applies to both files. The stable SSEGateway already pinned (`ssegateway#stable`) sends `ready` (D3). Keep the `readyReceived` reset on close and on every `createEventSource`. Specs that wait for `connected` then wait for `ready`. |
| FE16 | D3 | 7 | missing | No `rejected` handling in worker or provider; no `reconnect` command; `reconnect()` does nothing when the worker ref exists; no spec. | PilotApp (`8b8cf41`, ported from DA): worker `rejected` listener, `rejectedTerminal`, `reconnect` command; provider probes `/api/auth/self`, `showErrorRef` toast, `reconnect()` fix, `__sseForceWorkerReconnect` bridge, `playwright-binding.d.ts`. No `ready`. Its spec `sse-connect-refusal.spec.ts` covers the dev path only. | Use PilotApp's copy as the base (cleaner than DA's; same behaviour). Its commit message says to take the template's side on the next `copier update`. The new spec needs the backend hook `POST /api/testing/sse/force-callback-error` (phase 5, BE-T11; absent from the backend template) and preview mode (FE17). The root suite runner builds with plain `pnpm build` and runs the dev server, so nothing sets `PLAYWRIGHT_PREVIEW_MODE` in CI. Phase 7 or 8 must add a test-mode build step to `root/template/tools/suite_runner/local.py.jinja`, or the spec always skips. |
| FE17 | D1 | 6 | missing | No `--preview` in `scripts/testing-server.sh`; no `PLAYWRIGHT_PREVIEW_MODE` in `servers.ts`. The inversion still exists in `vite.config.ts.jinja`: `define` forces `VITE_TEST_MODE` to `'false'` when `NODE_ENV=production`; `build.rollupOptions.external` lists `./src/lib/test/*` only when production and test mode are both on. | none (IoTSupport's `vite.config.ts` has the same `define`) | Take DA's `define` (`process.env.VITE_TEST_MODE \|\| 'false'`) and `external` unless `VITE_TEST_MODE === 'true'`. The key is `rollupOptions` on Vite 7 and `rolldownOptions` on Vite 8 (DA's name); use the one that matches the pin. `pnpm build` must not run with `VITE_TEST_MODE=true` set in its environment. The image build now leaks the bridges if it does, and `verify:build` only warns (exit 0). The existing SharedWorker specs in `sse-connectivity.spec.ts` (lines 275 and 324) run through the direct path under the dev server, so they pass without testing the worker. Gate them like the FE16 spec. Document the two-step run in `frontend/CLAUDE.md` (DA's `docs/testing.md` is app-created). |
| FE18 | D1 | 6 | missing | `servers.ts` timeouts 30 s / 90 s / 30 s; no `lastStatus`/`lastBody` in the timeout error; startup time logged only with log streaming on; worker fixture `timeout: 120_000` (`fixtures-infrastructure.ts.jinja:561`). | none | Take 120 s for each service, 300 s for the fixture, the body-in-error and the remaining-interval sleep. Keep 200 ms polling and reject 503 (DA's 503 acceptance is DA-specific, and D5 keeps readyz 503 only for critical checks). |
| FE19 | S6 | 7 | missing | No `diagnostics` in `toast.tsx` or `toast-context-provider.tsx`; no `src/lib/utils/error-diagnostics.ts`. Only the `items-center` alignment has landed. | none | Take the frontend copy plus `error-diagnostics.ts` (leave out the vitest file). The gate is DA's `useGetUiSetup`, which needs the S6 endpoint from phase 3. The hook is in no generated client: `frontend/test-app-domain/src/lib/api/generated/{hooks,types}.ts` and `openapi-cache/openapi.json` are checked in and copied by `regen.sh`, so refresh them from the phase 3 backend. Show the button on "internals fact true", not on DA's `stage !== PRD` test. |
| FE20 | D1 | 6 | landed (differently) | v0.20.4 (`f160008`): the placeholder `src/routes/index.tsx.jinja` draws a header with `UserDropdown` when `use_oidc and not use_app_shell`, which satisfies the unchanged `auth.spec.ts`. `.search` to `.searchStr` landed in `ca85567`. | ZigbeeControl and PilotApp render `UserDropdown`; FieldnotesApp reimplements the same test ids in `triage/user-menu.tsx` | Only a fresh app gets the placeholder route (app-owned, `_skip_if_exists`). The three existing no-shell apps already satisfy the spec. No change. `frontend/regen.sh` generates only `use_app_shell=true`, so the no-shell variant is never built or tested by the harness. Raise with the operator whether to add a second generated variant. |
| FE21 | D6 | 7 | partial | Landed: `@import "./styles/app-theme.css"` in `index.css` (app-owned hook for theme tokens); a `.text-destructive` dark override. Missing: `button { cursor: pointer }`, `td { vertical-align }` (DA frontend only, optional), and the dark tokens `--primary`/`--ring`/`--link-hover` (220 70% 65%) and `--destructive` (0 72% 51%). | EI, ZigbeeControl and FieldnotesApp set their own `--destructive` in `app-theme.css`; no app sets `cursor` | Dark-token edits reach only IoTSupport, DHCPApp and PilotApp. `src/styles/button.ts` is app-owned and already has `cursor-pointer`. The hook for DA's `@source` and `@plugin` lines is `app-theme.css`; whether Tailwind 4 honours `@plugin`/`@source` from an imported file is not checked: test it in phase 7. Leave out `--stage-indicator` and the slide-down keyframes unless FE32 needs the colour. |
| FE23 | S1 | 6 | missing | See Details. | none (PilotApp's frontend is the template's SQLite code; its design is `pilotapp_database_testing_design.md` §4.6) | See Details. |
| FE27 | D3 | 7 | missing | `src/components/sse/sse-gate.tsx` renders an empty `sse.gate.loading` div until `isConnected`. | none (all apps carry the blocking gate; no test or app code uses `sse.gate.loading`) | Take the portal's pass-through. Only `useSSETask` buffers events before subscribing; `useVersionSSE`/the deployment provider just register listeners, so a late `version` event is still delivered. `DeploymentProvider` registers `__deploymentSseControls` below the gate, so the bridge now appears earlier (helps FE06). |
| FE28 | D6 | 7 | missing | `dialog.tsx` has no `preventOutsideClose`. | none | Take the portal's version (honours `contentProps.onInteractOutside` when false, adds `data-testid="dialog-overlay"`). Behaviour change for every existing dialog. Say so in the changelog. |
| FE29 | D6 | 7 | missing | `button.tsx` swaps the icon for a spinner while loading; `buttonBaseClasses` has no `whitespace-nowrap`. | none | Take the frontend copy (portal's wraps `asChild` children and breaks `Slot`). `src/styles/button.ts` is app-owned, so `whitespace-nowrap` reaches only new apps; for existing apps mention it in the changelog. |
| FE32 | D9b | 7 | missing | No stage indicator in `top-bar.tsx`; no `stage-indicator.tsx`. | none | `use_app_shell` only (top bar). Take `stage-indicator.tsx` without the divider and docs link, hidden on `prd`, reading the stage from the `ui-setup` response (shares the client work with FE19). The `--stage-indicator` token is in FE21's file. No dev-health indicator, no `/health` proxy (not taken). |

#### Details (FE)

- **Merged items.** No FE item carries a "Merged in" or "Merged into" note. The one cross-reference is RT10, which is merged into BE-C27 and FE31. D9a leaves FE31 in DA; RT10's "paged lists order stably" rule goes to the S5 conventions guide. Nothing taken is lost.
- **Not taken but related, found while checking.** FE22 (coverage), FE24 (vitest), FE26, FE30, FE31 stay in DA per D9. DA's `vite.config.ts` also holds FE22's istanbul plugin and FE34's `fs.allow`: take neither when porting FE12.
- **FE23, today.**
  - `tests/support/global-setup.ts` (identical in all six apps): looks for `<backend>/scripts/initialize-sqlite-database.sh`. If it is absent (`use_database=false`: DHCPApp, ZigbeeControl and FieldnotesApp) it logs and skips. Otherwise it makes `mkdtemp('pw-seed-')`, runs the script with `--db <tmp>/seed.sqlite --load-test-data` and `OIDC_ENABLED=false`, and sets `PLAYWRIGHT_SEEDED_SQLITE_DB`. The script runs `poetry run cli load-test-data --yes-i-am-sure` on `sqlite:////<path>`. Nothing deletes the seed directory; there is no global teardown.
  - `fixtures-infrastructure.ts.jinja` (worker-scoped `_serviceManager`, line 356 on): copies the seed file into a per-worker `mkdtemp` directory and passes it as `sqliteDbPath`; removes it on dispose. `ServiceManager.sqliteDbPath` is set but read nowhere.
  - `process/servers.ts`: `startBackend` adds `--sqlite-db <path>` when given. It always sets `OIDC_ENABLED=false`.
  - `backend/template/scripts/testing-server.sh.jinja` (phase 2 changes it): `--sqlite-db PATH` exports `DATABASE_URL=sqlite:////PATH`; sets `FLASK_ENV=testing`; `exec poetry run python -m flask run`. No `--database-url`, no `.env.test` loading (BE-C09, phase 2 step 8).
  - Pool env names the backends read already exist: `DB_POOL_SIZE`, `DB_POOL_MAX_OVERFLOW` (`backend/template/app/config.py.jinja`).
- **FE23, what phase 6 builds** (PilotApp design §4.6, DA files `pg-admin.ts`, `global-setup.ts`, `global-teardown.ts`):
  - New template-owned `tests/support/helpers/pg-admin.ts` and `tests/support/global-teardown.ts`; `playwright.config.ts` gains `globalTeardown`; `package.json.jinja` gains `pg` and `@types/pg` (^8).
  - Take from the design, not DA: admin URL from `TEST_DATABASE_ADMIN_URL` (default `postgresql+psycopg://postgres:postgres@localhost:5432/postgres`). `pg` needs the `postgresql://` form, so strip `+psycopg` for the admin client and keep `+psycopg` for the backend's `DATABASE_URL`. Seed created `TEMPLATE template0 ENCODING 'UTF8' LOCALE_PROVIDER icu ICU_LOCALE 'und' LC_COLLATE 'C' LC_CTYPE 'C'`. A per-run prefix (a random 8-hex suffix), published in an env var for the workers. The start sweep drops without `FORCE` and skips databases in use. The end of the run drops its own with `FORCE`. Workers clone `<prefix>_w<parallelIndex>`; drop-if-exists first, since Playwright reuses worker indices after a restart. Leave out DA's `app_ci`/`app_ci_ai` collations and the fixed `test_da_*` prefix (derive from `project_name`).
  - Seed: `uv run cli load-test-data --yes-i-am-sure` in `backend/` with `DATABASE_URL` at the seed and `OIDC_ENABLED=false`. Poetry until phase 1 lands; the phase 1 step for the frontend template covers this call.
  - Backends: pass `--database-url`, plus `DB_POOL_SIZE=2` and `DB_POOL_MAX_OVERFLOW=3` in the env.
  - Open point: the frontend template has no `use_database` question. The skip-when-no-database check keyed on `initialize-sqlite-database.sh`, which phase 2 step 7 deletes. Phase 6 needs another marker (a `use_database` answer in `frontend/copier.yml`, or a backend file that only exists with a database, such as `scripts/init-dev-database.py`). Phase 6 keys on `backend/alembic.ini`, which the backend template renders only with `use_database`, so no new question is needed (plan correction 11).
  - After phase 6, the leftover SQLite plumbing in the frontend goes: `sqliteDbPath`, `PLAYWRIGHT_SEEDED_SQLITE_DB`, the `--sqlite-db` argument.
  - EI, IoTSupport and PilotApp use `initialize-sqlite-database.sh` through this path today; moving their backends is for phases 11 to 16.
- **Pins now** (`frontend/template/package.json.jinja`; the six apps carry the same specifiers): `@playwright/test` `1.60.0` (exact, on purpose, MAT-5/MAT-8: v0.20.3 `b061912`; keep it in every bump), `vite` `^7.1.2`, `typescript` `~5.9.0`, `eslint` and `@eslint/js` `^9.33.0`, `typescript-eslint` `^8.39.1`, `eslint-plugin-react-hooks` `^7.0.1`, `eslint-plugin-react-refresh` `^0.4.20`, `knip` `^5.85.0`, `@vitejs/plugin-react` `^5.0.0`, `@types/node` `^24.10.0`, `globals` `^16.3.0`, `openapi-typescript` `^7.0.0`, `"packageManager": "pnpm@9.0.0"`. DA ran vite 8, TypeScript 6, ESLint 10, knip 6 and plugin-react 6. None of the FE items need those; FE17's `rolldownOptions` key is the only place the Vite version shows. EI also has `vitest ^4.0.18` (its own).
- **`knip-template-ignore.json` changes.** The list names helpers one by one and globs `tests/support/process/**`, `src/components/layout/**`, `tests/infrastructure/**`.
  - Add (phase 6, FE23): `tests/support/helpers/pg-admin.ts`, `tests/support/global-teardown.ts`.
  - Add (phase 7, FE19): `src/lib/utils/error-diagnostics.ts`.
  - No entry needed: `src/components/layout/stage-indicator.tsx` (FE32, covered by `layout/**`), `tests/infrastructure/sse/sse-auth-recovery.spec.ts` (FE16, covered by `tests/infrastructure/**`).
  - Nothing is removed from the list. Deletions: none in `frontend/template` (the SQLite code is rewritten in place). `pg` is imported from files knip traces (`fixtures-infrastructure.ts`), so it needs no `ignoreDependencies` entry.
- **Harness note.** `frontend` in `.kubecoder/project.yaml` has no `test:` entry, and a full frontend Playwright run took the sidecar to its 5 GiB limit once. Per-worker PostgreSQL databases and a preview build add memory; phase 6's "Playwright suite green" gate is run by hand per the comment in `.kubecoder/project.yaml`.

### Root items and conventions

Phase 9 sources are all in DA and none of the templates' docs state these conventions (the templates have no `docs/` folder; `backend/CLAUDE.md` and `frontend/CLAUDE.md` do not mention them). The apps state some: see the Notes column.

| ID | Ruling | Phase | Status | Where it stands now | Sources in DA | Notes for the phase |
|---|---|---|---|---|---|---|
| RT07 | D9: take, discover components | 8 | missing | No template, no app has it. `grep` over all six apps and the three templates finds no `check_updates`, `poetry show --outdated` or `pnpm outdated` script. | `scripts/check_updates.py` (232 lines, stdlib). Lists hard-coded: Python `backend` and `ROOT`; npm `frontend`, `portal`, `packages/shared-ui`. Python via `poetry show --outdated --no-ansi` (text parse), npm via `pnpm outdated --format json`. Classifies major/minor/patch from installed vs latest; `--json` output; per-project failure becomes a warning. | Discover components: any directory with `pyproject.toml` or `package.json` (skip `node_modules`, `.venv`, `test-app`). Replace `poetry show --outdated` with `uv pip list --outdated` or `uv tree --outdated` for uv apps (FieldnotesApp, PilotApp; phase 1 makes all apps uv). Run it inside the `modern-app` container. Add a `lint`-free entry; nothing depends on it. |
| RT08 | S5 | 9 | missing | Not stated in any template or app. No `status-labels.ts` or `never` guard in the frontend template. | `docs/conventions.md` "Status enum exhaustiveness" (L197-209, 13 lines). Example code in the text. | Strip: `ContentAssetResponseSchema`, "frontend and portal", entity examples (content asset, session, workspace access). Keep: the `Literal[...]` backend rule, `never` default, one central mapper file. The path `src/lib/utils/status-labels.ts` is a convention, not template code; say so. |
| RT09 | S5 | 9 | missing | The template has the global `onError` toast path (`core-providers.tsx`, `toast-instrumentation.ts`), but no text states "no success toast for visible outcomes". ZigbeeControl's frontend `CLAUDE.md` has one line against status toasts. | `docs/conventions.md` "Toast discipline" (L211-215, 5 lines). | Strip: "the portal skips 409" exception. The inventory asked to verify that the template's `query-client.ts` handles mutation errors globally; this is a code check for phase 9 (not done in phase 0). |
| RT11 | S5 | 9 | missing | Not stated anywhere. | `docs/conventions.md` "API paths" (L125-128, UUID rule; second bullet, the `/api/portal/` prefix, is DA-specific) and "Long-running operations" (L140-148, 9 lines). | Keep (a) UUID paths and (b) the 2 s p95 rule with 202 + `task_id` + SSE progress, `useSSETask`. Strip the whole Celery/RabbitMQ/`WorkItem`/advisory lock/queue tier text (bullets 2-7), and the DA examples. The template's hook is `useSSETask` (`src/hooks/use-sse-task.ts`). |
| RT13 | S5 | 9 | partial | The template enforces part of it in code: the `no-route-mocks` ESLint rule (`frontend/template/scripts/eslint-rules/testing/`), `pytest.exit` pre-flight in `tests/conftest_infrastructure.py.jinja`, `/api/testing/` endpoints. No text states the rules. The preview-mode gotcha has no home yet (`PLAYWRIGHT_PREVIEW_MODE` is not in the templates; it arrives with FE17, phase 7). | `docs/conventions.md` "Testing" (L99-106), "Testability" (L176-181), "Worker in Playwright tests" (L162-167, Celery-specific, skip), "Resource-contention test flakes" (L183-187); `frontend/docs/testing.md` (46 lines); `frontend/docs/code-style.md` (26 lines). The preview-mode gotcha (specs `test.skip` without `PLAYWRIGHT_PREVIEW_MODE`) is `frontend/docs/testing.md` L22-30 plus one line in `frontend/CLAUDE.md` L40. | Strip: Keycloak `test-da-` prefix, RabbitMQ, portal, worker, "remote test runner's shared pod". Keep: real dependencies, no `page.route`/mock SSE, wait on instrumentation events, testing endpoints as blocking prerequisite, no UI feature without Playwright coverage, retry-accepted flakes vs consistent failures. Write the preview-mode paragraph only after phase 7 lands FE17 and read its final env names. |
| RT14 | S5 | 9 | partial | `perf_counter` is used in template code and in `ElectronicsInventory/backend/CLAUDE.md` (L218-230, L317) with a never-`time.time()` rule; no other app or template states fail-fast or the `window.open` download rule (grep: none). The template uses `time.time()` only for absolute timestamps (auth `exp`, SSE heartbeat, one test). | `backend/docs/code-style.md` (45 lines), `frontend/docs/code-style.md` (26 lines), `portal/docs/code-style.md` (29 lines; same as frontend), `backend/docs/testing.md` (41 lines). | Take three rules only (ruling): `perf_counter`, fail fast (custom exceptions, no silent try/except), `window.open(url)` for backend-served downloads (explains the cookie BFF auth reason; reserve blob for client-generated files). Skip the file-creation order and the guidepost comments unless the operator wants them. EI's CLAUDE.md is a ready text source for the `perf_counter` rule. |
| BE-T17 | S5 | 9 | partial | `pytest.exit` pre-flight exists in `conftest_infrastructure.py.jinja`; no doc states the test conventions or SSE targeting. SSE targeting is also BE-T10 in the backend phases (it has code: `Target.*`, `BROADCAST_TARGET` reserved). | `backend/docs/testing.md` (41 lines: layout, `Test<Service>`, required coverage), `backend/docs/sse-event-targeting.md` (21 lines, six rules), `docs/conventions.md` testing and flake sections. DA CLAUDE.md "Never dismiss test failures as flaky". | Strip: `test-da-` Keycloak prefix, portal user resolution (rule 5) and rule 3-4 (dual-path workspace events), `Target.workspace_events()`. Keep: explicit targets, no broadcast for domain events, no fallback chains. Take `Target.*` names from the backend template as it ends up after phase 5, not from DA. The "pre-flight with `pytest.exit` instead of `skipif`" rule comes from commit `6b5f9567`. |
| D9a rule | "paged lists order stably" | 9 | missing | `apply_sorting()` (BE-C27 backend half) is not in the template. EI pages with `limit/offset` and `order_by(Part.created_at.desc())` only: no id tiebreaker (`part_service.py:132`, `inventory_service.py:358`). | `docs/conventions.md` "Pagination & sorting" (L130-138); the last bullet is the stable-order rule (`id` as secondary sort key). Backend helper: BE-C27 in the inventory. | One sentence plus the reason (rows repeat or vanish between pages when the sort key has duplicates). Strip the rest of the section (frontend `DataTable`, `table-configs.ts`, 50-item rule is a DA choice). `apply_sorting()` lands in phase 5; the rule stands either way. Flag to the EI phase: its paged lists lack the tiebreaker. |

Left open: MAT-12's placement (operator question 5). DA's `test_process.py` stays out unless the operator wants a root test gate. Phase 9 confirms the template's `query-client.ts` error path before writing RT09.

### CI, images and architecture items

| ID | Ruling | Phase | Status (missing/partial/landed) | Where it stands now | Notes for the phase |
|---|---|---|---|---|---|
| RT02 | Diff at dedup: validation Jenkinsfile. Template takes the estate shape; PostgreSQL via `services:` (S1), `STAGE=tst` (D9b) | 8 (step 1, step 6) | partial | All six apps run `modernApp.test` in a hand-moved declarative file; the template `root/template/Jenkinsfile.jinja` is still the scripted v0.1.6 file that calls library functions that no longer exist. PilotApp's file is the shape. | Replace the file as in CI pipeline §3. Take only `--build-cache`; leave everything else of DA's file (CI pipeline §4). Add `STAGE=tst` and PostgreSQL in `services:`. |
| RT05 | S3: pnpm build cache for CI and image builds | 8 (step 1, step 2) | missing | Service live at `http://build-cache.jenkins-prd.svc.cluster.local` (empty now, 14-day TTL). The template has no `build-cache-*.sh`, no suite-runner switch, no Dockerfile restore. Canonical scripts: `HomelabAppsDeploy/jenkins/chart/scripts/`. | Scripts into root `scripts/`; enable via env in `modernApp.test`'s `env:` (library cannot pass flags); inline the restore in the frontend `Dockerfile` (context is `frontend/`); fixed or `{{ project_name }}` prefix. |
| RT06 | D8: every app is an architecture producer | 8 (step 4) | partial | Landed in FieldnotesApp and PilotApp (one root model, one-stage file) and in the other four (two models, two stages); AaC jobs exist for all six. Missing in the template. | Take PilotApp's `Jenkinsfile.architecture` with `architectureProducer`, not DA's script; no `scripts/arch-validate.py` (`aac-tools` has it); add `aac-tools` to `.kubecoder/config.yaml.jinja` and an `arch-validate` lint step; `_skip_if_exists` for the file; `CLAUDE.md` nudge names `/seed-architecture` and the central update. Plan text (take from DA) should be corrected. Per new app, operator creates `AaC/<Repo>` and the `pipeline-producers.yaml` entry. |
| BE-C17 | S3: shared `modern-app-backend*` base images | 8 (step 2) | missing | Images exist (`latest`, built 2026-06-17; only DA uses them). Backend template and all six apps still use `python:3.13-slim` with inline `apt-get`. `modern-app-backend-build` has Poetry and no uv. | Add uv to `modern-app-backend-build` in a DockerImages clone (commit, do not push); change the backend template `Dockerfile.jinja` to the two images with `uv sync --locked --no-dev --no-install-project`; the frontend `Dockerfile` to `modern-app-frontend-build`. Phase 17 must push DockerImages and let it build before the apps. |

## 2. The root diff (RT01, RT03, RT04)

Method: file-by-file `diff` of DA against `root/template/` (jinja stripped). The root template was extracted from DA's tooling, so most of it is identical or a superset. The table lists only differences. Out of scope here: the Jenkinsfile (RT02), build cache (RT05), architecture producer (RT06).

### RT01 — suite runner, display and process helpers

| DA has | DA file | Root template counterpart | Take/leave | Why |
|---|---|---|---|---|
| `display.py`, unchanged | `tools/suite_runner/display.py` | `tools/suite_runner/display.py` | n/a | Byte-identical apart from import order. Nothing to port. |
| `process.py` with the loud `=== TIMEOUT ... ===` kill line, psutil peak-RSS tracking | `tools/suite_runner/process.py` | `tools/suite_runner/process.py` | n/a | The template already has both. The template is ahead: `run()` takes an `env` argument. |
| Unit test for the timeout kill line (`test_run_tracked_timeout_emits_kill_line` and a streamed variant, 64 lines) | `tools/suite_runner/tests/test_process.py` | none (no `tests/` in the root template; root `pyproject.toml.jinja` has no pytest; root `.kubecoder` project has no `test:`) | leave | Needs a pytest dev dependency and a root test gate for one 64-line file. `process.py` is identical, so the behaviour is not at risk. Operator can flip this. |
| `poetry lock --no-update` retry when `poetry install` fails with a lock error | `tools/suite_runner/local.py` (backend install step) | `local.py.jinja` (single `poetry install --no-interaction`, no retry) | leave | Poetry-only, and phase 1 moves the root to uv. Silently re-locking in CI hides a stale lockfile. Under uv the equivalent is `uv sync --locked`, which should fail loudly. |
| Readiness helpers `_wait_for_tcp`, `_wait_for_http` (wall-clock-aware polling, optional body check, 200 only so 503 keeps waiting) and `_wait_for_services` with a hard-coded list (postgres, rabbitmq, document-conversion, opensearch) | `local.py` | `local.py.jinja` calls the app hook `backend/scripts/wait-for-services.py` if it exists (the script is not in the backend template) | take (helpers only) | Phase 8 adds PostgreSQL to the validation Job "with a wait for it". Ship a small generic `wait_for_tcp` / `wait_for_http` in `tools/suite_runner/` or in the hook. Leave the service list. |
| `--build-cache` flag, `_build_cache_get/_put`, pnpm-store restore | `local.py`, `scripts/build-cache-{get,put}.sh` | none | n/a | RT05 (§6.2). It keys on the root `pnpm-lock.yaml`, which assumes RT17's workspace; the template's frontend is standalone (`frontend/pnpm-lock.yaml`). |
| `--build-full` flag (`pnpm build` vs `build-fast`) | `local.py` | none (template always runs `pnpm build`) | leave | DA's frontend has a `build-fast` script that skips `pnpm check`; the template's has no such script. |
| `--portal-args`, `portal` suite, `ALL_SUITES = [backend, frontend, portal]`, per-frontend loop | `local.py`, `__init__.py` | `ALL_SUITES = [backend, frontend]` | leave | Multi-frontend workspace (RT17). |
| Vitest step per frontend after the build (`pnpm exec vitest run`, `--bail` from `--max-failures`, junit output) | `local.py` | none | leave | The frontend template has no Vitest. Revisit only if an app adds Vitest (listed under Optional in the rulings). |
| Root-level `pnpm install` for the workspace; `SKIP_UNSHARE` switch (`pnpm exec playwright` vs `pnpm playwright`) | `local.py` | frontend installed in `frontend/`; always `pnpm playwright test` | leave | RT17 and `frontend/package.json` wraps `playwright` in `unshare --user --pid --fork`, which the remote pod cannot do, hence `SKIP_UNSHARE`. |
| `VITE_TEST_MODE=true` and `PLAYWRIGHT_PREVIEW_MODE=true` exported for the whole frontend phase | `local.py` | not set (template sets `PLAYWRIGHT_BACKEND_LOG_STREAM=true`) | take, with FE17 | Only if FE17's opt-in preview mode needs the runner to set them. Phase 7 decides; phase 8 then edits `local.py.jinja`. |
| Run `wait_for_services` before the backend install; remote runner `run-suite-remote` | `local.py`, `remote.py` (534 lines) | none | leave (remote) | RT21: remote runner is product-grade, ruled leave. |
| Timeouts: pytest 600 s, Playwright 1200 s | `local.py` | pytest 1800 s, Playwright 3600 s, installs 600-900 s | n/a | Template is looser. Keep the template's. |

Template-only, kept: `HAS_PYTHON313` venv pin, Playwright Chromium install step (the CI image carries no browser), the `wait-for-services.py` hook, `APP_NAME` from `repo_name`. Phase 1 replaces the Python pin and the Poetry commands in `local.py.jinja` with uv's (FieldnotesApp and PilotApp already run uv here; §3 lists their edits).

### RT03 — dev orchestration

| DA has | DA file | Root template counterpart | Take/leave | Why |
|---|---|---|---|---|
| `dev.py`: honcho in a PTY plus `unshare --user --pid --fork`, ANSI-stripped `logs/<svc>.log`, signals ignored | `scripts/dev.py` (92 lines) | `scripts/dev.py.jinja` (184 lines) | n/a | The template is a strict superset: `dev.py stop`, `logs/dev.pid`, SIGINT/SIGTERM forwarded as Ctrl-C through the PTY, a held stop until all services have started (honcho KeyError), positional service subset, `cexec modern-app` wrapper. DA has nothing the template lacks. |
| Procfile with `worker`, `beat`, `portal`, `canon-site`, `uat-site` services | `Procfile.dev` | `Procfile.dev.jinja` (`backend`, `frontend`, `gateway`) | leave | Celery (BE-C19), portal (RT17), canon/UAT sites are DA-specific. |
| Backend line `PORT=3401 scripts/dev-watch.sh poetry run dev` (watchmedo auto-restart on `*.py;*.env*;*/app/assets/*`, SIGTERM, 3 s throttle) | `Procfile.dev`, `backend/scripts/dev-watch.sh`, `backend/pyproject.toml` (`watchdog[watchmedo]`) | `Procfile.dev.jinja` backend line is `env -u VIRTUAL_ENV -u POETRY_ACTIVE PORT=... poetry run dev`; header comment says "Werkzeug auto-reload"; `backend/template/scripts/dev-server.sh` is a manual restart loop | take (BE-C29) | Ruled take. Phase 8 changes the Procfile line, the stale "Werkzeug auto-reload" comment, and wraps the line in the watcher. The `env -u VIRTUAL_ENV -u POETRY_ACTIVE` prefix is a Poetry workaround; check what uv needs (phase 1). Where `dev-watch.sh` lives (backend template, `scripts/`) and the `watchdog` dependency belong to the backend side of BE-C29. |
| `dev-sse-gateway.sh` with `RABBITMQ_URL` and `RABBITMQ_ENV_PREFIX=local-dev` | `scripts/dev-sse-gateway.sh` | `scripts/dev-sse-gateway.sh.jinja` | leave | RabbitMQ SSE transport (BE-T20) is Optional. The template version is better (`set -euo pipefail`, template variables for ports). |
| `regenerate-openapi.py`: free port, poll `/api/docs/openapi.json` rather than `/health/readyz`, stop backend cleanly | `scripts/regenerate-openapi.py` | `scripts/regenerate-openapi.py.jinja` | n/a | The template has the same flow, same polling, same readyz rationale, plus an `OPENAPI_PATH` constant and a "Customize" section. Nothing missing. |
| `run_prepare()` (`poetry run cli prepare`) before starting the backend; `--portal` target | `scripts/regenerate-openapi.py` | none (comment: DB migrated by `kc project setup`) | leave | DA's `cli prepare` and portal are DA-specific. |
| `portpicker` dependency in the root | `pyproject.toml` | none | leave | Not imported anywhere in DA's `scripts/` or `tools/` (the script uses `socket`); a dead dependency. |
| Other dev scripts: `backend/scripts/dev-{minio,opensearch,document-conversion}.sh` (docker sidecars), `scripts/cleanup-rabbitmq.sh`, `scripts/sync-env.sh` (diff `.env*` across sibling checkouts), `scripts/docker-{build,run,stop}.sh`, `scripts/run-frontend.sh`, `scripts/serve-{canon,uat}.sh`, `scripts/setup-kube-access.sh` (remote runner), `scripts/preflight.py` + `build-all.py` + `_initd_log.py` (RT22) | `scripts/`, `backend/scripts/` | none | leave | RT21, RT22 and RT24 are DA-specific. Sidecars come from KubeCoder services in the template. |

MAT-12 (accepted: name `scripts/regenerate-openapi.py --frontend` in `pnpm generate:api`'s error and in `frontend/package.json`; a test that fails on a stale `frontend/openapi-cache/openapi.json`):

- DA had neither. `frontend/scripts/fetch-openapi.js` fails with "Failed to fetch OpenAPI spec from all URLs" and no pointer. `package.json` has `generate:api` and `generate:api:build` with no mention of the script. No test in `backend/tests` or `frontend/tests` compares the cache with the backend. DA's CLAUDE.md and `run-slice.md` mention `regenerate-openapi.py`, and the cache is refreshed by "Regenerate OpenAPI spec" commits by hand.
- Where the template stands: `frontend/template/scripts/fetch-openapi.js.jinja` and `package.json` have the same gap (the error text is at line 73 and 169). The root `CLAUDE.md.jinja` names the script; the frontend does not.
- It does not belong with RT03's port. RT03 yields nothing to take from DA. MAT-12 is new work: part 1 is a frontend-template edit (`fetch-openapi.js.jinja`, `package.json`), part 2 is a test that runs the root script in a subprocess and checks `git status` (or builds the app in a subprocess), so it needs the root script and a home (backend `tests/` or a frontend Playwright-free check). Because it touches the frontend template and the root, assign it to phase 8 (root dev stack) with the frontend edit in phase 7, or to a separate card. The operator decides; the card itself says "the route from here is the operator's".

### RT04 — root `pyproject.toml`, `.kubecoder`, `.vscode`, workspace file, `CLAUDE.md`

| DA has | DA file | Root template counterpart | Take/leave | Why |
|---|---|---|---|---|
| Scripts `code-health`, `run-suite-remote`; deps `pathspec`, `jsonschema`, `jsonpatch`, `portpicker`; dev deps `canon` (path `../CanonApp`), `pytest` | `pyproject.toml` | `pyproject.toml.jinja` (`run-suite` only; deps `honcho`, `psutil`; dev dep `ruff` pinned) | leave | Code-health grader (RT16), remote runner (RT21), canon tooling: DA-specific. |
| No Ruff pin or config | `pyproject.toml` | `[tool.ruff]` rule set pinned to the backend's, `ruff check scripts tools` as the root lint | n/a | Template ahead. |
| Dependency checker needs no entry (run as a script) | `scripts/check_updates.py` | none | take (RT07) | See the second table. |
| `.kubecoder/config.yaml` with `profile: claude-dev`, `ref: develop`, 5 extra repos, services postgres/opensearch/rabbitmq/minio, `OPENAI_API_KEY` secret, port 5000, preamble facts. No `project.yaml`. | `.kubecoder/config.yaml` | `.kubecoder/config.yaml.jinja` + `project.yaml.jinja` | leave | Entirely DA services and repos. The template already has `project.yaml` with setup/build/test/lint verbs; nothing to add. |
| `.vscode/settings.json` hiding `backend`, `frontend`, `portal`, caches, `.site-stage`; `search.exclude` for `*.meta.json`; `python.analysis.include` | `.vscode/settings.json` | `.vscode/settings.json` (formatOnSave off, `__pycache__`) | leave | The template's workspace file shows `backend/` and `frontend/` through the root folder; hiding them would conflict. Hiding `node_modules` is the only generic idea and the template has no complaint about it. |
| `.vscode/tasks.json` with "Dev Services", "Claude" (`claudebox`) and more tasks (126 lines) | `.vscode/tasks.json` | tasks live in `{{ repo_name }}.code-workspace.jinja` ("Dev Services" only) | leave | Claude/llmbox tasks are replaced by the KubeCoder extension (the template says so in a comment). |
| Workspace folders for specs, `portal`, `CanonApp`, `CanonAppSpecs` | `DesignAssistant.code-workspace` | `{{ repo_name }}.code-workspace.jinja` (root + `../<repo>Specs`) | leave | DA-specific folders. |
| `CLAUDE.md`: orchestrator role, slice workflow, Trello issue log, canon, push notification script, "Do not reference `/work/ModernAppTemplate`", tech stack, federated architecture section | `CLAUDE.md` (108 lines) | `CLAUDE.md.jinja` (repo structure, `kc project` verbs, template ownership table, extension points) | leave, except one | All DA process text is DA-specific. Exception: the federated-architecture nudge section goes in with RT06 (phase 8 step 4, already planned). The "Do not reference ModernAppTemplate" line must not be copied. |
| `.gitignore` extras (`.site-stage`, `coverage_report.md`, `*.conversation.json`) | `.gitignore` | `.gitignore` | leave | DA-specific outputs. |

Counts: RT01 has 14 entries (1 take, 1 take-with-FE17, 5 n/a, 7 leave); RT03 has 8 (1 take, 3 n/a, 4 leave); RT04 has 9 (1 take, 1 n/a, 7 leave). Net result: the root template already contains DA's runner, dev launcher and OpenAPI script. The take list is BE-C29, the wait helpers, the FE17 env, RT07, and RT06's CLAUDE.md section.

## 3. The uv reference

### The reference edits

Sources: FieldnotesApp `55adfdc` (2026-09-26) and PilotApp `8b5c8ed` (2026-10-14), both "uv instead of Poetry, for the root and the backend". PilotApp's message says "as FieldnotesApp". Both then replaced the scripted `Jenkinsfile` wholesale with the declarative `modernApp.test` file (FieldnotesApp `03b20ca`, PilotApp `a49e4ad`). The frontend layer needed no uv edit in either app: the frontend template has no Poetry call. Playwright's global setup runs `backend/scripts/initialize-sqlite-database.sh`, and the per-worker backend starts through `backend/scripts/testing-server.sh`. Both are backend-layer files.

#### Ownership check (from the `_skip_if_exists` lists)

The apps' `CLAUDE.md`s call some of these files template-owned. The copier files say otherwise.

| File | Owner | Source |
|------|-------|--------|
| root `pyproject.toml` | app-owned | root `copier.yml` |
| root `.kubecoder/project.yaml`, `.kubecoder/config.yaml`, `CLAUDE.md`, `scripts/regenerate-openapi.py` | app-owned | root `copier.yml` |
| `backend/pyproject.toml`, `backend/Dockerfile`, `backend/vulture_whitelist.py`, `backend/tests/test_smoke.py` | app-owned | backend `copier.yml` |
| `Jenkinsfile`, `Procfile.dev`, `scripts/dev.py`, `tools/suite_runner/local.py` | template-owned | root template |
| `backend/scripts/dev-server.sh`, `testing-server.sh`, `initialize-sqlite-database.sh` | template-owned | backend template |

Consequence: `copier update` never changes an existing app's `pyproject.toml`, `Dockerfile` or `project.yaml`. Those convert by hand (phases 11-16 step 6). The template versions only matter for newly generated apps.

#### Template-owned edits, FieldnotesApp and PilotApp (identical unless noted)

Root layer:

| File | Change |
|------|--------|
| `Jenkinsfile` (scripted, first commit) | `cd /work && poetry install --no-interaction --without dev` becomes `cd /work && uv sync --locked --no-dev`. `poetry run run-suite ...` becomes `uv run --no-sync run-suite --output-mode full --junitxml-dir /work/results --retries 2`. |
| `Jenkinsfile` (declarative, later commit) | Both apps: `modernApp.test(job: '<app>-validation', install: 'uv sync --locked --no-dev', run: 'uv run --no-sync', suites: ['backend', 'frontend'], services: [], env: [:], secrets: [])`. The install and run strings are the only uv content. §4 sets the file's shape. |
| `Procfile.dev` | Header comments say uv. The backend line becomes `backend:  cd backend && env -u VIRTUAL_ENV PORT=<port> uv run dev` (was `env -u VIRTUAL_ENV -u POETRY_ACTIVE PORT=.. poetry run dev`). New comment: "honcho runs from the root project's venv and children inherit VIRTUAL_ENV; `uv run` in backend/ uses backend/.venv regardless, but warns about the mismatch. Clear it." Lower-level hint is `uv run honcho -f Procfile.dev start`. |
| `scripts/dev.py` | The `pty.spawn` argv `"poetry", "run", "honcho", "start", "-f", "Procfile.dev"` becomes `"uv", "run", "honcho", "start", "-f", "Procfile.dev"`. Docstring: "neither uv nor honcho"; "it installs the uv and pnpm dependencies". |
| `tools/suite_runner/local.py` | Docstring and comments say uv. Install block replaced (below). `["poetry", "run", "python", str(wait_script)]` becomes `["uv", "run", "python", str(wait_script)]`. `pytest_cmd = ["poetry", "run", "pytest", ...]` becomes `["uv", "run", "pytest", "-v", "--tb=short"]`. |

`local.py` install block, new text:

```python
cmds = [["uv", "sync", "--locked"] + (["--python", "python3.13"] if HAS_PYTHON313 else [])]
```

It replaces:

```python
cmds = []
if HAS_PYTHON313:
    cmds.append(["poetry", "env", "use", "python3.13"])
cmds.append(["poetry", "install", "--no-interaction"])
```

Backend layer:

| File | Change |
|------|--------|
| `backend/scripts/dev-server.sh` | `poetry run dev` becomes `uv run dev` |
| `backend/scripts/testing-server.sh` | `exec poetry run python -m flask run --host="$HOST" --port="$PORT"` becomes `exec uv run python -m flask run ...` |
| `backend/scripts/initialize-sqlite-database.sh` | PilotApp only (FieldnotesApp has no database): `poetry run cli load-test-data --yes-i-am-sure` becomes `uv run cli load-test-data --yes-i-am-sure`. `poetry run cli upgrade-db` becomes `uv run cli upgrade-db`. |

Frontend layer: none.

#### App-owned files both apps edited in the same commit (the template's equivalents are in "Poetry uses to change")

| File | Change |
|------|--------|
| `scripts/regenerate-openapi.py` | `["poetry", "run", "dev"]` becomes `["uv", "run", "dev"]`, and the docstring line |
| `backend/vulture_whitelist.py` | comment `# Run vulture with: uv run vulture app/ vulture_whitelist.py --min-confidence 80` |
| `backend/tests/test_smoke.py` | PilotApp only (FieldnotesApp has none): docstring says `uv run check` |
| `CLAUDE.md` | "(Python, uv)"; ad-hoc `uv`/`pnpm` commands need `cexec modern-app` |

#### Where the two apps differ, and which the template takes

| Item | FieldnotesApp | PilotApp | Template takes |
|------|---------------|----------|----------------|
| `initialize-sqlite-database.sh` | not edited (no database) | `uv run cli ...` | PilotApp. The template has the script under `use_database`. |
| `Procfile.dev`, `dev.py`, `local.py`, dev/testing scripts | same edits | same edits | Either. The text is identical. Use PilotApp's `dev.py` docstring wording, which also covers `dev.py stop`. |
| Backend `Dockerfile` | `uv sync --locked --no-dev --no-install-project --no-editable`, plus `COPY packages`, `COPY mcp-server`, `COPY eval/pyproject.toml` for its workspace members | `uv sync --locked --no-dev --no-install-project`, with `libpq-dev`/`libpq5` | PilotApp's line. `--no-editable` and the member COPYs are FieldnotesApp's workspace, not template material. |
| Root project name | `fieldnotes-workspace` | `pilot-workspace` | `{{ project_name }}-workspace`, so the root and backend locks do not describe a package of the same name. |
| `backend/pyproject.toml` | adds `[tool.uv.workspace]`, `[tool.uv.sources]`, pytest-asyncio and more | plain | PilotApp's shape. No workspace in the template. |
| `CLAUDE.md` list of standing edits | names Jenkinsfile, suite runner, Procfile.dev, dev.py, dev/testing scripts | adds `scripts/regenerate-openapi.py` and "backend's Dockerfile and scripts" | Phase 11-16 step 5 removes both lists. Note `regenerate-openapi.py` and `Dockerfile` are app-owned, so they never conflicted. |

Both apps run `uv` in the `modern-app` sidecar, and CI uses the same image. The Jenkinsfile needs uv on `registry:5000/kube-coder-modern-app-toolchain:node-24`. FieldnotesApp's commit says "The validation image has uv from modern-app-dev". It does: the toolchain image installs uv with the astral installer (§4.2).

### App-owned packaging

Both apps: two projects, no uv workspace across them. Root `uv.lock` and `backend/uv.lock`. The root `pyproject.toml` has no `[tool.uv.workspace]`, so `backend/` resolves standalone. uv writes `.venv/.gitignore` itself, so the root `.gitignore` needs no `.venv` line (the backend template's `.gitignore` already has `.venv/`).

Method for the lock: both commit messages say "uv.lock resolving exactly the versions poetry.lock held". The procedure is not recorded. Phase 11-16 should run `uv lock`, then compare the versions in `uv.lock` against the old `poetry.lock` (name and version per package) before dropping `poetry.lock`.

#### Root `pyproject.toml` (PilotApp; FieldnotesApp identical except names)

```toml
[project]
name = "pilot-workspace"
version = "0.1.0"
description = "The project manager that runs multi-step work across the KubeCoder fleet"
authors = [{ name = "Pieter van Ginkel", email = "pvginkel@gmail.com" }]
requires-python = ">=3.13,<4"
dependencies = [
    "honcho>=2,<3",
    "psutil>=5,<6",
]

[project.scripts]
run-suite = "tools.suite_runner.local:cli"

[dependency-groups]
dev = [
    "ruff==0.11.13",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tools"]
```

The `[tool.ruff]` sections stay as they were.

#### `backend/pyproject.toml` (PilotApp; the dependency list is that app's)

```toml
[project]
name = "pilot"
version = "0.1.0"
description = "..."
authors = [{ name = "Pieter van Ginkel", email = "pvginkel@gmail.com" }]
readme = "README.md"
requires-python = ">=3.13,<4"
dependencies = [
    "flask>=3.0.0,<4",
    ...
    "prometheus-flask-exporter>=0.23.0,<0.24",
    "psycopg[binary]>=3.1.0,<4",
    ...
]

[project.scripts]
cli = "app.cli:main"
dev = "run:main"
check = "scripts.check:main"

[dependency-groups]
dev = [
    "copier>=9.0.0,<10",
    "ruff>=0.11.0,<0.12",
    "mypy>=1.8.0,<2",
    "pytest>=7.4.0,<8",
    ...
    "vulture>=2.14,<3",
]

# Only app/ is a package; run.py and scripts/ are reached through the editable
# install's path entry (the project root), which is what `uv run dev` and
# `uv run check` need. The image installs no project at all (--no-install-project).
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

The `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]` and `[tool.coverage]` sections stay as they were.

Conversion rules the apps applied:

| Poetry | uv |
|--------|----|
| `[tool.poetry] name/version/description/readme` | `[project]` |
| `authors = ["A <a@b>"]` | `authors = [{ name = "A", email = "a@b" }]` |
| `python = "^3.13"` | `requires-python = ">=3.13,<4"` |
| `x = "^1.2.3"` | `"x>=1.2.3,<2"` |
| `x = "^0.23.0"` | `"x>=0.23.0,<0.24"` |
| `psycopg = {extras = ["binary"], version = "^3.1.0"}` | `"psycopg[binary]>=3.1.0,<4"` |
| `[tool.poetry.group.dev.dependencies]` | `[dependency-groups] dev = [...]` (uv syncs `dev` by default; `--no-dev` drops it) |
| `[tool.poetry.scripts]` | `[project.scripts]`, same `name = "module:func"` strings |
| `packages = [{include = "app"}]` | `[tool.hatch.build.targets.wheel] packages = ["app"]` |
| `poetry-core` build backend | `hatchling` |
| `package-mode = false` (template repos) | no `[build-system]`, and `[tool.uv] package = false` if a `[project]` table exists |

Entry points: every `[tool.poetry.scripts]` entry (`cli`, `dev`, `check`, `run-suite`) became the same line under `[project.scripts]`. Nothing else replaced them. `uv run dev` and `uv run check` work because the hatchling editable install puts the project root on `sys.path`, so `run:main` and `scripts.check:main` resolve. This needs the `[build-system]` and `[tool.hatch.build.targets.wheel]` blocks. The root project needs the same for `tools`.

#### `.kubecoder/project.yaml` (PilotApp)

```yaml
projects:
  root:
    setup: cexec modern-app uv sync --locked
    lint:
      - cexec modern-app uv run ruff check scripts tools
    # `uv run run-suite` is what CI keeps using (comment text only)
  backend:
    setup:
      - cexec modern-app uv sync --locked
      - "test -f .env || printf 'DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/pilot\\n' > .env"
      - cexec modern-app uv run python scripts/init-dev-database.py
      - cexec modern-app uv run cli upgrade-db
    test: cexec modern-app uv run pytest
    lint:
      - cexec modern-app uv run ruff check .
      - cexec modern-app uv run ruff format --check .
      - cexec modern-app uv run mypy .
      - cexec modern-app uv run vulture app/ vulture_whitelist.py --min-confidence 80
```

FieldnotesApp is the same without the database lines. Mapping: `poetry install --no-interaction` becomes `uv sync --locked`; `poetry run X` becomes `uv run X`. No `--no-interaction` equivalent is needed.

#### Backend `Dockerfile` (PilotApp; app-owned)

```dockerfile
FROM python:3.13-slim AS build

# uv uses the image's own Python and never downloads one; copy mode, because
# the cache and the venv are on different filesystems in a build.
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_LINK_MODE=copy
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
...
RUN pip install uv

WORKDIR /app

# --- Reproduce the environment ---
COPY pyproject.toml uv.lock /app/

# Install project deps into .venv
RUN uv sync --locked --no-dev --no-install-project
```

The runtime stage is unchanged (`COPY --from=build /app/.venv /app/.venv`, `PATH="/app/.venv/bin:${PATH}"`). The three `POETRY_*` ENV lines are removed, and `RUN pip install poetry` becomes `RUN pip install uv`.

#### Jenkinsfile install commands (declarative, both apps)

```groovy
modernApp.test(
    job: 'pilot-validation',
    install: 'uv sync --locked --no-dev',
    run: 'uv run --no-sync',
    ...
)
```

The Poetry apps today have `install: 'poetry install --no-interaction --without dev'` and `run: 'poetry run'` (ElectronicsInventory lines 50-51, IoTSupport 53-54, DHCPApp 46-47, ZigbeeControl 49-50). These two strings become the uv pair above.

#### What the Poetry apps carry (heads-up for phases 11-16)

Surveyed read-only. All four have the same shape as the apps above: root `pyproject.toml` + `poetry.lock`, `backend/pyproject.toml` + `backend/poetry.lock`, `[tool.poetry.scripts]` with `cli`/`dev`/`check` (backend) and `run-suite` (root), no git or path dependencies.

| App | Extras for the converter |
|-----|--------------------------|
| ElectronicsInventory | Dockerfile installs with `poetry install --no-root` (no `--only main`). `psycopg` and `boto3-stubs` extras. `.kubecoder/project.yaml` runs tests as `cd .. && cexec modern-app poetry run run-suite --suite backend`. `.kubecoder/config.yaml` comments (lines 3, 6, 74, 78) name Poetry. |
| IoTSupport | `.kubecoder/project.yaml` comment (line 40) says "`poetry run ruff` deliberately reaches the lockfile's ruff, not the newer" one. Reword it for uv. Header comment lines 6-7 name `poetry run run-suite`. Dockerfile uses a combined `ENV POETRY_... \` block (lines 3-4) and `COPY pyproject.toml poetry.lock ./`. |
| DHCPApp | `--no-root` Dockerfile. No `initialize-sqlite-database.sh` (no database). |
| ZigbeeControl | `--no-root` Dockerfile. `project.yaml` comments (lines 5-6, 17, 40) name `poetry run`. Backend `authors` is `"Pieter van Ginkel <...>"`. |

DHCPApp's backend `authors` is `"Pieter <pieter@example.com>"`; convert it as is.

### Poetry uses to change

Counts are lines containing `poetry` (case-insensitive), excluding lockfile bodies, `node_modules` and regenerated test-apps. "history" means a changelog line, a past-tense doc or a planning doc that stays.

| Repo | Lines to change | Files |
|------|-----------------|-------|
| Backend template (`backend/template/`) | 18 | 7 |
| Frontend template (`frontend/template/`) | 0 | 0 |
| Root template (`root/template/`) | 38 | 8 |
| Backend repo own files | 15, plus `poetry.lock` | 4 (`pyproject.toml`, `poetry.lock`, `regen.sh`, `CLAUDE.md`) |
| Frontend repo own files | 10, plus `poetry.lock` | 4 |
| Parent harness (`.kubecoder`, `root/regen.sh`, `scripts/`, `CLAUDE.md`, `pyproject.toml`) | 31, plus `poetry.lock` | 6 |
| Parent `docs/` | 37 | 5 |
| `.claude/agents/` | 11 | 3 |
| History (leave) | 6 changelog lines, 3 planning docs, 1 design doc | |

Total to change: 160 lines (56 template + 25 backend and frontend repos + 31 harness + 37 docs + 11 agents). Plus 4 `poetry.lock` files (parent, backend, frontend, `backend/test-app`) to replace with `uv.lock`.

#### Backend template (`/work/ModernAppTemplate/backend/template/`)

- [ ] `pyproject.toml.jinja`, whole file (change). Lines 1, 9, 14, 43, 59, 60: `[tool.poetry]`, `[tool.poetry.scripts]`, `[tool.poetry.dependencies]`, `[tool.poetry.group.dev.dependencies]`, `requires = ["poetry-core"]`, `build-backend = "poetry.core.masonry.api"`. Convert with the rules above. The `{% if use_database %}`, `use_oidc` and `use_s3` blocks sit inside the dependency lists, so they move into the `dependencies = [...]` and `dev = [...]` arrays. Keep each entry on its own line with a trailing comma. Python-magic, boto3, pillow, `types-pillow`, `boto3-stubs[s3]` follow the extras rule. Python is `>=3.13,<4`. Add `[build-system]` with hatchling and `[tool.hatch.build.targets.wheel] packages = ["app"]`.
- [ ] `Dockerfile.jinja` (change): L3 `ENV POETRY_HOME=/opt/poetry`, L4 `ENV POETRY_VIRTUALENVS_IN_PROJECT=1`, L5 `ENV POETRY_VIRTUALENVS_CREATE=1` (replace with `UV_PYTHON_DOWNLOADS=never`, `UV_LINK_MODE=copy`); L25 `RUN pip install poetry`; L30 `COPY pyproject.toml poetry.lock /app/`; L33 `RUN poetry install --only main --no-root --no-interaction --no-ansi` (becomes `uv sync --locked --no-dev --no-install-project`).
- [ ] `scripts/dev-server.sh` L4: `poetry run dev`.
- [ ] `scripts/initialize-sqlite-database.sh` L64: `poetry run cli load-test-data --yes-i-am-sure`; L67: `poetry run cli upgrade-db`.
- [ ] `scripts/testing-server.sh.jinja` L91: `exec poetry run python -m flask run --host="$HOST" --port="$PORT"`. (BE-C09 rewrites this line to `uv run dev` in phase 2. Do not do both; phase 1 changes only the runner.)
- [ ] `vulture_whitelist.py.jinja` L4: `# Run vulture with: poetry run vulture app/ vulture_whitelist.py --min-confidence 80`.
- [ ] `tests/test_smoke.py` L4: "fail `poetry run check`".
- [ ] `scripts/check.py`: no change. It calls `ruff`, `mypy`, `vulture`, `pytest` from PATH, which `uv run check` provides.
- [ ] Add a template-level `README`/step: a fresh app has no `uv.lock`. See open question 3.

#### Frontend template (`/work/ModernAppTemplate/frontend/template/`)

- [ ] Nothing. A grep for `poetry`, `.venv` and `python` over the template finds no Poetry call. `tests/support/global-setup.ts` runs `backend/scripts/initialize-sqlite-database.sh`, which is a backend-template file.

#### Root template (`/work/ModernAppTemplate/root/template/`)

- [ ] `Jenkinsfile.jinja` L84 `cd /work && poetry install --no-interaction --without dev`, L85 `poetry run run-suite --output-mode full --junitxml-dir /work/results --retries 2` (change; §4 replaces the file, and the content is `install: 'uv sync --locked --no-dev'`, `run: 'uv run --no-sync'`).
- [ ] `pyproject.toml.jinja`, whole file (change). Lines 1, 8, 13, 16, 20, 21. Name becomes `{{ project_name }}-workspace`, with `[project.scripts] run-suite`, `[dependency-groups] dev = ["ruff==0.11.13"]`, hatchling and `packages = ["tools"]`. Keep the `[tool.ruff]` sections.
- [ ] `.kubecoder/project.yaml.jinja` (change): L6 `poetry install --no-interaction`; L9 `poetry run ruff check scripts tools`; L15 comment `poetry run run-suite`; L22 `poetry install --no-interaction`; L30 `poetry run python scripts/init-dev-database.py`; L31 `poetry run cli upgrade-db`; L33 `poetry run pytest`; L36-38 `poetry run ruff check .`, `poetry run mypy .`, `poetry run vulture ...`.
- [ ] `CLAUDE.md.jinja` L9 "(Python, Poetry)"; L14 "ad-hoc `poetry`/`pnpm` commands".
- [ ] `Procfile.dev.jinja` L2 `poetry run honcho -f Procfile.dev start`; L9 "neither poetry nor pnpm"; L11-13 the VIRTUAL_ENV/POETRY_ACTIVE comment; L14 `env -u VIRTUAL_ENV -u POETRY_ACTIVE PORT={{ backend_port }} poetry run dev`.
- [ ] `scripts/dev.py.jinja` L16 "neither poetry nor honcho"; L24 "installs the poetry and pnpm dependencies"; L171 `"poetry", "run", "honcho", "start", "-f", "Procfile.dev"`.
- [ ] `scripts/regenerate-openapi.py.jinja` L18 "started with `poetry run dev`"; L112 `["poetry", "run", "dev"]`.
- [ ] `tools/suite_runner/local.py.jinja` L6 "install the backend (Poetry)"; L13 "backend's Poetry venv"; L42 "Pin its Poetry venv"; L152-153 `poetry env use python3.13` / `poetry install --no-interaction` (replace with the single `uv sync --locked [--python python3.13]` command); L171 `["poetry", "run", "python", str(wait_script)]`; L185 `["poetry", "run", "pytest", "-v", "--tb=short"]`.
- [ ] `.gitignore`: no change (uv's `.venv` carries its own ignore file).

#### Backend repo own files (`/work/ModernAppTemplate/backend/`)

- [ ] `pyproject.toml` (change; copier and the mother suite come from here). Lines 1, 8, 11, 17, 18: `[tool.poetry]`, `[tool.poetry.dependencies]`, `[tool.poetry.group.dev.dependencies]`, `poetry-core`. Content: python `^3.13`, dev `copier ^9.0.0`, `pytest ^8.0.0`, `pytest-mock ^3.12.0`, `package-mode = false`.
- [ ] `poetry.lock` (change): delete, add `uv.lock`.
- [ ] `regen.sh` L17 `poetry run copier copy . test-app --trust --defaults --vcs-ref HEAD \`; L46 `cd test-app && poetry sync -q`.
- [ ] `CLAUDE.md` L11 "The container includes poetry"; L13 heading "Poetry Virtual Environments"; L15 "**Always use `poetry run`**"; L19 `poetry run pytest tests/ -v`; L56-57 and L118-119 `poetry run pytest ../tests/ -v`, `poetry run pytest tests/ -v`.
- [ ] `test-app/` (tracked render; regenerated by `regen.sh`, never hand-edited): `Dockerfile`, `pyproject.toml`, `poetry.lock` (becomes `uv.lock`), `scripts/dev-server.sh`, `scripts/initialize-sqlite-database.sh`, `scripts/testing-server.sh`, `tests/test_smoke.py`, `vulture_whitelist.py`. Commit the regenerated render and `uv.lock`.
- [ ] `docs/`: the repo has none. `tests/` (mother suite) has no Poetry use.

#### Frontend repo own files (`/work/ModernAppTemplate/frontend/`)

- [ ] `pyproject.toml` (change). Lines 1, 9, 12, 16, 17. Python `^3.11`, dev `copier ^9.0.0`, `package-mode = false`. It carries copier only for `regen.sh`; see open question 2.
- [ ] `poetry.lock` (change): delete, add `uv.lock`, or drop both (open question 2).
- [ ] `regen.sh` L17 `poetry run copier copy . test-app --trust --defaults --vcs-ref HEAD \`.
- [ ] `CLAUDE.md` L11 "includes poetry"; L13 heading; L15 "uses Poetry for copier"; L19 `poetry run copier copy ...`.
- [ ] `test-app/`: no Poetry use.

#### Parent harness (`/work/ModernAppTemplate/`)

- [ ] `.kubecoder/project.yaml` (change): L24 `cexec modern-app poetry install --no-interaction` (backend setup); L34-35 `poetry run pytest ../tests/` and `poetry run pytest tests/`; L36 comment "test-app's own `poetry run check`"; L38-40 `poetry run ruff check .`, `poetry run mypy .`, `poetry run vulture ...`; L47 `cexec modern-app poetry install --no-interaction` (frontend setup, installs copier for regen); L67 comment `poetry run run-suite --suite frontend`; L68-69 `poetry run run-suite --suite backend`, `poetry run ruff check scripts tools`.
- [ ] `.kubecoder/config.yaml` L34 comment: "drives copier under Poetry, the backend template's test-app is a Poetry/pytest project".
- [ ] `root/regen.sh` L20 `(cd "$REPO_ROOT/backend" && poetry run copier copy "$REPO_ROOT" ...`; L48 `cd test-app && poetry install -q`; L53-54 the printed hints `poetry run ruff check scripts tools`, `poetry run run-suite --suite backend`.
- [ ] `scripts/test_all.py` L157 `["poetry", "env", "use", "python3.13"]`; L158 `["poetry", "install", "--no-interaction"]`; L166 `["poetry", "lock", "--no-update", "--no-interaction"]` (retry on a stale lock; becomes `uv lock`); L179 `["poetry", "run", "pytest", "-v", "--tb=short"]`. It finds backends by the presence of `pyproject.toml`, which still holds.
- [ ] `scripts/find_template_violations.py`, `pull_all.py`, `push_all.py`, `review_all.py`, `changes_since_sync.py`, `workspace.py`: no Poetry use. The violation finder's `python scripts/...` usage lines need no change; they use plain `python`.
- [ ] `CLAUDE.md` L39 "prefix Poetry, `copier` and pnpm commands"; L40 `cexec modern-app sh -c 'cd test-app && poetry install'`; L78 `poetry run pytest ../tests/ -v && poetry run pytest tests/ -v`; L94 `poetry run ruff check scripts tools && poetry run run-suite --suite backend`; L117 "copier comes from the backend template's Poetry env"; L118-120 the three `cexec modern-app poetry -P /work/ModernAppTemplate/backend run copier update --trust --defaults` lines; L133 "`poetry run check` runs ruff, mypy, vulture, and pytest". L51-52 ("on uv, not Poetry") change when the two apps sync (phase 16), not in phase 1.
- [ ] `pyproject.toml` (parent; `[tool.poetry]`, `package-mode = false`, python `^3.13`, no dependencies) and `poetry.lock`: delete both, or convert (open question 2). `cexec modern-app poetry install` runs against it only from the backend and frontend project cwd, not the parent's.
- [ ] `.claude/agents/code-writer.md` L83 `poetry run copier copy . test-app --trust \`, L93 `poetry install`, L99-100 `poetry run pytest ../tests/ -v`, `poetry run ruff check ../template/ .`, L112-113 checklist items; `.claude/agents/code-reviewer.md` L133-134; `.claude/agents/plan-writer.md` L98-99.

#### Parent `docs/`

- [ ] `change_workflow.md`: L138 `poetry run copier copy . test-app --trust \`; L148 `echo "# Test App" > README.md && poetry install`; L159 `poetry run pytest ../tests/ -v`; L162 `poetry run ruff check ../template/ .`; L165 `poetry run mypy . --ignore-missing-imports`; L292 "copier comes from the backend template's Poetry env"; L294 and L355-356 `cexec modern-app poetry -P /work/ModernAppTemplate/backend run copier update --trust --defaults`; L398 `rm -rf test-app && poetry run copier copy . test-app --trust ...`; L401 `cd test-app && poetry run pytest ../tests/ -v`.
- [ ] `copier_approach.md`: L61 `poetry run pytest ../tests/ -v && poetry run pytest tests/ -v`; L63 `poetry run ruff check scripts tools && poetry run run-suite --suite backend`; L74 "running `poetry run run-suite`"; L83 "root Poetry project with honcho, psutil"; L90 "under the backend's Poetry venv"; L337 "test-app's poetry environment"; L411 `poetry run copier copy . test-app --trust \`; L440 `cd test-app && poetry install`.
- [ ] `downstream_sync_process.md`: L27-29 `poetry run python scripts/find_template_violations.py ...` (the script is stdlib; `python3 scripts/...` works); L53-54 `poetry run pytest ../tests/ -v`, `poetry run pytest tests/ -v`; L95 comment "copier lives in the backend template's Poetry env"; L98 the `COPIER=` command; L128 and L206 `poetry run python scripts/find_template_violations.py .`; L168 "`poetry lock && poetry install`" (example text). L189-190 (FieldnotesApp and PilotApp rows, "Moved from Poetry to uv on its own") change in phase 16.
- [ ] `frontend_porting_guide.md` L39, L132, L185: `poetry run copier copy . ... --trust --defaults \`.
- [ ] `backend_porting_guide.md` L36 `poetry run copier copy . ...`; L79 `poetry install`; L314 `poetry run copier update --trust --defaults -d use_s3=true -d use_sse=true`.
- [ ] `copier_approach.md` L37 and L172 describe `pyproject.toml` as "Dev dependencies"/"dependencies"; no Poetry word, check wording.

#### History (leave as is)

- `changelog.md` L43, L134, L417, L521, L523, L795: past entries. Add one new coordinated entry for the uv move, with migration steps from "App-owned packaging" above.
- `docs/da_port_plan.md`, `da_port_decisions.md` (S7), `da_port_inventory.md` (BE-C09, BE-C30, BE-T-series, RT-series mention `poetry run dev`, `poetry run coverage`, `poetry show --outdated`): these describe DesignAssistant or the plan. BE-C09, BE-C30 and the RT07 dependency checker (`poetry show --outdated`) need uv wording when built, not now.
- `docs/pilotapp_database_testing_design.md` L176, L189 (`poetry run cli ...`, `poetry run run-suite`): a design record. Leave. (`/tmp/database-testing-design.md` is gitignored.)

### Open questions for phase 1

1. **Scripts: `[project.scripts]` with hatchling, or `uv run` of a module?** Recommendation: `[project.scripts]` plus hatchling, as both apps did. It keeps `uv run dev`, `uv run cli`, `uv run check` and `uv run run-suite`, so every doc, project.yaml and the `Procfile.dev` line keep their shape. The alternative (`package = false` and `uv run python run.py`) changes every call site and loses `cli`/`check`. Cost of the recommendation: a build backend and `[tool.hatch.build.targets.wheel] packages = [...]`, plus the editable-install path trick so `run:main` and `scripts.check:main` import. The two apps run this way; phase 0 didn't test it separately.

2. **How copier is provided, and the new sync command.** Recommendation:

   ```bash
   cexec modern-app uv run --project /work/ModernAppTemplate/backend copier update --trust --defaults
   ```

   Run from the component's directory, as today. `--project` selects the backend repo's project without changing the working directory. Phase 0 checked this in a scratch project: `cd <dir> && uv run --project <other> sh -c "pwd; copier --version"` printed `<dir>` and the pinned copier 9.11.3. It built `<other>/.venv` and `uv.lock` on first use. `.venv/` is gitignored in the backend repo; `uv.lock` is tracked and must be committed. Add `--locked` to keep the version from drifting. The `Poetry -P` form it replaces had the same semantics.
   - Do not use `uvx copier`: it resolves the latest copier (9.19.1 today) and the template repos pin 9.11.3 in `poetry.lock`. A copier minor change can change update behaviour.
   - Do not use the app's own dev group copier (`copier>=9.0.0,<10` is in every app's `dev` group): it covers `backend/` only. The root and frontend components have no copier.
   - Not verified: a real `copier update` through this command from inside an app's `backend/` (a cwd that has its own `pyproject.toml`). Run the first update of phase 16's FieldnotesApp with it and record the result in the phase log. If `--project` misbehaves there, fall back to the absolute path `/work/ModernAppTemplate/backend/.venv/bin/copier`, after `uv sync` in the backend repo.
   - Decide the frontend repo's `pyproject.toml`/`poetry.lock`: the only user is `frontend/regen.sh`. Either convert it (copier pin, `uv.lock`) or have `frontend/regen.sh` use `uv run --project ../backend copier copy ...` and delete the file. The second leaves one copier pin. Same for the parent `pyproject.toml`/`poetry.lock`: delete both.

3. **A fresh app has no `uv.lock`.** `uv sync --locked` (what both apps use in `project.yaml`) fails with no lock. Poetry created `poetry.lock` on first `poetry install`. Recommendation: the generated `project.yaml.jinja` says `uv sync` (no `--locked`) in `setup`, which writes the lock on first run; the `Jenkinsfile`, `local.py` and `Dockerfile` keep `--locked`. Also state in the generated `CLAUDE.md` that the first commit includes both `uv.lock` files. Alternatively add a `_tasks` entry in `copier.yml` that runs `uv lock`, but that makes generation need network and uv.

4. **Regen drift.** `regen.sh` does `rm -rf test-app`, so `test-app/uv.lock` is re-resolved each regen. Poetry had the same behaviour (lock churn is already noted in CLAUDE.md). With uv, add `UV_LINK_MODE=copy` to `regen.sh` and the harness commands: in the sidecar the cache and the test-app are on different filesystems, and uv warns about hardlinking (seen in phase 0's scratch run).

5. **Pin `copier` in the backend repo's `pyproject.toml`.** Keep `copier>=9.0.0,<10` as the range, but the lock decides. A fresh `uv lock` would resolve a newer copier than 9.11.3. Either pin `copier==9.11.3` for phase 1 and bump in the dependency-bump step, or accept the newer version and run the mother suite and one sync to check. Recommend pin first.

6. **Root project name.** Take `{{ project_name }}-workspace` (both apps did). Existing apps already renamed or will rename in their step 6.

7. **Pytest and ruff pins.** The template dev group is pytest `^7`/`^8`, ruff `^0.11`. Phase 1 step 5 bumps pytest 9 and ruff 0.15 in the same change. Convert first with the same ranges, keep that commit green, then bump, so a failure is attributable.

8. **Python pin in `local.py`.** The apps changed `poetry env use python3.13` to `uv sync --locked --python python3.13`. With `requires-python = ">=3.13,<4"` and `UV_PYTHON_DOWNLOADS` unset in the sidecar, uv could download a Python. The sidecar has `/usr/bin/python3.13` (cpython 3.13.7), so `--python python3.13` picks it. Keep the `HAS_PYTHON313` condition as the apps did.

9. **Blockers.** None for starting phase 1. Two checks the phase log should record: the toolchain image used by CI has uv (it does, §4.2), and the real `copier update` through the new command (question 2).

## 4. The CI pipeline

Read: `root/template/Jenkinsfile.jinja` (root v0.1.6), the `kubecoder:jenkins-pipelines` skill and its site (https://dev-guides.home/pipelines/, type page `types/modern-app`), PilotApp's `Jenkinsfile`, `vars/modernApp.groovy` and `vars/podYaml.groovy` in `/work/scratch/JenkinsPipelineUtils`, DA's `Jenkinsfile`.

**The apps are ahead.** All six apps already run their tests through `modernApp.test` in a declarative file; none still runs the scripted template file. They got there by hand (PilotApp commit `a49e4ad`, "template-owned", FieldnotesApp the same). ElectronicsInventory, IoTSupport, DHCPApp and ZigbeeControl are on `run: 'poetry run'`, FieldnotesApp and PilotApp on `run: 'uv run --no-sync'`. Only the template is stale: `Jenkinsfile.jinja` still calls `containerTemplates.k8s` and positional `helmCharts.kaniko`, which the library no longer has, so a freshly rendered app does not build. Phase 8 therefore replaces the template file with the guide's modern-app shape, and every app's `copier update` sees a small diff against its hand-moved file, not a rewrite.

### 1. Template, guide and PilotApp compared

| Aspect | Root template `Jenkinsfile.jinja` | Guide (`types/modern-app`, FILE/PROP/GRAN/LABEL rules) | PilotApp `Jenkinsfile` |
|---|---|---|---|
| Form | scripted `podTemplate`/`node` | one declarative `pipeline {}` (FILE-1) | declarative |
| Test Job | ~170 lines of inline Job YAML, summary and JUnit code | `modernApp.test(...)` in `script {}` (LIB-6) | `modernApp.test(...)` |
| Services | RustFS sidecar in the Job YAML when `use_s3`; no PostgreSQL | `services:` entries | `services: []` (PilotApp has a PostgreSQL database but CI does not run one yet) |
| Install and run | `poetry install ...` / `poetry run run-suite` | `install:` and `run:` arguments | `uv sync --locked --no-dev` / `uv run --no-sync` |
| Image build | positional `helmCharts.kaniko(...)` (gone from the library) | `helmCharts.kaniko2(...)` (LIB-6) | `kaniko2`, context `backend` and `frontend` |
| Stage labels | `Cloning repo`, `Run validation`, `Building <image>` | `Checkout`, `Test`, `Build <image> image`, `Write image pins` (LABEL-1/2) | guide labels |
| Options | none | `disableConcurrentBuilds(abortPrevious: true)`, `skipDefaultCheckout()`, `timeout(60 MINUTES)`, `timestamps()`, `githubPush()` | all of them |
| Header | none | header comment ending in `Controller config:` (FILE-3), library line (FILE-5) | yes |
| Pins | `cicd.writeVersionPins` in `k8s` container | same, in a stage after the builds (GRAN-6) | same |

PilotApp's file is the guide's reference shape (ElectronicsInventory's `docs/examples/modern-app.groovy`) with PilotApp's values. Nothing in it is structurally PilotApp-specific. The PilotApp-specific values are: `job: 'pilot-validation'`, `services: []`, `env: [:]`, the image names `pilot` and `pilot-ui`, the pins `images.pilot` and `images.pilotUI` into `pvginkel/PilotDeploy`, the `Job: PilotApp` header line and the comment text. All of these are already copier answers (`project_name`, `backend_image`, `frontend_image`, `*_pin_key`, `deploy_repo`, `repo_name`).

Header job name: PilotApp and FieldnotesApp have root-level jobs (`PilotApp`, `FieldnotesApp`); ElectronicsInventory's reference header says `ElectronicsInventory/ElectronicsInventory`. The template renders `Job: {{ repo_name }}`. The operator creates the job, so this line is only a record. Phase 8 does not need a new copier question.

### 2. What `modernApp.test` does

Source: `/work/scratch/JenkinsPipelineUtils/vars/modernApp.groovy` (doc: `docs/pages/reference/modernApp.md`).

- Arguments, all required, no defaults: `job`, `install`, `run`, `suites`, `services`, `env`, `secrets`. `services`, `env` and `secrets` may be empty. Unknown or missing arguments fail the build with a named error.
- It runs in the `k8s` container (`podYaml(templates: ['k8s'])`). It tars the workspace (excluding `.git`, `node_modules`, `.venv`, `test-results`, `.pnpm-store`), applies a Job `<job>-<build>` on the image of `podYaml`'s `modern-app-toolchain` template (`registry:5000/kube-coder-modern-app-toolchain:node-24`), runs as uid 1000 with an emptyDir at `/work`, requests `cpu: "1"`, deadline 3600 s, `ttlSecondsAfterFinished` 3600.
- The `validation` container waits for the `ready` file, extracts the tar, runs `cd /work && <install>`, then `<run> run-suite --output-mode full --junitxml-dir /work/results --retries 2`, writes `exit-code` and sleeps. The step copies results out, writes `validation-summary.log`, archives, publishes JUnit, sets the build description, and always deletes the Job.
- `services:` entries are maps with `name`, `image` and optionally `env` and `resources` (`requests`/`limits`). Each becomes another container in the same pod, so a service is on `localhost:<port>`. `env:` is the `validation` container's environment. `secrets:` names build-environment variables (from `withVault`) passed through without entering a Groovy string.
- **It does not wait for any service.** The pod's containers start together and the step only waits for the `validation` container. The wait belongs to the suite: the root suite runner (`root/template/tools/suite_runner/local.py.jinja:165-173`) runs `backend/scripts/wait-for-services.py` after the backend install if the file exists. No template ships that file today (PilotApp's design, `docs/pilotapp_database_testing_design.md` §4.7, has it app-owned and not yet written; `PilotApp/backend/scripts/` does not have it).
- **Poetry or uv** is only the `install:` and `run:` strings. The toolchain image carries Poetry, uv and ruff (`DockerImages/kube-coder-modern-app-toolchain/Dockerfile`), Node 24, pnpm, Chromium OS deps. Nothing in the library is Poetry-specific. The suite runner itself still calls `poetry` (phase 1).
- **Build cache:** the library knows nothing about it. The `run-suite` flags are fixed, so `--build-cache` (DA passes it) cannot be added from the Jenkinsfile.

### 3. What the template `Jenkinsfile` becomes (phase 8)

Render the guide's modern-app type from `docs/examples/modern-app.groovy`, with Jinja only where a flag or an answer changes it:

- Header: what the job does, `Controller config:` with `Job: {{ repo_name }}`, `SCM: {{ github_owner }}/{{ repo_name }}, branch main`, `Script Path: Jenkinsfile`. Library line `library identifier: 'JenkinsPipelineUtils', changelog: false`.
- `agent { kubernetes { inheritFrom 'jenkins-agent kaniko'; yamlMergeStrategy merge(); yaml podYaml(templates: ['k8s']) } }`. Options and `githubPush()` as above.
- Stages: `Checkout`; `Test`; `Build {{ backend_image }} image`; `Build {{ frontend_image }} image` (writes `frontend/git-rev` with `git rev-parse HEAD` first); `Write image pins` (`cicd.writeVersionPins`, same pins as today).
- `Test` calls `modernApp.test(job: '{{ project_name }}-validation', install: 'uv sync --locked --no-dev', run: 'uv run --no-sync', suites: ['backend', 'frontend'], services: [...], env: [...], secrets: [])`.
- **PostgreSQL (S1), `use_database`:** `services` gets `[name: 'postgres', image: 'postgres:18-trixie', env: [POSTGRES_PASSWORD: 'postgres']]`, optionally with `resources`. No `env` is needed for it, the defaults match (design §4.7). Image tag matches production (18) and the dev sidecar (18.6).
- **S3, `use_s3`:** today's sidecar moves into `services`: `[name: 's3storage', image: 'rustfs/rustfs:latest', env: [RUSTFS_ACCESS_KEY: 's3storage', RUSTFS_SECRET_KEY: 's3storage']]`, with `env` `S3_ENDPOINT_URL: 'http://localhost:9000'`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` (both `s3storage`) and `S3_BUCKET_NAME: '{{ project_name }}-validation'`. ElectronicsInventory's file is the worked example. Keep the comment on why a sidecar and a throwaway bucket.
- **`STAGE=tst` (D9b):** `env: [STAGE: 'tst']`. No library change.
- **The wait:** no library change. The template backend must ship a template-owned `backend/scripts/wait-for-services.py`: wait up to a minute for `TEST_DATABASE_ADMIN_URL` (when `use_database`) and for `S3_ENDPOINT_URL` (when `use_s3`) to accept a TCP connection, fail with a clear message, return at once when they are unset (local runs). The runner calls it after the backend install, via `uv run python` (phase 1 changes the call). **Gap in the plan:** no phase lists this file. Phase 2 (S1) is the natural owner; phase 8 only depends on it. If phase 2 does not ship it, phase 8 must.
- **pnpm build cache (RT05):** the library cannot pass `--build-cache`. Do it without a library change: add `BUILD_CACHE: 'true'` (name is phase 8's choice) to `env:`, and have the root suite runner turn the cache on from that variable as well as from `--build-cache`. The Job runs in the Jenkins namespace, so the default `BUILD_CACHE_URL` resolves. Alternative, if the operator prefers: a new optional `args` argument on `modernApp.test` for extra `run-suite` flags. That is a library change, needs a `vars/modernApp.md` update (LIB-5) and goes through the operator. Recommendation: the env variable.
- **Base images (S3):** no Jenkinsfile change. The kaniko stages already build `backend/Dockerfile` and `frontend/Dockerfile`; the Dockerfiles change.
- **uv (S7):** `install` and `run` strings only.
- **Frontend image build context.** The Jenkinsfile builds the frontend with `context: 'frontend'`. DA's `frontend/Dockerfile` copies `scripts/build-cache-get.sh` from a repo-root context, which does not exist here. The Dockerfile restore step must either inline the `curl | tar` (preferred, 3 lines, no file) or come with the script under `frontend/`. See §6.2.

What stays as the app's: extra image stages (ElectronicsInventory's docs image), `withVault` plus `secrets:` (IoTSupport's Keycloak admin client), extra services (IoTSupport's OpenSearch). A `copier update` conflict on this template-owned file resolves to the app's side, as PilotApp's commit message already states.

Library gaps for the above: none required. Optional: an `args` argument for extra `run-suite` flags (see cache). The Job's 3600 s deadline is below DA's 7200 s; a Playwright-heavy app that needs more would need a library argument; the template apps do not.

Follow-ups outside this repo, for the operator: the guide's modern-app type page (`JenkinsPipelineUtils/docs/pages/types/modern-app.md`) lists five apps and says "a file of this type follows the reference file below, not the template". After phase 8 the template renders that type; the page and the skill's "two files predate the guide" paragraph (jenkins-pipelines skill, `KubeCoderConfig/kubecoder/skills/jenkins-pipelines/SKILL.md`) are then stale. Both are other repos; flag it to the operator, or take it in phase 9 where the KubeCoderConfig clone is open.

### 4. What DA's `Jenkinsfile` has that neither has (RT02)

Compared with the template and PilotApp. Take or leave:

| DA feature | Take? | Why |
|---|---|---|
| `run-suite --build-cache` | Take (RT05) | see above |
| `--max-failures 14` | Leave | the library fixes the `run-suite` flags; a template app has too few tests to need a cap |
| Branch to tag map (`origin/main`->`tst`, `origin/develop`->`dev`), images tagged `<prefix>-<build>` | Leave | DA's tiers; the template pins `:<build>` into the Argo deploy repo from `main` only |
| `cicd.helmDeploy()` | Leave | replaced by `writeVersionPins` and Argo CD (D53) |
| `canon` lint stage | Leave | DA-specific |
| Playwright image chosen from `pnpm-lock.yaml` | Leave | already retired in the template (toolchain image, v0.1.x changelog) |
| `withVault` Keycloak secrets, `secrets:` | Leave | per-app; IoTSupport is the precedent |
| Requests `cpu: 2`, `memory: 4Gi` and limits | Leave | Kyverno sets memory requests on prd; the library books `cpu: "1"` |
| `activeDeadlineSeconds: 7200` | Leave | library fixes 3600 |
| Extra services (MinIO, RabbitMQ, OpenSearch, document-conversion) | Leave | DA-only dependencies, in `services:` if an app needs them |
| `STAGE`-like env (`PLAYWRIGHT_PREVIEW_MODE: "true"`) | Take, as a note | RT13 (preview-mode gotcha) goes into the conventions guide in phase 9; the Jenkinsfile sets `STAGE=tst` |
| `PostgreSQL pgvector/pgvector:pg18-trixie` container | Take the idea, not the image | S1 uses plain `postgres:18-trixie`; take pgvector only if an app needs it |
| Third image stage (portal), `Jenkinsfile.deploy-uat`, `Jenkinsfile.deploy-prd` | Leave | not RT02; no UAT pipeline in the template (UAT is a per-app deploy matter, `da_port_decisions.md` line ~200) |

## 5. Per app

Facts are read from `/work/<App>` at HEAD and from the deploy repos cloned to `/work/scratch/deploy/`. Template baselines: backend v0.13.2 (IoTSupport, EI, DHCPApp, ZigbeeControl, FieldnotesApp) or v0.13.3 (PilotApp); frontend v0.20.3 (first four), v0.20.2 (FieldnotesApp), v0.20.4 (PilotApp); root v0.1.3 (first four), v0.1.2 (FieldnotesApp), v0.1.6 (PilotApp).

### Facts that hold for every app

- **Roles are hard-coded.** Each app builds `AuthService` in `backend/app/services/container.py` with literal role names. No env var, `app_config.py` field, `.env.example` line or deploy value sets a role. Phases 11-16 change roles by editing `container.py` (app-owned).
- **Keycloak assignments are not code.** Realm `homelab` at `https://auth.ginbov.nl` is a Keycloak with its own database (`HelmCharts/charts/keycloak` is a Deployment plus a PVC for themes). There is no realm export and no `keycloak_openid_client` / `keycloak_role` / `keycloak_user` resource in any repo of `gh repo list pvginkel`, in the six deploy repos (their `terraform/providers.tf` declares the `keycloak` provider and nothing uses it), `HelmCharts`, `Charts`, `Ansible` or `PlatformAddOnsDeploy`. Namespace `keycloak-prd` holds only `kube-root-ca.crt` and `tf-presync-revision` ConfigMaps (checked read-only on context `prd`). The client IDs sit in OpenBao leaves (`eso/prd/<app>/prd/oidc`) that this environment cannot read. **Only the operator can answer the role questions; each app lists what to check.**
- **The token carries realm and client roles.** `AuthService` merges `realm_access.roles` and `resource_access.<client>.roles` (`auth_service.py:42`). "Holds the role" may mean a realm role shared across apps or a client role of that app's client. The operator says which, per app.
- **Env vars live in the deploy chart templates, not in `config/prd/values.yaml`.** The values files hold `oidc.issuerUrl`, `baseUrl`, image pins and secret wiring. The backend container's `env:` list is in `chart/templates/*deployment*.yaml`. Adding `STAGE=prd` and `HOMELAB_INTERNAL=true` means editing that template (literal values, or `STAGE` from `.Values.global.environment`, which is `prd` in five of the six values files; PilotApp's has none). No deploy repo sets `FLASK_ENV` except IoT's init container; the images set `FLASK_ENV=production`.
- **Public hostnames.** `HOMELAB_INTERNAL=true` shows exception text in 500 responses (S4). Four apps are on public hostnames: IoTSupport (`iot.ginbov.nl`), ElectronicsInventory (`parts.ginbov.nl`), ZigbeeControl (`z2m.webathome.org`), PilotApp (`pilot.ginbov.nl`). FieldnotesApp has a public webhook host (`fieldnotes-hooks.webathome.org`). DHCPApp is internal only. The operator confirms the flag for the public ones before phases 11, 12, 14, 15 and 16.
- **Template-owned `send_event` sites change by `copier update`, in every app:** `app/services/task_service.py:74,206`, `app/services/frontend_version_service.py:79,121`, `app/api/testing_sse.py:181` (and `start_task(..., caller_subject=...)` at `:116`), and `app/utils/log_capture.py:111` (a different `send_event`, on a log client). The copies are byte-identical to the template in every app except FieldnotesApp's `sse_connection_manager.py`. The tables below list app-owned sites only.
- **Playwright sessions already carry roles.** Every `auth.createSession(...)` call in the six frontends passes `roles` (`['editor']` or the app's role) except one comment in EI's `role-gating.spec.ts:10`. D2 breaks no Playwright session. Backend tests that call `generate_test_jwt` also pass `roles` explicitly.
- **`modern-app-backend-build` is Poetry today** (`/work/scratch/DockerImages/modern-app-backend-build/Dockerfile`: `pip install poetry`). The two uv apps cannot use it until phase 8 makes it uv-ready. `modern-app-backend` (runtime) holds tini, netcat-openbsd, libmagic1, the image libs and libpq5.
- **CI needs PostgreSQL for the three database apps.** `.kubecoder/config.yaml` already lists the `postgres` sidecar for IoTSupport, EI and PilotApp. Their `Jenkinsfile` `modernApp.test(... services: ...)` has no `postgres` (IoT lists `s3storage` and `opensearch`, EI lists `s3storage`, PilotApp lists none). Phase 8 sets the shape; phases 11, 12 and 16 apply it.
- **Every app's `Jenkinsfile` is already a declarative `modernApp.test` file,** not the template's scripted one (`find_template_violations` shows `Jenkinsfile` modified in all six, +86..+116 / -175..-228). None of the four Poetry apps' `CLAUDE.md` says so. Phase 8's new template `Jenkinsfile` is reconciled with these in 11-16.

### IoTSupport

Backend v0.13.2 on Poetry. Flags: use_database, use_oidc, use_s3, use_sse. `CLAUDE.md` lists no standing template edits.

**1. Roles**

| Item | Value |
|---|---|
| `AuthService` | `backend/app/services/container.py:101-106`: `write_role="editor"`, `additional_roles=["pipeline"]`; no `read_role`, no `admin_role` |
| `@allow_roles` | `pipeline` on `api/pipeline.py:41,100,130` |
| `@public` | `api/iot.py:68,184,237,284,361` (device endpoints), `api/pipeline.py:157,196` (`upload.sh`, `upload.ps1`), auth and testing-auth |
| `.env.example` / deploy values | no role setting |
| `read_role` unset | yes |

D2 lockout: every domain GET is open today to any signed-in `homelab` account (`api/devices.py:43,123,223,307,381`, `device_models.py:32,107,251`, `coredumps.py:39,78,106`, `images.py:40`, `cas.py:25`, `rotation.py:30,100`, `tasks.py:20`). After D2 each needs `editor` (or the read tier phase 4 defines). A signed-in account without `editor` loses the whole UI. Unaffected: `/api/iot/*` and `/api/pipeline/upload.*` (`@public`), `/api/pipeline/*` with `pipeline`, and `/internal/rotation-nudge` (outside the `/api` blueprint, `startup.py:76`).

Open question for phase 4: a `pipeline` token on a plain GET passes today (any authenticated user). After D2 it still passes: the hoisted check asks for any configured role, and `pipeline` is one (`additional_roles`). So nothing changes for it.

Operator checks (Keycloak, realm `homelab`, IoTSupport's client): who holds `editor`; which other accounts sign in to `iot.ginbov.nl` (name them); whether `editor` is a realm or a client role; which `pipeline` service accounts exist and what they hold.

**2. `send_event` sites (D3)**

| File:line | Sends | Meant for |
|---|---|---|
| `app/services/device_log_stream_service.py:297` | `device-logs` with a batch of log documents, once per `request_id` in `_subscriptions_by_entity_id` | One connection each: the subscriber that called subscribe (`api/device_log_stream.py:75`, identity checked by `_verify_identity` `:172` from `caller_subject`). A targeted send. |
| `app/services/rotation_nudge_service.py:56` | `rotation-updated`, empty payload, `request_id=None` | Broadcast to every connection. Callers: `api/iot.py:180` (device fetched config), `api/rotation.py:83` (web), `api/internal.py:36` (rotation cronjob), `api/testing_device_sse.py:188`. |

Other SSE paths: `device_log_stream_service.py:65` `register_on_disconnect`, `:186` `get_connection_info`. No `start_task` caller in app code. Tests touching these: `tests/services/test_device_log_stream_service.py` (14 refs), `tests/services/test_rotation_nudge_service.py` (4), `tests/api/test_testing_device_sse.py`.

**3. SQLite / per-test-app tests (S1)**

35 test files, 697 tests; at least 481 tests in 24 files take `app`, `client`, `session` or `container` directly.

| Where | What | Tests |
|---|---|---|
| `tests/conftest.py:33-68` | App-owned `test_settings` override hard-codes `database_url="sqlite:///:memory:"` and `flask_env="development"` (keeps testing-only endpoints gated). Must take the template's PostgreSQL URL. | all that use `app` |
| `tests/conftest_infrastructure.py:103,187-227,417-452` | Template-owned: SQLite template connection, `backup()` clone per test, `StaticPool`. Replaced by phase 2 on update. | all |
| `tests/api/test_testing.py:29,91-146` | Own SQLite template (`testing_template_connection`) and a per-test `testing_app` from `create_app(...)` in `flask_env=testing`, with `upgrade_database(recreate=True)` (`:115`). | 29 tests in 8 classes (27 take `testing_client`) |
| `tests/api/test_testing_device_sse.py:31` | Imports those fixtures. | 28 tests (24 take `testing_client`) |
| `tests/api/test_pipeline.py` | `oidc_app` (template fixture) | 3 |

No SQLite-only SQL, `PRAGMA` or dialect branch in IoTSupport's app-owned `app/` code. `test_testing.py` is the only file that needs a second, differently configured app, so it needs phase 2's extra-app tier or a settings-override hook. `tests/services/test_logsink_service.py:425,527` use `threading.Event` for MQTT callbacks, not for the database.

Playwright and scripts also use SQLite (phases 2 and 6): `frontend/tests/support/global-setup.ts`, `fixtures-infrastructure.ts`, `process/servers.ts`; `backend/scripts/initialize-sqlite-database.sh`, `testing-server.sh`, `init-dev-database.py`.

**4. Dockerfile** (`backend/Dockerfile`, 41 lines)

App-customised, shorter than the template. Base `python:3.13-slim`, two stages. Poetry (`pip install poetry`, `poetry install --only main --no-root`). Runtime installs only `tini netcat-openbsd`: no libpq, libmagic or image libs (relies on `psycopg[binary]` and wheels). Copies `run.py alembic.ini app alembic`. No `DATA_PATH`; `FLASK_ENV=production`; `EXPOSE 3101`. `Dockerfile` is in `_skip_if_exists` (`backend/copier.yml:90`), so `copier update` never touches it; phase 11 rewrites it by hand onto `modern-app-backend*`. Note: `app/utils/mime_handling.py:1` does `import magic` and the image has no `libmagic1`; nothing imports that module (grep), so it is dead code today.

**5. Deploy repo**

`https://github.com/pvginkel/IotDeploy`. Values: `config/prd/values.yaml`. The env list is the `iotsupport.env` helper in `chart/templates/_iotsupport.tpl`, included at `chart/templates/iotsupport-deployment.yaml:32` (init container `iotsupport-setup`), `:41` (container `iotsupport-app`) and `iotsupport-rotation-cronjob.yaml:24`. Adding `STAGE` and `HOMELAB_INTERNAL` to the helper covers all three.

Current env (`_iotsupport.tpl`): `TIMEZONE`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DATABASE_URL`, `BASEURL`, `DEVICE_BASEURL`, `OIDC_ENABLED`, `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_TOKEN_URL`, `KEYCLOAK_BASE_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_ADMIN_CLIENT_ID`, `KEYCLOAK_ADMIN_CLIENT_SECRET`, `WIFI_SSID`, `WIFI_PASSWORD`, `MQTT_URL`, `DEVICE_MQTT_URL`, `ROTATION_CRON`, `ROTATION_CRITICAL_THRESHOLD_DAYS`, `SECRET_KEY`, `ELASTICSEARCH_URL`, `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`, `ARCHITECTURE_PIPELINE_TRIGGER_URL`. The app container adds `MQTT_USERNAME`, `MQTT_PASSWORD`, `PARSE_SIDECAR_*`, `SSE_CALLBACK_SECRET`, `THUMBNAIL_STORAGE_PATH` (`:42-69`).

**`FLASK_ENV` is set** on the init container: `iotsupport-deployment.yaml:33`, `value: db` (for `python -m app.cli upgrade-db`). The app container inherits `FLASK_ENV=production` from the image. D9b's default (`prd` under a production `FLASK_ENV`) says nothing about `db`; phase 11 sets `STAGE=prd` on the init container, and phase 3 must define what `FLASK_ENV=db` resolves to. `global.environment: prd` is in the values file. Public host `iot.ginbov.nl`.

**6. Gates** (`.kubecoder/project.yaml`)

| Verb | Command |
|---|---|
| root setup / lint | `cexec modern-app poetry install --no-interaction` / `poetry run ruff check scripts tools` |
| backend setup | poetry install; `scripts/generate-dev-env.sh`; `poetry run python scripts/init-dev-database.py`; `poetry run cli upgrade-db` |
| backend test | `cexec modern-app poetry run pytest` |
| backend lint | `ruff check .`; `mypy .`; `vulture app/ vulture_whitelist.py --min-confidence 80` |
| frontend setup | `pnpm install --frozen-lockfile ...`; `pnpm playwright install chromium` |
| frontend build / test / lint | `pnpm build` / `pnpm playwright test` / `pnpm check` |

Full suite: `cexec modern-app poetry run run-suite` (CI adds `--output-mode full`). Playwright by hand: `cexec modern-app poetry run run-suite --suite frontend`. Standing edits to reconcile: `Jenkinsfile` (`modernApp.test` with `s3storage` and `opensearch` services and Keycloak admin vault secrets, `:45-50`), root `.gitignore` (+3). `CLAUDE.md` says "Python/Poetry" (`:13`) and `poetry run run-suite` (`:29`); phase 11 edits both.

### ElectronicsInventory

Backend v0.13.2 on Poetry. Flags: use_database, use_oidc, use_s3, use_sse. `CLAUDE.md` lists no standing template edits; `docs/commands.md` holds the suite and database commands (10 `poetry` mentions).

**1. Roles**

| Item | Value |
|---|---|
| `AuthService` | `container.py:202-208`: `read_role="reader"`, `write_role="editor"`, `admin_role="admin"` (hierarchy admin > editor > reader) |
| `@allow_roles` | none. `@safe_query` on `api/parts.py:355`, `api/kits.py:267,316`. `@public` only on auth and testing-auth. |
| `.env.example` / deploy | no role setting |
| `read_role` unset | **no** |

D2 lockout: **none.** With `read_role` set, a user without `reader`, `editor` or `admin` already gets 403 on every GET ("No recognized role"), and `/api/auth/self` rejects them (`api/auth.py:129-134`). Operator check: none needed for D2.

**2. `send_event` and task sites (D3)**

No app-owned `send_event`. App-owned task starts:

| File:line | Sends | Meant for |
|---|---|---|
| `app/api/ai_parts.py:124` | `task_service.start_task(task=AIPartAnalysisTask, ...)`, no `caller_subject` | Task start, progress and completion events for the user who posted the analysis. With no `caller_subject`, `TaskService` broadcasts them to every connection (`task_service.py:284-310`). After BE-T10 they go to the caller, so the call must pass the caller. |
| `app/api/ai_parts.py:258` | `task_service.start_task(task=AIPartCleanupTask, part_key=...)`, no `caller_subject` | Same. |

Tests: `tests/api/test_testing.py` (11 refs; `TestTaskEventEndpoint` has 7 tests), `tests/test_utils_api.py` (11 refs, mocks `send_event`).

**3. SQLite / per-test-app tests (S1)**

61 test files, 1146 tests; at least 829 tests in 49 files take an app-building fixture directly.

| Where | What | Tests |
|---|---|---|
| `tests/conftest.py:79-130` | App-owned session fixture `sse_server`: `create_app` on a SQLite clone of `template_connection`, a real Flask server on a thread. `sse_client_factory` and `sse_gateway_server` (`:191,205`) depend on it. No test uses any of the three. | 0 (dead fixtures) |
| `tests/conftest_infrastructure.py` | Template-owned SQLite fixtures (as IoT). | all |
| `tests/test_role_based_access.py:501-561` | Own `oidc_role_app`: a second app from `template_connection.backup()` and `create_app(...)`. | 17 tests (file: 85) |
| `tests/api/test_testing.py:384-412` | `TestTestingEndpointsNonTestingMode`: dedicated SQLite connection, `create_app`, `db.create_all()`. | 3 |
| `tests/test_database_upgrade.py:12-60` | Tests the SQLite recreate branch of `upgrade_database()` (asserts `dialect.name == "sqlite"`). Goes with phase 2's removal of that branch. | 1 of 2 (delete) |
| `tests/test_startup.py:33,71,235` | `_DummySession(dialect_name="sqlite")`, `sqlite:///hook-test.db`, `test_sqlite_skips_sequence_reset`. | 1 of 9 (delete) |
| `tests/test_database_constraints.py:84-85,191-198` | `PRAGMA foreign_keys=ON`; a timestamp assertion that swallows its failure "in SQLite". Uses the Flask-SQLAlchemy global `db.session` (143 uses), which phase 2's container-session rebinding does not cover. | 29 |
| `tests/test_capacity_validation.py`, `tests/domain_fixtures.py` | More direct `db.session` uses (4 each) | few |
| `tests/test_transaction_rollback.py:376-571` | Raw `text()` SQL, hand `commit()`/`rollback()`, rollback sentinels. Tests the real commit boundary, so it needs a database where `commit()` is real (phase 2's committed tier). | 38 |
| `tests/test_box_service.py:110-135` | PostgreSQL-only concurrency test (`ThreadPoolExecutor`, two sessions), skipped on SQLite today. Needs the committed tier. | 1 (unskip) |
| Literal sequence numbers | `box_no == <n>` at 9 places in `test_box_service.py`, `test_database_constraints.py`, `test_test_data_service.py`, `api/test_dashboard_api.py`, `api/test_parts_api.py`, `api/test_shopping_list_lines_api.py`, `services/test_shopping_list_line_service.py`; literal `/api/boxes/<n>` in `test_box_api.py`. SQLite numbering restarts per test (`app/services/box_service.py:53-59` computes `max+1` for SQLite); a PostgreSQL sequence does not roll back. | about 20 |

About 90 tests in 7 files depend on SQLite or a per-test app, plus about 20 literal-number asserts to rewrite. SQLite branches in app-owned code to delete: `app/services/box_service.py:53-59`, `app/models/part.py:44` (`with_variant(JSON, "sqlite")`), `alembic/versions/003_create_parts_tables.py:38` and `004_add_document_tables.py:32` (`with_variant(..., "sqlite")`). Also `frontend/tests/e2e/shopping-lists/line-deletion-undo.spec.ts:297` (comment on SQLite ID reuse) and the Playwright SQLite files (phase 6). `.kubecoder/config.yaml` preamble says "The backend suite runs on in-memory SQLite ... neither suite touches the `postgres` sidecar"; phase 12 rewrites it.

**4. Dockerfile** (`backend/Dockerfile`, 60 lines)

Template-shaped: equals the template render for `use_database` + `use_s3` (build deps, `libpq-dev`, image libs; runtime `tini netcat-openbsd libmagic1 libjpeg62-turbo libpng16-16t64 libwebp7 libwebpmux3 libwebpdemux2 libpq5`; `DATA_PATH=/app/data`; `FLASK_ENV=production`; `EXPOSE 3001`). One difference: `poetry install --no-root --no-interaction --no-ansi` without `--only main`, so the image carries dev dependencies. App-owned. The runtime layer equals `modern-app-backend`, so phase 12 swaps the base cleanly.

**5. Deploy repo**

`https://github.com/pvginkel/ElectronicsInventoryDeploy`. Values: `config/prd/values.yaml`. Env: `chart/templates/app-deployment.yaml`, container `electronics-inventory-app` (`env:` at `:72`) and init container `electronics-inventory-setup` (`env:` at `:38`).

Current env, app container: `TIMEZONE`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DATABASE_URL`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `OPENAI_API_KEY`, `DRAIN_AUTH_KEY`, `SSE_CALLBACK_SECRET`, `MOUSER_SEARCH_API_KEY`, `BASEURL`, `OIDC_ENABLED`, `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_TOKEN_URL`, `SECRET_KEY`. Init container: `DB_*`, `DATABASE_URL`, `SECRET_KEY`. `FLASK_ENV` is not set (image default). `global.environment: prd` exists. Public host `parts.ginbov.nl`.

**6. Gates**

| Verb | Command |
|---|---|
| root setup / lint | `cexec modern-app poetry install --no-interaction` / `poetry run ruff check scripts tools` |
| backend setup | poetry install; writes `backend/.env` and `.env.test` if missing (Postgres `localhost:5432/electronics_inventory`, S3 `localhost:9000`); `scripts/init-dev-database.py`; `cli upgrade-db` |
| backend test | `cd .. && cexec modern-app poetry run run-suite --suite backend` |
| backend lint | `ruff check .`; `mypy .`; `vulture ...`; `cexec aac-tools arch-validate docs/architecture/*.yaml` |
| frontend setup / build | pnpm install, `generate:api:build`, `generate:routes`, playwright chromium / install + `pnpm build` |
| frontend test | `cd .. && cexec modern-app poetry run run-suite --suite frontend` |
| frontend lint | `pnpm check`; `arch-validate` |

Playwright by hand: the same `run-suite --suite frontend`. Standing edits: `Jenkinsfile` (`modernApp.test`, `s3storage` service), root `.gitignore` (+2). `CLAUDE.md` (`:14,18`) and `docs/commands.md` name Poetry; phase 12 updates them.

### DHCPApp

Backend v0.13.2 on Poetry. Flags: use_oidc, use_sse (no database, no S3). `CLAUDE.md` lists no standing template edits. It has no deploy repo of its own: it shares `DnsmasqDeploy` with dnsmasq.

**1. Roles**

| Item | Value |
|---|---|
| `AuthService` | `container.py:71-75`: `write_role="editor"`; no `read_role`, no `admin_role` |
| `@allow_roles` / `@public` | none besides auth and testing-auth |
| `.env.example` / deploy | none (`.env.example:50` `OIDC_ENABLED=false`) |
| `read_role` unset | yes |

D2 lockout: `GET /api/dhcp/leases`, `/pools`, `/pools/usage` (`api/dhcp.py:24,35,46`) and `GET /api/tasks/<id>/status` are open to any signed-in `homelab` account. This is a read-mostly dashboard, so non-`editor` readers are the realistic users. After D2 they get 403. Unaffected: `POST /internal/notify-lease-change` (`api/internal.py:26`) is on a blueprint outside `/api`, called by dnsmasq's `dhcp-script` with no OIDC.

Operator checks (Keycloak, DHCPApp's client): which accounts sign in to `dhcp.home`; which of them lack `editor`. Decide whether DHCPApp gets a `reader` role (`read_role="reader"` in `container.py`) or keeps `editor` as its only role.

**2. `send_event` sites (D3)**

| File:line | Sends | Meant for |
|---|---|---|
| `app/api/internal.py:50` | `data_changed` with `event_type` and timestamp, `send_event(None, event_data, "data_changed", "dhcp")`, after a lease-file change | Broadcast to every connected UI. The caller is dnsmasq (no user), so the typed target must say "all connections" explicitly. |

Test: `tests/test_internal_api.py` (4 refs). No `start_task` caller.

**3. SQLite tests (S1):** not applicable, no database.

**4. Dockerfile** (`backend/Dockerfile`, 53 lines)

Template-shaped, rendered without database and S3 (no libpq, no image libs, no alembic). Runtime `tini netcat-openbsd`. Poetry. One difference: `poetry install --no-root` without `--only main`. `EXPOSE 3301`. App-owned. The app needs no libmagic or libpq, so `modern-app-backend` carries libraries it does not use; S3 accepts that.

**5. Deploy repo**

`https://github.com/pvginkel/DnsmasqDeploy`. Values: `config/prd/values.yaml`. Env: `chart/templates/dhcp-app-deployment.yaml`, container `dhcpapp-app` (`env:` at `:124`). The chart also carries dnsmasq, DNS and the management API; those containers need no change.

Current env: `TINI_SUBREAPER`, `TIMEZONE`, `ROOT_PATH`, `SSE_CALLBACK_SECRET`, `SECRET_KEY`, `BASEURL`, `OIDC_ENABLED`, `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_TOKEN_URL`. `FLASK_ENV` is not set (image default). `global.environment: prd` exists. Host `dhcp.home` (internal, TLS terminated by `nginx-prd`).

**6. Gates**

| Verb | Command |
|---|---|
| root setup / lint | `poetry install --no-interaction` / `poetry run ruff check scripts tools` |
| backend setup / test | `poetry install --no-interaction` / `poetry run pytest` |
| backend lint | `ruff check .`; `mypy .`; `vulture ...` |
| frontend setup / build / test / lint | pnpm install + playwright chromium / `pnpm build` / `pnpm playwright test` / `pnpm check` |

Playwright by hand: `cexec modern-app poetry run run-suite --suite frontend`. CI job `Dnsmasq/DHCPApp` (`project.yaml: jenkins`). Standing edits: `Jenkinsfile` only (`modernApp.test`, `services: []`). `CLAUDE.md` (`:21,27`) names Poetry and describes the deploy path through `DnsmasqDeploy` (`:36-56`).

### ZigbeeControl

Backend v0.13.2 on Poetry. Flags: use_oidc, use_sse (no database). `use_app_shell=false`. `CLAUDE.md` lists no standing template edits.

**1. Roles**

| Item | Value |
|---|---|
| `AuthService` | `container.py:77-81`: `write_role="editor"`; no `read_role`, no `admin_role` |
| `@allow_roles` / `@public` | none besides auth and testing-auth |
| `.env.example` / deploy | none (`.env.example:50` has `OIDC_ENABLED=true`) |
| `read_role` unset | yes |

D2 lockout: `GET /api/config` (`api/config.py:19`, the tab list the UI needs to render at all) and `GET /api/tasks/<id>/status` are open to any signed-in `homelab` account. `POST /api/restart/<idx>` (`api/restart.py:20`) already needs `editor`. After D2 a signed-in account without `editor` gets 403 on `/api/config` and sees no tabs. The app is on the public host `z2m.webathome.org`. Operator checks (Keycloak, ZigbeeControl's client): who signs in (name them) and which of them lack `editor`.

**2. `send_event` sites (D3)**

| File:line | Sends | Meant for |
|---|---|---|
| `app/services/tab_status_service.py:34` | `tab_status` with `tab_index`, `state`, `message`: `send_event(None, ..., "tab_status", "status")` from `emit()` | Broadcast to every connected UI. Callers: `kubernetes_service.py:90,116,130,140` (rollout status), `api/testing_tabs.py:43`. |
| `app/services/tab_status_service.py:40` | `tab_status` for every tab: `send_event(request_id, ...)` from `_on_client_connect` (`register_on_connect`, `:23`) | The one connection that just connected. A targeted send; depends on the connect-callback signature that BE-T11/T12 touch. |

Test: `tests/services/test_tab_status_service.py` (5 refs). No `start_task` caller.

**3. SQLite tests (S1):** not applicable.

**4. Dockerfile** (`backend/Dockerfile`, 53 lines)

Same as DHCPApp's: the template's render without database and S3, Poetry, `poetry install --no-root` without `--only main`, runtime `tini netcat-openbsd`, `EXPOSE 3201`. App-owned.

**5. Deploy repo**

`https://github.com/pvginkel/Zigbee2mqttDeploy`. Values: `config/prd/values.yaml` (a snapshot of the last HelmCharts deploy, comments dropped). Env: `chart/templates/app-deployment.yaml`, container `zigbee-control-app` (`env:` at `:25`).

Current env: `TIMEZONE`, `APP_TABS_CONFIG`, `SSE_CALLBACK_SECRET`, `SECRET_KEY`, `BASEURL`, `OIDC_ENABLED`, `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_TOKEN_URL`, `OIDC_COOKIE_SAMESITE`, `OIDC_COOKIE_PARTITIONED`. `FLASK_ENV` is not set (image default). `global.environment: prd` exists. Public host `z2m.webathome.org`.

**6. Gates**

As DHCPApp, plus: backend setup writes `backend/.env` with `APP_TABS_CONFIG=test/tabs.yaml`; frontend setup writes `frontend/.env` with `APP_TABS_CONFIG=../backend/test/tabs.yaml`. CI job `ZigbeeControl`. Playwright by hand: `cexec modern-app poetry run run-suite --suite frontend`. Standing edits: `Jenkinsfile` (`modernApp.test`, `services: []`), root `.gitignore` (+1). `CLAUDE.md` (`:14,28,31`) names Poetry; phase 14 updates it.

### FieldnotesApp

Backend v0.13.2 base, **uv** (workspace). Flags: use_oidc, use_sse. `use_app_shell=false`. Own deploy repo.

**1. Roles**

| Item | Value |
|---|---|
| `AuthService` | `container.py:74`: `write_role="editor"`; no `read_role`, no `admin_role` |
| `@allow_roles(EDITOR)` | `api/triage.py:100,112,130,148,165,177`; `api/inbox.py:73,86,106,123` |
| `@public` | `api/fieldnotes.py:182,195,208,223,240,252,269,301,338` (agent API, bearer-checked in the handler; the three `hooks/*` verify their own secrets), auth and testing-auth |
| `.env.example` / deploy | none |
| `read_role` unset | yes |

D2 lockout: low. Every human-facing endpoint is already `@allow_roles(EDITOR)`, a complete override that a read tier does not change (`docs/design.md:425-427`). The one endpoint left on the read tier is `GET /api/tasks/<id>/status` (`api/tasks.py:20`), which the UI polls for inbox and actioner tasks. A signed-in account without `editor` loses only that, and cannot use the UI anyway. Operator check: who holds `editor` on the Fieldnotes client; confirm no second account needs the UI.

**2. `send_event` and task sites (D3)**

No app-owned `send_event`. Task starts and identity binding:

| File:line | Sends | Meant for |
|---|---|---|
| `app/fieldnotes/actioner.py:491` | `tasks.start_task(_Start(self))`, no `caller_subject` | A system-level actioner run. Its task events broadcast to every connection today. The UI reads actioner state from `GET /api/triage/actioner`, so the events have no single recipient; the typed target needs a decision in phase 15 (broadcast, or none). |
| `app/fieldnotes/inbox.py:522` | `tasks.start_task(follow, caller_subject=subject)` (begin a sitting) | The editor who started the sitting. |
| `app/fieldnotes/inbox.py:554` | same (a turn) | The editor who sent the turn. |
| `app/fieldnotes/inbox.py:671` | `start_task(follow, caller_subject=current.subject)` (a follower takes over) | The sitting's owner, not the request's caller. |
| `app/api/oidc_hooks.py:137-139` | `sse_connection_manager.bind_unbound_identity(request_id, subject)` | Not a send. Binds an SSE connection to a user from the `X-SSE-Request-Id` header (FN-38). |

Tests: `tests/test_sse_identity.py` (2 refs; patches `_send_event_to_token`), `tests/fieldnotes/test_actioner_follow.py` (1), `tests/fieldnotes/test_inbox.py` (4).

**FieldnotesApp carries its own SSE identity code in template-owned files**, not named in `CLAUDE.md` (commits `34f6d65`, `169ecfb`): backend `app/api/oidc_hooks.py` (+41/-8), `app/services/sse_connection_manager.py` (+24, `bind_unbound_identity` at `:316`; the only app copy of a non-Jinja file that differs from the template); frontend `src/contexts/sse-context-provider.tsx` (+5/-2), `src/lib/utils/random.ts` (+11/-3), `src/workers/sse-worker.ts` (+2/-10). BE-T10/T11 and FE15/FE16 overlap them. A `copier update` conflicts on all five; plan correction 10 settles it: phase 15 checks that BE-T11 makes it redundant and drops it, or keeps it as a listed standing edit.

**3. SQLite tests (S1):** not applicable, no database.

**4. Dockerfile** (`backend/Dockerfile`, 62 lines)

The template's shape moved to uv (`pip install uv`, `uv sync --locked --no-dev --no-install-project --no-editable`, `UV_PYTHON_DOWNLOADS=never`, `UV_LINK_MODE=copy`), customised for the workspace: it copies `pyproject.toml uv.lock`, `packages/`, `mcp-server/` and `eval/pyproject.toml` into the build stage. Runtime adds `git` and `ca-certificates` to `tini netcat-openbsd` (the store is a real git checkout). `EXPOSE 3401`. No libpq or libmagic. App-owned. Moving to `modern-app-backend` leaves `git`/`ca-certificates` as an app layer on top; it also needs a uv-ready build image (phase 8).

**5. Deploy repo**

`https://github.com/pvginkel/FieldnotesDeploy`. Values: `config/prd/values.yaml` (snapshot). Env: `chart/templates/app-deployment.yaml`, container `app` (`env:` at `:39`, then `{{- include "fieldnotes.apiEnv" . }}` at `:80` from `chart/templates/_fieldnotes_env.tpl`). Container `mcp` (`:121`, `args: ["fieldnotes-mcp"]`) uses the same image but is not the Flask app, so it needs no `STAGE`.

Current env, app container: `TIMEZONE`, `SECRET_KEY`, `DRAIN_AUTH_KEY`, `SSE_CALLBACK_SECRET`, `BASEURL`, `OIDC_ENABLED`, `OIDC_ISSUER_URL`, `OIDC_TOKEN_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `FIELDNOTES_STORE_DIR`, `FIELDNOTES_CACHE_DIR`, plus the helper's `FIELDNOTES_STORE_URL/BRANCH/TOKEN`, `FIELDNOTES_MODELS_URL`, `FIELDNOTES_EMBED_MODEL`, `FIELDNOTES_MATCH_*`, `FIELDNOTES_GITHUB_*`, `FIELDNOTES_YOUTRACK_*`, `FIELDNOTES_KUBECODER_*`. `FLASK_ENV` is not set (image default). `global.environment: prd` exists. Hosts `fieldnotes.home`, `fieldnotes-api.home`, `fieldnotes-mcp.home`; `fieldnotes-hooks.webathome.org` is public.

**6. Gates**

| Verb | Command |
|---|---|
| root setup | `cexec modern-app uv sync --locked`; `scripts/dev-instance-setup.sh` |
| root lint | `uv run ruff check scripts tools` |
| backend setup / test | `uv sync --locked` / `uv run pytest` |
| backend lint | `ruff check .`; `ruff format --check .`; `mypy .`; `vulture ...` |
| frontend | as DHCPApp (`pnpm playwright test`) |

No `jenkins:` key in `project.yaml`. Playwright by hand: `cexec modern-app uv run run-suite --suite frontend`. **Standing edits to reconcile** (documented, `CLAUDE.md:100-103`): `Jenkinsfile`, `tools/suite_runner/local.py`, `Procfile.dev`, `scripts/dev.py`, `backend/scripts/dev-server.sh`, `backend/scripts/testing-server.sh` (uv; resolve to the uv side until phase 1 makes the template uv, then the edits drop). **Not documented:** `backend/.gitignore` (+3, eval harness) and the five SSE files above. The `CLAUDE.md` sentence "The template takes uv on later" is the one phase 15 deletes.

### PilotApp

Backend v0.13.3 base, **uv**. Flags: use_database, use_oidc, use_sse. `use_app_shell=false`. Own deploy repo.

**1. Roles**

| Item | Value |
|---|---|
| `AuthService` | `container.py:75-77`: `read_role="editor"`, `write_role="editor"`; no `admin_role` |
| `@allow_roles` / `@public` | none besides auth and testing-auth |
| `.env.example` / deploy | none |
| `read_role` unset | **no** (set to `editor`) |

D2 lockout: **none.** Every endpoint on the API blueprint already needs `editor`, reads included (`docs/sign-in.md:14`), and the SSE connect callback already refuses an account without it. `tests/test_editor_gate.py` (6 tests) and `tests/test_sse_callback.py:107-134` cover roles `[]`, `["admin"]`, `["reader"]` giving 403. Operator check: that `editor` is a client role of `pilot-app` (the doc says so) and who holds it. `pilot.ginbov.nl` is public; the client registers `https://pilot.ginbov.nl/api/auth/callback`.

**2. `send_event` sites (D3)**

No app-owned `send_event`, no app-owned `start_task`, no domain SSE events yet (`app/models/` holds `__init__.py` only; `app/api/` holds only template files). The one caller is a test: `tests/test_editor_gate.py:36` `task_service().start_task(task)` with no `caller_subject`.

**PilotApp carries its own SSE refusal code in template-owned files** (commits `3f84260`, `8b8cf41`; described in `docs/sign-in.md`, not among the four edits `CLAUDE.md` names): backend `app/api/sse.py` (+99/-49: the connect callback answers 401/403), `app/api/testing_auth.py` (+28, `POST /api/testing/sse/force-callback-error`), `app/schemas/testing_auth.py` (+28/-1), `app/services/testing_service.py` (+24); frontend `src/contexts/sse-context-provider.tsx` (+117/-5), `src/workers/sse-worker.ts` (+102/-2), `src/types/playwright-binding.d.ts` (+3). This is BE-T11 and FE16 built in the app. Phases 5 and 7 build the template version; phase 16 drops these edits and keeps or rewrites the app's `tests/test_sse_callback.py` and `frontend/tests/infrastructure/sse/sse-connect-refusal.spec.ts` to match what the template ships. Expect `copier update` to conflict on all seven files.

**3. SQLite / per-test-app tests (S1)**

PilotApp's runtime (dev stack, deploy) is on PostgreSQL, but its tests are not. Nothing in `docs/pilotapp_database_testing_design.md` is implemented in `/work/PilotApp`. `tests/conftest.py` is 9 lines that import `tests/conftest_infrastructure.py`, and that file is the unmodified template v0.13.3 SQLite file (`git log`: one commit, `c58ca33`, the generation). It uses in-memory `sqlite3`, `StaticPool`, a session-scoped `template_connection`, a per-test `backup()` clone (`:122-184`), `oidc_app` the same way (`:348-404`) and an autouse Prometheus registry clear. None of the design's parts exist: no per-run PostgreSQL database, no `TEST_DATABASE_ADMIN_URL`, no session-scoped app, no savepoint session, no extra-app tier, no drift or migration tests, no sweep. There are no models and no revision, so slice 002, which the design puts first, has not landed. `PilotAppSpecs` is not checked out here (`/work/PilotAppSpecs` is absent).

The template's phase 2 will own the design, so phase 16's conftest work is `copier update` plus keeping `tests/conftest.py` at its 9 lines. Design §4.8 says pytest needs no template-owned edit and Playwright does (`global-setup.ts`, `fixtures-infrastructure.ts`, `process/servers.ts`, `playwright.config.ts`, `testing-server.sh`). None of those Playwright edits exist yet either, so `CLAUDE.md` does not list them.

Test files: 5 (`test_access_log.py` 3, `test_cli.py` 2, `test_editor_gate.py` 6, `test_smoke.py` 1, `test_sse_callback.py` 15), 27 tests; 9 take `app`/`client`/`oidc_client` directly. None names SQLite. `tests/test_cli.py` sets `SQLALCHEMY_DATABASE_URI` on the app to a fake PostgreSQL URL and monkeypatches `check_db_connection`, so it works on any session app. SQLite remains in template-owned files only: `scripts/initialize-sqlite-database.sh` (edited for uv), `scripts/init-dev-database.py`, `testing-server.sh`, `app/config.py`, `app/database.py`, `app/services/metrics_service.py`, and three Playwright support files.

**4. Dockerfile** (`backend/Dockerfile`, 58 lines)

The template's render for `use_database` without S3, moved to uv: `pip install uv`, `uv sync --locked --no-dev --no-install-project`, `UV_PYTHON_DOWNLOADS=never`, `UV_LINK_MODE=copy`; build deps include `libpq-dev`; runtime `tini netcat-openbsd libpq5`; copies `alembic.ini` and `alembic`. `EXPOSE 3501`, `FLASK_ENV=production`. The nearest of the six to what phase 1 makes the template default. App-owned.

**5. Deploy repo**

`https://github.com/pvginkel/PilotDeploy`. Values: `config/prd/values.yaml`. Env: `chart/templates/deployment.yaml`, container `backend` (`env:` at `:74`) and init container `migrate` (`env:` at `:43`, runs `python -m app.cli upgrade-db`). `tests/render-chart.py` renders the chart as Argo does and checks the values; update it with the env change.

Current env, backend: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DATABASE_URL`, `SECRET_KEY`, `DRAIN_AUTH_KEY`, `SSE_CALLBACK_SECRET`, `BASEURL`, `OIDC_ENABLED`, `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`. Init container: `DB_*`, `DATABASE_URL`, `SECRET_KEY`. `FLASK_ENV` is not set; the chart comment at `deployment.yaml:38` relies on the image's `FLASK_ENV=production`. `global.environment` is **not** in this values file; `render-chart.py:32` fixes `STAGE = "prd"` for its own use, so add `STAGE` as a literal. Public host `pilot.ginbov.nl` (`publicHost`).

**6. Gates**

| Verb | Command |
|---|---|
| root setup | `cexec modern-app uv sync --locked` |
| root lint | `uv run ruff check scripts tools`; `cexec aac-tools arch-validate docs/architecture/*.yaml` |
| backend setup | `uv sync --locked`; writes `.env` (`postgresql+psycopg://postgres:postgres@localhost:5432/pilot`); `uv run python scripts/init-dev-database.py`; `uv run cli upgrade-db` |
| backend test | `uv run pytest` |
| backend lint | `ruff check .`; `ruff format --check .`; `mypy .`; `vulture ...` |
| frontend | `pnpm playwright test` (as DHCPApp) |

Playwright by hand: `cexec modern-app uv run run-suite --suite frontend`. `Jenkinsfile`: `modernApp.test(job: 'pilot-validation', install: 'uv sync --locked --no-dev', run: 'uv run --no-sync', suites: ['backend','frontend'], services: [], ...)`; S1 adds the `postgres` service here. **Standing edits to reconcile** (`CLAUDE.md:58-68`): uv in `tools/suite_runner/local.py`, `Procfile.dev`, `scripts/dev.py`, `scripts/regenerate-openapi.py`, the backend `Dockerfile` and scripts (`dev-server.sh`, `testing-server.sh`, `initialize-sqlite-database.sh`); `backend/alembic/env.py` (+4/-1, keeps app loggers in-process); `backend/app/cli.py` (+7/-2, masks the password in the printed URL, MAT-13); the `Jenkinsfile`. **Not documented in `CLAUDE.md`:** the seven SSE files in point 2. `tests/test_cli.py` pins the `cli.py` mask, so if MAT-13 lands in the template the test stays and the edit drops.

### Across the apps

| App | read_role unset | Lockout risk (D2) | send_event sites | SQLite-dependent tests | Dockerfile | Deploy repo | Values file for env |
|---|---|---|---|---|---|---|---|
| IoTSupport | yes (`write_role=editor`, `additional_roles=[pipeline]`) | Medium: every domain GET is open to any signed-in account today and needs `editor` after | 2 app-owned (`device_log_stream_service.py:297` targeted, `rotation_nudge_service.py:56` broadcast) | 57 tests in 2 files with their own SQLite `testing_app`; the `test_settings` override (`conftest.py:33`) and the template fixtures affect all 697 | Custom, short; Poetry; no libpq/libmagic | `pvginkel/IotDeploy` | Env in `chart/templates/_iotsupport.tpl` (helper, 3 users); values `config/prd/values.yaml`; `FLASK_ENV=db` on the init container |
| ElectronicsInventory | no (`reader`/`editor`/`admin`) | None: already 403 without a role | 0 `send_event`; 2 `start_task` without caller (`ai_parts.py:124,258`) | About 90 tests in 7 files, plus about 20 literal sequence-number asserts and 1 PG-only test to unskip (1146 tests total) | Template-shaped; Poetry; installs dev deps | `pvginkel/ElectronicsInventoryDeploy` | `chart/templates/app-deployment.yaml:72`; values `config/prd/values.yaml` |
| DHCPApp | yes (`write_role=editor`) | Medium: lease and pool dashboard GETs open to any signed-in account | 1 broadcast (`internal.py:50`) | n/a (no database) | Template-shaped, no db/S3; Poetry; dev deps | `pvginkel/DnsmasqDeploy` | `chart/templates/dhcp-app-deployment.yaml:124`; values `config/prd/values.yaml` |
| ZigbeeControl | yes (`write_role=editor`) | Medium: `GET /api/config` (the tab list) open to any signed-in account | 2 (`tab_status_service.py:34` broadcast, `:40` to the connecting client) | n/a | As DHCPApp | `pvginkel/Zigbee2mqttDeploy` | `chart/templates/app-deployment.yaml:25`; values `config/prd/values.yaml` |
| FieldnotesApp | yes (`write_role=editor`) | Low: all human endpoints already `@allow_roles(EDITOR)`; only `GET /api/tasks/<id>/status` changes | 0 `send_event`; 4 `start_task` (`actioner.py:491` no caller; `inbox.py:522,554,671` with caller); 1 identity bind (`oidc_hooks.py:139`) | n/a | uv; workspace members; adds `git`, `ca-certificates` | `pvginkel/FieldnotesDeploy` | `chart/templates/app-deployment.yaml:39` plus helper `_fieldnotes_env.tpl`; values `config/prd/values.yaml` |
| PilotApp | no (`editor` for read and write) | None: all endpoints and the SSE callback already need `editor` | 0 (no domain events yet; one test `start_task` without caller) | 9 of 27 tests use the SQLite app fixtures; the suite sits on the template's SQLite conftest (design not implemented) | uv; database, no S3; `libpq5` | `pvginkel/PilotDeploy` | `chart/templates/deployment.yaml:74` (init `:43`); values `config/prd/values.yaml` (no `global.environment`) |

Totals: 5 app-owned `send_event` calls (IoT 2, DHCPApp 1, ZigbeeControl 2); 6 app-owned `start_task` calls (EI 2, FieldnotesApp 4); 1 identity bind (FieldnotesApp). Template-owned sites arrive with `copier update` in every app. SQLite-dependent tests: 57 (IoT) + about 90 (EI) + 9 (PilotApp, plus its whole-suite template conftest) = about 156, plus EI's about 20 literal-number asserts.

**Open, and who answers** (Keycloak holds the role data; no repo has it):

1. IoTSupport, DHCPApp, ZigbeeControl: for each app's Keycloak client in realm `homelab`, list the accounts that sign in and which of them lack `editor`. Those lose read access under D2. Per app, decide: grant `editor`, add a `reader` role (`read_role` in `container.py`), or accept the lockout.
2. Whether `editor` (and `reader`, `admin`, `pipeline`) is a realm role shared across apps or a client role of each app's client. This decides whether granting `editor` for one app grants it for another.
3. IoTSupport's `pipeline` accounts: answered. `pipeline` is a configured role, so D2 changes nothing for them.
4. `HOMELAB_INTERNAL=true` on the public hosts (IoTSupport, EI, ZigbeeControl, PilotApp; FieldnotesApp's webhook host): confirm showing exception text there is intended.
5. PilotApp slice 002 state (the spec repo is not in this environment): confirm no model or revision is in flight before phase 16 replaces the test conftest.
6. FieldnotesApp and PilotApp SSE edits: settled by plan correction 10.

## 6. Infrastructure

### 1. The `modern-app-*` images

Evidence: registry `http://registry:5000/v2/<image>/manifests/latest` and config blobs (read-only from here); sources `/work/scratch/DockerImages/modern-app-backend/Dockerfile`, `modern-app-backend-build/Dockerfile`, `modern-app-frontend-build/Dockerfile`.

| Image | Base | Contains | Not contained |
|---|---|---|---|
| `registry:5000/modern-app-backend` (runtime) | `python:3.13-slim` (3.13.14) | `tini`, `netcat-openbsd`, `libmagic1`, `libjpeg62-turbo`, `libpng16-16t64`, `libwebp7`, `libwebpmux3`, `libwebpdemux2`, `libpq5` | no Poetry, no uv |
| `registry:5000/modern-app-backend-build` | `python:3.13-slim` (3.13.14) | `curl`, `ca-certificates`, `build-essential`, `libffi-dev`, `libssl-dev`, `pkg-config`, `zlib1g-dev`, `libjpeg-dev`, `libpng-dev`, `libwebp-dev`, `libpq-dev`; `pip install poetry` (latest at build time); env `POETRY_HOME=/opt/poetry`, `POETRY_VIRTUALENVS_IN_PROJECT=1`, `POETRY_VIRTUALENVS_CREATE=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1` | **no uv**; no `tini`, `libmagic`, `libpq5` (runtime image only) |
| `registry:5000/modern-app-frontend-build` | `node:lts-slim` (Node 24.16.0) | `curl`, `ca-certificates`, `corepack enable && corepack prepare pnpm@latest --activate` (pnpm version is whatever was latest at build time; not recorded in the image env) | no Playwright (`tar` and `sha256sum` come with Debian slim) |

Tags in the registry: `latest`, `2032`, `2095` for all three (DockerImages build numbers). The latest was built 2026-06-17 (build 2095). Each has `version-poller.json` with `{"schedule": "0 2 * * 1"}`.

Where they are built: `pvginkel/DockerImages` (private), folders `modern-app-backend`, `modern-app-backend-build`, `modern-app-frontend-build`, built by the Jenkins job `DockerImages` (https://jenkins.webathome.org/job/DockerImages/, `Jenkinsfile` at the repo root, kaniko, last build 2632 green). A push that changes a folder rebuilds that image and every image built on top of it. `AaC/DockerImages` is its architecture producer. Commits: `38a451e` "Added base images for Modern App apps", `b50aea3` "Added scheduled to all modern app images".

Who uses them: only DA (`/work/scratch/DesignAssistant/backend/Dockerfile`: `FROM registry:5000/modern-app-backend-build` and `FROM registry:5000/modern-app-backend`; `frontend/Dockerfile`: `FROM registry:5000/modern-app-frontend-build`). None of the six apps and none of the backend/frontend templates use them; all use `python:3.13-slim` (backend, with inline `apt-get` and, for Poetry apps, `pip install poetry`; PilotApp and FieldnotesApp `pip install uv`) and `node:lts-slim` plus `corepack ... pnpm@latest` in the frontend `Dockerfile`s, and `nginx:alpine` for the final stage.

**Not uv-ready.** `modern-app-backend-build` has Poetry and no uv. `modern-app-backend` needs no change (uv is a build-time tool; the runtime stage only copies `.venv`). Phase 8 change, in a `/work/scratch/DockerImages` clone (committed, not pushed), in `modern-app-backend-build/Dockerfile`:

- Add uv, pinned: `COPY --from=ghcr.io/astral-sh/uv:<version> /uv /uvx /bin/` (DevGuides' Dockerfile uses `uv:0.13.1`; `kube-coder-modern-app-toolchain` installs the current uv with the astral installer; pick the version phase 1 settles on).
- Set `UV_PYTHON_DOWNLOADS=never` (or `UV_PYTHON_PREFERENCE=only-system`) and `UV_LINK_MODE=copy`, as the apps' Dockerfiles do.
- Drop `pip install poetry` and the four `POETRY_*` env lines. Nothing else uses the image (DA is archived and not synced), so removing Poetry breaks no one. If the operator wants DA to keep building, keep Poetry too.
- The `apt-get` block stays.

The apps' backend `Dockerfile` then becomes, for uv: `FROM registry:5000/modern-app-backend-build AS build`; `COPY pyproject.toml uv.lock`; `RUN uv sync --locked --no-dev --no-install-project`; source; `FROM registry:5000/modern-app-backend`; the same `COPY --from=build` and `ENTRYPOINT ["tini", "--"]` as today. `modern-app-frontend-build` needs no change for pnpm and already has `curl` for the cache.

**Ordering risk for phase 17 (the push):** every app Dockerfile that is moved to `modern-app-backend-build` fails its first Jenkins build (`uv: not found`) unless the DockerImages change is pushed and its job has built it first. Push DockerImages before the apps, and check `latest` in the registry has uv. The registry images have not been rebuilt since 2026-06-17, so the operator should also confirm that a DockerImages build of `modern-app-backend-build` actually runs (the job rebuilds only changed folders and their dependents).

### 2. The pnpm build cache (RT05)

What DA did (`/work/scratch/DesignAssistant`): `scripts/build-cache-get.sh` and `build-cache-put.sh` (POSIX sh; args `<prefix> <lockfile> <path>`; key `<prefix>-<sha256 of lockfile>.tgz`; `curl -f` GET, or `curl -T -` PUT of a tar of the pnpm store). `tools/suite_runner/local.py` (`--build-cache`, `CACHE_KEY = "design-assistant"`): restores the store before `pnpm install`, uploads it on a miss. `frontend/Dockerfile`: `COPY scripts/build-cache-get.sh`, then `scripts/build-cache-get.sh design-assistant pnpm-lock.yaml "$(pnpm store path)" || true` before `pnpm install --frozen-lockfile`. DA's Jenkinsfile passes `--build-cache` to `run-suite`.

The service: nginx with WebDAV `PUT`, directory `/var/build-cache` on a PVC, in the Jenkins chart `pvginkel/HomelabAppsDeploy` (`/work/scratch/HomelabAppsDeploy/jenkins/chart/`): `templates/build-cache-{deployment,service,pvc,cronjob,configmap}.yaml`, `files/nginx/nginx.conf`, Terraform volume `jenkins/terraform/main.tf`. URL: `http://build-cache.jenkins-prd.svc.cluster.local` (port 80, ClusterIP; `/health` returns 200). A cronjob `build-cache-cleanup` deletes files older than 14 days daily at 03:00. The canonical copies of the two scripts live in the chart: `jenkins/chart/scripts/build-cache-{get,put}.sh` (identical to DA's, with tests in `scripts/test/`). Neither the library nor the shared images carry them. Checked from this environment: the URL resolves and answers 200; the cache is currently empty (DA is archived, 14-day TTL).

Use in CI and image builds:

- **Validation Job:** the Job runs in the Jenkins namespace, so the default URL works. Phase 8 adds the two scripts to the root template's `scripts/` (copy of the chart's), a `--build-cache` option and an env switch to the suite runner (`local.py.jinja`), as above. Cache prefix: the key is content-addressed by the lockfile hash, so a fixed prefix (for example `pnpm`) is safe; DA's per-app prefix is not needed. If kept per app, use `{{ project_name }}`.
- **Image builds:** `kaniko2` runs the build in a kaniko container of the same agent pod, so the Dockerfile's `RUN` can reach the service (DA does). Restore inside the frontend `Dockerfile` with `|| true` so a miss is non-fatal. The upload does not happen in the image build (nothing is pushed from there); the CI validation run does the upload on a miss, from the same lockfile, so image builds are hits afterwards. The pnpm store path must match: both use `pnpm store path` of the same pnpm major. Keep the image's pnpm and the toolchain's in step (both `latest`).
- Context: the template `Jenkinsfile` builds the frontend with `context: 'frontend'`, so a root `scripts/` is out of reach; inline the restore in the `Dockerfile` (`curl -sSf "$BUILD_CACHE_URL/pnpm-$(sha256sum pnpm-lock.yaml | cut -d' ' -f1).tgz" | tar -xzf - -C "$(pnpm store path)" || true`), and make sure it runs after `COPY package.json pnpm-lock.yaml` and before `pnpm install`.
- Also usable for uv: the inventory suggests a Poetry/venv cache; with uv the project cache is not needed, `uv sync` from the Job is fast. Leave it out.
- Not reachable? Unknown from a kaniko pod outside `jenkins-prd`: all Jenkins agents run in that namespace, so reachable. If the operator ever moves agents, `BUILD_CACHE_URL` is the override (`ARG`/env).

### 3. How DevGuides merges a guide from another repo

Evidence: `/work/scratch/DevGuides` (README, `sources.txt`, `Jenkinsfile`, `Dockerfile`, `tools/build_hub.py`, `tools/check_guide.py`, `tools/stage_context.py`, `.kubecoder/project.yaml`) and the `kubecoder:dev-guides` skill.

Mechanism: no submodule, no manifest beyond one list. A checkout at build time, side by side:

1. `sources.txt` lists the source repos by GitHub name (`DevGuides`, `DevGuidesPrivate`, `JenkinsPipelineUtils`).
2. `DevGuides/Jenkinsfile`, stage `Checkout`: `dir('DevGuides') { checkout scm }`, then one `dir('<Repo>') { git url: 'https://github.com/pvginkel/<Repo>.git', branch: 'main', credentialsId: '5f6fbd66-b41c-405f-b107-85ba6fd97f10' }` per other repo. Those clones are why a push to a source repo starts the `DevGuides` job: the source repos have no job of their own.
3. `DevGuides/Dockerfile`: `COPY . /src` of the workspace, then `uv run DevGuides/tools/build_hub.py /src`, which builds and checks every guide of every source repo (`tools/check_guide.py`), assembles `out/<path>/`, the index and the root `llms.txt`, and fails on any broken guide. nginx serves `out/`. The Jenkinsfile builds the image `registry:5000/dev-guides-home` and pins it into `pvginkel/DevGuidesDeploy`.
4. A guide is found by its `mkdocs.yml` in a top-level folder of a source repo. JenkinsPipelineUtils' guide is `docs/` there (`docs/mkdocs.yml`, `pyproject.toml`, `uv.lock`, `check_site.py`, `pages/`, `examples/`; `site_url: https://dev-guides.home/pipelines/`).

**Adding `pvginkel/ModernAppTemplate` as a source repo takes two edits in one DevGuides commit** (`kubecoder:dev-guides`): `ModernAppTemplate` on a line in `sources.txt`, and a `dir('ModernAppTemplate') { git url: 'https://github.com/pvginkel/ModernAppTemplate.git', branch: 'main', credentialsId: '5f6fbd66-b41c-405f-b107-85ba6fd97f10' }` clone in the `Checkout` stage. `kc project test` in DevGuides runs the hub over `/work`, so it expects `/work/ModernAppTemplate` (it exists in this environment's layout). `kc project build` stages `/work` through `stage_context.py` (git-ignored files such as `backend/`, `frontend/` and `root/test-app/` are excluded because they are gitignored in this repo). Note the Jenkins clone of ModernAppTemplate is the parent repo only (no `backend/`, `frontend/` checkouts), which is all the guide needs. The operator must push DevGuides, ModernAppTemplate and then wait for the `DevGuides` job (build 5 is the last run).

**What this repo must provide** (the contract, `check_guide.py` items 1-9):

- A new top-level folder with its own `mkdocs.yml`. `docs/` already holds the port's working documents, not a guide; use a distinct name (for example `conventions/`; the folder name is free). No `mkdocs.yml` at the repo root.
- `site_url: https://dev-guides.home/<one-segment>/` (for example `.../conventions/`), unique across the hub; `site_name` and `site_description` (the index card and the root `llms.txt` line).
- Toolchain in the folder: `pyproject.toml` and `uv.lock` with Zensical; builds with `uv run --locked zensical build --strict` into `site/`. Paths in the config relative to the guide's folder; no `!relative`.
- The `llmstxt` plugin with `full_output: llms-full.txt` and one section pattern `"*.md"`.
- Every page in the nav, every nav entry a real page, no root-absolute link; real files, no directory symlinks in `docs_dir`.
- Nav row `- Dev guides: https://dev-guides.home/`.
- The light/dark `theme.palette` block (copy from `JenkinsPipelineUtils/docs/mkdocs.yml`).
- Optional `check_site.py` in the folder, run after the build with `uv run --locked python check_site.py`.
- Rules as headings with an id anchor: `### CONV-1 - Title { #conv-1 }`; never renumber or reuse an id.
- `.gitignore` entries for the guide folder's `.venv/` and `site/`.
- The repo's gate: a `kc project test` entry running `uv run https://raw.githubusercontent.com/pvginkel/DevGuides/main/tools/check_guide.py <repo-dir>` (JenkinsPipelineUtils does this in its `docs` project, `cexec iac uv run ...`; this repo's `.kubecoder/project.yaml` has no uv-capable `cexec` target set up for it yet, so choose `iac` or `modern-app`, which has uv, in phase 9). Until DevGuides' `main` carries the checker version, run it from `/work/DevGuides/tools/check_guide.py` or from the clone `/work/scratch/DevGuides`.
- A skill in KubeCoderConfig (see below). One failing guide blocks every guide's publish, so the check must be green before the operator pushes.

**Shape of the pipelines skill** (`/work/scratch/KubeCoderConfig/kubecoder/skills/jenkins-pipelines/SKILL.md`, 212 lines, 12 KB; `data-modelling` 222 lines; `dev-guides` 101):

- Frontmatter: `name:` and a multi-line `description: |` that gives the guide's URL, "its hard rules by id, and where the guide details each", then "Use whenever ..." triggers (writing, editing, reviewing a Jenkinsfile, creating a job, deciding library placement).
- Body: an intro paragraph (the guide is strict; the skill names the rules in brief and the page holds exact wording, reason and recipe; read a rule's page before writing to it); a "Reading the guide" paragraph (URLs of `llms.txt`, `llms-full.txt`, a page's Markdown copy `.../<path>/index.md`, a rule anchor `#pod-4`); "Start from the type's reference file"; "Checking a file from a KubeCoder pod" (the linter curl, what is not available, how the real check is the build); "Two files predate the guide" (exceptions); then "The hard rules", one `###` section per guide page, linked to the page's `index.md`, each a bullet list of rules by id in a short sentence, ids in parentheses, e.g. `(POD-4)`.
- It carries: rule ids, one-sentence statements, the page each lives on, the operational how-to for the environment (what can be linted here). It points at: the wording, the reasons, recipes and reference files on the site.
- Maintenance rules (`KubeCoderConfig/CLAUDE.md`): bump `version` in `kubecoder/.claude-plugin/plugin.json` in the same commit (currently 0.13.2; a new skill is a minor bump, so 0.14.0); Markdown is Prettier-formatted at 80 columns (`npm run format`; `kc project lint` runs `format:check`); no copy of catalog contents. "A rule changed in the guide is changed in its skill in the same sitting."
- Model for phase 9: a `conventions` (or the guide's name) skill, frontmatter as above, intro, "Reading the guide", then a rule list grouped by the guide's pages (RT08 status enums, RT09 toasts, RT11 UUID paths and the 2 s rule, RT13 real dependencies and preview mode, RT14 `perf_counter`/fail fast/`window.open`, BE-T17 test conventions and SSE targeting, D9a stable paging), each a bullet with its `CONV-n` id. About 60-100 lines.

### 4. How the Jenkins job for an app's `Jenkinsfile.architecture` gets created

Findings: `AaC/PilotApp` and `AaC/FieldnotesApp` exist (and `AaC/ElectronicsInventory`, `AaC/IoTSupport`, `AaC/DHCPApp`, `AaC/ZigbeeControl`; there is no `AaC/DesignAssistant`). Their `config.xml` (read via `GET /job/AaC/job/<name>/config.xml` with `JENKINS_TOKEN`) is the guide's `config.xml` template: `CpsScmFlowDefinition`, repo `https://github.com/pvginkel/<Repo>.git`, credential `5f6fbd66-b41c-405f-b107-85ba6fd97f10`, branch `*/main`, script path `Jenkinsfile.architecture`, lightweight checkout, `GitHubPushTrigger`; the job properties and `DeclarativeJobAction` came from a first build. So they were made through the Jenkins API per the guide's "A new repo" page (`NEW-1` to `NEW-3`, https://dev-guides.home/pipelines/guide/new-repo/), not by job DSL, a seed job or a chart value. Who made them is not recorded in Jenkins; PilotApp's commit `c674aec` ("slice 001 P3") and Architecture's commit `d21ad8d` ("pilot-app is published by AaC/PilotApp, PilotApp slice 001 P8") show the sequence.

What a new app needs (the guide's recipe, step 7, and the Architecture repo):

1. `Jenkinsfile.architecture` and `docs/architecture/architecture.yaml` pushed to the app repo (the template ships the file; the YAML is authored per app, §5).
2. The job `AaC/<Repo>` created through the API, `POST $JENKINS_URL/job/AaC/createItem?name=<Repo>` with the guide's `config.xml` (`scriptPath` `Jenkinsfile.architecture`). Creating it starts no build; a push (or `POST .../build`) does. Needs the Jenkins `admin` token.
3. An entry in `pvginkel/Architecture`'s `pipeline-producers.yaml`: `- id: <app-id>`, `repo: pvginkel/<Repo>`, `jenkinsJob: AaC/<Repo>`, optional `defaultLogo`. Today there are entries for `electronics-inventory`, `iotsupport-app`, `dhcpapp`, `zigbee-control`, `fieldnotes-app` and `pilot-app`.
4. A GitHub push hook for the repo; Jenkins installs it when the job is created with `GitHubPushTrigger`, so nothing by hand.
5. Optional `.architecturerc` at the app repo root (for the central update's `sources` and `instructions`; none of the existing apps has one).

Per-app state for phases 11-16: all six apps already have steps 1-4 done. Fieldnotes and Pilot have a single root model, `docs/architecture/architecture.yaml`, and a one-stage `Jenkinsfile.architecture`. The other four (ElectronicsInventory, IoTSupport, DHCPApp, ZigbeeControl) have two models, `backend/docs/architecture/` and `frontend/docs/architecture/`, and two stages (`Validate architecture (backend)`, `Validate architecture (frontend)`). So the template's `Jenkinsfile.architecture` only affects new apps, and `copier update` of the four older apps should keep their two-stage file: either make the file `_skip_if_exists` in the root `copier.yml`, or ship the one-stage file and let the four apps resolve conflicts to their side (as for `Jenkinsfile`). Recommendation: `_skip_if_exists`, since the model layout is the app's.

Operator per new app, in order: seed the model (§5), push the repo, create `AaC/<Repo>` (API, or ask for the token to be used from a session), add the producer entry to Architecture (a commit to `pvginkel/Architecture`). Nothing is needed for the existing six.

**RT06 deviation from the plan.** Phase 8 says to take `Jenkinsfile.architecture` and `scripts/arch-validate.py` from DA. DA's pipeline is the scripted one the guide has since replaced (a `python` container running `./scripts/arch-validate.py`). The estate form is PilotApp's file: declarative, `podYaml(templates: ['aac-tools'])`, `architectureProducer.validate(files: [...])` and `.archive(files: [...])`. `arch-validate` ships in the `aac-tools` image (the Architecture repo's `.claude/architecture/arch-validate.py` is "the only copy"), so the template needs **no** `scripts/arch-validate.py`. The root template's `.kubecoder/config.yaml.jinja` should add the `aac-tools` toolchain (PilotApp's `.kubecoder/project.yaml` lints with `cexec aac-tools arch-validate docs/architecture/*.yaml`; the root template's `project.yaml.jinja` has no such step). The nudge text in the generated `CLAUDE.md` should name the central architecture update (`tooling/fleet.py update`, which keeps producers current) and `/seed-architecture`, not DA's `update-architecture` agent.

### 5. Can `/seed-architecture` run in this environment

- **Defined in:** `pvginkel/Architecture`, `/work/scratch/Architecture/.claude/skills/seed-architecture/SKILL.md` (179 lines). It is a project skill of the Architecture repo and of its "kit", not a plugin skill: `KubeCoderConfig` does not carry it, and neither `AIWorkflow` nor the `kubecoder` plugin. The kit is `.claude/agents/` (`update-architecture.md`, `triage-architecture.md`), `.claude/skills/seed-architecture/` and `.claude/architecture/` (`producer-manual.md`, `architecture.yaml` starter, `arch-validate.py`). `python3 tooling/fleet.py stage <Repo>` in the Architecture repo clones a producer to `/tmp/architecture-update/repos/<Repo>` and copies the kit into its `.claude/` (listed in `.git/info/exclude`) without starting a session; the session is then started in that clone.
- **Installed here:** no. `~/.claude/skills` and `~/.claude/plugins` hold no copy; only the Architecture repo's own `.claude` has it. This environment's `.claude/` (`/work/ModernAppTemplate/.claude/agents`) has only the template-project agents.
- **What it needs:** the kit staged into the app clone's `.claude/`; the Agent tool (it fans out up to 3 Explore sub-agents; it must run in the main conversation, not in a sub-agent); a clone of the app repo; `python3` (stdlib) for the validator; HTTPS to `https://architecture.webathome.org/api/validate` (reachable from here: GET returns 404, a POST route; not tried); operator triage of candidate elements mid-run. `fleet.py stage` needs `gh`/git access, which this environment has (read-write GitHub).
- **Verdict:** it can run here by staging the kit by hand (copy `.claude/skills/seed-architecture`, `.claude/architecture` and `.claude/agents` from `/work/scratch/Architecture` into the target repo's `.claude/`, untracked), or by running `fleet.py stage` (writes under `/tmp`). It is interactive (operator triage), so it is a per-app chat, not part of phase 8. It is only needed for **new** apps; the six existing apps already have models. For phase 8, the template ships the pipeline and the `CLAUDE.md` nudge only. A new app's AaC job fails until a model exists, so the template's `CLAUDE.md` should say: seed first, then create `AaC/<Repo>`.
- **No placeholder model.** Phase 8 ships no `docs/architecture/architecture.yaml`: the starter skeleton at `Architecture/.claude/architecture/architecture.yaml` is not a valid producer without edits, and the `CLAUDE.md` nudge says to seed first.

## 7. Overlapping MAT cards

Checked 2026-10-17: every unresolved card in MAT, plus unresolved cards elsewhere that mention ModernAppTemplate or DesignAssistant.

| Card | State | What it asks | Relation to this work | Close in |
|---|---|---|---|---|
| MAT-10 | Later | Task events reach SSE connections with no bound identity: `start_task(caller_subject=None)` broadcasts, and `api/sse.py` keeps a connection whose binding failed | Closed by BE-T10 (typed `Target`, task events go to the caller) and BE-T11 (the connect callback answers 401/403). The card itself says "sync with DesignAssistant". | Phase 5 |
| MAT-13 | New, Solution Known | `cli upgrade-db` and `load-test-data` print the database URL with its password | Not a DA item, but it sits in BE-C06's area (secret redaction at boot). Fold the card's fix (`make_url(...).render_as_string(hide_password=True)`) into BE-C06. PilotApp carries the fix as a standing divergence in its template-owned `cli.py` (P-3); phase 16 drops it. | Phase 3 |
| MAT-12 | Accepted | `generate:api`'s error and `package.json` name `regenerate-openapi.py --frontend`; a test fails on a stale OpenAPI cache | Not closed by this work: no ruling takes it. It touches RT03's `regenerate-openapi.py`, so phase 8 must not undo it, and could carry it if the operator wants. | Not this work |
| MAT-8 | Later | Lift the `@playwright/test` 1.60.0 pin once 1.63+ downloads its browser here | Not closed. Phase 1's dependency bumps must keep the pin. | Not this work |
| MAT-11 | Accepted | A doc on generating a new app from another environment | Not closed. Phase 1 rewrites the copier commands in the docs; the new recipe should use them if MAT-11 is done later. | Not this work |
