# ModernAppTemplate

Copier-based templates for generating self-contained monorepo applications: a root template (workspace scaffolding, CI, dev orchestration) wrapping a Flask backend and a React frontend project. Each generated project is plain Python/TypeScript with no runtime dependency on the template. Template updates via `copier update` with three-way merge.

## Repository Structure

This is the parent repo. It is itself the root template's Git root, and the backend and frontend templates have their own repos, checked out inside this directory:

```
ModernAppTemplate/                  # Parent repo (you are here) — also the root template's repo
├── CLAUDE.md                       # This file
├── copier.yml                      # Root template configuration (_subdirectory: root/template)
├── docs/                           # Shared documentation
│   ├── copier_approach.md          # Architecture, decisions, file ownership
│   ├── change_workflow.md          # How to make template changes
│   ├── downstream_sync_process.md  # How to keep apps in sync
│   └── backend_porting_guide.md    # How to port a backend app onto the template
├── guide/                          # Source of the modern app guide, https://dev-guides.home/modern-app/ (`kc project test guide` checks it)
├── root/                           # Root template source and test-app
│   ├── template/                   # Copier template source
│   ├── regen.sh                    # Root regeneration script (run after backend/frontend regens)
│   ├── test-app/                   # Generated test application (gitignored, DO NOT edit)
│   └── test-app-no-storage/        # The same with use_database=false, use_s3=false (gitignored)
├── scripts/                         # Cross-repo tooling (violation finder, test/pull/push/review-all, workspace helpers)
│   └── find_template_violations.py # Finds template drift in downstream apps
├── changelog.md                    # Coordinated changelog (all three templates)
├── backend/                        # Checkout of ModernAppBackendTemplate (NOT a submodule)
└── frontend/                       # Checkout of ModernAppFrontendTemplate (NOT a submodule)
```

`backend/` and `frontend/` are **not Git submodules** — they are separate repo checkouts listed in `.gitignore`. Copier does not understand submodules, so this arrangement keeps the template repos independent while colocating them for development. The root template lives at the parent repo's root (not in a separate checkout) because Copier versions a template by the git tags of the repository it lives in, so the root template is versioned by the parent repo's own tags (first release: v0.1.0).

Each template repo has its own `CLAUDE.md` with template-specific instructions.

## Environment

This repository runs in a KubeCoder environment.

- The three repos live at `/work/ModernAppTemplate`, with the two template repos checked out inside it at `backend/` and `frontend/` (separate git repos, not submodules), and the root template at the parent repo's own root. Git operations work in all three.
- The downstream apps (see below) are checked out at `/work/<App>`, one monorepo per app with the root layer at the repo root and the backend and frontend at `backend/` and `frontend/`.
- Language tooling lives in the `modern-app` tool container: prefix uv, `copier` and pnpm commands with `cexec modern-app`. The dev container itself has `node`, `npm`, `python3` and `git` only.
- `cexec` passes arguments through verbatim, so compound commands need a wrapper: `cexec modern-app sh -c 'cd test-app && uv sync'`.
- Curated entry points are in `.kubecoder/project.yaml`, run with `kc project setup|build|test|lint`.

## Downstream Apps

| App | Backend | Frontend | Notes |
|-----|---------|----------|-------|
| ElectronicsInventory | `/work/ElectronicsInventory/backend` | `/work/ElectronicsInventory/frontend` | Primary source for template extraction |
| IoTSupport | `/work/IoTSupport/backend` | `/work/IoTSupport/frontend` | Closest to template patterns |
| DHCPApp | `/work/DHCPApp/backend` | `/work/DHCPApp/frontend` | Synced |
| ZigbeeControl | `/work/ZigbeeControl/backend` | `/work/ZigbeeControl/frontend` | Synced; `use_app_shell=false` |
| FieldnotesApp | `/work/FieldnotesApp/backend` | `/work/FieldnotesApp/frontend` | Synced; `use_app_shell=false`; a uv workspace |
| PilotApp | `/work/PilotApp/backend` | `/work/PilotApp/frontend` | Synced; `use_app_shell=false` |

## Feature Flags (Shared Across Templates)

