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
├── root/                           # Root template source and test-app
│   ├── template/                   # Copier template source
│   ├── regen.sh                    # Root regeneration script (run after backend/frontend regens)
│   └── test-app/                   # Generated test application (gitignored, DO NOT edit)
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
- Language tooling lives in the `modern-app` tool container: prefix Poetry, `copier` and pnpm commands with `cexec modern-app`. The dev container itself has `node`, `npm`, `python3` and `git` only.
- `cexec` passes arguments through verbatim, so compound commands need a wrapper: `cexec modern-app sh -c 'cd test-app && poetry install'`.
- Curated entry points are in `.kubecoder/project.yaml`, run with `kc project setup|build|test|lint`.

## Downstream Apps

| App | Backend | Frontend | Notes |
|-----|---------|----------|-------|
| ElectronicsInventory | `/work/ElectronicsInventory/backend` | `/work/ElectronicsInventory/frontend` | Primary source for template extraction |
| IoTSupport | `/work/IoTSupport/backend` | `/work/IoTSupport/frontend` | Closest to template patterns |
| DHCPApp | `/work/DHCPApp/backend` | `/work/DHCPApp/frontend` | Synced |
| ZigbeeControl | `/work/ZigbeeControl/backend` | `/work/ZigbeeControl/frontend` | Synced; `use_app_shell=false` |

## Feature Flags (Shared Across Templates)

| Flag | Backend | Frontend | Root |
|------|---------|----------|------|
| `use_oidc` | OIDC authentication (BFF pattern with JWT cookies) | OIDC login/logout UI, token handling | (not used) |
| `use_s3` | S3 storage, CAS endpoints, image processing | (not used in frontend) | S3 sidecar in the dev environment and the CI validation Job |
| `use_sse` | Server-Sent Events via SSE Gateway | SSE client, real-time update components | SSE gateway in the dev stack |
| `use_database` | SQLAlchemy, Alembic, migrations | (backend only) | Postgres sidecar and database bootstrap in setup |

## Key Documentation

Read these before making changes:

- **`docs/copier_approach.md`** — Architecture decisions, file ownership model, template file inventory
- **`docs/change_workflow.md`** — Step-by-step workflow for template changes
- **`docs/downstream_sync_process.md`** — How to find and fix template drift in apps

## Quick Start

### Working on the backend template
```bash
cd /work/ModernAppTemplate/backend
# Edit files in template/, then:
cexec modern-app bash regen.sh
cexec modern-app sh -c 'cd test-app && poetry run pytest ../tests/ -v && poetry run pytest tests/ -v'
```

### Working on the frontend template
```bash
cd /work/ModernAppTemplate/frontend
# Edit files in template/, then:
cexec modern-app bash regen.sh
cexec modern-app sh -c 'cd test-app && pnpm run check && pnpm run build'
```

### Working on the root template
```bash
cd /work/ModernAppTemplate
# Edit files in root/template/, then (backend and frontend regens must run first):
cexec modern-app bash root/regen.sh
cexec modern-app sh -c 'cd root/test-app && poetry run ruff check scripts tools && poetry run run-suite --suite backend'
```

### Validating both templates

There is no combined validation script. `validate.sh` is described in
`docs/copier_approach.md` but was never added to this repo — run the backend,
frontend and root steps above in turn (backend and frontend first, root last).

### Syncing a downstream app

```bash
# Find violations
python scripts/find_template_violations.py /work/<App> --template-repo .
python scripts/find_template_violations.py /work/<App>/backend --template-repo backend
python scripts/find_template_violations.py /work/<App>/frontend --template-repo frontend

# Update app from template (each run needs a clean tree; commit between them).
# Run copier from the component's own directory: it resolves the relative
# _src_path in .copier-answers.yml against the current directory. copier comes
# from the backend template's Poetry env (the parent repo has none).
cd /work/<App>          && cexec modern-app poetry -P /work/ModernAppTemplate/backend run copier update --trust --defaults
cd /work/<App>/backend  && cexec modern-app poetry -P /work/ModernAppTemplate/backend run copier update --trust --defaults
cd /work/<App>/frontend && cexec modern-app poetry -P /work/ModernAppTemplate/backend run copier update --trust --defaults
```

## S3 Storage

The backend template's `.env.test` points at a local S3 endpoint on `http://localhost:9000` with `minioadmin`/`minioadmin` credentials. Downstream apps get S3 from a `minio` KubeCoder service in their dev environments, and from a RustFS sidecar in the CI validation Job. The backend's S3 preflight check treats any HTTP response as reachable (MinIO answers 403 to an anonymous GET).

Backend test suites with `use_s3=true` check S3 connectivity at startup (in `conftest_infrastructure.py`). If the `.env.test` file is missing or `S3_ENDPOINT_URL` is not set, tests abort immediately with a clear message. New downstream apps get `.env.test` seeded by their `.kubecoder/project.yaml` setup.

## Dead Code Analysis

Both templates include dead code detection as part of the `check` pipeline:

- **Backend**: `poetry run check` runs ruff, mypy, vulture, and pytest. Vulture whitelist is in `vulture_whitelist.py` (app-owned, skip_if_exists).
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
