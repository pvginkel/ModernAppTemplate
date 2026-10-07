# Template Changelog

This changelog tracks all changes to the template that affect downstream apps. Each entry includes migration instructions for updating apps from the template.

See `CLAUDE.md` for instructions on how to use this changelog when updating apps.

---

<!-- Add new entries at the top, below this line -->

## 2026-10-06 — Root v0.1.5

### The validation Job books no requests

**What changed:** `Jenkinsfile`'s validation container no longer requests `cpu: "1"` and `memory: 3584Mi`. On prd, Kyverno sets each pod's memory request at creation from a daily snapshot of measured usage (Ansible slice 053, argo-cd D65 as amended 2026-10-06).

**Migration steps:**
1. `copier update --trust --defaults` at the app root. An app whose `Jenkinsfile` runs its validation through the library's `modernApp.test` books no request of its own; the update changes nothing there.

## 2026-09-30 — Root v0.1.4, Backend v0.13.3, Frontend v0.20.4

### A fresh instance passes its own gates

**What changed:** a newly generated app (seen with `use_database=false`, `use_app_shell=false`) failed its gates until the app added code of its own.
- Backend v0.13.3: new app-owned `tests/test_smoke.py` (`_skip_if_exists`), one test that the app answers `/health/healthz`. With no tests at all, `pytest` exits 5 and `poetry run check` fails.
- Frontend v0.20.4: new app-owned `src/routes/index.tsx` (`_skip_if_exists`), a placeholder home page. With `__root` as the only route, the router's types collapse to `never` and `tsc` fails. With `use_oidc` and without `use_app_shell`, the page draws a header with the `UserDropdown`, which the template's auth specs look for.
- Frontend v0.20.4: `scripts/fetch-openapi.js` creates `openapi-cache/` before it writes the spec, so the first `pnpm generate:api` in a fresh app no longer fails with ENOENT.
- Root v0.1.4: the generated `CLAUDE.md` lists `after_commit()` and post-migration logic as extension points only with `use_database`.

**Migration steps:**
1. `copier update --trust --defaults` in `backend/` and `frontend/`. The update adds `backend/tests/test_smoke.py` to an app that has none; keep it or delete it. `src/routes/index.tsx` is skipped, since every app has one.

### `scripts/dev.py` stops on a signal, and the validation Job's tar extraction is clean

**What changed:**
- `scripts/dev.py` forwards SIGINT and SIGTERM to honcho as a Ctrl-C through its PTY instead of ignoring them, so a signal from another shell stops every service. Before, the only way to stop a backgrounded stack was to kill the cexec client, and that left the backend and the SSE gateway running as orphans in the `modern-app` sidecar. New `scripts/dev.py stop` signals the running stack through `logs/dev.pid` and waits for it to exit. A stop that comes in before honcho has started every service is held until then, because honcho crashes on a SIGINT during startup.
- `Jenkinsfile`: the validation Job extracts the context archive with `--strip-components=1`. That skips the archive's `./` entry, whose mode and mtime uid 1000 cannot set on the root-owned `/work` emptyDir. The old command printed "Cannot utime" / "Cannot change mode" and exited 2 on every run; the files were extracted anyway, so builds stayed green.

**Migration steps:**
1. `copier update --trust --defaults` at the app root. App additions to the validation Job spec go through the three-way merge; check them in the diff.

## 2026-09-30 — Root v0.1.3, Frontend v0.20.3

### S3 sidecar is `s3storage`, and Playwright is pinned to 1.60.0

**What changed:**
- Root v0.1.3: KubeCoder's catalog replaced the `minio` service with `s3storage`, a RustFS sidecar on the same `localhost:9000` with credentials `s3storage`/`s3storage`, and storage cleared on every start. An environment whose `config.yaml` names `minio` is refused on restart. The generated `.kubecoder/config.yaml` selects `s3storage`, and `.kubecoder/project.yaml` seeds `backend/.env` and `backend/.env.test` with the new credentials. CI's validation Job already ran RustFS with these credentials.
- Frontend v0.20.3: `package.json` pins `@playwright/test` to `1.60.0` instead of `^1.60.0`. 1.63.0's browser download times out in KubeCoder pods and in CI, while 1.60.0 downloads fine. This is a hold until a Playwright release fixes it, not a floor.

**Migration steps:** both files are generated once (`_skip_if_exists`), so `copier update` does not change them.
1. `copier update --trust --defaults` at the app root and in `frontend/`.
2. With `use_s3`: in `.kubecoder/config.yaml`, replace `- minio` under `services:` with `- s3storage`. In `.kubecoder/project.yaml`, replace `minioadmin` with `s3storage` in the `.env` and `.env.test` seeds. Also update any app-owned script that seeds the same credentials.
3. With `use_s3`, in each existing environment: the seeds never overwrite a file, so fix the S3 credentials in `backend/.env` and `backend/.env.test`, or delete the files and run `kc project setup`. Then `kc env restart`.
4. In `frontend/package.json`, change `"@playwright/test": "^1.60.0"` to `"1.60.0"`, and run `pnpm install` to update the lockfile's specifier.

## 2026-09-26 — Root v0.1.2

### Validation Job runs in the KubeCoder modern-app toolchain image

**What changed:** The `Jenkinsfile` validation Job runs in `registry:5000/kube-coder-modern-app-toolchain:node-24`, the image of the dev environment's `modern-app` sidecar, instead of `modern-app-dev-playwright:playwright-<version>`, which is retired; the lockfile lookup that picked that tag is gone. The image carries Chromium's OS dependencies but no browser, so the suite runner's `pnpm playwright install chromium` downloads Chromium on every run. It has no `/work`, so the Job mounts an emptyDir there.

**Migration steps:**
1. `copier update --trust --defaults` at the app root. App additions to the validation Job spec (extra env, sidecars) go through the three-way merge; check them in the diff.

## 2026-09-26 — Frontend v0.20.2

### Auth redirect test goes back to `/items`

**What changed:**
- `tests/infrastructure/auth/auth.spec.ts`: "preserves full path including query params in redirect" navigates to `/items?filter=active&sort=name` again. v0.20.0 had switched it to `/` (from DHCPApp), but apps whose index route redirects (EI to `/parts`, IoTSupport to `/devices`) drop the query string before the 401, so the test failed in their CI. `/items` is not a route in the apps, so nothing redirects it.

**Migration steps:**
1. `copier update --trust --defaults` in `frontend/`.

## 2026-09-26 — Root v0.1.1

### Suite runner timeouts sized for the largest suite

**What changed:** `scripts/dev.py`'s usage no longer suggests `-e gateway` to skip a service (honcho's `-e` is `--env`); a subset is started with positional names, e.g. `./scripts/dev.py backend frontend`. `tools/suite_runner/local.py` allows ElectronicsInventory's timeouts: backend install 600s, backend pytest 1800s, pnpm install 600s, frontend build 900s, Playwright browser install 900s, Playwright 3600s (were 300/900/300/600/300/1800).

**Migration steps:**
1. `copier update --trust --defaults` at the app root.

## 2026-09-26 — Backend v0.13.1, v0.13.2, Frontend v0.20.1

### Patch releases found while updating the apps

**What changed:**
- Backend v0.13.1: the `use_s3`/`use_oidc` gates in `testing_service.py` and `spectree_config.py` no longer leave doubled blank lines when the flag is off.
- Backend v0.13.2: `truncate_with_ellipsis` loses its unused `encoding` parameter (from EI), and the scaffold `vulture_whitelist.py` drops the matching `encoding` entry and no longer leaves doubled blank lines around its `use_database` blocks.
- Frontend v0.20.1: `routed-tabs.tsx` carries a file-level `react-refresh/only-export-components` disable, like `auth-context.tsx`.

