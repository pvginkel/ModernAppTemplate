# Porting an Existing Frontend onto the Template

This guide documents the strategy for porting an existing React frontend onto the ModernAppTemplate. It's based on the ElectronicsInventory port and covers the full process from preparation through verification.

## Overview

The porting process has five phases:

1. **Prepare** — upgrade the source app and resolve known friction points so the migration is clean
2. **Inventory** — diff the source app against a generated skeleton to produce a precise copy manifest
3. **Generate** — create the target project with `copier copy`
4. **Port** — copy domain files into the generated project
5. **Verify** — type-check, lint, build, and run tests

The key insight: the template owns infrastructure, the app owns domain logic. Porting means moving domain code into the template's structure. The more preparation you do in the source app (where you have a working test suite), the fewer surprises during migration.

## Prerequisites

- A working existing frontend to port from (must pass `pnpm run check` and `pnpm run build`)
- The template repo at `/work/ModernAppTemplate/frontend`
- Understanding of which feature flags the app needs:

| Flag | What it adds |
|------|-------------|
| `use_oidc` | Auth context, auth gate, user dropdown, login redirect, 401 handling |
| `use_s3` | File upload components (drop-zone), file validation, thumbnail URL utilities |
| `use_sse` | SSE context, SharedWorker, version tracking, deployment bar, task event hooks |

## Phase 1: Prepare the Source App

**Goal:** Make the source app's domain code compatible with a fresh `pnpm install` against the template's `package.json`. Every issue resolved here is an issue that won't block the migration.

### 1.1 Upgrade dependencies to match the template

Generate a fresh skeleton and compare the resolved versions:

```bash
cd /work/ModernAppTemplate/frontend
poetry run copier copy . /tmp/skeleton --trust --defaults \
  -d project_name=throwaway -d project_title=X \
  -d author_name=x -d author_email=x@x.com \
  -d use_oidc=true -d use_s3=true -d use_sse=true
cd /tmp/skeleton && pnpm install
```

Compare key package versions:

```bash
for pkg in @tanstack/react-router @tanstack/react-query react typescript vite tailwindcss; do
  old=$(cd /work/<App>/frontend && node -e "console.log(require('./node_modules/$pkg/package.json').version)")
  new=$(cd /tmp/skeleton && node -e "console.log(require('./node_modules/$pkg/package.json').version)")
  [ "$old" != "$new" ] && echo "$pkg: $old → $new"
done
```

Then upgrade each package in the source app, run the test suite, and fix breakage while the full app context is available. This is far easier than fixing type errors in a half-ported project.

**Known breaking changes from EI experience:**

| Package | Breaking Change | Typical Fix |
|---------|----------------|-------------|
| `@tanstack/react-router` 1.131 → 1.161+ | Route IDs for index routes changed (trailing slash). `useNavigate({ from: '/parts' })` becomes `'/parts/'` and vice versa. `search` param callbacks break when the path doesn't match. | Regenerate route tree with `tsr generate`, update all hardcoded route paths to match new IDs. |
| `@tanstack/react-query` 5.85 → 5.90+ | `mutate()` option callbacks (`onSuccess`, `onError`, `onSettled`) gained an additional argument. | Add the missing argument to every `.onSuccess?.(data, variables, context)` call. |

After each upgrade, run `pnpm run check && pnpm run build` to verify. Commit each upgrade separately so you can bisect if needed.

### 1.2 Adopt infrastructure tests into the template mother project

As you classify tests into infrastructure vs domain, adopt any infrastructure tests that make sense into the template mother project (`/work/ModernAppTemplate/frontend/tests/`). The port is the natural moment to do this — you're already separating the two concerns.

Infrastructure tests cover template-provided features: auth flow, SSE lifecycle, deployment banner, toast notifications, sidebar navigation, mobile menu, dialog accessibility, tooltip display, worker isolation, and test instrumentation.

For each infrastructure test:
1. Generalize it — remove domain-specific fixtures and replace with the template's test-app equivalents
2. Add it to the mother project's test suite
3. Verify it passes against the template's test-app
4. Remove it from the downstream app

Any infrastructure tests that are too app-specific to generalize easily can stay in the downstream app for now.

### 1.3 Fix customized template files

If the app has modified any template-owned files, refactor the domain code to work without the customization. This prevents breakage on future `copier update`.

**Known example — `tests/support/selectors.ts`:**

EI customized this template-owned file to re-export domain selectors:

```typescript
// EI's version (customized)
import { partsSelectors } from './selectors-domain';
export const selectors = { parts: partsSelectors, common: { ... } };
```

