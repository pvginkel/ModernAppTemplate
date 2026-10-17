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
| 1 | uv everywhere, dependency bumps | todo | |
| 2 | Backend: PostgreSQL testing | todo | |
| 3 | Backend: fixes, stages, internals fact | todo | |
| 4 | Backend: auth | todo | |
| 5 | Backend: readiness, SSE, small takes | todo | |
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
