# Server-sent events

The backend serves the browser's SSE stream itself, `GET /api/sse/stream`, and sends events to it
with `SSEConnectionManager.send_event()`; the frontend receives them through the SSE context. These
rules say who receives an event, and how the frontend lives with a stream that may be slow, down or
refused.

A browser holds one stream: in a production build one SharedWorker shares it between the tabs, and
under the Vite dev server each tab opens its own. A stream holds a backend request thread for as
long as it is open, and no database connection; `WAITRESS_THREADS` bounds the streams and the API's
requests together. The backend accepts a stream for a caller the API would serve a `GET`, sends it
a `ready` event, then the events sent to it, with a heartbeat comment when it is idle. It refuses
any other caller in the stream itself: a `200` with one `rejected` event,
`{"status": 401, "message": "UNAUTHORIZED"}` or `403` and `FORBIDDEN`, and the end, because an
`EventSource` does not reconnect a response that is not a `200`. A backend shutdown ends every
stream, and the provider reconnects.

Only the backend process that holds a stream delivers to it: an event sent from any other process,
a worker or a second replica, reaches nobody. The backend runs as one replica and sends every event
itself.

An event reaches the connections its `Target` names:

| Target | Reaches |
| --- | --- |
| `Target.subject(subject)` | Every connection of that user, in every tab, and the local admin's. |
| `Target.connection(request_id)` | That one connection. |
| `Target.channel(name)` | Every connection subscribed to it, the local admin's only if subscribed. |
| `LOCAL_ADMIN_TARGET` | The local admin's connections. |
| `BROADCAST_TARGET` | Every connection. |

With OIDC off, every connection is the local admin's, and the local admin sees every user's events.
With OIDC on, no connection is the local admin's, and a connection sees its own user's events and
its channels' only.

A channel carries events that concern whoever asks for them rather than one user, such as a
device's live log. A route of the app's subscribes the caller's connection to it with
`subscribe(request_id, channel)`, after the check of [SSE-6](#sse-6), and `unsubscribe()` ends
that; the browser sends the SSE context's `requestId`. Channel names are the app's: the manager
interprets none. A subscription goes with its connection, so a stream that reconnects starts with
none, and the frontend subscribes again once `isConnected` is true.

### SSE-1 — Every event names its target { #sse-1 }

Every `send_event()` call MUST pass the `Target` of the users the event concerns.

**Why.** An event reaches only the connections its target names, so who sees an event is decided
at the call, where a reader can check it. `send_event()` has no default target and refuses
anything that is not a `Target`, so there is no implicit broadcast to fall into.

### SSE-2 — Broadcast is for infrastructure events only { #sse-2 }

`BROADCAST_TARGET` MUST carry only an event that concerns every client whoever its user is, such
as `FrontendVersionService`'s new frontend version. A domain event, about the app's own data,
MUST name its users: `Target.subject()` for a user, `Target.connection()` for one tab,
`Target.channel()` for the connections subscribed to it, each checked as it subscribed
([SSE-6](#sse-6)).

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

**Why.** `isConnected` turns true only once the backend has accepted the stream, with its `ready`
event. A page that waits for it is blank while the stream is refused, or reconnecting after a
backend restart, for something no page needs in order to render. The template's `SseGate` renders
its children at once, for the same reason.

### SSE-5 — The SSE provider owns the connection { #sse-5 }

Frontend code MUST receive events through the SSE context: `useSseContext()`'s
`addEventListener()`, or a hook built on it, such as `useSSETask`. It MUST NOT open an
`EventSource` of its own, and MUST NOT retry a stream the backend refused.

**Why.** The backend refuses a stream whose session has expired or holds none of the app's roles,
with its `rejected` event. Retried as it is, the stream is refused again, in a loop that loads the
backend and never recovers. The provider recovers through the session instead: it refreshes the
session, reopens the stream once if the session is valid, and leaves a signed-out user to the login
redirect. An `EventSource` of the code's own is a second stream beside the provider's, which in a
production build one SharedWorker shares between the tabs, and it holds a second backend request
thread for as long as it is open.

### SSE-6 — A route subscribes only the caller's own connection { #sse-6 }

A route that subscribes a connection to a channel MUST first check that the connection is the
caller's own: `get_connection_info(request_id)` MUST return a connection whose `subject` is the
caller's, or the local admin's (`local_admin`). A `request_id` with no connection, or another
user's, MUST be refused. Whether the caller may see the channel's events at all is the app's own
check, as for any read.

**Why.** The route checks the caller, and the channel's events go to the connection. Only the
connection's identity ties the two together: a `request_id` is a token the browser made up, sent
in the stream's URL, and nothing in it says whose it is. Unchecked, the route subscribes whatever
connection a caller names, and the channel's events reach a user nobody checked. The local admin's
connection passes because the local admin sees every user's events; with OIDC on, no connection is
the local admin's, so that half of the check lets nobody through.

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

An endpoint that subscribes the caller's connection to a project's channel, in an app with OIDC,
and the send that reaches it:

```python
info = sse_connection_manager.get_connection_info(request_id)
auth = get_auth_context()
if info is None or not (
    info.local_admin or (auth is not None and info.subject == auth.subject)
):
    raise AuthorizationException("The SSE connection is not the caller's")
sse_connection_manager.subscribe(request_id, f"project:{project_id}")
```

```python
sse_connection_manager.send_event(
    Target.channel(f"project:{project_id}"),
    {"project_id": project_id},
    "project_changed",
    "project",
)
```