**Fix:** Update all page objects to import from `selectors-domain.ts` directly:

```typescript
// Before (fragile — depends on customized template file)
import { selectors } from '../selectors';
const input = selectors.parts.form.field('name');

// After (clean — imports from app-owned file)
import { partsSelectors } from '../selectors-domain';
const input = partsSelectors.form.field('name');
```

### 1.4 Fix misplaced files

Move any files that are in the wrong location per template conventions:

- Page objects should be in `tests/support/page-objects/`, not in test directories (e.g., move `tests/e2e/types/TypesPage.ts` → `tests/support/page-objects/types-page.ts`)

### 1.5 Verify the source app is clean

After all preparation work:

```bash
pnpm run check && pnpm run build
# Run domain Playwright tests if possible
```

Commit all preparation changes. The source app should now be at the latest dependency versions and free of template-file customizations.

## Phase 2: Inventory

**This is the most important phase.** Do not skip it. The EI port hit multiple issues from an incomplete inventory.

### 2.1 Generate a throwaway skeleton

```bash
cd /work/ModernAppTemplate/frontend
poetry run copier copy . /tmp/skeleton --trust --defaults \
  -d project_name=throwaway \
  -d project_title="Throwaway" \
  -d author_name="x" \
  -d author_email="x@x.com" \
  -d use_oidc=true \
  -d use_s3=true \
  -d use_sse=true
```

### 2.2 Produce file listings

```bash
# Template files (what copier generates)
(cd /tmp/skeleton && find . -type f | sed 's|^\./||' | sort) > /tmp/template-files.txt

# Source app files (all of src/ and tests/, plus top-level tests)
(cd /work/<App>/frontend && find src tests -type f | sort) > /tmp/app-files.txt
```

### 2.3 Classify every file

Compare the two listings. Every file in the source app falls into exactly one category:

| Category | Action | Example |
|----------|--------|---------|
| **Template-owned** (in both) | Do NOT copy — template generates it | `src/main.tsx`, `src/contexts/*.tsx`, `src/lib/test/*.ts` |
| **App-owned scaffold** (in both, but `_skip_if_exists`) | Overwrite with app's version | `src/lib/consts.ts`, `src/styles/app-theme.css`, `tests/support/fixtures.ts` |
| **Domain-only** (in app, not in template) | Copy | `src/routes/parts/`, `src/components/parts/`, `src/hooks/use-parts.ts` |
| **Template-only** (in template, not in app) | Keep generated version | `src/providers/index.tsx`, `tests/support/helpers/auth-factory.ts` |

**Critical: check ALL directories.** Don't assume you know the structure. During the EI port, `tests/api/` (API test factories), `tests/unit/`, `tests/examples/`, and `tests/smoke.spec.ts` were all missed on the first pass because only `tests/e2e/` and `tests/support/` were inventoried.

### 2.4 Check for remaining template-file customizations

Even after Phase 1.3, verify no customizations remain:

```bash
for f in $(comm -12 /tmp/template-files.txt /tmp/app-files.txt); do
  if ! diff -q "/tmp/skeleton/$f" "/work/<App>/frontend/$f" > /dev/null 2>&1; then
    echo "MODIFIED: $f"
  fi
done
```

Any remaining differences need to be handled during porting (see Phase 4.13).

## Phase 3: Generate the Project

### 3.1 Run copier copy

```bash
cd /work/ModernAppTemplate/frontend
poetry run copier copy . /work/<App>-new/frontend --trust --defaults \
  -d project_name=<app-name> \
  -d project_title="<App Title>" \
  -d project_description="<Description>" \
  -d author_name="<Author>" \
  -d author_email="<email>" \
  -d backend_port=<port> \
  -d sse_gateway_port=<port> \
  -d frontend_port=<port> \
  -d use_oidc=<true|false> \
  -d use_s3=<true|false> \
  -d use_sse=<true|false>
```

No lockfile copying needed — since Phase 1 upgraded the source app to current versions, a fresh `pnpm install` will resolve compatible versions without surprises.

## Phase 4: Port Domain Code

Use the inventory from Phase 2 as a checklist. The sections below list what to copy for a typical app.

### 4.1 App-owned identity files (overwrite generated defaults)

These are `_skip_if_exists` files that copier generates with defaults. Overwrite them with the app's versions:

```bash
cp <App>/src/lib/consts.ts <New>/src/lib/consts.ts
cp <App>/src/components/layout/sidebar-nav.ts <New>/src/components/layout/sidebar-nav.ts
cp <App>/src/styles/app-theme.css <New>/src/styles/app-theme.css
```

