# Backend code

How the backend measures time, raises its errors, and reports the failure of a system it calls.

### BE-1 — A duration is measured with `time.perf_counter()` { #be-1 }

Code that measures a duration or an elapsed time MUST use `time.perf_counter()`. It MUST NOT use
`time.time()`, which is for absolute timestamps only, such as a token's `exp`.

**Why.** `time.time()` is the wall clock, which NTP and the administrator move: a duration measured
with it can come out negative, or minutes off. `perf_counter()` only moves forward, at the highest
resolution the platform has. The template measures every duration with it, in its metrics, its
readiness checks and its lifecycle.

### BE-2 — An error is raised, never swallowed { #be-2 }

Code that meets an error MUST raise: the exceptions in `app/exceptions.py`, or those in
`app/core_exceptions.py`, with the context a reader needs in the message, such as the operation and
the record. The error handlers turn each exception into its HTTP status and the error envelope. An
endpoint MUST NOT build an error response by hand.

A `try`/`except` MUST either handle the error for real, recovering in a way the caller relies on,
or raise again, with `raise … from` the original. It MUST NOT log the error and carry on.

**Why.** An error that is swallowed shows up later and elsewhere, as wrong data or a missing
effect, with its cause gone. Raised at once, it fails the one request with a status that says what
went wrong, a message that says where, and a log entry. The handlers give every error one shape,
which [API-5](api.md#api-5) documents.

### BE-3 — A failing upstream raises `ExternalServiceException` { #be-3 }

When a system the backend calls fails, such as an HTTP API, a model provider or a mail server, the
code MUST raise `ExternalServiceException` from `app.core_exceptions`, `from` the original error.
Its `operation` follows "Cannot", and its `cause` says what went wrong:
`ExternalServiceException("fetch the forecast", f"the weather API answered {status}")`.

**Why.** The handlers answer it with `502`, which tells the frontend and the logs that the backend
works and a system behind it does not. The message, `Cannot <operation> because external service
failed: <cause>`, is the response's `error` and the logged warning, so both name the operation and
the failure. Raised as anything else, the same failure reads as the user's mistake (`400`) or as a
bug in the backend (`500`).
