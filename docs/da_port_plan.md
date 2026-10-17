# DesignAssistant port: delivery plan

This plan delivers every ruling in [`da_port_decisions.md`](da_port_decisions.md) as **one push**. All work is committed locally in each repo, and nothing leaves this environment until the operator approves the push at the end. That is possible because copier resolves each app's `_src_path` to the local template checkouts, so the apps can update to template tags that are not pushed yet.

## The shape

| Phase | What | Where | Ends with |
|---|---|---|---|
| 0 | Dedup and facts | read-only, all repos | `docs/da_port_worklist.md` |
| 1 | Backend template | `backend/` | commits, gates green |
| 2 | Frontend template | `frontend/` | commits, gates green |
| 3 | Root template | this repo | commits, gates green |
| 4 | Conventions guide and skill | this repo, DevGuides, KubeCoderConfig | commits |
| 5 | Release | all three templates | changelogs; tags backend v0.14.0, frontend v0.21.0, root v0.2.0 |
| 6 | Six apps | `/work/<App>` | per-app commits, each app's suite green |
| 7 | Deploy repos | six `*Deploy` repos | values commits |
| 8 | The push | everything | your go-ahead, then builds watched to green |

Each phase is one or more agents with a full brief. I review every diff myself and run the gates between steps. Phases 1 and 2 overlap where the frontend doesn't depend on backend work. Phase 6 runs one app at a time.

## Phase 0: dedup and facts

Read-only agents, run in parallel. They produce a worklist with the status of every taken item: not in the template, partly there, or already landed (for example, `after_commit()` is already in the template). They also establish these facts:

- **Root template vs DA's root** (RT01–RT04): what DA's suite runner, `dev.py`, Jenkinsfile and dev scripts have that the root template lacks.
- **The template's `Jenkinsfile` vs the estate pipeline guide.** PilotApp says the library no longer builds the template's scripted form, and has moved to `modernApp.test`. Its `services:` is also how CI gets PostgreSQL (S1).
- **Per app:**
  - which roles are configured, and whether any reader holds none (D2 could lock them out);
  - every `send_event` call site (D3 changes them);
  - app-owned tests that depend on SQLite or a per-test app (S1: ElectronicsInventory, IoTSupport, PilotApp);
  - the backend `Dockerfile` (app-owned, so S3 is a per-app edit);
  - the deploy repo and its values file.
- **Infrastructure:**
  - what `modern-app-backend`, `modern-app-backend-build` and `modern-app-frontend-build` contain (tini, libmagic, libpq, Poetry);
  - the build cache's in-cluster URL;
  - how DevGuides merges a guide from another repo (the JenkinsPipelineUtils precedent);
  - how a Jenkins job is created for `Jenkinsfile.architecture`.
- **Open MAT cards** that overlap and can close with this work (MAT-13 looks like one).

**Stop:** I come back only if a finding changes a ruling.

## Phase 1: backend template

The order matters: dependencies first, so everything after builds on them, and PostgreSQL second, so every later test runs on it.

1. **Dependency bumps** (BE-C08): Pillow 12, spectree 2, flask-cors 6, pytest 9 and ruff 0.15.
2. **PostgreSQL testing** (S1), following PilotApp's design §3.4 and §4:
   - Database setup: a per-run template database built by the revisions, the session-scoped app, and the savepoint session (real `commit()`/`rollback()`, no-op `close()`).
   - Test tiers: `committed_app` on a cloned database, the Prometheus registry cleared once, and `oidc_app` with its re-wire.
   - Hygiene: a sweep without `FORCE`, `TEST_DATABASE_ADMIN_URL`, production's locale, small pools (BE-C18), and the drift test.
   - SQLite goes: the recreate branch, `initialize-sqlite-database.sh`, and the test-only engine override.
   - `testing-server.sh` takes `--database-url` and runs through `poetry run dev` (BE-C09). The default `tests/conftest.py` for new apps follows.
3. **Fixes from D1:**
   - BE-C02, BE-C04, BE-C05 (current label set kept), BE-C06, BE-C10 and BE-C11;
   - BE-C03, if dedup shows a gap;
   - BE-T01 (with BE-C07) and BE-C16;
   - the tests BE-T04, BE-T05, BE-T14 and BE-T15.
4. **Stages and the internals fact** (D9b, S6, S4):
   - the `Stage` taxonomy and its FLASK_ENV-based default;
   - `HOMELAB_INTERNAL`, and the one fact that combines it with the stage;
   - the 500 handler, and `GET /api/ui-setup` returning the stage and the fact;
   - readyz reporting the stage, and the `prd` guards.
5. **Auth** (D2, D4, S2, D9c): BE-C01, BE-C12 with BE-T09, BE-T16 (the caller check), BE-C15 and BE-C25.
6. **Readiness** (D5): BE-C13's framework with a `critical` flag on each check, and BE-T13.
7. **SSE** (D3): typed `Target` with no implicit broadcast (BE-T10), connect-callback 401/403 plus the forced-rejection test hook (BE-T11), and BE-T12.
8. **Small takes** (D9): BE-C28; BE-C29, with its root half in Phase 3; and `apply_sorting()` with the pagination schemas (D9a).

## Phase 2: frontend template

1. **Fixes from D1:** FE01–FE14, FE17, FE18 and FE20.
2. **Playwright on PostgreSQL** (S1, PilotApp §4.6):
   - the seed database in global setup, cloned per worker through a `pg-admin.ts` (on the `pg` client);
   - a global teardown;
   - `--database-url`, and small pools.
