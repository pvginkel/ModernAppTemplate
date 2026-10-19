# Plan — the SSE transport in-process (the gateway folded into the backend)

Source: `PilotAppSpecs/handovers/sse-transport-in-process_2026-10-19.md`. Its §1 (what must not
change) is the contract; this plan maps the rest onto the three template repos, the guide and the
six apps, and names the choices the handover leaves open.

## Verdict

Doable as written, and the handover's premises hold against the code: `@public` and the tolerant
OIDC gate exist (`app/utils/auth.py`, `app/api/oidc_hooks.py`), the API blueprint carries the
gate, Waitress is pinned at 3.0.2, and `app/api/testing_logs.py` already serves an in-process SSE
stream the same way (a `Queue` per stream, a `PREPARE_SHUTDOWN` sentinel), so the pattern is
proven in the template.

Size, roughly:

| Area | Work | Weight |
|------|------|--------|
| Backend template | Rewrite `sse_connection_manager.py` (673 lines, half of it the HTTP send path), replace the callback (`api/sse.py.jinja`, 292) with the stream route, drop `sse_gateway_schema.py`, settings, readiness check; rewrite ~1,600 lines of SSE tests | The bulk |
| Frontend template | Mostly deletion: `ssegateway` devDependency, nginx location, Vite target, `DEFAULT_SSE_GATEWAY_PORT`, the gateway boot and log collector in the Playwright harness | Medium |
| Root template | `Procfile.dev`, `scripts/dev-sse-gateway.sh`, `scripts/dev.py`, `.kubecoder/` port and wording, the `sse_gateway_port` question | Small |
| Guide | `sse.md` (rewrite the transport, SSE-5's why, subscriptions), `playwright.md`, `readiness.md`, `testing.md` | Small |
| This repo's docs | `copier_approach.md` (inventory, decision 9), `CLAUDE.md` flag table, `backend/CLAUDE.md`, porting guide, `.kubecoder/project.yaml` comment, changelogs | Small |
| Six apps | `copier update` × 3 each, plus the by-hand items below; IoTSupport is the heavy one | Medium |
| Charts | Per app `<App>Deploy`: sidecar, secret, env, image pin | Operator |

## Decided: RabbitMQ support goes (operator, 2026-10-19)

The gateway's AMQP transport is the only way an event could reach a browser from a process other
than the one holding its stream (a worker, a second replica). No template or app uses it: the
only RabbitMQ code in the estate is inside the `ssegateway` package (and `amqplib` in each
frontend lockfile, which leaves with it), and DA's RabbitMQ SSE transport was deferred in the port
(`docs/da_port_inventory.md`, BE-T20). After this change only the backend process that holds a
connection delivers to it, so the backend stays one replica and events are sent from it; BE-T20
is retired, and the inventory says so in phase 5.

## Choices the handover leaves open — recommendations

1. **Threads, not async** (§6). Agreed: one parked Waitress thread per browser.
2. **`on_connect` / `on_disconnect` change signature.** Today they carry the gateway's token
   (`on_connect(request_id, token, url)`, `on_disconnect(token)`); in-process there is no token.
   Make `on_connect(request_id, subject, *, local_admin) -> SSEConnection` register the connection
   *and* bind its identity under one lock before the observers fire, and
   `on_disconnect(connection)` remove it only if it is still the current one for its
   `request_id` (the replaced-connection race the token check covers today). This also fixes an
   ordering wart: today the observers fire before `bind_identity`, so a connect observer sending to
   `Target.subject` misses the new connection. `bind_identity` stays public. Tests call
   `on_connect` directly to simulate a browser, no stream needed. Cost: app-owned tests that
   simulate connections (IoTSupport ~53 call sites, FieldnotesApp 3), fixed by hand at their sync.
3. **All refusals in-stream.** 400 (colon in `request_id`), 401 and 403 all answer `200` +
   `rejected`, as the gateway does today. The handover allows a plain HTTP error for other
   failures; parity costs nothing and keeps the provider's paths unchanged.
4. **Keep the route name `force-callback-error`.** PilotApp's app-owned
   `sse-connect-refusal.spec.ts` calls it; rename only `TestingService`'s methods
   (`*_forced_sse_connect_error`).
5. **Run part of the integration suite under Waitress.** Every automated run today uses Flask's dev
   server (the mother suite's `sse_server`, and Playwright's `testing-server.sh` runs `run.py` with
   `FLASK_ENV=testing`). The handover's §2 claims about flushing, `ClientDisconnected` and
   `channel_timeout` are Waitress-specific, so a `waitress_sse_server` fixture serves the
   flush, disconnect and idle-past-`channel_timeout` tests (with a short `channel_timeout`).
6. **Prove it on IoTSupport** (§5 step 5; operator to confirm). It is the heaviest SSE user: device
   log streaming at volume, rotation broadcasts, two e2e SSE specs, and most of the app-owned
   manager tests. Porting `DeviceLogStreamService`'s own subscription map onto
   `subscribe`/`Target.channel` is a follow-up, not part of this change.

## Risks to watch

- **Thread budget.** `WAITRESS_THREADS` defaults to 50, sized to the DB pool. A stream holds a
  thread but no DB connection, so API concurrency is 50 minus open browsers. Fine at the apps'
  scale; an app chart that sets a low `WAITRESS_THREADS` needs a look.
- **Request context.** Flask pops the request context (teardown, scoped session) when the view
  returns, before the body streams. The generator must touch only the connection's queue: no
  `request`, `g`, DB session or `Provide[...]` inside it. Do not use `stream_with_context`.
- **Stalled but connected client under Waitress.** Past `outbuf_high_watermark` (16 MB) the
  request thread blocks in the write, not on the queue, so the queue cap unregisters the
  connection but the thread stays parked until the socket dies (in production nginx's
  `proxy_send_timeout` ends it). Low risk; cover it in the stalled-client test.
- **Dev stack restarts drop streams.** `dev-watch.sh` restarts the backend through
  `PREPARE_SHUTDOWN`, so the browser reconnects. Today the gateway kept the browser's connection
  but the restarted backend had lost its registry, so this is a fix, not a regression.
- **OpenAPI churn.** SpecTree lists every route; `/api/sse/callback` leaves the document and
  `/api/sse/stream` joins it. The regen refreshes the frontend's `openapi-cache/`.

## Phases

Each phase ends green on its gate and commits. Playwright can only go green once phases 1–3 are
all in (the harness boots the gateway until phase 2, and the backend has no callback after
phase 1), so phases 1–3 are one unit for the end-to-end gate.

### Phase 1 — backend template (`backend/`)

- `app/services/sse_connection_manager.py`: per connection an `SSEConnection` with a bounded
  `queue.Queue` of formatted frames (cap a setting, `SSE_QUEUE_MAX_FRAMES=1000`), its identity and
  its channels; the registry under one `RLock`; observers and queue puts outside it. `send_event`
  formats once and `put_nowait`s per recipient; a full queue closes that connection (unregister,
  observers, its queue gets the close sentinel). `subscribe` / `unsubscribe` / `Target.channel`.
  Close every queue on `PREPARE_SHUTDOWN` (register with the lifecycle coordinator). Drop
  `requests`, the gateway readiness check, `SSE_GATEWAY_SEND_DURATION_SECONDS`; rename the metrics
  to `sse_*` (keep `sse_identity_binding_total`). Stays always-included (TaskService depends on
  it); without `use_sse` nothing ever connects and `send_event` answers `False`.
- `app/api/sse.py.jinja`: `GET /api/sse/stream` on `api_bp`, `@public`; the colon check, the
  testing hook, `_connection_identity` on the cookie (drop `_extract_token_from_headers` and the
  secret check), `on_connect`, then a generator that writes `ready`, drains the queue, writes
  `: heartbeat` after `sse_heartbeat_interval` idle, and in `finally` calls `on_disconnect`.
  Headers as `sse_utils.create_sse_response`, plus `X-Accel-Buffering: no`.
- Delete `app/schemas/sse_gateway_schema.py`; `copier.yml` drops its always-include note and the
  `sse_gateway_port` question.
- `app/config.py.jinja`, `.env.example.jinja`: drop `SSE_GATEWAY_URL`, `SSE_CALLBACK_SECRET`; add
  `SSE_QUEUE_MAX_FRAMES`. `app/services/container.py.jinja`: new constructor arguments.
  `app/__init__.py.jinja`: drop the root `sse_bp` registration. `testing_service.py.jinja`,
  `testing_sse.py`: the method rename.
- Tests: `tests/test_sse_api.py` and `tests/api/test_sse_callback.py` become
  `tests/api/test_sse_stream.py` (the role cases of §2, each read as a `200` stream whose first
  event is `ready` or `rejected`; Flask's test client with `buffered=False`, frames read one at a
  time); `tests/test_sse_connection_manager.py` rewritten (targets, replacement, queue cap,
  subscriptions, shutdown); `tests/integration/`: delete `sse_gateway_helper.py` and the
  `sse_gateway_server` fixture, point the three test files at the backend's stream, add the
  Waitress fixture (choice 5); `test_health_api.py` loses the `sse_gateway` check fixture;
  `test_metrics_service.py`, `test_config.py` follow. `template/tests/conftest_infrastructure.py.jinja`
  and `template/tests/test_smoke.py` lose the gateway settings and wording.
- Gate: `cexec modern-app bash regen.sh`; the mother suite and the test-app suite on `test-app`,
  the test-app suite on `test-app-no-storage`; ruff, mypy, vulture.

### Phase 2 — frontend template (`frontend/`)

- `package.json.jinja`: drop `ssegateway`; the lockfile follows.
- `nginx.conf.jinja`: drop the `/api/sse/` location (the `/api/` one serves it; `proxy.conf`
  already has `proxy_buffering off`).
- `vite.config.ts.jinja`: drop `gatewayProxyTarget` and `SSE_GATEWAY_URL`; the dev and preview
  `/api/sse` entries target the backend and keep `configureSseProxy`.
- `src/lib/consts.ts.jinja`: drop `DEFAULT_SSE_GATEWAY_PORT` (and its importers, if any).
- Playwright: `tests/support/process/servers.ts` loses `startSSEGateway`;
  `tests/support/fixtures-infrastructure.ts.jinja` loses `gatewayUrl`, `gatewayLogs`,
  `PLAYWRIGHT_GATEWAY_LOG_STREAM` and the three-step start (backend, then frontend);
  `tests/support/process/backend-logs.ts` loses the gateway collector; `global-setup.ts` wording;
  the three specs under `tests/infrastructure/sse/` keep their assertions, comments only.
- `copier.yml`: drop `sse_gateway_port`. `knip-template-ignore.json` if a path goes.
- Gate: `test-app` and `test-app-no-shell` check and build (Playwright waits for phase 3).

### Phase 3 — root template (this repo)

- `Procfile.dev.jinja`: drop the `gateway:` line and its comment. Delete
  `scripts/dev-sse-gateway.sh.jinja` and its `_exclude` line. `scripts/dev.py.jinja`: wording.
- `.kubecoder/config.yaml.jinja`: drop the `sse-gateway` port; wording in it and `project.yaml.jinja`.
- `copier.yml`: drop `sse_gateway_port`; `use_sse`'s help no longer names the gateway.
- This repo's `.kubecoder/project.yaml`: the comment that orders root last because the backend's
  integration tests take the gateway from `frontend/test-app/node_modules` (that reason goes; the
  order stays because root wraps both).
- Gate, the end-to-end one: `kc project build`, `kc project test`, `kc project lint` — the full
  Playwright suite on `root/test-app`, the SharedWorker preview run included.

### Phase 4 — guide (`guide/`)

- `pages/sse.md`: the backend serves the stream; the in-stream `rejected`; SSE-5's why without the
  gateway (the rule stands); subscriptions and `Target.channel`, with the ownership check
  (`get_connection_info(request_id).subject` against the caller, or the local admin).
- `pages/playwright.md` (the stack the specs run against; `isConnected` means the backend accepted
  the stream), `pages/readiness.md` (the gateway as the non-critical-check example goes; pick
  another), `pages/testing.md`.
- Gate: `kc project test guide`.

### Phase 5 — docs, changelogs, release

- `docs/copier_approach.md` (inventory, decision 9's rationale without the schema file,
  `dev-sse-gateway.sh`), `CLAUDE.md`'s flag table, `backend/CLAUDE.md` (the gateway as a test
  dependency), `docs/backend_porting_guide.md`; `docs/da_port_inventory.md` marks BE-T20 (the
  RabbitMQ SSE transport) retired.
