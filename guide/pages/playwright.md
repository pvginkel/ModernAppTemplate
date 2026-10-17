# Playwright

The frontend's specs run in a browser against the real backend, the SSE gateway and a database of
their own. The root suite runner runs them: `run-suite --suite frontend`.

### PW-1 — A UI feature ships with its specs { #pw-1 }

A change that adds or changes a UI feature MUST add or update the specs that cover it, in the same
change. A UI feature without them is not done.

**Why.** The specs are the only tests that run the frontend against the backend. A feature without
one breaks without anyone seeing it, until a user does.

### PW-2 — A spec mocks no request { #pw-2 }

A spec MUST NOT intercept or fake a request or a stream: no `page.route()` or `context.route()`,
no `route.fulfill()` or `route.abort()`, no mocked SSE. The ESLint rule `testing/no-route-mocks`
fails all of them under `tests/`. A comment that disables it MUST give its reason
(`-- <reason>`), and the mock it allows needs the operator's approval.

**Why.** A mocked response is the backend as the spec's author pictured it. It drifts from the
real backend without failing, and the spec then passes over a broken integration
([TEST-1](testing.md#test-1)).

### PW-3 — A spec waits on test events, never on time { #pw-3 }

A spec MUST wait for the app to reach a state through the app's test events: `waitTestEvent()`,
`waitForListLoading()`, `waitForUiState()`, `waitForSseEvent()` or the `testEvents` fixture. It
MUST NOT wait for a fixed time, as with `page.waitForTimeout()`.

A new loading, form or mutation flow MUST emit its events in the same change as its spec:
`useListLoadingInstrumentation()` for a list, `useFormInstrumentation()` or the `trackForm*`
functions for a form, and `useUiStateInstrumentation()` for other UI state.

**Why.** A fixed wait is too long on a quiet run and too short on a loaded one, so the suite is both
slow and flaky. A test event is emitted when the app reaches the state, so the spec goes on at that
moment. The events are emitted only when `isTestMode()` is true, in a build with
`VITE_TEST_MODE=true`, so the production bundle emits none.

### PW-4 — A spec that needs a production build carries `@preview` { #pw-4 }

A spec, or a `describe`, that tests a path only a production build runs, such as the SSE
SharedWorker, MUST carry the `@preview` tag, and MUST skip unless `PLAYWRIGHT_PREVIEW_MODE` is
`true`.

**Why.** Under the Vite dev server the production path never loads: `shouldUseSharedWorker()` is
false there, so the spec would test the direct `EventSource` path and pass for the wrong reason.
The skip keeps it out of the dev-server pass. The suite runner then selects the `@preview` specs
for a second pass: it rebuilds with `VITE_TEST_MODE=true` and runs them against `vite preview` on
that build, with `PLAYWRIGHT_PREVIEW_MODE=true`. A spec that skips without the tag runs in neither
pass.

### PW-5 — A spec that expects an SSE event waits for the stream first { #pw-5 }

A spec that expects an update the backend delivers over SSE MUST wait for the stream before it
sets off the event: `await deploymentSse.ensureConnected()`, or a wait for the `connected` SSE test
event, `waitForSseEvent(page, { streamId: 'connection', phase: 'open', event: 'connected' })`.

**Why.** The app renders before its stream is up ([SSE-4](sse.md#sse-4)), so a page that looks
ready may not receive events yet. An event the backend sends before the gateway accepted the stream
reaches nobody, and the spec waits for it until it times out. `ensureConnected()` returns once
`isConnected` is true, which means the gateway accepted the stream.

## Recipe

A spec of the SharedWorker path:

```ts
test('connects through the SharedWorker', { tag: '@preview' }, async ({ page }) => {
  test.skip(
    process.env.PLAYWRIGHT_PREVIEW_MODE !== 'true',
    'Needs PLAYWRIGHT_PREVIEW_MODE=true: the Vite dev server never uses the SharedWorker',
  );
  // ...
});
```

The preview pass by hand, in the app's `frontend/`. `VITE_TEST_MODE=true` puts the Playwright
bridges into the bundle, so it is never set for an image build:

```bash
VITE_TEST_MODE=true pnpm build
PLAYWRIGHT_PREVIEW_MODE=true pnpm playwright test --grep @preview
```