3. **Stages in the UI:** the client for `ui-setup`, the diagnostics button on toasts (FE19), and the stage badge (FE32).
4. **SSE** (D3):
   - `ready` gating (FE15);
   - `rejected` handling with session refresh and reconnect, plus its preview-mode spec (FE16);
   - the non-blocking gate (FE27).
5. **Defaults** (D6): FE21, FE28 and FE29.
6. **Housekeeping:** `knip-template-ignore.json` follows every template-owned file added or removed.

## Phase 3: root template

1. **CI:**
   - PostgreSQL in the validation Job, plus a wait for it, and `STAGE=tst` (S1);
   - the `Jenkinsfile` aligned with the estate pipeline guide, as Phase 0 finds;
   - the build cache (RT05);
   - the frontend `Dockerfile` (template-owned) on `modern-app-frontend-build`, and the backend `Dockerfile` default on the backend base images (S3).
2. **Dev stack:** `watchmedo` restarts (BE-C29), what Phase 0 takes from DA's `dev.py` and scripts (RT03), and `STAGE=local-dev` in the seeded `.env`.
3. **Architecture producer** (D8): `Jenkinsfile.architecture`, `scripts/arch-validate.py`, and the nudge in the generated `CLAUDE.md`.
4. **Tooling:** the dependency checker (RT07), with components discovered rather than listed.
5. **Rest of the root diff:** what Phase 0 takes from RT01, RT02 and RT04.

## Phase 4: conventions guide and skill (S5)

- **The guide:**
  - Source in this repo, laid out per the dev-guides contract.
  - Contents:
    - the conventions (RT08, RT09, RT11, RT13, RT14, BE-T17);
    - the paged-list ordering rule (D9a);
    - the SSE targeting rules;
    - the test conventions and the preview-mode gotcha.
- **Hosting:** DevGuides' pipeline merges the guide in, as it does JenkinsPipelineUtils'.
- **Skill:** one in KubeCoderConfig, modelled on the pipelines skill, points at the site.

## Phase 5: release

- **Changelogs:**
  - each template repo's own;
  - one coordinated entry in this repo's `changelog.md`, with migration steps per app: PostgreSQL tests, `STAGE` and `HOMELAB_INTERNAL`, typed SSE targets, the roles check, the backend `Dockerfile`, and the architecture YAML.
- **Gates:** `kc project build`, `test` and `lint` green.
- **Tags:** backend v0.14.0, frontend v0.21.0, root v0.2.0. Each is a minor bump, because these releases break things.

## Phase 6: the six apps

**Order:**

1. IoTSupport, which is closest to the template and uses a database;
2. ElectronicsInventory (database and S3);
3. DHCPApp;
4. ZigbeeControl;
5. FieldnotesApp;
6. PilotApp.

**Per app:**

1. **`copier update`** of root, backend and frontend, one commit each, on a clean tree.
2. **App-owned follow-ups:**
   - `tests/conftest.py` on PostgreSQL (database apps);
   - the backend `Dockerfile` on the base images;
   - the `send_event` call sites on typed targets;
   - the roles check;
   - `STAGE` and `HOMELAB_INTERNAL` in `.env`, `.env.test` and `.env.example`;
   - the architecture YAML;
   - whitelist upkeep (vulture, knip).
3. **The app's full suite** green in this environment. It has the `postgres` and `s3storage` sidecars.

**The two uv apps** follow their standing rule: where a template-owned file conflicts, resolve to the uv side, keeping the template's new behaviour. The template stays on Poetry in this push.

**PilotApp goes last.** Its slice 002 plans to build PostgreSQL testing app-side. If 002 hasn't run by then, the sync gives Pilot the template's version, and 002's plan drops that work. If it has run, the sync replaces Pilot's overrides with the template's.

## Phase 7: deploy repos

In each app's deploy repo (`ElectronicsInventoryDeploy`, `IotDeploy`, `DnsmasqDeploy`, `Zigbee2mqttDeploy`, `FieldnotesDeploy`, `PilotDeploy`), set `STAGE=prd` and `HOMELAB_INTERNAL=true` in `config/prd/values.yaml`. Both are safe before the new images arrive: the old images ignore them, and the new ones default to `prd` anyway.

## Phase 8: the push

You get a per-repo summary (commits, tags, gates). After your go, everything is pushed in dependency order:

1. DevGuides and KubeCoderConfig;
2. this repo, `backend/` and `frontend/`, with their tags;
3. the deploy repos;
4. the six apps, whose pushes start their builds.

I watch the builds to green through Jenkins, and the Argo CD syncs after them.

**Where it can still need you:**

- creating the per-app architecture Jenkins jobs, depending on Phase 0's finding;
- seeding each app's `architecture.yaml`, because the `/seed-architecture` skill isn't installed in this environment.

## Risks

- **One large release.** Every app takes a big three-way merge at once. Mitigations: template commits per step, gates after each, and every app suite green before the push.
- **PostgreSQL may expose real bugs** in ElectronicsInventory and IoTSupport tests, as it did in DA. Small ones I fix in the app; a large one is a stop.
- **D2 can lock out users without a role.** Phase 0 checks every app first, and an app that relies on role-less readers is a stop.
- **Size.** This is multi-day agent work. Most of it is in Phases 1, 2 and 6. I notify you at the stops and when the push is ready.
