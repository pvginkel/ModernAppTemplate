# Downstream App Sync Process

Process for keeping downstream apps clean against the template after active development.

## Why This Is Needed

When developing features in downstream apps, developers (human or AI) sometimes modify template-owned files directly. This is natural — it's the fastest way to get a feature working — but it creates drift that breaks on the next `copier update`. This process finds those modifications, classifies them, and routes each to the right fix.

## The Three Buckets

Every modification to a template-owned file falls into one of three buckets:

| Bucket | What it is | Action |
|--------|-----------|--------|
| **Upstream** | A genuinely good improvement that all apps benefit from | Merge into the template, then `copier update` the app |
| **Refactor out** | App-specific code that landed in a template file | Move to an app-owned file (startup.py, container.py, etc.), using existing or new hooks |
| **New hook needed** | App-specific code that *can't* be moved out because the template lacks an extension point | Add the hook to the template first, then refactor the app to use it |

## Per-App Workflow

### Phase 1: Discover

Run the violation finder from the parent repo, once per component. Downstream apps are monorepos, so run it against the root layer (the parent repo is its template) as well as the backend and frontend layers. It renders with the pinned copier, so it runs under the backend template's uv project:

```bash
cd /work/ModernAppTemplate
FINDER="cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py"
$FINDER /work/<App> --template-repo .
$FINDER /work/<App>/backend --template-repo backend
$FINDER /work/<App>/frontend --template-repo frontend
```

The script renders the template with the app's own answers (`.copier-answers.yml`), so the feature flags and the Jinja-rendered files are the app's. Copier renders from a clone of the template at the ref, so only files the template tracks count. It reports two things:

