# Server-sent events

The backend sends events to the browser through the SSE gateway: `SSEConnectionManager.send_event()`
on the backend, the SSE context on the frontend. These rules say who receives an event, and how the
frontend lives with a stream that may be slow, down or refused.

An event reaches the connections its `Target` names:

| Target | Reaches |
| --- | --- |
| `Target.subject(subject)` | Every connection of that user, in every tab, and the local admin's. |
| `Target.connection(request_id)` | That one connection. |
| `LOCAL_ADMIN_TARGET` | The local admin's connections. |
| `BROADCAST_TARGET` | Every connection. |

With OIDC off, every connection is the local admin's, and the local admin sees every user's events.
With OIDC on, no connection is the local admin's, and a connection sees its own user's events only.

### SSE-1 — Every event names its target { #sse-1 }

Every `send_event()` call MUST pass the `Target` of the users the event concerns.

**Why.** An event reaches only the connections its target names, so who sees an event is decided
at the call, where a reader can check it. `send_event()` has no default target and refuses
anything that is not a `Target`, so there is no implicit broadcast to fall into.

### SSE-2 — Broadcast is for infrastructure events only { #sse-2 }

`BROADCAST_TARGET` MUST carry only an event that concerns every client whoever its user is, such
as `FrontendVersionService`'s new frontend version. A domain event, about the app's own data,
MUST name its users: `Target.subject()` for a user, `Target.connection()` for one tab.

**Why.** A broadcast reaches every connection, every other user's included. A domain event
broadcast hands one user's data to all of them, decided by the send, not where the app decides who
may see what. A version event holds nothing that belongs to a user.

### SSE-3 — A task's events go to the user who started it { #sse-3 }

An endpoint that starts a task MUST pass the caller's subject to `TaskService.start_task()`: the
`subject` of `get_auth_context()` in an app with OIDC, and `None` in an app without it. Code MUST
NOT send a task's events to any other target, and MUST NOT fall back to another target when the
subject is missing.

**Why.** A task's progress and result concern the user who asked for it. The task service sends
all of them, its progress handle's included, to that one target: `Target.subject()` of the user,
or `LOCAL_ADMIN_TARGET` without a subject, never a broadcast. A fallback chain, the subject or
else the connection or else everyone, widens the audience in silence whenever the subject is lost.
With one target, a lost subject with OIDC on reaches nobody, which a test sees, instead of
everybody, which no test sees.

### SSE-4 — The UI renders without the stream { #sse-4 }

Frontend code MUST NOT wait for the SSE stream before it renders: no route, page or component is
gated on `isConnected`. A page renders from its queries, and an event updates what is already on
the screen.

**Why.** `isConnected` turns true only once the gateway has accepted the stream, with its `ready`
event. A page that waits for it is blank while the gateway is slow or down, for something no page
needs in order to render. The template's `SseGate` renders its children at once, for the same
reason.

### SSE-5 — The SSE provider owns the connection { #sse-5 }

Frontend code MUST receive events through the SSE context: `useSseContext()`'s
`addEventListener()`, or a hook built on it, such as `useSSETask`. It MUST NOT open an
`EventSource` of its own, and MUST NOT retry a stream the gateway refused.

**Why.** The gateway refuses a stream whose session has expired or holds none of the app's roles.
Retried as it is, the stream is refused again, in a loop that loads the gateway and the backend
and never recovers. The provider recovers through the session instead: it refreshes the session,
reopens the stream once if the session is valid, and leaves a signed-out user to the login
redirect. An `EventSource` of the code's own is a second stream beside the provider's, which in a
production build one SharedWorker shares between the tabs.

## Recipe

An endpoint that starts a task, in an app with OIDC:

```python
auth = get_auth_context()
started = task_service.start_task(
    ExportProjectTask(),
    caller_subject=auth.subject if auth else None,
    project_id=project_id,
)
```

A frontend hook that reacts to a domain event the backend sends to the user:

```ts
export function useProjectEvents(onChanged: (projectId: string) => void): void {
  const { addEventListener } = useSseContext();

  useEffect(
    () =>
      addEventListener('project_changed', (data) => {
        onChanged((data as { project_id: string }).project_id);
      }),
    [addEventListener, onChanged],
  );
}
```