Also overwrite the style variant files if the app has customized them:
```bash
for f in button.ts alert.ts card.ts toast.ts input.ts notification.ts progress-bar.ts index.ts; do
  cp <App>/src/styles/$f <New>/src/styles/$f
done
```

And UI components (also `_skip_if_exists`):
```bash
cp -r <App>/src/components/ui/* <New>/src/components/ui/
```

### 4.2 Domain routes

Copy all route directories and files except `__root.tsx` (template-owned):

```bash
# Copy directory-based routes
for dir in <list of route dirs>; do
  cp -r <App>/src/routes/$dir <New>/src/routes/
done

# Copy root-level route files
cp <App>/src/routes/index.tsx <New>/src/routes/index.tsx
cp <App>/src/routes/about.tsx <New>/src/routes/about.tsx
# ... any other top-level routes
```

### 4.3 Domain components

Copy component directories that are not template-owned:

```bash
# Domain component directories (varies per app)
for dir in <domain dirs>; do
  cp -r <App>/src/components/$dir <New>/src/components/
done
```

**Template-owned component directories (do NOT copy):**
- `src/components/auth/` — auth gate
- `src/components/layout/` — sidebar, top-bar, user-dropdown, screen layouts (except `sidebar-nav.ts` which is app-owned)
- `src/components/primitives/` — all Radix+Tailwind primitives

**Domain icons:** Copy app-specific icons. The template provides a few generic icons (ExternalLinkIcon, ImagePlaceholderIcon, UploadIcon, clear-button-icon). If the app has additional icons in `src/components/icons/`, copy those.

### 4.4 Domain hooks

Copy only domain-specific hooks. Do NOT overwrite template hooks:

```bash
# Template hooks to skip:
TEMPLATE_HOOKS="use-auth.ts use-confirm.ts use-deployment-notification.ts
  use-form-instrumentation.ts use-form-state.ts use-paginated-fetch-all.ts
  use-sse-task.ts use-toast.ts use-version-sse.ts"

for f in <App>/src/hooks/*.ts; do
  basename=$(basename "$f")
  # Skip if it's a template hook
  if echo "$TEMPLATE_HOOKS" | grep -qw "$basename"; then continue; fi
  cp "$f" <New>/src/hooks/
done
```

### 4.5 Domain types

Copy domain type files, not template `.d.ts` declarations:

```bash
# Template types to skip:
# get-port.d.ts, playwright-binding.d.ts, split2.d.ts

# Copy domain types only
cp <App>/src/types/<domain-type>.ts <New>/src/types/
```

### 4.6 Domain utilities

Copy domain utils, not template utils:

```bash
# Template utils to skip:
# debounce.ts, error-parsing.ts, file-validation.ts, random.ts, thumbnail-urls.ts

# Copy domain utils only
cp <App>/src/lib/utils/<domain-util>.ts <New>/src/lib/utils/
```

### 4.7 API generated files

```bash
mkdir -p <New>/src/lib/api/generated
cp <App>/src/lib/api/generated/* <New>/src/lib/api/generated/
```

If the app has an OpenAPI cache for offline builds:
```bash
mkdir -p <New>/openapi-cache
cp <App>/openapi-cache/openapi.json <New>/openapi-cache/
```

### 4.8 Assets

```bash
mkdir -p <New>/src/assets
cp <App>/src/assets/* <New>/src/assets/
cp <App>/public/favicon.png <New>/public/favicon.png
```

### 4.9 Test support files

```bash
# Domain fixtures and selectors (overwrite generated scaffolds)
cp <App>/tests/support/fixtures.ts <New>/tests/support/fixtures.ts
cp <App>/tests/support/selectors-domain.ts <New>/tests/support/selectors-domain.ts

# Domain test helpers (not template-provided)
cp <App>/tests/support/helpers/<domain-helper>.ts <New>/tests/support/helpers/

# Page objects
mkdir -p <New>/tests/support/page-objects
cp -r <App>/tests/support/page-objects/* <New>/tests/support/page-objects/
```

**Template-owned test helpers (do NOT copy):**
- `auth-factory.ts`, `deployment-reset.ts`, `deployment-sse.ts`, `file-upload.ts`, `test-events.ts`, `toast-helpers.ts`

### 4.10 Test files

**Check ALL test directories**, not just `tests/e2e/` and `tests/support/`. Apps may have:
- `tests/api/` — API client and test data factories
- `tests/unit/` — unit tests
- `tests/examples/` — example specs
- `tests/smoke.spec.ts` — smoke tests
- Other top-level test files