**Migration steps:**
1. `copier update --trust --defaults` in `backend/` and `frontend/`.
2. Optional: remove `encoding  # unused variable` from the app's `vulture_whitelist.py` (app-owned).

## 2026-09-26 — Root v0.1.0, Backend v0.13.0, Frontend v0.20.0

### Monorepo: a root template, and per-repo CI leaves the component templates

**What changed:** The apps are monorepos (backend and frontend in one repo, one CI pipeline). A third template now generates the root layer, and the backend and frontend templates stop generating the per-repo CI and Docker-era scripts that the conversion made dead.

**Root template (new, v0.1.0).** Lives in this repo: `copier.yml` at the root, the template in `root/template/`, versioned by this repo's tags. Generates:
- Template-owned: `Jenkinsfile` (validation Job on `modern-app-dev-playwright:playwright-<version>` running `run-suite`, RustFS S3 sidecar when `use_s3`, kaniko builds of both images, `cicd.writeVersionPins` into the Argo CD deploy repo), `tools/suite_runner/` (`run-suite`), `Procfile.dev`, `scripts/dev.py`, `scripts/dev-sse-gateway.sh` (`use_sse`), `.gitignore`, `.vscode/settings.json`.
- Generated once (`_skip_if_exists`): `pyproject.toml` (with the pinned `[tool.ruff]` and ruff dev group), `CLAUDE.md`, `<repo_name>.code-workspace`, `scripts/regenerate-openapi.py`, `.kubecoder/config.yaml`, `.kubecoder/project.yaml`.
- The suite runner runs `backend/scripts/wait-for-services.py` after the backend install when that file exists — the hook for CI sidecars that are slow to come up.

**Backend v0.13.0:**
- Removed: `Jenkinsfile`, `scripts/{args,build,push,run,stop}.sh`, `scripts/dev-sse-gateway.sh` (now root), and the `repo_url`, `image_name`, `validation_jenkins_job` questions.
- `scripts/testing-server.sh` has its own default port instead of sourcing `args.sh`.
- Flask 3 typing: `types-flask` dropped from the scaffold `pyproject.toml`; `app/app.py` gains `current_container()` (and declares `diagnostics_service` with `use_database`); `dict[str, Any]` health checks; App-typed CLI handlers; `BaseException` in `close_session`; `ProxyFix` assignment marked `method-assign`.
- New `app/utils/after_commit.py` (`use_database`): `after_commit(callback)` runs the callback only after the request's transaction commits; `close_session` runs or drops them.
- S3 preflight in `tests/conftest_infrastructure.py` treats any HTTP response as reachable (MinIO answers `GET /` with 403).
- New `scripts/init-dev-database.py` (`use_database`): creates the dev database on the Postgres sidecar.
- Flag fixes: `testing_service.py`, `spectree_config.py`, `vulture_whitelist.py` and `flask_error_handlers.py` docstrings are feature-gated; `app/models` is excluded without `use_database`.
- Scaffold fixes for new apps: `README.md` (poetry install needs it), `.dockerignore`, `app_config.py` defines `thumbnail_storage_path` for `use_s3`, `Dockerfile` installs `--only main`, the SQLAlchemy mypy plugin is gone (removed in SQLAlchemy 2.1).

**Frontend v0.20.0:**
- Removed: `Jenkinsfile`, `Jenkinsfile.validation`, `scripts/validation-entrypoint.sh`, and the `repo_url`, `image_name`, `backend_repo_url`, `backend_image_name`, `backend_jenkins_job`, `frontend_jenkins_job`, `validation_jenkins_job`, `generate_validation_pipeline` questions.
- `knip.config.ts` no longer ignores `@tanstack/router-devtools` and `class-variance-authority` (unused); the scaffold `package.json` drops them, requires `@playwright/test ^1.60.0` and uses `github:pvginkel/SSEGateway#stable`.
- `DebouncedSearchInput` syncs the URL term during render (eslint-plugin-react-hooks 7.1 rejects setState in effects).
- New `RoutedTabs` primitive (from IoTSupport). `DialogContent` accepts `data-testid`. Vite ignores `.pnpm-store`. SegmentedTabs indicator contrast and toast alignment (from EI).
- `global-setup.ts` runs the seed script with `OIDC_ENABLED=false`; `auth.spec.ts` redirect test uses `/` instead of `/items`.
- `.dockerignore` scaffold.

**Migration steps:**
1. On a clean tree: `cd backend && copier update --trust --defaults`, then `cd ../frontend && copier update --trust --defaults`. Deleted template files that the app still has (e.g. `backend/scripts/build.sh`) are removed; resolve any conflicts.
2. Adopt the root template (once): from the repo root, `copier copy --trust --defaults <path-to>/ModernAppTemplate . --vcs-ref v0.1.0` with the app's answers (`-d project_name=… -d repo_name=… -d backend_image=… -d frontend_image=… -d deploy_repo=… -d backend_image_pin_key=… -d frontend_image_pin_key=…` plus ports and flags), then review `git diff`: keep genuine app additions in the template-owned files (extra Jenkinsfile stages, extra `.gitignore` lines); the `_skip_if_exists` files are left untouched. Commit; from then on `copier update` at the root.
3. `backend/pyproject.toml`: remove `types-flask`; remove the `sqlalchemy.ext.mypy.plugin` line if the app moves to SQLAlchemy 2.1.
4. `frontend/package.json`: remove `@tanstack/router-devtools` and `class-variance-authority`, then `pnpm install` — knip flags them otherwise.
5. Replace hand-edits of `close_session` in `app/__init__.py` with `after_commit()` calls from the service code.
6. Move any sidecar wait the app does in the suite runner into `backend/scripts/wait-for-services.py`.

## 2026-06-05 — Frontend v0.19.1

### Fix: validation extracts source to /work/backend and /work/frontend

**What changed:** The v0.19.0 streaming validation extracted the source to `/work/backend-src` and `/work/frontend-src`. That broke the Playwright test harness: `tests/support/process/servers.ts` resolves the backend repo root as `<frontendRoot>/../backend`, so it spawns `/work/backend/scripts/testing-server.sh` — which didn't exist (`spawn … ENOENT`). The Job now renames the extracted dirs to `/work/backend` and `/work/frontend` (the same sibling layout the old `Dockerfile.validation` produced via `COPY`), and `validation-entrypoint.sh` `cd`s into those paths.

Frontend template files changed:
- `template/Jenkinsfile.validation.jinja` (`mv /work/backend-src /work/backend` + `mv /work/frontend-src /work/frontend` after extract)
- `template/scripts/validation-entrypoint.sh` (`cd /work/backend` and `cd /work/frontend`)

**Migration steps:**
1. `copier update --trust` on the frontend — picks up the rename and the entrypoint paths.

## 2026-06-05 — Frontend v0.19.0

### Validation runs on the prebaked Playwright image; no per-build validation image

**What changed:** The validation pipeline no longer builds a `Dockerfile.validation` image with kaniko. Instead, `Jenkinsfile.validation` resolves the Playwright version from `frontend-src/pnpm-lock.yaml`, runs the validation Job directly on `registry:5000/modern-app-dev-playwright:playwright-<version>` (browsers prebaked), and streams the source into the Job via `tar` + `kubectl cp`.

This fixes validation jobs hanging after `playwright install` downloaded Chromium on the plain `modern-app-dev` base image. The Job runs as `runAsUser: 1000` so the prebaked browser cache (owned by `ubuntu`) is found, and results are copied out of the still-running pod via `kubectl cp` instead of the base64-in-logs hack. The source now extracts to `/work/backend-src` and `/work/frontend-src`.

