# DesignAssistant port: decisions

This page holds the rulings needed to port DesignAssistant's changes into the template. Item IDs (BE-C01, FE15, …) refer to [`da_port_inventory.md`](da_port_inventory.md), which has the detail behind each one. Every inventory item falls under one of the rulings below; the mapping is at the end.

## Settled (2026-10-17)

- **S1. Backend tests run on PostgreSQL; SQLite goes.** This covers pytest and the backends Playwright boots, locally and in CI. Every test database is built by the Alembic revisions. The design basis is PilotApp's write-up, [`pilotapp_database_testing_design.md`](pilotapp_database_testing_design.md), which improves on DA's version (BE-T06, BE-T07, BE-C18, FE23) in five ways:
  - The sweep of leftover databases at startup skips databases still in use, instead of dropping them with `FORCE` and killing a concurrent run.
  - On the savepoint-bound session, `commit()` and `rollback()` stay real, so `after_commit()` remains testable. DA turned them into no-ops.
  - Tests that need commits seen by a second connection get their own database, cloned from a template.
  - Test databases use production's locale, and the admin URL comes from an environment variable.
  - A drift test compares the models with the revisions.
- **S2. The OIDC `redirect_uri` comes from the request's origin**, not `BASEURL`, and redirect parameters must be relative paths (BE-C15).
- **S3. Builds use the shared `modern-app-backend*` base images and the pnpm build cache** (BE-C17, RT05).
- **S4. Exception text in 500 responses is shown only where S6 allows it** (BE-C14).
- **S5. The conventions become a guide on dev-guides.home** (RT08, RT09, RT11, RT13, RT14, BE-T17). The guide's source stays in this repo, since it is tied to the template, and the DevGuides pipeline (`pvginkel/DevGuides`) merges it in, as it does the JenkinsPipelineUtils guide. A skill in KubeCoderConfig points at the site, like the pipelines skill.
- **S6. One fact decides whether an app exposes internal information**: true when `STAGE` is not `prd`, or when the app is marked `HOMELAB_INTERNAL`. Two things follow it: exception text in 500 responses (S4) and the copy-diagnostics button on error toasts (FE19). The backend hands the fact to the frontend; DA did this through `GET /api/ui-setup`. The template has no `STAGE` today, only `FLASK_ENV`, which reads `production` in every deployed environment, so this needs D9b's `STAGE`. The hobby apps run as `prd` with `HOMELAB_INTERNAL` set. Whether `HOMELAB_INTERNAL` is a copier answer or a deploy setting is settled at design time.

## Ruled (2026-10-17)

Every recommendation below was accepted, except D9b and D9c, which were changed as written there. The delivery plan is [`da_port_plan.md`](da_port_plan.md).

### D1. Port the small fixes as one batch

**Recommendation: yes.** This covers the 26 Port items other than BE-C01, plus the small Port-adapted ones that have no design choice in them: BE-C16 (upload limit, default 50 MB), FE17 (opt-in production-build mode for Playwright, plus the inverted test-mode logic in `vite.config.ts`), FE18, FE20, BE-T14 and BE-T15. BE-C01 is D2.

Three changes in the batch are visible to apps:

- **BE-C05:** request metrics become always on. DA's version drops `status` from the duration histogram, which breaks any dashboard that uses it. *Recommendation: keep the current label set.*
- **FE14:** Playwright stops recording video by default. *Recommendation: off, with an env var that turns `retain-on-failure` back on.*
- **FE13:** nginx forwards `Host` with its port. This only matters for an app served on a non-standard port.

BE-C08 brings dependency major bumps with it: spectree 2, flask-cors 6, pytest 9, ruff 0.15 and Pillow 12.

### D2. Users with none of the app's roles

Today, an app that leaves `read_role` unset lets **any authenticated user** call every GET endpoint, including a user with none of the app's roles. DA denies such a user everywhere (BE-C01).

**Recommendation: deny, as DA does.** On a shared Keycloak realm, the current behaviour lets every account in the realm read every such app. The cost is that each app's readers must hold one of its roles. The dedup pass checks each app's role configuration before this lands.

### D3. SSE reliability bundle

The bundle has five parts:

