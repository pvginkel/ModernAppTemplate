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

Run the violation finder script from the template repo:

```bash
cd /work/ModernAppTemplate
poetry run python scripts/find_template_violations.py /path/to/downstream/app --template-repo backend
```

The script reads `copier.yml` and the app's `.copier-answers.yml` to automatically determine which files are template-owned, app-owned, and feature-flag-excluded. It detects drift using two methods:

- **Git diff** — modifications since the last `copier update` commit
- **Source comparison** — direct comparison of non-Jinja template files against the app's copies (catches pre-existing divergence)

Useful flags:
- `--commits` — show which commits touched each violated file
- `--diff` — show the actual diffs
- `--commits --diff` — both

For each finding, classify the change into one of the three buckets.

### Phase 2: Upstream good changes to the template

For changes that belong in the template:

1. Implement the change in `template/` (with Jinja conditionals if feature-flag-dependent).
2. Regenerate test-app: `bash regen.sh`
3. Run the template test suites:
   ```bash
   cd test-app
   poetry run pytest ../tests/ -v
   poetry run pytest tests/ -v
   ```
4. Validate flag combinations with `ruff check` (at minimum: minimal, all-on).
5. **Update `changelog.md`** with what changed and migration steps (see [Changelog Discipline](#changelog-discipline) below).
6. Commit to the template repo.

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

1. **Read `changelog.md`** to understand all template changes and their migration steps. This is the primary guide for what needs to happen during the update.
2. Run `copier update` in the downstream app.
3. Resolve any merge conflicts. Template-owned files should now accept the template's version cleanly, since the good changes were upstreamed.
4. Follow the migration steps from `changelog.md` for each entry since the app's current `_commit`.
5. Move any remaining app-specific code out of template-owned files:
   - Business logic → app services or `startup.py` hooks
   - Extra endpoints → app-owned blueprints registered via `register_blueprints()`
   - Test utilities → `tests/conftest.py` or app-specific test helpers
6. Run the app's full test suite.
7. Re-run the violation finder to confirm a clean report.
8. Commit.

### Phase 5: Document in the downstream app's CLAUDE.md

Add a section to the downstream app's `CLAUDE.md` explaining:

```markdown
## Template Ownership Rules

This app uses the ModernAppTemplate. Files are either **template-owned** (overwritten
by `copier update`) or **app-owned** (`_skip_if_exists`, never overwritten).

### NEVER modify these files directly
Template-owned files are determined by `copier.yml` in the template repo. Run
the violation finder to check: `poetry run python scripts/find_template_violations.py .`

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
- "After update, add `new-package` to your `pyproject.toml` and run `poetry lock && poetry install`"
- "Move any custom logic from `database.py` into `startup.py:post_migration_hook()`"

### 2. When running `copier update`: read the entries

Before (or during) a `copier update`, **read all changelog entries** between the app's current `_commit` (in `.copier-answers.yml`) and the template's HEAD. The migration steps tell you exactly what manual work is needed beyond what copier handles automatically.

This is especially important because `copier update` only overwrites template-owned files — it cannot modify `pyproject.toml`, `container.py`, `startup.py`, or other app-owned files that may need corresponding changes.

---

## Current Status (2026-02-20)

All 4 apps are synced to the latest template versions:

| App | Backend | Frontend | Notes |
|-----|---------|----------|-------|
| ElectronicsInventory | v0.7.2 | v0.8 | Clean |
| IoTSupport | v0.7.2 | Not templated | 4 pre-existing test failures (CoreDump model) |
| ZigbeeControl | v0.7.2 | v0.8 | Clean |
| DHCPApp | v0.7.2 | v0.8 | Clean |

Known minor deviations (all intentional, will merge cleanly on next update):
- EI/IoTSupport/ZigbeeControl: `.gitignore` has `.claude/` added post-update (matches template)
- IoTSupport: `metrics_service.py` trailing newline removed post-update (matches template)
- EI: `alembic/versions/.gitkeep` and `scripts/dev-sse-gateway.sh` missing (copier three-way merge doesn't add files the app never had)

---

## Preventing Future Drift

### In the template's CLAUDE.md
Already documented. The key rule: "Never Edit test-app Directly" has an analog for downstream apps: "Never edit template-owned files directly."

### In each downstream app's CLAUDE.md
Add the template ownership section shown in Phase 5 above. This gives Claude (and human developers) a lookup table for "where does this go?"

### Process check after feature work
After completing a feature in a downstream app, before merging:
1. Run `poetry run python scripts/find_template_violations.py .` from the template repo
2. If any violations → classify into the three buckets and act accordingly
3. This can be a PR review checklist item

### Periodic sync cadence
Even without active feature work, run the violation finder monthly to catch drift early. Smaller, more frequent syncs are easier than large catch-up sessions.