This requires the `modern-app-dev-playwright` image to be published for the Playwright version pinned in the app's lockfile (currently `1.58.2`).

Frontend template files changed:
- `template/Jenkinsfile.validation.jinja` (rewrote the `Run validation` stage; dropped the `Build validation image` kaniko stage)
- `template/scripts/validation-entrypoint.sh` (reads `/work/backend-src` and `/work/frontend-src`; dropped the base64 JUnit export trap — results now leave via `kubectl cp`)
- `template/Dockerfile.validation` (removed)
- `copier.yml` (removed `Dockerfile.validation` from `_skip_if_exists` and `_exclude`; removed the now-unused `validation_image_name` variable; updated `generate_validation_pipeline` help text)

**Migration steps:**
1. `copier update --trust` on the frontend — `Jenkinsfile.validation` and `scripts/validation-entrypoint.sh` update and `Dockerfile.validation` is deleted. The `validation_image_name` answer is dropped automatically.
2. Ensure `registry:5000/modern-app-dev-playwright` is published for the Playwright version in your `pnpm-lock.yaml`. If your app pins a version with no published image, bump to a published one or have the image built for it.
3. If your app's validation Job injects extra env/secrets (e.g. S3, Keycloak, Elasticsearch), re-add them to the new Job spec — the template's validation Job ships no app-specific env by default.

## 2026-03-15 — Frontend v0.18.0

### UI components now template-owned

**What changed:** The `src/components/ui/` directory is no longer fully `_skip_if_exists`. Only `src/components/ui/index.ts` remains app-owned (for managing re-exports of app-specific additions). All other template UI components (badge, skeleton, empty-state, key-value-badge, etc.) are now template-owned and will be updated by `copier update`.

Additionally:
- **Skeleton**: Now accepts optional `className` prop for additional styling (margin, etc.)
- **EmptyState**: `action` prop now accepts `ReactNode` in addition to `ActionConfig`, supporting custom action elements like `<Link><Button>...</Button></Link>`

Frontend template files changed:
- `copier.yml` (`_skip_if_exists` changed from `src/components/ui` to `src/components/ui/index.ts`)
- `src/components/ui/skeleton.tsx` (added `className` prop)
- `src/components/ui/empty-state.tsx` (action accepts `ReactNode | ActionConfig`)

**Migration steps:**
1. `copier update --trust` on frontend — skeleton.tsx and empty-state.tsx will be updated automatically.
2. If your app has **customized any template ui component** (other than index.ts), the three-way merge will attempt to reconcile. Review merge results carefully.
3. If your app uses Skeleton with `className` for sizing (e.g. `className="h-12 w-full"`), refactor to `height="h-12" width="w-full"`. Use `className` only for non-size styling like margins.
4. If your app uses EmptyState with `data-testid`, change to `testId`.
5. Apps can still **add their own components** to `src/components/ui/` — copier only manages the files defined in the template. Update `index.ts` to export your additions.

## 2026-03-15 — Frontend v0.17.1

### fetch-openapi.js BACKEND_PORT env var override

**What changed:** `scripts/fetch-openapi.js` now reads `process.env.PORT` as a fallback before the copier-rendered `backend_port`. This allows overriding the backend port at runtime without editing the file. Extracted from DesignAssistant.

Frontend template files changed:
- `scripts/fetch-openapi.js.jinja` (template-owned, auto-updated by copier)

**Migration steps:**
1. `copier update --trust` on frontend — `fetch-openapi.js` is template-owned (Jinja-rendered) and will be updated automatically.

## 2026-03-15 — Frontend v0.17.0

### useCopyToClipboard hook, KeyValueBadge copy support, grouped sidebar navigation

**What changed:**

1. **New `useCopyToClipboard` hook** (`src/hooks/use-copy-to-clipboard.ts`) — Reusable hook for clipboard copy with visual feedback. Returns `{ copyState, copy, reset }` where `copyState` cycles through `'idle' → 'success'/'error' → 'idle'` with a configurable reset delay (default 1500ms). Eliminates duplicated clipboard logic across components.

2. **`KeyValueBadge` copy support** (`src/components/ui/key-value-badge.tsx`) — New optional `copyValue` prop. When provided, hovering the badge reveals a copy icon; clicking copies the value to clipboard with success/error feedback. Uses the new `useCopyToClipboard` hook. (Note: `src/components/ui/` is `_skip_if_exists` — existing apps must manually update their copies.)

3. **Grouped sidebar navigation** (`src/components/layout/sidebar.tsx`) — `SidebarItem` now supports an optional `children` array for grouped navigation. Child items render indented below the parent, hidden when sidebar is collapsed. Parent highlights when any child route is active. Backward-compatible — items without `children` render identically to before.