- The connect callback rejects with 401/403 instead of opening a stream that silently receives nothing (BE-T11).
- The frontend handles `rejected` by refreshing the session and reconnecting, instead of looping (FE16).
- `connected` waits for the gateway's `ready` event (FE15).
- Events carry typed targets, with no implicit broadcast (BE-T10).
- The FrontendVersionService leak is fixed (BE-T12).

**Recommendation: yes.** All five apps run OIDC with SSE, and an expired session today leaves a dead stream. Two costs:

- It needs no gateway work. The stable SSEGateway, which the template already pins, sends `ready` without RabbitMQ, and turns a 400/401/403 from the connect callback into an in-stream `rejected` event.
- Typed targets change every `send_event` call site in the apps.

Take the non-blocking `SseGate` (FE27) with it. Waiting for `ready` makes the blank page DA hit more likely while the gateway is slow or down.

### D4. Auth flow refactor

There is one identity-resolution path instead of three copies. A `@public` endpoint refreshes and sees the user when one is logged in, instead of treating an expired token as anonymous. `@no_role_check` keeps logout reachable (BE-C12, BE-T09). Task endpoints check the caller (BE-T16).

**Recommendation: yes,** without DA's user-seeding glue. It lands after D2, which it builds on.

### D5. What makes readiness fail

DA's health rework (BE-C13, BE-T13) has two parts:

- **The framework:** services register their own checks, which run concurrently with a timeout and a 30 s cache.
- **The rule:** readyz returns 503 when *any* check fails.

**Recommendation: take the framework, and return 503 only for checks registered as critical** (the database; S3 where `use_s3`). Other checks are reported but don't fail the probe. Under DA's rule, an outage of a non-essential dependency takes every pod out of service, and DA's own Playwright harness had to accept 503 to cope. The readyz response format changes either way, so the root template's probes move with it. BE-C02 (migration errors no longer swallowed) goes first.

### D6. Frontend defaults

| Item | Change | Recommendation |
|---|---|---|
| FE21 | `button { cursor: pointer }`, readable dark-mode red and blue, and an app-owned CSS hook so apps stop editing `index.css` | Yes |
| FE28 | Dialogs don't close on a backdrop click (protects half-filled forms) | Yes |
| FE29 | A loading button keeps its width (spinner overlaid) | Yes |
| FE19 | A copy-diagnostics button on error toasts, shown where S6 allows it | Yes |

### D7. Where the conventions go

Settled as S5.

### D8. Architecture producers

DA published `docs/architecture/architecture.yaml` and validated it in its own Jenkins pipeline (RT06).

**Question:** should every template app be a producer? **Recommendation: yes, if the federated model is meant to cover the estate.** The root template would carry `Jenkinsfile.architecture` and `scripts/arch-validate.py`, and each app would author its own YAML with `/seed-architecture`.

### D9. Optional features

**Recommendation: leave them in DA**, with three cheap exceptions:

- **BE-C28:** `ExternalServiceException` (502) and documented error-response schemas.
- **BE-C29:** restarts through `watchmedo` instead of the Werkzeug reloader. This ends the double-process class of bugs and respects graceful shutdown.
- **RT07:** a dependency-update checker across components.

These stay in DA until an app needs them: the Celery worker and Beat, email, multi-tenancy, i18n, ICU collations, the RabbitMQ SSE transport, S3 presigned URLs, coverage tooling, the code-health grader, the multi-frontend workspace and the memory profiler.

Seven more are under consideration; their pros and cons follow.

#### D9a. Pagination and sorting (BE-C27, FE31, RT10)

- **What it is:**
  - Backend: `apply_sorting()` sorts by a whitelisted column and always adds `id` as a tiebreaker. A base query schema carries `page`, `per_page`, `sort_by` and `sort_dir`, and a meta schema describes the page (39 lines plus the schemas).
  - Frontend: a `DataTable` on `@tanstack/react-table`, `useServerSort` (which remembers the sort in localStorage), `usePagination`, and a step in `generate-api.js` that emits each endpoint's sortable columns from the OpenAPI spec.
  - Convention: every list endpoint sorts on the server.
- **Pros:**
  - Lists that page are sorted where the data is, so a page boundary never shuffles rows. The `id` tiebreaker alone fixes rows that repeat or vanish between pages, a bug any paged list has without it.
  - The generated sort config keeps backend and frontend column names in step.
