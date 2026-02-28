# ModernAppTemplate

Copier-based templates for generating self-contained Flask backend and React frontend projects. Each generated project is plain Python/TypeScript with no runtime dependency on the template. Template updates via `copier update` with three-way merge.

## Repository Structure

This is the parent repo. Backend and frontend templates have their own repos, checked out inside this directory:

```
ModernAppTemplate/                  # Parent repo (you are here)
├── CLAUDE.md                       # This file
├── docs/                           # Shared documentation
│   ├── copier_approach.md          # Architecture, decisions, file ownership
│   ├── change_workflow.md          # How to make template changes
│   ├── downstream_sync_process.md  # How to keep apps in sync
│   └── backend_porting_guide.md    # How to port a backend app onto the template
├── scripts/
│   └── find_template_violations.py # Finds template drift in downstream apps
├── changelog.md                    # Coordinated changelog (both templates)
├── validate.sh                     # Regenerate + test both templates
├── backend/                        # Checkout of ModernAppBackendTemplate (NOT a submodule)
└── frontend/                       # Checkout of ModernAppFrontendTemplate (NOT a submodule)
```

`backend/` and `frontend/` are **not Git submodules** — they are separate repo checkouts listed in `.gitignore`. Copier does not understand submodules, so this arrangement keeps the template repos independent while colocating them for development.

Each template repo has its own `CLAUDE.md` with template-specific instructions.

## Sandbox Environment

- This repository is bind-mounted into `/work/ModernAppTemplate` inside a container.
- Template repos are checked out at `backend/` and `frontend/` (separate git repos, not submodules).
- Git operations work in both the parent and the template repos.
- The container includes poetry, node/npm, and standard toolchains.

## Downstream Apps

| App | Backend | Frontend | Notes |
|-----|---------|----------|-------|
| ElectronicsInventory | `/work/ElectronicsInventory/backend` | `/work/ElectronicsInventory/frontend` | Primary source for template extraction |
| IoTSupport | `/work/IoTSupport/backend` | `/work/IoTSupport/frontend` | Closest to template patterns |
| DHCPApp | `/work/DHCPApp/backend` | `/work/DHCPApp/frontend` | Needs more migration work |
| ZigbeeControl | `/work/ZigbeeControl/backend` | `/work/ZigbeeControl/frontend` | Needs more migration work |

## Feature Flags (Shared Across Templates)

| Flag | Backend | Frontend |
|------|---------|----------|
| `use_oidc` | OIDC authentication (BFF pattern with JWT cookies) | OIDC login/logout UI, token handling |
| `use_s3` | S3 storage, CAS endpoints, image processing | (not used in frontend) |
| `use_sse` | Server-Sent Events via SSE Gateway | SSE client, real-time update components |
| `use_database` | SQLAlchemy, Alembic, migrations | (backend only) |

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
bash regen.sh
cd test-app && poetry run pytest ../tests/ -v && poetry run pytest tests/ -v
```

### Working on the frontend template
```bash
cd /work/ModernAppTemplate/frontend
# Edit files in template/, then:
bash regen.sh
cd test-app && npm test
```

### Validating both templates
```bash
cd /work/ModernAppTemplate
bash validate.sh
```

### Syncing a downstream app
```bash
# Find violations
python scripts/find_template_violations.py /work/<App>/backend --template-repo backend

# Update app from template
cd /work/<App>/backend && copier update --trust --defaults
```

## S3 Storage (Ceph)

The test environment uses a **Ceph cluster** (radosgw) for S3-compatible storage — not MinIO. Connection details are in each project's `.env.test` file:

```
S3_ENDPOINT_URL=http://srvceph1:7480
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=<project>-test
```

Backend test suites with `use_s3=true` check S3 connectivity at startup (in `conftest_infrastructure.py`). If the `.env.test` file is missing or `S3_ENDPOINT_URL` is not set, tests abort immediately with a clear message. When creating a new downstream app, copy the Ceph credentials from `/work/ElectronicsInventory/backend/.env` into the app's `.env.test` and set an appropriate `S3_BUCKET_NAME`.

## Dead Code Analysis

Both templates include dead code detection as part of the `check` pipeline:

- **Backend**: `poetry run check` runs ruff, mypy, vulture, and pytest. Vulture whitelist is in `vulture_whitelist.py` (app-owned, skip_if_exists).
- **Frontend**: `pnpm run check` runs eslint, tsc, and knip. Template exclusions are in `knip-template-ignore.json` (template-owned, updated on each `copier update`).

**Maintaining `knip-template-ignore.json`**: When adding or removing template-owned source files in the frontend template, update `template/knip-template-ignore.json` accordingly. This file lists all template-owned paths that knip should skip during unused-export analysis. Without it, template exports that aren't consumed by a particular app would be flagged as dead code.

## Commit Guidelines

- **Parent repo**: Commit docs and scripts here
- **Template repos**: Commit template changes in `backend/` or `frontend/`, tag releases there independently
- **Changelog**: Update `changelog.md` in the parent for cross-template changes; each template repo has its own changelog for template-specific changes

## Template Change Workflow

**Always follow `docs/downstream_sync_process.md` when making template changes.** This covers the full process: upstreaming the fix, regenerating test-app, running tests, writing the changelog entry, committing and tagging the template repo(s), and running `copier update` on all downstream apps.

Key things to not skip:
- Commit and tag **each template repo** that was changed (`backend/` and/or `frontend/`)
- Commit the **parent repo** changelog
- After `copier update`, commit **both the backend and frontend repos** of each downstream app — they are separate git repos