```bash
# E2E tests (domain + infrastructure — keep both until mother project has its own test suite)
mkdir -p <New>/tests/e2e
cp -r <App>/tests/e2e/* <New>/tests/e2e/

# API factories, unit tests, etc.
for dir in api unit examples; do
  if [ -d "<App>/tests/$dir" ]; then
    cp -r <App>/tests/$dir <New>/tests/
  fi
done

# Top-level test files
for f in <App>/tests/*.spec.ts; do
  [ -f "$f" ] && cp "$f" <New>/tests/
done
```

### 4.11 Other app files

- `docs/` — VitePress documentation (if applicable)
- `scripts/` — app-specific scripts (deployment, dev helpers)
- `.env.example` — environment variable documentation

### 4.12 Package.json

Add app-specific dependencies and scripts to the generated `package.json`. The template provides all infrastructure dependencies. Common app additions:

- **Scripts:** `docs:dev`, `docs:build`, `dev:sse-gateway`, deployment scripts
- **Dev dependencies:** `vitepress` (if app has docs), domain-specific test utilities
- **Dependencies:** domain-specific libraries

### 4.13 Customized template files

If Phase 2.4 identified any remaining modified template-owned files, handle them now. Evaluate case by case whether to copy the app's version or update domain code to work with the template's version. Ideally Phase 1.3 eliminated all of these.

## Phase 5: Verify

### 5.1 Install and generate

```bash
cd <New>
pnpm install
pnpm exec tsr generate  # Generate TanStack Router route tree
```

### 5.2 Type-check

```bash
pnpm run check:type-check
```

If Phase 1 was done thoroughly, this should pass on the first try. If not, common issues:
- **Missing imports** — a file wasn't copied. Check the error path and copy it.
- **Selector property errors** — a template-file customization wasn't resolved in Phase 1.3.

### 5.3 Lint

```bash
pnpm run check:lint
```

### 5.4 Build

```bash
pnpm run build
```

This runs the full pipeline: API generation → route generation → lint → type-check → Vite build → production build verification.

### 5.5 File count comparison

As a final sanity check, compare file counts:

```bash
echo "Source: $(find /work/<App>/frontend/src -type f | wc -l) src, $(find /work/<App>/frontend/tests -type f | wc -l) tests"
echo "Ported: $(find <New>/src -type f | wc -l) src, $(find <New>/tests -type f | wc -l) tests"
```

Small differences are expected:
- Template may add files the app didn't have (e.g., `src/providers/index.tsx`, `tests/support/helpers/auth-factory.ts`)
- App may have files the template doesn't generate (these should all be domain files you copied)

Investigate any unexpected differences with a file listing diff:

```bash
diff \
  <(cd /work/<App>/frontend && find src tests -type f | sort) \
  <(cd <New> && find src tests -type f | sort)
```

## Common Pitfalls

### 1. Incomplete test directory inventory

Apps may have test files outside `tests/e2e/` and `tests/support/`. Always check the top-level `tests/` directory for additional subdirectories like `tests/api/`, `tests/unit/`, `tests/examples/`, and root-level spec files.

### 2. Template hooks vs domain hooks

Not all files in `src/hooks/` are domain code. The template provides 9 infrastructure hooks. Copying the app's version of a template hook risks overwriting template improvements. Only copy hooks that don't exist in the template.

### 3. Missing OpenAPI cache

If the app uses `generate:api:build` (cache-only mode) in the build script, the `openapi-cache/openapi.json` file must exist. Copy it from the source app or generate it with `generate:api` (requires running backend).

### 4. Skipping Phase 1

It's tempting to jump straight to generation and fix issues later. Don't. During the EI port, a TanStack Router version jump (1.131 → 1.161) caused ~13 route type errors and a TanStack Query change caused ~30 mutation callback errors. These are much easier to fix in the source app where you have the full test suite and IDE support, than in a half-assembled ported project.

## Template-Owned File Reference

Files that copier generates and owns (overwritten by `copier update`). **Do NOT copy these from the source app:**

**Config:** `vite.config.ts`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `tsconfig.playwright.json`, `eslint.config.js`, `playwright.config.ts`, `tsr.config.json`, `postcss.config.js`, `index.html`

**Core source:** `src/main.tsx`, `src/App.tsx`, `src/index.css`, `src/vite-env.d.ts`, `src/.gitignore`

**Providers:** `src/providers/core-providers.tsx`, `auth-providers.tsx`, `sse-providers.tsx`, `index.tsx`