| Flag | Backend | Frontend | Root |
|------|---------|----------|------|
| `use_oidc` | OIDC authentication (BFF pattern with JWT cookies) | OIDC login/logout UI, token handling | (not used) |
| `use_s3` | S3 storage, CAS endpoints, image processing | (not used in frontend) | S3 sidecar in the dev environment and the CI validation Job |
| `use_sse` | Server-Sent Events: the backend serves the browser's stream (`GET /api/sse/stream`) | SSE client, real-time update components | (not used) |
| `use_database` | SQLAlchemy, Alembic, migrations | (backend only) | Postgres sidecar and database bootstrap in setup; `postgres` service in the CI validation Job |

## Key Documentation

Read these before making changes:

- **`docs/copier_approach.md`** — Architecture decisions, file ownership model, template file inventory
- **`docs/change_workflow.md`** — Step-by-step workflow for template changes
- **`docs/downstream_sync_process.md`** — How to find and fix template drift in apps

## Quick Start

### Working on the backend template
```bash
cd /work/ModernAppTemplate/backend
# Edit files in template/, then (regen.sh renders test-app and test-app-no-storage):
cexec modern-app bash regen.sh
cexec modern-app sh -c 'cd test-app && uv run pytest ../tests/ -v && uv run pytest tests/ -v'
cexec modern-app sh -c 'cd test-app-no-storage && uv run pytest tests/ -v'
```

### Working on the frontend template
```bash
cd /work/ModernAppTemplate/frontend
# Edit files in template/, then (regen.sh renders test-app and test-app-no-shell):
cexec modern-app bash regen.sh
cexec modern-app sh -c 'cd test-app && pnpm run check && pnpm run build'
cexec modern-app sh -c 'cd test-app-no-shell && pnpm run check && pnpm run build'
```

### Working on the root template
```bash
cd /work/ModernAppTemplate
# Edit files in root/template/, then (backend and frontend regens must run first;
# root/regen.sh renders root/test-app and root/test-app-no-storage):
cexec modern-app bash root/regen.sh
cexec modern-app sh -c 'cd root/test-app && uv run ruff check scripts tools && uv run run-suite --suite backend'
cexec modern-app sh -c 'cd root/test-app-no-storage && uv run ruff check scripts tools && uv run run-suite --suite backend'
```

### Validating both templates

`kc project build` regenerates all the test-apps (backend, frontend, root, in
that order); `kc project test` and `kc project lint` then run the gates above
against them. Each component renders two:

- **`test-app`**, every flag on (`use_database`, `use_s3`, `use_oidc`,
  `use_sse`, `use_app_shell`), with the hand-written domains from
  `test-app-domain/`. `root/test-app` wraps the backend's and the frontend's,
  and Playwright runs there.
- **The variants**, gitignored, so they churn nothing:
  - `frontend/test-app-no-shell`: `use_app_shell=false`, as ZigbeeControl,
    FieldnotesApp and PilotApp run. `build` and `lint` check it.
  - `backend/test-app-no-storage`: `use_database=false` and `use_s3=false`, as
    DHCPApp, ZigbeeControl and FieldnotesApp run, with `use_oidc` and
    `use_sse` on, as all three have them. A fresh render without the
    database-bound Items domain: `test` runs its own suite (the mother suite
    needs the full render), and `lint` runs ruff check, `ruff format --check`,
    mypy and vulture on it, as on `test-app`.
  - `root/test-app-no-storage`: the root template with the same flags, around
    `backend/test-app-no-storage` and `frontend/test-app-no-shell` (two of the
    three apps run without the shell). `root/regen.sh` refreshes its
    frontend's OpenAPI cache from that backend. `test` runs its backend suite
    and `lint` its ruff check; no Playwright.

`validate.sh`, described in `docs/copier_approach.md`, was never added to this
repo. The regens churn the tracked `test-app/` lockfiles and
`.copier-answers.yml` in `backend/` and `frontend/`; commit that with the
template change or discard it.

### Syncing a downstream app