- **Cons:**
  - The hobby apps' lists are small enough to sort in the browser. A server-side contract on every list endpoint is real ceremony for them.
  - `DataTable` brings a dependency and a second table component next to whatever the apps already use.
  - DA's generator step had DA-specific paths hard-coded in it.
- **Recommendation: take the backend half only**: `apply_sorting()` with its tiebreaker, plus a "paged lists order stably" rule in the conventions skill. Leave the frontend half until an app has a list that needs paging. ElectronicsInventory is the likely first; the dedup pass will show what it does today.

#### D9b. `STAGE` tiers (BE-C24)

- **What it is:** a `STAGE` setting (`local-dev`, `dev`, `uat`, `prd`, `local-tst`, `tst`) separate from `FLASK_ENV`. DA used it to:
  - derive defaults (the S3 bucket name, the queue prefix);
  - guard destructive commands and test endpoints outside `prd`;
  - report the stage in readyz;
  - show a stage badge in the top bar, hidden on `prd` (FE32);
  - gate the toast diagnostics button (FE19).
- **Pros:**
  - One answer to "which environment is this?" for the app, its logs and its users.
  - The badge prevents "I thought this was test" mistakes.
  - Destructive tooling gets a reliable guard.
- **Cons:**
  - Every hobby app has one environment, so today it would always read `prd`. That is fine under S6, which marks them `HOMELAB_INTERNAL` instead.
  - Six values is more than anyone needs. The `local-*` variants exist for DA's test setup.
  - Defaults derived from the stage hide configuration that is better stated outright in the deploy values.
- **Ruling: take DA's version.** The operator's next app runs at least `dev` and `prd`, besides `local-dev` and `local-tst`. Taken:
  - all six values, and the `Stage` wrapper with `is_local()` and `is_env()`;
  - readyz reporting the stage;
  - the local-stage skip for the version broadcast;
  - guards on destructive commands and test-only endpoints on `prd`;
  - the top-bar badge (FE32), hidden on `prd`.
- **Default when unset:** `prd` under a production `FLASK_ENV`, `local-tst` under testing, and `local-dev` in development. A deployment that forgets `STAGE` therefore exposes nothing (S6). The CI validation Job sets `tst`.
- **Left out:** defaults derived from the stage, such as DA's per-stage S3 bucket name. Existing apps run on fixed bucket names, and a derived default would quietly move them to a new bucket.

#### D9c. Role hierarchy (BE-C25)

- **What it is:** the `AuthService` gains `role_hierarchy={"editor": ["portal"]}` on top of the linear read → write → admin chain. It validates the roles, detects cycles and expands the implications (about 100 lines, 24 tests, off by default).
- **Pros:**
  - It handles an app with two audiences, such as staff and customers, where staff should also pass the customers' endpoints, without listing both roles on every endpoint.
  - It is backward compatible, and DA's tests come with it.
- **Cons:** no app has a second audience, and the linear chain plus `@allow_roles` covers everything they do. It is one more concept in the auth model for someone to understand.
- **Ruling: take it.** It is backward compatible (off by default), and nobody comes back to DA for it later.

#### D9d. Vitest (FE24)

- **What it is:** a unit and component test runner next to Playwright: `vitest.config.ts`, jsdom, Testing Library, a `test:unit` script and knip wiring. DA had nine test files in total, mostly pure functions (an error serialiser, markdown and diff logic).
- **Pros:**
  - Pure logic such as parsers, formatters and state machines gets tested in milliseconds instead of through a browser.
  - Edge cases are cheap to enumerate.
- **Cons:**
  - A second runner to wire into the suite runner, CI, knip and tsconfig.
  - Component tests invite the mocking the template's Playwright rules forbid (`no-route-mocks`).
  - The hobby apps have little pure frontend logic. Even DA, with far more of it, wrote nine files.
- **Recommendation: leave.** Add it to the app that first has logic worth unit-testing. Promote it to the template if a second app wants it.

#### D9e. Route loaders (FE26)

- **What it is:** each route prefetches its data in a TanStack Router loader, through a query-options factory whose key equals the generated hook's key, so the page renders with its data instead of a spinner. It comes with:
  - a pending component after 200 ms;
  - a thin progress bar for slow navigations;
  - `NotFoundRedirect`, which turns a loader's 404 into a toast and a redirect.