- Changelogs (each repo's and the coordinated one): "removes the SSE gateway sidecar; adds
  subscriptions", with the by-hand list below.
- Tag backend v0.16.0, frontend v0.23.0, root v0.3.0 (pushes on the operator's word).

### Phase 6 — the apps

IoTSupport first; the other five once it is green and deployed. Per app, the usual three
`copier update`s, then:

- **All six:** the chart in `<App>Deploy` (sidecar container, generated callback secret, the
  backend's `SSE_CALLBACK_SECRET` env, the gateway image pin) — operator; drop `SSE_GATEWAY_URL`
  and `SSE_CALLBACK_SECRET` from `backend/.env`, `.env.test` where the setup seeded them.
- **IoTSupport:** `tests/services/test_sse_connection_manager.py` (41 calls on the old
  constructor and `on_connect`/`on_disconnect`; it largely re-tests the template's manager, so
  likely delete), `tests/api/test_device_log_stream.py` (7), `tests/services/test_mqtt_service.py`
  (5); `frontend/tests/e2e/devices/devices-logs-sse.spec.ts` (its "gateway callback race" note and
  "gateway may not be available" skips).
- **PilotApp:** `backend/tests/test_sse_callback.py` (the `editor` role cases) rewritten against
  the stream route; `backend/app/access_log.py`'s `RedactSecret` and `test_access_log.py` go
  (nothing left to mask); `PilotDeploy/architecture.yaml`.
- **FieldnotesApp:** `access_log.py` and its test as Pilot; `tests/fieldnotes/test_inbox.py`
  (3 manager calls); a comment in `tests/fieldnotes/test_api.py`.
- **ElectronicsInventory:** its app-owned copy of the integration harness
  (`tests/integration/sse_gateway_helper.py`, the SSE fixtures in `tests/conftest.py`).
- **DHCPApp, ZigbeeControl:** nothing beyond the template and the chart expected.

## End-to-end behaviour (handover §4) — where each is proven

| Behaviour | Proven by |
|-----------|-----------|
| One connection per browser, two tabs, broadcast and subject events | Playwright preview run (one connection); two tabs by hand on the test bed |
| Dev build, one connection per tab, task events | Playwright `task-events.spec.ts` |
| Refused connect, session probe, reopen, login redirect | Playwright `sse-auth-recovery.spec.ts` |
| Backend restart: streams end, reconnect, `ready` again | Backend test (`PREPARE_SHUTDOWN` ends a stream); by hand on the dev stack |
| Stalled client past the cap | Backend test (queue cap); Waitress test for the parked thread |
| Idle past `channel_timeout` | Waitress integration test with a short `channel_timeout` |
| Load: hundreds of events/s, thread count | By hand on IoTSupport (device logs) |
| nginx image streams unbuffered | By hand after IoTSupport's deploy |