```bash
# Find violations: template-owned files that differ from the render with the
# app's answers, and the app-owned files the next release changed, sorted by
# what the sync must do by hand (copier update leaves app-owned files alone).
# It renders with the pinned copier, so it runs under the backend's uv project.
cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py /work/<App> --template-repo .
cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py /work/<App>/backend --template-repo backend
cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py /work/<App>/frontend --template-repo frontend

# Update app from template (each run needs a clean tree; commit between them).
# Run copier from the component's own directory: it resolves the relative
# _src_path in .copier-answers.yml against the current directory. copier is the
# one pinned in the backend template repo's uv project (the parent repo has
# none); --project selects it without changing the working directory.
cd /work/<App>          && cexec modern-app uv run --project /work/ModernAppTemplate/backend --locked copier update --trust --defaults
cd /work/<App>/backend  && cexec modern-app uv run --project /work/ModernAppTemplate/backend --locked copier update --trust --defaults
cd /work/<App>/frontend && cexec modern-app uv run --project /work/ModernAppTemplate/backend --locked copier update --trust --defaults
```

## S3 Storage

The backend template's `.env.test` points at a local S3 endpoint on `http://localhost:9000` with `s3storage`/`s3storage` credentials, served by this environment's `s3storage` KubeCoder service (RustFS). CI's validation Job runs the same RustFS image with the same credentials as a sidecar. Downstream apps select the same `s3storage` service in their `.kubecoder/config.yaml` and seed its credentials into `backend/.env` and `backend/.env.test`. The backend's S3 preflight check treats any HTTP response as reachable (MinIO answers 403 to an anonymous GET).

Backend test suites with `use_s3=true` check S3 connectivity at startup (in `conftest_infrastructure.py`). If the `.env.test` file is missing or `S3_ENDPOINT_URL` is not set, tests abort immediately with a clear message. New downstream apps get `.env.test` seeded by their `.kubecoder/project.yaml` setup.

## Dead Code Analysis

Both templates include dead code detection as part of the `check` pipeline:

- **Backend**: `uv run check` runs ruff, mypy, vulture, and pytest. Vulture whitelist is in `vulture_whitelist.py` (app-owned, skip_if_exists).
- **Frontend**: `pnpm run check` runs eslint, tsc, and knip. Template exclusions are in `knip-template-ignore.json` (template-owned, updated on each `copier update`).

**Maintaining `knip-template-ignore.json`**: When adding or removing template-owned source files in the frontend template, update `template/knip-template-ignore.json` accordingly. This file lists all template-owned paths that knip should skip during unused-export analysis. Without it, template exports that aren't consumed by a particular app would be flagged as dead code.

## Commit Guidelines

- **Parent repo**: Commit docs and scripts here; root-template changes are also committed and tagged in the parent repo (it is the root template's own repo)
- **Template repos**: Commit template changes in `backend/` or `frontend/`, tag releases there independently
- **Changelog**: Update `changelog.md` in the parent for cross-template changes; each template repo has its own changelog for template-specific changes

## Template Change Workflow

**Always follow `docs/downstream_sync_process.md` when making template changes.** This covers the full process: upstreaming the fix, regenerating test-app, running tests, writing the changelog entry, committing and tagging the template repo(s), and running `copier update` on all downstream apps.

**Never apply a template change by directly editing files in downstream apps.** If you find yourself making the same edit to `nginx.conf`, `proxy.conf`, or any other template-owned file across multiple apps, stop — that is the wrong path. The correct path is always: change `template/` → regen → test → commit/tag the template repo → `copier update` each app. Direct edits to downstream template-owned files create drift that looks clean but isn't tracked by copier, and causes merge conflicts on the next real update.

Key things to not skip:
- Commit and tag **each template repo** that was changed (`backend/` and/or `frontend/`), and commit/tag the **parent repo** for root-template changes
- Commit the **parent repo** changelog
- After `copier update`, commit the downstream app's repo — backend and frontend live in the same repo, so one commit per template update keeps the history readable
- When a template change also requires editing an app-owned file (e.g. removing a dependency from `pyproject.toml`): run `copier update` first on a clean repo, then make the app-owned edits. Copier requires a clean working tree, so editing before updating forces an awkward stash/pop dance.
