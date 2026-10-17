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
- **S4. Exception text in 500 responses becomes a setting.** The template default keeps today's behaviour (details shown); a public-facing app turns it off (BE-C14).

## To rule

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

- It depends on an SSEGateway release that emits `ready` and `rejected` for the HTTP-callback transport. DA tied these to its RabbitMQ transport, so this needs checking and possibly gateway work.
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
| FE19 | A copy-diagnostics button on error toasts; needs a "non-production" signal | Leave |

### D7. Where the conventions go

DA wrote down rules worth keeping: exhaustive status enums, when to toast, UUID paths, background tasks for anything over 2 s, testing against real dependencies, `perf_counter`, and failing fast (RT08, RT09, RT11, RT13, RT14, BE-T17). Per your standing rule, these go into a skill.

**Question:** which home? **Recommendation:** a `modern-app` conventions skill in KubeCoderConfig, next to the other estate skills.

### D8. Architecture producers

DA published `docs/architecture/architecture.yaml` and validated it in its own Jenkins pipeline (RT06).

**Question:** should every template app be a producer? **Recommendation: yes, if the federated model is meant to cover the estate.** The root template would carry `Jenkinsfile.architecture` and `scripts/arch-validate.py`, and each app would author its own YAML with `/seed-architecture`.

### D9. Optional features

**Recommendation: leave them in DA**, with three cheap exceptions:

- **BE-C28:** `ExternalServiceException` (502) and documented error-response schemas.
- **BE-C29:** restarts through `watchmedo` instead of the Werkzeug reloader. This ends the double-process class of bugs and respects graceful shutdown.
- **RT07:** a dependency-update checker across components.

These stay in DA until an app needs them: the Celery worker and Beat, email, multi-tenancy, i18n, ICU collations, the RabbitMQ SSE transport, pagination and sorting, S3 presigned URLs, `STAGE` tiers, role hierarchy, coverage tooling, Vitest, route loaders, the code-health grader, the multi-frontend workspace, the memory profiler, the remote suite runner and staged deploys.

### D10. How the work runs

**Recommendation:**

1. A dedup pass checks the selected items against the current template and the five apps. Some have landed already: PilotApp's write-up shows the template already has `after_commit()`.
2. The D1 batch becomes one straightforward-changes handover.
3. PostgreSQL testing (S1), the SSE bundle (D3), the auth refactor (D2 and D4) and readiness (D5) become four separate pieces of work, in that order. Each goes through the template change workflow and then `copier update` in every app.

## Mapping

- **S1:** BE-T06, BE-T07, BE-C18, FE23
- **S2:** BE-C15
- **S3:** BE-C17, RT05
- **S4:** BE-C14
- **D1:** all Port items except BE-C01; BE-C16, FE17, FE18, FE20, BE-T14, BE-T15
- **D2:** BE-C01
- **D3:** BE-T10, BE-T11, BE-T12, FE15, FE16, FE27
- **D4:** BE-C12, BE-T09, BE-T16
- **D5:** BE-C13, BE-T13
- **D6:** FE19, FE21, FE28, FE29
- **D7:** RT08, RT09, RT11, RT13, RT14, BE-T17
- **D8:** RT06
- **D9:** all other Optional items
- **Dedup pass:** RT01–RT04
- **Skip:** the 15 Skip items, as listed in the inventory