- **Pros:**
  - No spinner flash, and no layout jump on detail pages.
  - Fetching and 404 handling live in one place per route.
  - Hover prefetch becomes possible.
- **Cons:**
  - DA wrote its 14 factories by hand. If a factory's key drifts from the generated hook's key, the page silently fetches twice.
  - Loaders block navigation, so pending UI becomes mandatory.
  - It broke the template's ui-state instrumentation. FE08, ported in D1, is the fix.
  - Every app's routes change.
- **Recommendation: leave for now.** The template-worthy version generates the query-options factories in `generate-api.js`, so the keys cannot drift. That is template work of its own, and worth doing only when an app's detail pages visibly need it.

#### D9f. Remote suite runner (RT21)

- **What it is:** `run-suite-remote` (534 lines) builds a Kubernetes Job like CI's validation Job, uploads the working tree, runs `run-suite` in the pod, copies the results back and deletes the Job. DA built it because its dev container had no database or browser.
- **Pros:**
  - The CI-identical suite runs from a dev session without a push.
  - It gets more memory and CPU than the dev container.
  - Several runs can go in parallel.
- **Cons:**
  - KubeCoder already provides the sidecars and the browser, so `kc project test` runs the suite locally. DA's reason for building it is gone.
  - It is a second copy of the Job manifest that the root `Jenkinsfile` and the library's `modernApp.test` generate. The copies drift.
  - It needs rights to create Jobs. This environment has them only in prd's `development` namespace.
- **Recommendation: leave.** If dev containers start running out of memory on full Playwright runs, the right home is a `kc` or library feature that reuses `modernApp.test`'s manifest, not per-app Python.

#### D9g. Staged deploys (RT20)

- **What it is in DA:** Build-Main tags images `tst-<n>`. Deploy-UAT retags a chosen build as `uat-<n>` with `crane`, Deploy-PRD retags a UAT build as `prd-<n>`, and each deploys through HelmCharts.
- **What it would be today:** the template no longer deploys through HelmCharts. The build pins its images in the deploy repo's `config/prd/values.yaml`, and Argo CD syncs that commit (argo-cd D53). A staged version pins into `config/uat/values.yaml` instead, and a promote job copies the pin from `uat` to `prd`. Nothing is retagged, because the image tag already names the build. DA's `crane` approach does not carry over.
- **So, yes: it is pipeline and deploy work, done per app.** The app needs a second Argo application with its own database, OIDC client redirect URI, S3 bucket, SSE gateway and hostname, all set in the deploy values. The app's code needs nothing, unless it wants the stage visible (D9b).
- **Pros:** a bad build reaches `uat` first, and production gets exactly the image that was tried.
- **Cons:**
  - A second running copy of every service, and its data, per app.
  - A manual promote step on every release.
  - For a single-user hobby app, `uat` is mostly the operator clicking through the same thing twice.
- **Recommendation: per app, not in the template.** Do it for an app whose users would be hurt by a bad deploy. If two apps end up with the same promote job, lift it into the root template or the library then.

### D10. How the work runs

Replaced by the operator's ruling: everything ships in one push. See [`da_port_plan.md`](da_port_plan.md).

## Mapping

- **S1:** BE-T06, BE-T07, BE-C18, FE23
- **S2:** BE-C15
- **S3:** BE-C17, RT05
- **S4:** BE-C14
- **S5:** RT08, RT09, RT11, RT13, RT14, BE-T17
- **S6:** BE-C24 (reduced, see D9b), FE19
- **D1:** all Port items except BE-C01; BE-C16, FE17, FE18, FE20, BE-T14, BE-T15
- **D2:** BE-C01
- **D3:** BE-T10, BE-T11, BE-T12, FE15, FE16, FE27
- **D4:** BE-C12, BE-T09, BE-T16
- **D5:** BE-C13, BE-T13
- **D6:** FE21, FE28, FE29 (FE19 is S6)
- **D8:** RT06
- **D9:** all other Optional items; D9a–D9g cover BE-C27, FE31, RT10, BE-C24, BE-C25, FE24, FE26, RT21, RT20
- **Dedup pass:** RT01–RT04
- **Skip:** the 15 Skip items, as listed in the inventory