Frontend template files changed:
- `src/hooks/use-copy-to-clipboard.ts` (new)
- `src/components/ui/key-value-badge.tsx` (updated — `_skip_if_exists`, won't auto-update)
- `src/components/layout/sidebar.tsx` (updated — template-owned, will auto-update)
- `knip-template-ignore.json` (updated)

**Migration steps:**
1. `copier update --trust` on frontend — updates sidebar.tsx (template-owned) and knip-template-ignore.json automatically.
2. **KeyValueBadge**: If your app uses `key-value-badge.tsx` with inline clipboard logic (like EI), refactor to use `useCopyToClipboard` hook. The template version is `_skip_if_exists` so won't overwrite your copy.
3. **Grouped sidebar**: No action needed unless your app has customized `sidebar.tsx` — copier's three-way merge will apply the changes. If you have grouped nav items, add `children` arrays to your `sidebar-nav.ts`.
4. Any component with duplicated clipboard logic can now use `import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard'` instead.

## 2026-03-09 — Frontend v0.16.0

### Validation pipeline improvements

**What changed:** Several improvements to the validation pipeline in the frontend template:
- Removed `validation_credential_id` from `copier.yml` — credentials are now fully app-customized in the `Jenkinsfile.validation` (which is `_skip_if_exists`)
- Added resource requests (1 CPU, 3.5Gi memory) to the validation K8s Job
- Enabled backend log streaming in validation entrypoint for better diagnostics
- Added `--retries=2` to Playwright in validation entrypoint
- Fixed Groovy parse error in validation log cleanup
- Used `utils.cleanLog()` for validation log cleanup instead of shell sed/tr
- Strip ANSI codes and Unicode emoji from validation.log

Frontend template files changed:
- `copier.yml` (removed `validation_credential_id` variable)
- `template/Jenkinsfile.validation.jinja` (simplified, credentials removed from template)
- `template/scripts/validation-entrypoint.sh` (retries, log streaming, cleanup improvements)

**Migration steps:**
1. `copier update --trust` on frontend — only updates `.copier-answers.yml` (removes `validation_credential_id`).
2. `Jenkinsfile.validation` and `scripts/validation-entrypoint.sh` are `_skip_if_exists` — existing files won't be overwritten. If you want the new entrypoint improvements, manually update your copies from the template's `test-app/` versions.

## 2026-03-09 — Backend v0.12.0, Frontend v0.15.0

### Jenkins validation pipeline support

**What changed:** Both templates now support a Jenkins validation pipeline that runs test suites before promoting images to `:latest`. When `validation_jenkins_job` is set, the Jenkinsfile builds without tagging `:latest`, archives build metadata as a JSON artifact, and triggers a validation job. The validation job (in the frontend template) resolves the image pair, clones source repos, builds a validation Docker image, runs backend + frontend tests in a K8s Job, then promotes images and deploys Helm on success.

New backend variables:
- `validation_jenkins_job` — validation job name (empty = old build+deploy flow)

New frontend variables:
- `validation_jenkins_job` — validation job name (empty = old build+deploy flow)
- `backend_repo_url` — backend git URL for cloning in validation
- `backend_image_name` — backend Docker image for crane tag promotion
- `backend_jenkins_job` — backend Jenkins job name for copyArtifacts
- `frontend_jenkins_job` — frontend Jenkins job name for copyArtifacts
- `validation_image_name` — validation Docker image name
- `validation_credential_id` — Jenkins secret file credential ID for test env vars

New frontend template files (all `_skip_if_exists`, excluded when `validation_jenkins_job` is empty):
- `Jenkinsfile.validation.jinja`
- `Dockerfile.validation`
- `scripts/validation-entrypoint.sh`

**Migration steps:**
1. `copier update --trust` on backend — adds `validation_jenkins_job` variable. Set to your validation job name or leave empty.
2. `copier update --trust` on frontend — adds all new variables. Provide values for your app.
3. For apps not yet using validation: existing Jenkinsfiles are `_skip_if_exists` and won't change.
4. For apps adopting validation: after `copier update`, manually update the existing Jenkinsfile to the new flow (or delete it and re-run `copier update` to get the template version).
5. Create the validation Jenkins pipeline job pointing to `Jenkinsfile.validation` in the frontend repo.
6. If the app needs test secrets (S3, OIDC, etc.), set `validation_credential_id` and create the corresponding Jenkins secret file credential.

## 2026-03-09 — Frontend v0.14.3

### Frontend: Fix useListLoadingInstrumentation not emitting ready when query data is cached on mount

**What changed:** When a component mounted with query data already in the TanStack Query cache (`isLoading=false`, `isFetching=false` from the start), the `useListLoadingInstrumentation` hook never entered the loading state and therefore never transitioned to `ready`. This caused `waitForListLoading()` calls in Playwright tests to time out. The fix emits `ready` immediately on first render when data is already available.

Frontend template files changed:
- `template/src/lib/test/query-instrumentation.ts`

**Migration steps:**
1. Run `copier update` on the frontend — the file is template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Frontend v0.14.2

### Frontend: Whitelist 400 errors in Playwright console handler

**What changed:** The console error handler in `fixtures-infrastructure.ts` now whitelists HTTP 400 (BAD REQUEST) responses. When OIDC is disabled in test mode, navigating to `/api/auth/login` returns 400, and the browser's error message doesn't include the URL path — so the existing `/api/auth/` filter didn't catch it.

### Frontend: Make auth-shell tests conditional on SIDEBAR_VISIBLE

**What changed:** `auth-shell.spec.ts` now imports `SIDEBAR_VISIBLE` from `consts.ts` and skips sidebar/hamburger tests when it's `false`. Apps with `use_app_shell=true` but `SIDEBAR_VISIBLE=false` (top bar only, no sidebar) were failing because the test assumed a hamburger button always exists.

Frontend template files changed:
- `template/tests/support/fixtures-infrastructure.ts.jinja`
- `template/tests/infrastructure/auth/auth-shell.spec.ts`

**Migration steps:**
1. Run `copier update` on the frontend — both files are template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Frontend v0.14.1

### Frontend: Templatize backend-url.ts with backend_port variable

**What changed:** `tests/support/backend-url.ts` is now a Jinja template (`backend-url.ts.jinja`) that renders the `DEFAULT_BACKEND_URL` using the `backend_port` copier variable instead of hardcoding port 5000. This matches how `vite.config.ts`, `nginx.conf`, and `consts.ts` already work.

Frontend template files changed:
- `template/tests/support/backend-url.ts` → `template/tests/support/backend-url.ts.jinja`

**Migration steps:**
1. Run `copier update` on the frontend — the file is template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Frontend v0.14.0

### Frontend: SseGate component, SSE auto-connect fix, test improvements

**What changed:** Four related improvements to SSE and test infrastructure:

1. **New `SseGate` component** (`src/components/sse/sse-gate.tsx`). Blocks rendering of children until the SSE connection is established. Used in `SseProviders` to ensure the app only renders once SSE is ready.

2. **SSE auto-connect in all modes.** Removed the `hasSharedWorkerParam`/`shouldAutoConnect` guard in `sse-context-provider.tsx` that was preventing SSE from auto-connecting in test mode. SSE now connects unconditionally on mount.

3. **Infrastructure tests use `fixtures-infrastructure` directly.** `tests/infrastructure/auth/auth.spec.ts` and `tests/infrastructure/test-infrastructure.spec.ts` now import from `fixtures-infrastructure` instead of `fixtures`. Infrastructure tests should not depend on app-specific domain fixtures.

4. **Auth tests use `roles: ['editor']` and 401 tests re-enabled.** All `auth.createSession()` calls in infrastructure auth tests now pass `roles: ['editor']` to match role-gated backends. The two previously-skipped 401 redirect tests are now enabled using `auth.forceError(401)` to reliably trigger the redirect flow.

Frontend template files changed:
- `template/src/components/sse/sse-gate.tsx` — new file
- `template/src/providers/sse-providers.tsx` — wraps `DeploymentProvider` in `SseGate`
- `template/src/contexts/sse-context-provider.tsx` — removed `shouldAutoConnect` guard
- `template/tests/infrastructure/auth/auth.spec.ts` — `fixtures-infrastructure` import, `roles: ['editor']`, re-enabled 401 tests
- `template/tests/infrastructure/auth/auth-shell.spec.ts` — `roles: ['editor']` on all sessions
- `template/tests/infrastructure/test-infrastructure.spec.ts` — `fixtures-infrastructure` import
- `copier.yml` — exclude `src/components/sse` when `use_sse=false`
- `template/knip-template-ignore.json` — added `src/components/sse/**`

**Migration steps:**
1. Run `copier update` on the frontend — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-07 — Backend v0.11.0

### Backend: Reverse proxy support (ProxyFix + Waitress trusted_proxy)

**What changed:** The backend now correctly handles `X-Forwarded-*` headers from reverse proxies (nginx, ingress controllers, etc.):

1. **`ProxyFix` middleware** added at the end of `create_app()`. Rewrites `request.remote_addr`, `request.url_root`, and `request.scheme` from `X-Forwarded-For`, `X-Forwarded-Host`, and `X-Forwarded-Proto` headers respectively. Configured with `x_for=1, x_host=1, x_proto=1`.

2. **Waitress `trusted_proxy` settings** added to production server startup. Configures Waitress to trust proxy headers from any upstream (`trusted_proxy="*"`, `trusted_proxy_count=1`) and passes `x-forwarded-for`, `x-forwarded-proto`, and `x-forwarded-host`.

3. **Debug logging in `check_authorization()`** — when a 403 is raised (no recognized role, or insufficient permissions), the user's roles, configured roles, and required roles are now logged at DEBUG level for easier diagnosis.

Backend template files changed:
- `template/app/__init__.py.jinja` — added `ProxyFix` import and middleware setup before `return app`
- `template/run.py` — added `trusted_proxy`, `trusted_proxy_count`, `trusted_proxy_headers` to Waitress `serve()` call
- `template/app/utils/auth.py` — added `logger.debug()` calls before both `AuthorizationException` raises in `check_authorization()`

**Migration steps:**
1. Run `copier update` on the backend — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes required.

## 2026-03-01 — Backend v0.10.0

### Backend: OIDC state in URL parameter + partitioned cookies (iframe support)

**What changed:** Two related improvements that allow the OIDC login flow to work inside cross-origin iframes (e.g. Home Assistant):

1. **State moved from cookie to encrypted URL parameter.** The PKCE auth state (code_verifier, redirect URL, nonce) is now encrypted with Fernet and carried as the OAuth `state` query parameter instead of a short-lived `auth_state` cookie. Third-party cookie blocking in cross-origin iframes would have silently dropped that cookie, breaking the callback.

2. **Partitioned (CHIPS) cookie support.** A new `OIDC_COOKIE_PARTITIONED` env var (default `False`) sets the `Partitioned` attribute on all auth cookies. When set alongside `SameSite=None; Secure`, this allows cookies to work in cross-origin iframes without being treated as third-party cookies.

3. **`get_cookie_kwargs()` replaces `get_cookie_secure()`.** A single helper now returns all common `set_cookie()` keyword arguments (httponly, secure, samesite, partitioned), keeping every call-site consistent.

4. **`itsdangerous` dependency removed.** Auth state is now encrypted with `cryptography.fernet` (already a dependency). `itsdangerous` is no longer in the OIDC dependency block.

Backend template files changed:
- `template/app/config.py.jinja` — added `OIDC_COOKIE_PARTITIONED` env var and `oidc_cookie_partitioned` setting
- `template/app/utils/auth.py` — `serialize_auth_state`/`deserialize_auth_state` use Fernet; `get_cookie_secure()` replaced by `get_cookie_kwargs()`
- `template/app/services/oidc_client_service.py` — added `create_auth_state()` and `build_authorization_url()` methods; `generate_authorization_url()` is now a convenience wrapper
- `template/app/api/auth.py` — login endpoint no longer sets `auth_state` cookie; callback reads encrypted state from `state` param; logout uses `get_cookie_kwargs()`
- `template/app/api/oidc_hooks.py` — uses `get_cookie_kwargs()`
- `template/app/api/testing_auth.py` — uses `get_cookie_kwargs()`
- `template/pyproject.toml.jinja` — removed `itsdangerous` from OIDC dependencies

**Migration steps:**
1. Run `copier update` on the backend — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes required.
3. **Optional:** To enable iframe embedding, set `OIDC_COOKIE_PARTITIONED=True`, `OIDC_COOKIE_SAMESITE=None`, and ensure your deployment uses HTTPS (`OIDC_COOKIE_SECURE=True` or `BASEURL=https://...`).
4. If your app has `itsdangerous` pinned in its `pyproject.toml` for other purposes, leave it. If it was only there for OIDC, you may remove it and run `poetry lock`.

## 2026-03-01 — Frontend v0.13.3

### Frontend: Increase nginx upload size limit to 50 MB

**What changed:** Added `client_max_body_size 50M;` to the `http {}` block in `nginx.conf`. The previous default (1 MB) was causing 413 Entity Too Large errors on file uploads. Note: this limit is enforced by nginx independently of `proxy_buffering off` — both must be sufficient for large uploads.

Frontend template files changed:
- `template/nginx.conf.jinja` — added `client_max_body_size 50M;` in the `http {}` block

**Migration steps:**
1. Run `copier update` on the frontend — the only change is in `nginx.conf` (template-maintained).
2. No app-owned file changes required.

## 2026-02-28 — Backend v0.9.1

### Backend: Normalize BASEURL trailing slash

**What changed:** `Settings.load()` now strips any trailing slash from `BASEURL` before storing it. This prevents double-slash URLs (e.g. `https://example.com//api/auth/callback`) when `BASEURL` is configured with a trailing slash.

Backend template files changed:
- `template/app/config.py.jinja` — `baseurl=env.BASEURL.rstrip("/")`

**Migration steps:**
1. Run `copier update` on the backend — the only change is in `app/config.py` (template-maintained).
2. No app-owned file changes required.


## 2026-02-27 — Backend v0.9.0, Frontend v0.13.0

### Backend: Role hierarchy and 403 forbidden handling

**What changed:** Added a full role hierarchy system to `AuthService` with `read_role`, `write_role`, `admin_role`, and `additional_roles` parameters. Method-based access control now automatically infers required role from HTTP method (GET/HEAD → read_role, mutating methods → write_role). The `@allow_roles` decorator overrides method inference. `/api/auth/self` now returns 403 when a user is authenticated but has no recognized hierarchical role. Startup validation (`validate_allow_roles_at_startup`) catches typos in `@allow_roles` decorators at boot time. OpenAPI spec is annotated with per-endpoint security info (`x-required-role`, `x-auth-roles`).

Backend template files changed:
- `template/app/services/auth_service.py` — Role hierarchy: `read_role`, `write_role`, `admin_role`, `additional_roles` params; `expand_roles()`, `resolve_required_role()`, `configured_roles`, `hierarchy_roles`
- `template/app/utils/auth.py` — `@safe_query` decorator; updated `check_authorization()` with `auth_service` + `http_method` params; `validate_allow_roles_at_startup()`
- `template/app/utils/spectree_config.py` — `BearerAuth` JWT security scheme; `annotate_openapi_security()` that injects `x-required-role` into OpenAPI operations
- `template/app/__init__.py.jinja` — Added startup block (within `{% if use_oidc %}`): `validate_allow_roles_at_startup` + `annotate_openapi_security`
- `template/app/api/auth.py` — 403 `AuthorizationException` for users with no recognized hierarchical role; role expansion in test sessions and local user
- `template/app/api/oidc_hooks.py` — Role expansion in test sessions; pass `http_method` to `check_authorization` and `authenticate_request`

**App configuration required:** After running `copier update`, edit `app/services/container.py` and add role parameters to your `AuthService` provider:

```python
auth_service = providers.Singleton(
    AuthService,
    config=config,
    write_role="editor",          # required for POST/PUT/PATCH/DELETE
    # additional_roles=["pipeline"],  # for non-hierarchical roles (e.g. CI/CD)
)
```

**Migration steps:**
1. Run `copier update` on the backend — template-maintained files update automatically.
2. Edit `app/services/container.py`: add `write_role="editor"` (and `additional_roles` if needed) to the `AuthService` provider.
3. If you use `@allow_roles` decorators, review them — startup validation will now raise `ValueError` at boot for any role not in `configured_roles`.

### Frontend: 403 forbidden handling and role constants generation

**What changed:** Added 403 detection throughout the auth stack. `isForbiddenError()` predicate added to `api-error.ts`. `isForbidden` flag added to `useAuth`, `AuthContext`, and `AuthGate`. `AuthGate` now shows a "No Access" screen with a logout button when the backend returns 403 from `/api/auth/self`. `generate-api.js` now generates `roles.ts` and `role-map.json` from `x-required-role` annotations in the OpenAPI spec (used with `Gate` components to enforce role checks in the UI).

Frontend template files changed:
- `template/src/lib/api/api-error.ts` — Added `isForbiddenError()` predicate for 403 detection
- `template/src/hooks/use-auth.ts` — Added `isForbidden` flag; 403 excluded from `effectiveError`
- `template/src/contexts/auth-context.tsx` — Added `isForbidden` to `AuthContextValue`; emits `'forbidden'` test event phase
- `template/src/components/auth/auth-gate.tsx` — Added `AuthForbidden` component (lock icon, "No Access" message, logout button)
- `template/src/lib/test/test-events.ts` — Added `'forbidden'` to `UiStateTestEvent.phase` union
- `template/scripts/generate-api.js` — Added `generateRoles()` producing `roles.ts` (typed role constants) and `role-map.json` (hook→constant mapping) from OpenAPI `x-required-role` annotations

**Migration steps:**
1. Run `copier update` on the frontend — all changed files are template-maintained.
2. No app-owned file changes required.
3. After running `generate-api` with a backend that has the role system configured, `roles.ts` will contain typed constants for each non-reader role endpoint. Use these with `Gate` components to enforce access in the UI (app-specific work, no template changes needed).

## 2026-02-25 — Backend v0.8 / v0.8.1, Frontend v0.12 / v0.12.1

### Backend: Unified check script and vulture dead code detection

**What changed:** Added `scripts/check.py` — a unified code quality runner that executes ruff, mypy, vulture, and pytest in sequence. Added vulture as a dev dependency with `vulture_whitelist.py` for false positives (callback signatures, TYPE_CHECKING patterns). Tightened ruff config: added ERA (commented-out code) and RUF100 (unused noqa) rules, per-file-ignores for alembic and tools directories.

Backend template files changed:
- `template/scripts/check.py` — **New:** unified check runner
- `template/vulture_whitelist.py` — **New:** vulture false-positive whitelist (app-owned via `_skip_if_exists`)
- `template/pyproject.toml.jinja` — Added vulture dep, `check` script entry point, ERA/RUF100 rules, per-file-ignores, mypy override for vulture_whitelist
- `template/app/__init__.py.jinja` — Removed now-unnecessary `# noqa: F401` comments
- `template/app/database.py` — Fixed import sort order
- `template/app/config.py.jinja` — Used `_options` for unused param in non-database path (v0.8.1)
- `template/alembic/env.py` — Removed unnecessary `# noqa: E402`
- `template/tests/conftest.py` — Removed unnecessary F401 from noqa directive
- `copier.yml` — Added `vulture_whitelist.py` to `_skip_if_exists`

### Frontend: Knip dead code analysis

**What changed:** Added knip for detecting unused files, exports, types, and dependencies. Template-owned files are excluded via `knip-template-ignore.json` (template-maintained). Template-provided dependencies that are only used in ignored files are listed in `ignoreDependencies`.

Frontend template files changed:
- `template/knip.config.ts` — **New:** knip configuration loading template-ignore list
- `template/knip-template-ignore.json` — **New:** template-owned file exclusions (~60 paths)
- `template/package.json.jinja` — Added `knip` devDependency, `check:knip` script, updated `check` to include knip

**Migration steps:**
1. Run `copier update` for both backend and frontend — template-maintained files update automatically.
2. Backend: Run `poetry lock && poetry install` to install vulture. Run `ruff check --fix .` to auto-fix RUF100/ERA findings in app-owned files. Review and extend `vulture_whitelist.py` for any app-specific false positives.
3. Frontend: Run `pnpm install` to install knip. Run `pnpm run check:knip` and fix any findings in app-owned code (remove unused exports, delete unused files, unexport types only used locally).
4. Use `poetry run check` (backend) or `pnpm run check` (frontend) as the single command for all code quality checks.

## 2026-02-21 — Frontend v0.9

### SSE: switch from named events to {type, payload} envelope format

**What changed:** The SSE Gateway now sends all events as unnamed data-only messages with a `{type, payload}` envelope instead of named SSE events. This eliminates a race condition where events were silently dropped before per-event-type `addEventListener` calls could be attached (especially on fast backend responses).

Frontend template files changed:
- `src/workers/sse-worker.ts` — Replaced per-event subscriptions with single `onmessage` handler; removed `subscribe` command from worker protocol; added version payload caching for late-joining tabs
- `src/contexts/sse-context-provider.tsx` — Replaced per-event `addEventListener`/subscription logic with single `onmessage` envelope unwrapping; removed `attachedEventsRef`, `workerSubscribedEventsRef`, `ensureDirectEventSourceListener`, `ensureWorkerSubscription`
- `tests/infrastructure/sse/sse-connectivity.spec.ts` — Updated task event tests to use envelope format; added 2 SharedWorker tests
- `tests/infrastructure/deployment/deployment-banner.spec.ts` — Removed `correlation_id` matching (not in version payloads)
- `tests/infrastructure/sse/task-events.spec.ts` — **New:** generic task event infrastructure tests (receive, payload structure, sequencing)

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained and will be updated automatically.
2. Run `pnpm update ssegateway` to pick up the new SSE Gateway `#stable` commit.
3. If your app has custom code that uses `es.addEventListener('eventName', ...)` to listen for SSE events, switch to `es.onmessage` and unwrap the `{type, payload}` envelope.
4. If your app sends `subscribe` commands to the SharedWorker, remove them — the worker no longer needs per-event subscriptions.

## 2026-02-20 (v0.7.2)

### Stderr logging in testing mode for Playwright visibility

**What changed:** All apps now get stderr logging enabled when `FLASK_ENV=testing`, so request logs and exception tracebacks appear in the process output captured by Playwright.

Files changed:
- `template/app/__init__.py.jinja` — Adds a `StreamHandler(sys.stderr)` block before the log capture handler. The `root_logger.setLevel(logging.INFO)` call moves into this block so it's set regardless of SSE feature flag. The `import logging` is no longer conditional on `use_sse`.

### dev-sse-gateway.sh uses backend_port variable

**What changed:** The dev SSE gateway script now uses the `backend_port` Copier variable instead of hardcoded port 5000. Also excluded from non-SSE apps via `_exclude`.

Files changed:
- `template/scripts/dev-sse-gateway.sh` → `template/scripts/dev-sse-gateway.sh.jinja` — Uses `{{ backend_port }}`
- `copier.yml` — Added `scripts/dev-sse-gateway.sh` to SSE exclude list

### Import ordering fix in testing_sse.py

**What changed:** Fixed ruff I001 import sorting violation in `testing_sse.py`.

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained and will be updated automatically.
2. No app-owned file changes needed.

## 2026-02-19 (v0.7.0)

### Subject-based task event filtering

**What changed:** Task events (started, progress, completed, failed) are no longer broadcast to all SSE connections. They are now filtered by the subject of the user who started the task. Version events remain broadcast to everyone.

Files changed:
- `template/app/services/sse_connection_manager.py` — `send_event()` accepts optional `target_subject` parameter; in broadcast mode, restricts delivery to connections with matching subject or the `"local-user"` sentinel
- `template/app/services/task_service.py` — `start_task()` accepts `caller_subject`; threads it through `_execute_task()`, `TaskProgressHandle`, and `_broadcast_task_event()` to reach `send_event(target_subject=...)`
- `template/app/schemas/task_schema.py` — `TaskInfo` gains `subject: str | None` field
- `template/app/api/testing_sse.py` — `start_test_task()` derives `caller_subject` from `get_auth_context()` and passes it to `start_task()`
- `template/regen.sh` — Added `--vcs-ref HEAD` so copier picks up uncommitted template changes

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained and will be updated automatically.
2. If your app calls `task_service.start_task(task, ...)` directly, add `caller_subject=<subject>` to filter task events to that user's SSE connections. Pass `None` to broadcast to all (backward-compatible default).
3. If your app has custom identity verification on SSE task subscriptions (e.g., IoTSupport's `_verify_identity()`), the template now handles subject filtering at the event delivery layer. The app-level check may still be needed for subscription authorization but is no longer the only line of defense.

## 2026-02-16 (v0.6.3)

### Background service startup registry and register_root_blueprints hook

**What changed:**

1. **`container.py` scaffold** — Adopted the `register_for_background_startup` pattern. Infrastructure service startup is now declared co-located with provider definitions, and `start_background_services(container)` runs them all. App-specific services register their starters the same way.

2. **`__init__.py`** — Inline startup calls (`temp_file_manager().start_cleanup_thread()`, `task_service().startup()`, `s3_service().startup()`, `frontend_version_service()`) replaced with a single call to `start_background_services(container)`.

3. **`startup.py` scaffold** — New hook: `register_root_blueprints(app)` for registering blueprints directly on the Flask app (not under `/api`). Called after template blueprints (health, metrics) and before feature-gated blueprints (SSE, OIDC, S3).

**Migration steps:**
1. Run `copier update` — `__init__.py` is template-maintained and will be updated automatically.
2. Add to your `app/startup.py` (app-owned):
   ```python
   def register_root_blueprints(app: Flask) -> None:
       """Register app-specific blueprints directly on the app."""
       pass
   ```
3. Add the startup registry to your `app/services/container.py` (app-owned):
   ```python
   from collections.abc import Callable
   from typing import Any

   _background_starters: list[Callable[[Any], None]] = []

   def register_for_background_startup(fn: Callable[[Any], None]) -> None:
       _background_starters.append(fn)

   # After each provider that needs startup:
   register_for_background_startup(lambda c: c.temp_file_manager().start_cleanup_thread())
   register_for_background_startup(lambda c: c.task_service().startup())
   # etc.

   def start_background_services(container: Any) -> None:
       for starter in _background_starters:
           starter(container)
   ```
4. Move any root-level blueprint registrations from `__init__.py` overrides into `register_root_blueprints()`.

## 2026-02-16 (v0.6.2)

### SSE OIDC identity auto-binding in connect callback

**What changed:** `app/api/sse.py` is now a Jinja template (`sse.py.jinja`) that conditionally includes OIDC identity binding when `use_oidc=true`.

When both `use_sse` and `use_oidc` are enabled:
- `_extract_token_from_headers(headers, cookie_name)` — extracts Bearer token or cookie from forwarded SSE Gateway headers
- `_bind_identity(request_id, headers, sse_connection_manager, auth_service, settings)` — validates OIDC token and binds identity to the SSE connection (falls back to sentinel subject when OIDC is disabled at runtime)
- `handle_callback()` injects `AuthService` and calls `_bind_identity()` after `on_connect()`

When `use_oidc=false`: no OIDC imports, no identity binding code — identical to the previous `sse.py`.

**Migration steps:**
1. Run `copier update` — `sse.py` is template-maintained and will be updated automatically.
2. No breaking changes. Identity binding is additive and only active when OIDC is enabled.
3. If your app has custom code in `sse.py`, move it to a separate module — `sse.py` will be overwritten by copier.

## 2026-02-16 (v0.6.1)

### SSE connection manager: identity binding and disconnect observers

**What changed:** `sse_connection_manager.py` now supports:
- `bind_identity(request_id, subject)` — associate an OIDC subject with an SSE connection
- `get_connection_info(request_id)` — retrieve connection info including bound identity
- `register_on_disconnect(callback)` — observe disconnect events (symmetric with existing `register_on_connect`)
- `ConnectionInfo` dataclass — returned by `get_connection_info()`
- `SSE_IDENTITY_BINDING_TOTAL` Prometheus counter

Identity map is cleaned up automatically on disconnect. Disconnect observers are notified outside the lock, matching the existing on_connect pattern.

**Migration steps:**
1. Run `copier update` — `sse_connection_manager.py` is template-maintained.
2. No breaking changes. New features are additive.

## 2026-02-16 (v0.6.0)

### Background service lifecycle improvements

**What changed:**

1. **`run.py`** — Werkzeug reloader parent detection. In debug mode, background services are now skipped in the reloader parent process to avoid duplicate threads, MQTT connections, etc.

2. **`task_service.py`** — Cleanup thread start is deferred to a new `startup()` method instead of running in `__init__()`. This improves test isolation (no daemon threads spawned during container construction).

3. **`s3_service.py`** — Added `startup()` (wraps `ensure_bucket_exists()` with warning-only error handling), `list_objects(prefix)` (paginated listing), and `delete_prefix(prefix)` (best-effort bulk delete). Also moved `mypy_boto3_s3` imports under `TYPE_CHECKING` and added a module logger.

4. **`__init__.py`** — Background service startup block now calls `task_service.startup()` and `s3_service.startup()` instead of inline code.

5. **`conftest_infrastructure.py`** — Test fixtures (`app`, `oidc_app`) now pass `skip_background_services=True` to `create_app()`. Background cleanup threads and S3 bucket checks are no longer started during tests.

6. **`testing_service.py`** — Added `clear_all_sessions()` method for test isolation.

**Migration steps:**
1. Run `copier update` — all changed files are template-maintained.
2. If your app starts background services in `__init__.py` (e.g., `s3_service.ensure_bucket_exists()`), remove that code — the template now handles it via `s3_service.startup()`.
3. If your tests relied on background services starting during `create_app()`, they now need explicit startup calls or the services must register for lifecycle STARTUP events.

## 2026-02-16

### Add SpectTree validation and send_task_event endpoint to testing SSE endpoints

**What changed:** The testing SSE endpoints (`app/api/testing_sse.py`) now use SpectTree schema validation, matching the pattern used by `testing_content.py` and other template endpoints. A new endpoint `POST /api/testing/sse/task-event` allows integration tests to inject fake task events directly into SSE connections without running actual background tasks.

New files:
- `template/app/schemas/testing_sse.py` — Pydantic request/response schemas for all testing SSE endpoints

Files changed:
- `template/app/api/testing_sse.py` — Added `@api.validate()` decorators, added `send_task_event` endpoint, switched to lazy `reject_if_not_testing` import pattern; declared `HTTP_400=TestErrorResponseSchema` on `send_task_event` so SpectTree doesn't reject error responses
- `copier.yml` — Added `app/schemas/testing_sse.py` to SSE feature-flag exclusion list

**Migration steps:**
1. Run `copier update` — both files are template-maintained and will be created/updated automatically
2. If your app has a custom `app/schemas/testing_sse.py`, it will be overwritten by the template version. Move any app-specific schemas to a different file name
3. If your app's integration tests reference `resp.json()["task_id"]` from the start-task endpoint, no change needed — the response format uses snake_case field names
4. If your app's tests assert camelCase keys in testing SSE responses (e.g., `requestId`, `taskId`, `eventType`), update to snake_case (`request_id`, `task_id`, `event_type`)

## 2026-02-14

### Fix auth/self endpoint not extracting token from request

**What changed:** The `/api/auth/self` endpoint is decorated with `@public` (to handle its own auth logic), but this meant the `before_request` OIDC hook skipped it entirely. When OIDC is enabled and a user has a valid token cookie, the endpoint would fail with "No valid token provided" because `get_auth_context()` returned `None`.

Fixed by injecting `AuthService` and falling back to manually extracting and validating the token from the request when `auth_context` is not set by the hook.

Files changed:
- `template/app/api/auth.py` — Added `auth_service` DI parameter; added fallback token extraction via `extract_token_from_request()`

**Migration steps:**
1. Run `copier update` — this file is template-maintained and will be updated automatically

### Upgrade ruff to 0.11+ and modernize Python syntax

**What changed:** Upgraded ruff from `^0.1.0` to `^0.11.0` to support `py313` target version. Fixed all new lint findings:

- Moved ruff config to `[tool.ruff.lint]` section (old top-level format deprecated)
- `str, Enum` → `StrEnum` (UP042) in `task_schema.py`, `lifecycle_coordinator.py`
- `Generator[X, None, None]` → `Generator[X]` (UP043) in `conftest_infrastructure.py`, `sse_utils.py`
- `TypeVar` → PEP 695 type parameters (UP047) in `request_parsing.py`
- Quoted type annotations → unquoted (UP037) in `alembic/env.py`
- Import sorting fixes (I001) in `database.py`

Files changed:
- `template/pyproject.toml.jinja` — ruff `^0.11.0`, `[tool.ruff.lint]` config format
- `template/app/schemas/task_schema.py` — `StrEnum`
- `template/app/utils/lifecycle_coordinator.py` — `StrEnum`
- `template/app/utils/request_parsing.py` — PEP 695 type params
- `template/app/utils/sse_utils.py` — simplified `Generator` type
- `template/app/database.py` — import order
- `template/alembic/env.py` — unquoted annotation
- `template/tests/conftest_infrastructure.py.jinja` — simplified `Generator` types

**Migration steps:**
1. Run `copier update` — template-maintained files will be updated automatically
2. After update, run `ruff check --fix .` to auto-fix any remaining issues in app-owned files
3. Manually fix any `str, Enum` → `StrEnum` classes in app-owned code

## 2026-02-13

### Add service layer files (infrastructure services and DI container scaffold)

**What changed:** Added the service layer files extracted from Electronics Inventory. These provide the infrastructure services that all generated apps share, plus a scaffold DI container for app-specific customization.

Template-maintained service files (overwritten on `copier update`):
- `template/app/services/__init__.py` - Empty services package
- `template/app/services/health_service.py` - Health check callback registry (healthz/readyz/drain)
- `template/app/services/metrics_service.py` - Background polling service for Prometheus metrics
- `template/app/services/task_service.py` - Background task management with SSE progress updates
- `template/app/services/base_task.py` - Abstract base classes for background tasks (BaseTask, BaseSessionTask)
- `template/app/services/sse_connection_manager.py` - SSE Gateway token mapping and event delivery (always included)
- `template/app/services/auth_service.py` - JWT validation with JWKS discovery (use_oidc)
- `template/app/services/oidc_client_service.py` - OIDC authorization code flow with PKCE (use_oidc)
- `template/app/services/s3_service.py` - S3-compatible storage operations (use_s3)
- `template/app/services/cas_image_service.py` - CAS thumbnail generation and image processing (use_s3)
- `template/app/services/frontend_version_service.py` - Frontend version SSE notifications (use_sse)
- `template/app/services/diagnostics_service.py` - Request/query performance profiling (use_database)

App-maintained scaffold (skip_if_exists, generated once):
- `template/app/services/container.py.jinja` - DI container with infrastructure providers; app adds domain providers

Also changed:
- `template/app/utils/temp_file_manager.py` - Reordered constructor params to put `lifecycle_coordinator` first; added defaults for `base_path` ("/tmp/app-temp") and `cleanup_age_hours` (24.0) so the scaffold container works without app-specific config

**Migration steps:**
1. Copy all new service files from template into your app's `app/services/` directory
2. Review your existing `app/services/container.py` - the scaffold is a starting point; your container should already have these infrastructure providers plus your domain-specific ones
3. If your `TempFileManager` usage passes `base_path` and `cleanup_age_hours` as positional args, update to use keyword arguments since the parameter order changed (lifecycle_coordinator is now first)
4. The `sse_connection_manager.py` and `base_task.py` are always included regardless of feature flags (TaskService depends on them)

## 2026-02-13

### Add schemas, build/deploy, alembic, scripts, and test infrastructure files

**What changed:** Added the remaining template files extracted from Electronics Inventory:

Schema files:
- `template/app/schemas/__init__.py` - Schema package init
- `template/app/schemas/health_schema.py` - Health check response schema (Pydantic)
- `template/app/schemas/task_schema.py` - Task status, events, progress schemas (Pydantic)
- `template/app/schemas/sse_gateway_schema.py` - SSE Gateway callback/send schemas (Pydantic)
- `template/app/schemas/upload_document.py` - Document upload schemas (use_s3, generic - no EI model dependency)

Build/deploy files:
- `template/run.py` - Development/production server entry point (Waitress + Flask debug)
- `template/.gitignore` - Standard Python/Flask gitignore
- `template/Dockerfile.jinja` - Multi-stage Docker build with feature-flagged system deps
- `template/Jenkinsfile.jinja` - Jenkins CI/CD pipeline with template variables
- `template/pyproject.toml.jinja` - Poetry project config with feature-flagged dependencies (skip_if_exists)
- `template/.env.example.jinja` - Environment variable documentation grouped by feature flag (skip_if_exists)

Alembic files (use_database only):
- `template/alembic.ini.jinja` - Alembic configuration with templated DB URL
- `template/alembic/env.py` - Alembic environment (offline/online migrations, test connection reuse)
- `template/alembic/script.py.mako` - Migration script template
- `template/alembic/versions/.gitkeep` - Empty versions directory

Scripts:
- `template/scripts/args.sh.jinja` - Shared variables (project name, ports) with template variables
- `template/scripts/build.sh` - Docker build script
- `template/scripts/dev-server.sh` - Development server restart loop
- `template/scripts/dev-sse-gateway.sh` - SSE Gateway development restart loop
- `template/scripts/initialize-sqlite-database.sh` - SQLite database initialization
- `template/scripts/push.sh` - Docker push to registry
- `template/scripts/run.sh` - Docker run script
- `template/scripts/stop.sh` - Docker stop script
- `template/scripts/testing-server.sh` - Testing server (generic, no EI references)

Test infrastructure:
- `template/tests/__init__.py` - Test package init
- `template/tests/conftest_infrastructure.py.jinja` - Infrastructure fixtures with feature-flagged sections (database clone pattern, OIDC mocks, SSE server, S3 checks)
- `template/tests/conftest.py` - Scaffold that imports infrastructure fixtures (skip_if_exists)

EI-specific code removed:
- `upload_document.py`: Replaced `AttachmentType` model import with generic `str | None`
- `pyproject.toml`: Removed openai, anthropic, celery, beautifulsoup4, validators, reportlab, types-beautifulsoup4 dependencies
- `conftest_infrastructure.py`: Removed AI/Mouser/document settings from `_build_test_app_settings`
- `testing-server.sh`: Replaced "Electronics Inventory" with generic "backend"
- `Dockerfile`: Changed from PyPy to CPython 3.12, removed jiter/openai patches

**Migration steps:**
1. These are new files - no migration needed for existing downstream apps
2. For new apps generated from the template, all files are created automatically
3. Existing apps should:
   - Compare their `pyproject.toml` against the template and ensure infrastructure dependencies match
   - Adopt `conftest_infrastructure.py` pattern: import infrastructure fixtures in `conftest.py`
   - Move from custom Dockerfile to the template Dockerfile pattern if not already using it
   - Replace EI-specific `upload_document.py` imports with generic types if using S3

## 2026-02-13

### Add core application files (app factory, config, CLI, exceptions, database)

**What changed:** Added the core application layer files extracted from Electronics Inventory:

- `template/app/__init__.py.jinja` - Flask application factory with feature-flagged sections for database, OIDC, S3, and SSE
- `template/app/app.py` - Custom Flask App class with typed container attribute
- `template/app/config.py.jinja` - Two-layer configuration (Environment + Settings) with feature-flagged field groups
- `template/app/cli.py.jinja` - CLI commands (upgrade-db, load-test-data) with feature-flagged database sections
- `template/app/consts.py.jinja` - Project constants scaffold (skip_if_exists)
- `template/app/app_config.py` - App-specific settings scaffold (skip_if_exists)
- `template/app/startup.py` - Hook functions scaffold (skip_if_exists)
- `template/app/exceptions.py` - Base exception classes scaffold (skip_if_exists)
- `template/app/extensions.py` - Flask-SQLAlchemy initialization (use_database only)
- `template/app/database.py` - Database operations: migrations, health checks, upgrade (use_database only)
- `template/app/models/__init__.py` - Empty models scaffold (skip_if_exists, use_database only)

EI-specific code removed: dashboard_metrics, sync_master_data_from_setup, SetupService import, InsufficientQuantityException, CapacityExceededException, DependencyException.

**Migration steps:**
1. These are new files - no migration needed for existing downstream apps
2. For new apps generated from the template, all files are created automatically
3. Existing apps should compare their `app/__init__.py`, `app/config.py`, `app/cli.py` against these templates and adopt the hook-based pattern if not already using it
