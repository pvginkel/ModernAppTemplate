# Frontend code

When the frontend shows a toast, and how it downloads a file the backend serves.

### UI-1 — No success toast for an outcome the user sees { #ui-1 }

A success toast MUST NOT be shown when the outcome is on the screen: a record appears in a list, a
row disappears, a dialog closes, an inline edit is saved, or the page moves to the new record. A
success toast is for an outcome the user cannot see, such as an email sent, a background task
finished, or a change made elsewhere.

**Why.** A toast that repeats what the screen shows is noise over the screen. A user who sees one
after every click learns to ignore toasts, and then misses the one that says something.

### UI-2 — A mutation's error is toasted once, by the global handler { #ui-2 }

The query client's default mutation `onError` (`src/lib/query-client.ts`) toasts every mutation
error, with the message `parseApiError()` reads from the response. Code MUST NOT toast a
mutation's error itself, with `showError()` or `showException()`. It MUST NOT pass `onError` to a
mutation hook either: that replaces the global handler for the mutation. What a component does on
an error, such as keeping a dialog open, goes in `mutate(variables, { onError })` or in a `catch`
around `mutateAsync()`, which run beside the global handler.

**Why.** A second toast for one error is a duplicate. The server's message is the one to show: the
server has the most context on what went wrong. TanStack Query lays a mutation's own options over
the defaults, so an `onError` given to the hook leaves that mutation's errors untoasted, while the
callbacks of one `mutate()` call run after the hook's.

### UI-3 — A file the backend serves downloads through `window.open()` { #ui-3 }

A file the backend serves MUST download with `window.open(url)` on its endpoint, which answers with
`Content-Disposition: attachment`. Such a download MUST NOT go through `fetch()`, a `Blob` and
`URL.createObjectURL()`. That path is for a file the frontend makes itself, such as an export of
data it already holds.

**Why.** The session is a cookie, which the browser sends on a plain navigation as it does on an
API call, so the endpoint authenticates the download as any other request. The browser then saves
the file as it arrives, with its own download progress. The `Blob` path holds the whole file in
memory first, shows nothing while it loads, and needs a link made by hand to save it.