**Contexts:** `src/contexts/auth-context.tsx`, `correlation-context*.ts`, `deployment-context*.ts`, `sse-context*.ts`, `toast-context*.ts`, `use-correlation-id.ts`, `get-global-correlation-context.ts`

**Infrastructure hooks:** `src/hooks/use-auth.ts`, `use-confirm.ts`, `use-deployment-notification.ts`, `use-form-instrumentation.ts`, `use-form-state.ts`, `use-paginated-fetch-all.ts`, `use-sse-task.ts`, `use-toast.ts`, `use-version-sse.ts`

**Lib:** `src/lib/api/client.ts`, `api-error.ts`, `.gitignore`; `src/lib/auth-redirect.ts`, `query-client.ts`, `utils.ts`; `src/lib/config/test-mode.ts`, `sse-request-id.ts`; `src/lib/test/*` (all instrumentation modules); `src/lib/utils/debounce.ts`, `error-parsing.ts`, `file-validation.ts`, `random.ts`, `thumbnail-urls.ts`; `src/lib/ui/index.ts`

**Components:** `src/components/auth/auth-gate.tsx`; `src/components/layout/sidebar.tsx`, `top-bar.tsx`, `user-dropdown.tsx`, `form-screen-layout.tsx`, `detail-screen-layout.tsx`, `list-screen-layout.tsx`, `list-screen-counts.tsx`; `src/components/primitives/*` (all); `src/components/icons/ExternalLinkIcon.tsx`, `ImagePlaceholderIcon.tsx`, `UploadIcon.tsx`, `clear-button-icon.tsx`

**Workers:** `src/workers/sse-worker.ts`

**Routes:** `src/routes/__root.tsx` only

**Scripts:** `scripts/generate-api.js`, `fetch-openapi.js`, `verify-production-build.cjs`, `testing-server.sh`, `eslint-rules/`

**Types:** `src/types/get-port.d.ts`, `playwright-binding.d.ts`, `split2.d.ts`

**Test support:** `tests/support/fixtures-infrastructure.ts`, `global-setup.ts`, `helpers.ts`, `selectors.ts`, `test-id.ts`, `backend-url.ts`; `tests/support/helpers/auth-factory.ts`, `deployment-reset.ts`, `deployment-sse.ts`, `file-upload.ts`, `test-events.ts`, `toast-helpers.ts`; `tests/support/process/servers.ts`, `backend-logs.ts`

## App-Specific Migration Notes

### IoTSupport

**Feature flags:** `use_oidc=true`, `use_s3=false`, `use_sse=true`

**Phase 1 preparation:**
- Upgrade TanStack Router and Query to current versions, fix any breakage
- Adopt infrastructure tests into the template mother project (IoT has Playwright tests already)
- Check for template-file customizations

**Specific concerns:**
- `esptool-js` — domain-specific dependency, add to app's `package.json`
- Vite config may have esptool-js mock for test mode — check if this needs an app-specific vite plugin
- SSE: IoT uses simpler direct EventSource. The template's SharedWorker approach replaces it — no special handling
- Has Playwright tests already — adopt template's test instrumentation framework

**Expected effort:** Low — mostly moving domain files into the generated structure.

### DHCPApp

**Feature flags:** `use_oidc=true`, `use_s3=false`, `use_sse=true`

**Phase 1 preparation:**
- **Tailwind 3 → 4 migration** — this is the biggest prep item. The template uses Tailwind 4 with `@tailwindcss/vite` plugin. Migrate before porting.
- Replace custom `SSEClient` class with template's SSE context pattern
- Set up OpenAPI code generation (`scripts/generate-api.js`) against DHCP's backend spec
- No tests to remove (none exist yet)

**Specific concerns:**
- Tailwind migration touches every component file — do this in the source app where you can verify visually
- Manual API client needs converting to generated hooks

**Expected effort:** Medium — Tailwind migration is the main cost.

### ZigbeeControl

**Feature flags:** `use_oidc=true`, `use_s3=false`, `use_sse=false`

**Phase 1 preparation:**
- Add TanStack Router: convert Zustand tab switching to file-based routes
- Replace Zustand store with TanStack Query for API data
- Migrate from CSS modules to Tailwind + Radix primitives
- Set up OpenAPI code generation

**Specific concerns:**
- Dynamic iframe proxies from YAML — app-specific vite config extension needed
- No tests to remove (none exist yet)
- This is essentially a UI rewrite, not a port — consider deferring until the template is battle-tested with the other apps

**Expected effort:** High — the most work of any migration.