- **Template-owned files** — every file of the render at the app's `_commit`, the Jinja-rendered ones included, compared with the app's copy. A difference is an edit to a template-owned file; `*` marks the ones changed since the last `copier update`. Files the render has and the app lacks are listed as missing. Either makes the script exit 1.
- **App-owned files** (`_skip_if_exists`) — sorted by their render at the app's `_commit`, their render at the release `copier update` takes (the latest release tag) and the app's copy. `copier update` leaves them alone (step 3 below), so this list is the sync's by-hand work:
  - *take by hand* — the template changed the file and the app still has the old render;
  - *merge by hand* — the template changed it and the app has its own edits;
  - *already current* — the app's copy equals the new render;
  - *new* (the update creates it where the app has none, and keeps an app's own copy), *dropped by the template*, *deleted by the app* (the update re-creates it).

  The files the template didn't change are counted, and listed with `--all`.

Useful flags:
- `--diff` — the diffs: render to app for template-owned files, the template's change (old render to new) for app-owned ones
- `--commits` — the commits since the last `copier update` that touched each differing file
- `--new-ref HEAD` — sort the app-owned files against an unreleased template change
- `--old-ref <tag>` — sort them from an earlier release, such as the one the app came from after its update

For each template-owned finding, classify the change into one of the three buckets.

### Phase 2: Upstream good changes to the template

For changes that belong in the template:

1. Implement the change in `template/` (with Jinja conditionals if feature-flag-dependent).
2. Regenerate test-app: `bash regen.sh`
3. Run the template test suites:
   ```bash
   cd test-app
   uv run pytest ../tests/ -v
   uv run pytest tests/ -v
   ```
4. Validate flag combinations. `kc project build`, `test` and `lint` render and check every flag on (`test-app`), and the shapes without a database and S3 (backend and root `test-app-no-storage`) and without the shell (frontend `test-app-no-shell`). Render any other combination the change touches and `ruff check` it.
5. **Update `changelog.md`** with what changed and migration steps (see [Changelog Discipline](#changelog-discipline) below).
6. **Commit to the template repo(s) and tag.** Don't forget: `backend/` and `frontend/` are separate git repos. Commit and tag each one that was changed:
   ```bash
   cd /work/ModernAppTemplate/backend
   git add -p && git commit -m "..."
   git tag vX.Y.Z

   cd /work/ModernAppTemplate/frontend
   git add -p && git commit -m "..."
   git tag vX.Y.Z
   ```
   Root-template changes are committed and tagged in the parent repo itself, since `ModernAppTemplate` is the root template's own Git root:
   ```bash
   cd /work/ModernAppTemplate
   git add -p && git commit -m "..."
   git tag vX.Y.Z
   ```
7. **Commit the parent repo changelog** (`/work/ModernAppTemplate/changelog.md`).

### Phase 3: Add new hooks if needed

If a change can't be upstreamed (it's app-specific) and can't be refactored out (no hook exists):

1. Design the hook in the template. Prefer the simplest mechanism:
   - A new function in `startup.py` (e.g., `register_root_blueprints(app)`)
   - An existing function with a broader signature
   - A callback/observer pattern (e.g., `register_on_disconnect()`)
2. Implement the hook in `template/`, with a no-op default in the scaffold.
3. Regenerate, test, commit — same as Phase 2.
4. **Update `changelog.md`** — document the new hook and how apps should use it.

### Phase 4: Refactor the downstream app

With the template updated (Phases 2-3 complete):

1. **Read `changelog.md`** to understand all template changes and their migration steps. This is the primary guide for what needs to happen during the update. Run the violation finder (Phase 1) before the updates too, and keep its app-owned *take by hand* and *merge by hand* lists for step 4.
2. Run `copier update` per component — root, backend, frontend — each against a clean working tree, committing between them since copier needs the whole monorepo's tree clean:
   ```bash
   # copier lives in the backend template's uv project, in the modern-app tool
   # container. Run it from the component's directory: copier resolves the
   # relative _src_path in .copier-answers.yml against the current directory.
   COPIER="cexec modern-app uv run --project /work/ModernAppTemplate/backend --locked copier update --trust --defaults"
   cd /work/<App>          && $COPIER && git add -A && git commit -m "Update to root template vX.Y.Z"
   cd /work/<App>/backend  && $COPIER && git add -A . && git commit -m "Update to backend template vX.Y.Z"
   cd /work/<App>/frontend && $COPIER && git add -A . && git commit -m "Update to frontend template vX.Y.Z"
   ```
3. Resolve any merge conflicts. They are in template-owned files only, which should now accept the template's version cleanly, since the good changes were upstreamed. `copier update` leaves app-owned (`_skip_if_exists`) files alone, whether the app edited them or not, in all three components: every release after backend v0.14.0 and frontend v0.21.0 lists each entry twice, once with the `backend/` or `frontend/` prefix, and the update reads the new release's list ([How `copier update` treats app-owned files](copier_approach.md#how-copier-update-treats-app-owned-files)). Updates to those two releases and earlier merged the template's changes into the app-owned files an app had edited. A conflict or `.rej` file in an app-owned file now means its entry lacks a twin: keep the app's version, delete the `.rej` file, and add the twin to the template.
4. Follow the migration steps from `changelog.md` for each entry since the app's current `_commit`. They are the only way a template change to an app-owned file reaches the app, since `copier update` leaves those files alone. Every file on the finder's *take by hand* and *merge by hand* lists should have a step. A file without one is a gap in the changelog: take the template's change from the finder's `--diff`, and report the gap.
5. Move any remaining app-specific code out of template-owned files:
   - Business logic → app services or `startup.py` hooks
   - Extra endpoints → app-owned blueprints registered via `register_blueprints()`
   - Test utilities → `tests/conftest.py` or app-specific test helpers
6. Run the app's full test suite.
7. Re-run the violation finder to confirm a clean report: no template-owned file differs from the render but the app's recorded standing edits. Pass `--old-ref <the _commit before the update>` to check the app-owned files: each one the release changed is *already current*, or on *merge by hand* with the step applied to the app's own edits.
8. **Commit the downstream app.** Backend and frontend live in one repo per app (`/work/<App>`):
   ```bash
   cd /work/<App> && git add -p && git commit -m "Update to backend template vX.Y.Z / frontend template vX.Y.Z"
   ```

### Phase 5: Document in the downstream app's CLAUDE.md

Add a section to the downstream app's `CLAUDE.md` explaining:

```markdown
## Template Ownership Rules

This app uses the ModernAppTemplate. Files are either **template-owned** (overwritten
by `copier update`) or **app-owned** (`_skip_if_exists`, never overwritten).

### NEVER modify these files directly
Template-owned files are determined by `copier.yml` in the template repo. Run
the violation finder from the template's parent repo to check (once per
component): `cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py /work/<App>/backend --template-repo backend`

### Where to put app-specific code instead
| Need | Put it in | Hook/mechanism |
|------|-----------|----------------|
| New API endpoints | `app/api/your_module.py` | `register_blueprints()` in `startup.py` |
| Root-level blueprints (not under /api/) | `app/api/your_module.py` | `register_root_blueprints()` in `startup.py` |
| New services | `app/services/your_service.py` | Wire in `container.py` |
| Background service startup | `container.py` | `register_for_background_startup()` |
| Error handlers | `startup.py` | `register_error_handlers()` |
| CLI commands | `startup.py` | `register_cli_commands()` |
| Post-migration logic | `startup.py` | `post_migration_hook()` |
| Test fixtures | `tests/conftest.py` | Import from `conftest_infrastructure`, add app fixtures |
| Extra exceptions | `app/exceptions.py` | Extend `BusinessLogicException` |
| Side effects after a request commits | service code | `after_commit()` from `app/utils/after_commit.py` |
| Sidecars CI must wait for | `backend/scripts/wait-for-services.py` | called by the root suite runner |

### If you need something the template doesn't support
Do NOT modify a template-owned file. Instead:
1. Check if an existing hook can accommodate the need.
2. If not, open an issue / make a change in the template to add a hook.
3. Then use the hook from the app-owned file.
```

---

## Changelog Discipline

The template's `changelog.md` is the contract between the template and downstream apps. It serves two purposes:

### 1. When making template changes: write the entry

Every template change that affects downstream apps **must** get a changelog entry with:
- Date
- What changed and why
- Which files were added/modified
- **Migration steps** — concrete instructions for what a downstream app developer (or AI) needs to do after running `copier update`

Good migration steps are specific and actionable:
- "Run `copier update` — this file is template-maintained and will be updated automatically"
- "After update, add `new-package` to your `pyproject.toml` and run `uv lock && uv sync`"
- "Move any custom logic from `database.py` into `startup.py:post_migration_hook()`"

### 2. When running `copier update`: read the entries

Before (or during) a `copier update`, **read all changelog entries** between the app's current `_commit` (in `.copier-answers.yml`) and the template's HEAD. The migration steps tell you exactly what manual work is needed beyond what copier handles automatically.

This is especially important because `copier update` only overwrites template-owned files — it cannot modify `pyproject.toml`, `container.py`, `startup.py`, or other app-owned files that may need corresponding changes. So when a template change edits an app-owned file, its entry needs a migration step that names the file and the edit: nothing else brings the change to an existing app. The violation finder's *take by hand* and *merge by hand* lists show which app-owned files a release changed, so a sync can check that every one has its step.

---

## Current Status (2026-10-17)

All six apps are synced to root v0.2.1, backend v0.15.0 and frontend v0.22.0, all on uv:

| App | Root | Backend | Frontend | Notes |
|-----|------|---------|----------|-------|
| ElectronicsInventory | v0.2.1 | v0.15.0 | v0.22.0 | Jenkinsfile keeps an extra docs-image stage (standing edit); the role-gating lint rules live in app-owned `frontend/eslint.app.config.js` |
| IoTSupport | v0.2.1 | v0.15.0 | v0.22.0 | Jenkinsfile keeps the Vault-wrapped validation with Keycloak env and an OpenSearch sidecar; `vite.config.ts` carries an esptool mock alias and `optimizeDeps` (app-specific edits to a template-owned file) |
| DHCPApp | v0.2.1 | v0.15.0 | v0.22.0 | Uses `public/favicon.svg`; `copier update` re-creates the deleted `public/favicon.png` (`_skip_if_exists`), so delete it again after each update |
| ZigbeeControl | v0.2.1 | v0.15.0 | v0.22.0 | `use_app_shell=false`; `index.html` adds a Material Symbols font link |
| FieldnotesApp | v0.2.1 | v0.15.0 | v0.22.0 | `use_app_shell=false`; a uv workspace (`packages/`, `mcp-server/`, `eval/`), so the backend `Dockerfile` keeps its extra `COPY` lines, the runtime `git ca-certificates` install and `--no-editable`; `backend/.gitignore` ignores `.run/` (standing edit) |
| PilotApp | v0.2.1 | v0.15.0 | v0.22.0 | `use_app_shell=false`; no standing edits to template-owned files |

DesignAssistant is no longer part of the sync: the project is archived.

---

## Preventing Future Drift

### In the template's CLAUDE.md
Already documented. The key rule: "Never Edit test-app Directly" has an analog for downstream apps: "Never edit template-owned files directly."

### In each downstream app's CLAUDE.md
Add the template ownership section shown in Phase 5 above. This gives Claude (and human developers) a lookup table for "where does this go?"

### Process check after feature work
After completing a feature in a downstream app, before merging:
1. Run the violation finder from the parent repo against each component (Phase 1)
2. If any violations → classify into the three buckets and act accordingly
3. This can be a PR review checklist item

### Code health ignore files
Downstream apps may have a `.codehealthignore` file in each project root (e.g., `backend/.codehealthignore`, `frontend/.codehealthignore`) that excludes template-owned files from code health analysis. This prevents duplication reports from flagging template-sourced files across apps. When syncing, keep these files up to date: if the template adds or removes files, update the corresponding `.codehealthignore` entries to match.

### Periodic sync cadence
Even without active feature work, run the violation finder monthly to catch drift early. Smaller, more frequent syncs are easier than large catch-up sessions.
