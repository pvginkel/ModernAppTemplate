# Database testing: PostgreSQL in every suite, SQLite gone

*Advice for slice 002's planner, and for whichever slice lands it. Written 2026-10-17 at the
operator's request, against PilotApp `7a0347e`, DesignAssistant `053e921` and the PostgreSQL 18.6
sidecar of `pvginkel-pilotapp-addac6`. The operator's position is settled: SQLite is not used to
test Pilot. This document makes the case for that, describes DesignAssistant's working precedent,
and sets out the design that replaces SQLite. How much of it slice 002 takes on is the planner's to
propose (§5.1 recommends).*

## 1. The decision

- **Every suite that touches the database runs on PostgreSQL 18.** That means the backend's pytest
  suite and the backends Playwright boots per worker, locally and in CI. No test path builds a
  SQLite database.
- **Every test database is built by the Alembic revisions**, through the same
  `upgrade_database()` that `cli upgrade-db` and production's `migrate` init container run. None is
  built by `create_all`.
- **pytest builds one migrated template database per run.** A test runs inside a transaction that
  is rolled back, at about 0.3 ms per test. A test that needs commits a second connection can see
  gets a fresh clone of the template, at about 70 ms with its drop.
- **Playwright builds one seeded database per run** (`cli load-test-data`), and each worker clones
  it with `CREATE DATABASE … TEMPLATE`.
- **CI runs PostgreSQL 18 as a container beside the suite**, through `modernApp.test`'s
  `services:`. `backend/scripts/wait-for-services.py` waits for it.
- **Test databases use production's locale** (ICU `und`, `C` ctype) and never touch the dev
  stack's database `pilot`.
- **For slice 002:**
  - Tests that run in every build replace the one-off proof of item 5 (§4.5).
  - Criteria V02, V03, V19 and V22 change (§5.3).
  - P1, P2 and P9 no longer need SQLite workarounds, so none gets built.

## 2. Why not SQLite

### 2.1 The precedent

DesignAssistant started its backend tests on SQLite, the template's default, and moved them to
PostgreSQL. In the operator's account, two things went wrong on SQLite:

- **PostgreSQL-specific behaviour went untested.** The surface looks small, but it kept having
  impact.
- **The suite was slow.** Once it moved to PostgreSQL, it got a lot faster.

DesignAssistant's GitHub history starts at slice 153 (2026-04-21), after the move, so the switch
itself is in no commit. One residue is still in its code: `app/services/timeline_event_service.py`
applies `FOR UPDATE` "only on dialects that support it". That is a dialect branch on the very
construct item 5 is about.

### 2.2 What SQLite gets wrong in slice 002's own schema

None of this is hypothetical. Each row was run on 2026-10-17 with SQLAlchemy 2.1.4, twice: once on
an in-memory SQLite database built the way the template's fixture builds it (`create_all`), once on
the sidecar's PostgreSQL 18.6. Each row is a convention the data model (DB §7) sets for the tables
slice 002 creates.

| The record's convention | In-memory SQLite | PostgreSQL 18 | What it costs |
|---|---|---|---|
| `bigint` ids on internal rows: Document Version, Save Error, Block, Block Option, Project Member, Project Transition (DB §7.1) | The insert fails: `NOT NULL constraint failed`. SQLite autoincrements only `INTEGER PRIMARY KEY` | An identity; the insert succeeds | Every such model would need `BigInteger().with_variant(Integer, "sqlite")`, a test-only hack in production code. Without it, P9's seed fails. |
| Partial unique index `plan_notes (project_id, note_id) where deleted_at is null` (DB §7.6) | `postgresql_where` is ignored, so the index is unique over all rows and a struck note's id cannot be saved again | Correct | V15's "its id saved again is a new note" fails on SQLite, unless every model repeats its predicate as `sqlite_where`. The same holds for `documents (project_id, path) where project_id is set`. |
| Foreign keys | A row whose parent does not exist is **accepted**. SQLite enforces foreign keys only under `PRAGMA foreign_keys=ON`, and nothing in the app sets it | Rejected | Every foreign-key, cascade and "nothing is deleted" test passes vacuously. |
| Nineteen reference entities as enums, "checked by the database" (DB §7.2) | The value `'junk'` is accepted | Rejected | The database check DB §7.2 relies on does not exist. |
| `timestamptz`, UTC (DB §7.1, F114) | Read back **naive** | Read back aware, in UTC | Comparing with an aware time raises `TypeError` on one dialect only. The engine parses `at` and `done` as UTC (design 1 §6.1). |
| The ingest's row lock, `SELECT … FOR UPDATE` (design 1 §5.3, TD §8.5) | Compiled **without** `FOR UPDATE` | `… FOR UPDATE` | The statement under test is not the one production runs. |
| `cards text[]` with a GIN index on `waits` (DB §7.3, §7.6; the Wait slice's) | `UnsupportedCompilationError` | Created | Once Waits land, `create_all` cannot build the schema at all: the SQLite route has an end date. |
| Document text as `text` with `lz4` compression (DB §7.1) | Cannot be expressed | Set by the revision | The tested schema differs from production's by construction. |

Two of the rows would force dialect code into production models only so the tests can run:
`with_variant` on every `bigint` id and `sqlite_where` on every partial index. That is the opposite
of what tests are for. The other rows pass tests that production would fail, or cannot be tested
on SQLite at all.

### 2.3 The suites never run a migration

Today, `upgrade_database(recreate=True)` on SQLite drops every table, runs `create_all` and stamps
head (`backend/app/database.py:182-206`). Both pytest's template and Playwright's seed are built
this way. So no automated test exercises the first revision, which reaches production at slice
002's test-phase push and can never be edited afterwards.

The plan compensates twice:

- P1 and P2 prove the revisions on PostgreSQL by hand and record that in the done-record (V02).
- P1 invents "a route a test holds to the migration's", so that the reference rows and Pilot's User
  also reach the SQLite databases (V03).

On PostgreSQL, the revisions are the test schema. V02 becomes a test, and V03's machinery is no
longer needed.

### 2.4 Concurrency cannot be tested at all

The pytest fixture keeps the database inside one in-memory SQLite connection behind a `StaticPool`
(`backend/tests/conftest_infrastructure.py:122-181`). There is no second connection to contend
with, and SQLite would lock the whole database anyway.

"Two saves of one document never interleave" (V19) is a property of PostgreSQL's row locks under
READ COMMITTED. Only PostgreSQL can show it, and only with two connections. Item 5's answer is to
prove it once by hand and write that into the done-record. Such a proof holds only for the commit
it ran on: nothing re-checks it when P6's code changes, and CI never sees it. §4.5 makes it a test.

### 2.5 Speed

The measurements below were taken on the sidecar, on a schema of roughly slice 002's shape: 45
tables, 19 enum types, two indexes per table and 48 seed rows.

| Per test | Median |
|---|---|
| Today: a copy of the in-memory SQLite template (`sqlite3.backup`) | 0.0 ms |
| Today: `create_app()`, run for every test because the app is bound to that copy's connection | 18.8 ms, at skeleton size |
| PostgreSQL: a transaction and a savepoint, rolled back; the app is created once per run | 0.3 ms |
| PostgreSQL: `CREATE DATABASE … TEMPLATE` (`WAL_LOG`, the default) plus `DROP DATABASE` | 39.4 + 28.8 ms |
| PostgreSQL: the same with `STRATEGY FILE_COPY` | 1,059 ms (do not use) |
| PostgreSQL: `TRUNCATE` of 41 tables | 23.3 ms |

The gain does not come from PostgreSQL out-running in-memory SQLite on queries. It comes from what
each database allows:

- **An in-memory SQLite database lives inside one connection**, so a fresh database per test means
  a fresh app per test.
- **A PostgreSQL database is a URL**, so the app lives for the whole run and a test costs one
  rollback.

`create_app()` grows with every blueprint, service and wired module, so 19 ms is its floor. This is
the effect the operator saw in DesignAssistant.

### 2.6 What it costs

- **A PostgreSQL server for every run.** Locally, one already exists: this environment declares the
  `postgres` service, and `kc project setup` needs it. CI gains one container.
- **Template-owned files diverge.** Several template-owned Playwright files and one backend script
  diverge from ModernAppTemplate, which still ships SQLite fixtures (§4.8).
- **Multi-connection tests are slower.** The few that need commits seen by a second connection cost
  about 70 ms each.

## 3. The precedent in detail: DesignAssistant

This section was read at `053e921`.

### 3.1 pytest (`backend/tests/conftest_infrastructure.py`)

- **A database per run.** The session-scoped fixture `pg_seed_db` works like this:
  - Its admin URL, `postgresql+psycopg://postgres:postgres@localhost:5432/postgres`, is hardcoded.
    The database it makes is named `{PYTEST_PG_DB_PREFIX or "test_da_backend"}_{uuid8}`.
  - At start, it drops **every** database with that prefix, `WITH (FORCE)`, to clean up after
    interrupted runs.
  - It creates its database `TEMPLATE template0 ENCODING 'UTF8' LOCALE_PROVIDER icu ICU_LOCALE
    'und'` and adds DesignAssistant's two ICU collations.
  - It builds an app on the new database and runs `upgrade_database()`: the Alembic revisions one
    by one, through the same function Pilot has.
  - At the end, it drops the database `WITH (FORCE)`.
- **A session-scoped app** is bound to that URL, with a test pool of 5 + 5 (`TEST_DB_POOL_SIZE` and
  `TEST_DB_POOL_MAX_OVERFLOW` in `app/config.py`).
- **Each test is isolated by a rollback.**
  - The `session` fixture opens a connection, begins a transaction, and binds
    `_NoCloseSession(bind=connection, join_transaction_mode="create_savepoint")` to it. Its
    teardown closes the session, rolls back the connection's transaction and returns the
    connection.
  - `_NoCloseSession` makes `close()`, `commit()` **and** `rollback()` no-ops, so Flask's
    `teardown_request` can neither detach objects, nor commit, nor roll back. Services call
    `flush()`.
  - The `container` fixture overrides `session_maker` with a maker that returns the test's session,
    and resets `db_session`.
- **`oidc_app` builds a second app on the same URL.** It uses
  `render_as_string(hide_password=False)`, because `str(url)` masks the password. It clears the
  Prometheus registry first. Afterwards it re-wires the main app's container
  (`app.container.wire(packages=['app.api'])`), because wiring applies per package.
- **Migration tests run against the per-run database.**
  `test_migration_040_llm_configuration_prompt_seeds.py` asserts the rows a revision wrote, and
  re-runs that revision's `upgrade()` to prove it idempotent.
- **Committed rows are written by hand.** `test_cleanup_commands.py` inserts them through
  `engine.connect()` with raw SQL and `commit()`, and deletes them by hand afterwards.
- It has no drift test (no `compare_metadata`) and does not use `pytest-xdist`.

### 3.2 Playwright (`frontend/tests/support/`)

- **`global-setup.ts`**:
  - Drops every database with the prefix (`PLAYWRIGHT_PG_DB_PREFIX`, or `test_da_frontend`).
  - Creates `<prefix>_seed` from `template0`, with ICU and the collations.
  - Runs `poetry run cli load-test-data --yes-i-am-sure` with `DATABASE_URL` pointing at the seed,
    which drops, migrates and seeds it.
- **`fixtures-infrastructure.ts`**, per worker:
  - Drops `<prefix>_<parallelIndex>` if it exists, then creates it with `TEMPLATE <prefix>_seed`.
  - Boots the backend with `testing-server.sh --database-url`.
  - Drops the database at worker teardown.
- **`global-teardown.ts`** drops every database with the prefix, on a best-effort basis.
- **`helpers/pg-admin.ts`** holds the admin operations, on the npm `pg` client.

### 3.3 CI (`Jenkinsfile`)

A scripted pipeline starts a hand-written Job. The Job has:

- **The validation container**, which runs `poetry run run-suite --retries 2 …` with
  `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/postgres`.
- **A `database` container** beside it, running `pgvector/pgvector:pg18-trixie` with
  `POSTGRES_PASSWORD=postgres`.
- **The other services**: MinIO, RabbitMQ, OpenSearch and the conversion sidecar.

Before the suites start, its suite runner waits until the `DATABASE_URL` host and port accept
connections (`tools/suite_runner/local.py:135`).

### 3.4 What Pilot copies, and what it does not

Pilot copies:

- the per-run database built by the revisions;
- the session-scoped app;
- rollback isolation, with the session on savepoints;
- the second app on the same URL, followed by the re-wire;
- migration tests against the run's database;
- Playwright's seed-and-clone;
- PostgreSQL 18 in the CI pod;
- ICU `und`.

Pilot does not copy:

- **The prefix sweep `WITH (FORCE)` at start.** Two sessions in one KubeCoder environment can run
  suites against the same sidecar, such as a run loop's test phase and a dev session. The second
  run's sweep would then kill the first run's database mid-run. Pilot's sweep drops without `FORCE`
  and skips any database in use.
- **No-op `commit()` and `rollback()`.** Pilot's after-commit behaviour is under test:
  - `after_commit()` callbacks run from `teardown_request`, and only after the commit succeeds
    (`backend/app/__init__.py:222-253`).
  - The engine's bus delivers an event only once the transaction that caused it has committed (P5).

  With the session on a savepoint, both calls are real. `commit()` releases the savepoint: the
  `after_commit` event fires, and the rows stay inside the test's transaction. `rollback()` returns
  to the savepoint. Only `close()` is suppressed, so objects stay attached across a request. This
  was checked on the sidecar: `after_commit` and the rollback both fired, and nothing outlived the
  test.
- **Hand-committed rows with hand cleanup.** When such a test fails, it leaks its rows into every
  later test. Pilot gives a test like that a database of its own (§4.3).
- **The hardcoded admin URL.** Pilot reads it from an environment variable, with the same default.
- **The ICU collations**, which are specific to DesignAssistant: Pilot's record names none.
- **The dialect branch** around `FOR UPDATE`.

## 4. Pilot's design

### 4.1 Where the database comes from

- **Locally**, the environment's `postgres` sidecar serves at `localhost:5432`, with user and
  password `postgres` (`kc env describe`). `cexec modern-app` reaches it, so `kc project test`
  needs nothing new.
- **In CI**, a container in the validation Job's pod serves at the same address, with the same
  credentials (§4.7).
- **The admin URL** comes from `TEST_DATABASE_ADMIN_URL`, which defaults to
  `postgresql+psycopg://postgres:postgres@localhost:5432/postgres`.
- **The suites connect to nothing else.** They use only the `postgres` maintenance database and the
  databases they make, so the dev stack's `pilot` is never touched.
- **No secret enters the repo.** The password is a throwaway local default, and it is already in
  `.kubecoder/project.yaml`.

### 4.2 Names, locale and cleanup

- **Names.** A run's databases share a run prefix: `pilot_test_<8 hex>` for pytest and
  `pilot_e2e_<8 hex>` for Playwright.
- **Locale.** Every test database is either created with `TEMPLATE template0 ENCODING 'UTF8'
  LOCALE_PROVIDER icu ICU_LOCALE 'und' LC_COLLATE 'C' LC_CTYPE 'C'`, or cloned from one that was.
  These are production's settings:
  - `pilot_prd_db` is made from `template0` (PilotDeploy
    `terraform/modules/postgres-db/main.tf:75-78`).
  - Its cluster was initialised with exactly these settings (`postgres-pas-prd`'s Cluster
    `postgres`, `spec.bootstrap.initdb`).

  The sidecar's default is libc `en_US.utf8`, which sorts text differently. A database with these
  settings was created on the sidecar to check that it works.
- **Cleanup.**
  - At start, a run drops the databases earlier runs left behind. Each `pilot_test_%` or
    `pilot_e2e_%` database is dropped **without** `FORCE`. One that is in use (`ObjectInUse`,
    because another run owns it) is skipped.
  - At its end, a run drops its own databases `WITH (FORCE)`.
- **Connections.** The sidecar allows 50 connections, and the dev stack may be running beside the
  suites, so test apps get small pools:
  - pytest's: `sqlalchemy_engine_options={"pool_size": 2, "max_overflow": 3}`. The template's test
    `Settings` otherwise leave SQLAlchemy's default of 5 + 10.
  - Each Playwright backend's: `DB_POOL_SIZE=2` and `DB_POOL_MAX_OVERFLOW=3` in its environment. It
    reads `Settings.load()`, whose default is 20 + 30.

### 4.3 pytest: one template, two tiers

At session start:

1. Sweep (§4.2).
2. Create `<run>_tpl`, build an app on it, and run `upgrade_database()` followed by
   `post_migration_hook(app)`, as `cli upgrade-db` does. Then shut the app down and dispose its
   engine: a database cannot be cloned while it has open connections.
3. Clone `<run>_main` from `<run>_tpl`. The session-scoped `app` binds to `<run>_main`.

**Tier 1, the default: rollback.**

- The `session` fixture opens a connection on the app's engine, begins a transaction, and binds a
  Session with `join_transaction_mode="create_savepoint"`.
- The `container` fixture makes `session_maker` return that Session, so requests, services and the
  test all share it.
- `commit()` releases a savepoint, `rollback()` returns to one, and `close()` is a no-op.
- Teardown rolls back the connection's transaction.

It costs about 0.3 ms per test.

**Tier 2: a database of its own, for tests that need real commits seen by another connection.**

- The `committed_app` fixture clones `<run>_n` from `<run>_tpl` (about 40 ms) and builds an app on
  it, clearing the Prometheus registry first. It drops the database afterwards (about 30 ms).
- Its tests use the app's real `session_maker`, so every session gets its own connection and every
  commit is real.
- It is for:
  - the row lock (§4.5);
  - code that runs in other threads or opens its own sessions: the template's task service now,
    007's turn watcher later;
  - anything that asserts what a second connection sees after a commit.

A test that only needs to see its own commit stays in tier 1.

Sketch for `backend/tests/conftest.py`, which is app-owned. The template's star import stays first,
and the same-named fixtures defined after it replace the template's:

```python
ADMIN_URL = os.environ.get(
    "TEST_DATABASE_ADMIN_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
LOCALE = "ENCODING 'UTF8' LOCALE_PROVIDER icu ICU_LOCALE 'und' LC_COLLATE 'C' LC_CTYPE 'C'"
TEST_POOL = {"pool_size": 2, "max_overflow": 3}


@pytest.fixture(scope="session")
def run_prefix() -> Iterator[str]:
    prefix = f"pilot_test_{uuid.uuid4().hex[:8]}"
    sweep("pilot_test_")                         # DROP DATABASE, no FORCE; skip ObjectInUse
    create_database(f"{prefix}_tpl", template="template0", options=LOCALE)
    migrate(f"{prefix}_tpl")                     # create_app, upgrade_database(), post_migration_hook,
    yield prefix                                 #   then dispose: no connection may stay open
    drop_databases(prefix)                       # WITH (FORCE)


@pytest.fixture(scope="session")
def app(run_prefix: str) -> Iterator[Flask]:
    create_database(f"{run_prefix}_main", template=f"{run_prefix}_tpl")
    app = create_app(settings_for(f"{run_prefix}_main"),   # _build_test_settings() + URL + TEST_POOL
                     app_settings=_build_test_app_settings(), skip_background_services=True)
    yield app
    app.container.lifecycle_coordinator().shutdown()


@pytest.fixture
def session(app: Flask) -> Iterator[Session]:
    with app.app_context():
        connection = db.engine.connect()
        outer = connection.begin()
        test_session = _KeptOpenSession(       # close() is a no-op; commit() and rollback() are real
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
        try:
            yield test_session
        finally:
            Session.close(test_session)
            outer.rollback()
            connection.close()
```

Four things change along with the fixtures:

- **The Prometheus registry.** The template's autouse `clear_prometheus_registry` (function scope)
  unregisters every collector before and after each test. With a session-scoped app, it would strip
  the app's metrics after the first test. `conftest.py` replaces it with a no-op of the same name,
  and instead clears the registry once per session and before each extra app (`oidc_app`,
  `committed_app`), as DesignAssistant does.
- **`oidc_app`** is replaced the same way: it uses the same `<run>_main` URL with OIDC switched on,
  and the main container is re-wired afterwards (§3.1).
- **In-memory state** that services keep, such as the task service's tasks, now lives for the whole
  run. A test must clean up what it starts, as the editor-gate tests already do by cancelling
  theirs.
- **The template's SQLite parts.** `template_connection` and the template's SQLite imports stay in
  the template-owned file, unused.

### 4.4 Schema tests

- **The revisions apply to an empty database.** Every run does this (step 2 above), so a broken
  revision fails the whole suite at setup, locally and in CI.
- **No drift between the models and the revisions.** One test runs
  `alembic.autogenerate.compare_metadata(MigrationContext.configure(connection), db.metadata)` on
  the run's database and asserts that it returns nothing. This is V02's "no difference left for
  autogenerate to find", checked in every build.

  The drift test also guards the setup itself. The template-owned `get_pending_migrations()`
  swallows every error and then reports nothing pending, so a migration that was silently skipped
  leaves an empty schema. The drift test turns that into a failure.
- **What the models cannot carry.** One test reads `pg_attribute.attcompression` for the document
  text columns and asserts `'l'` (lz4).
- **The rows a revision writes** — the four reference tables' rows and Pilot's `agent` User — exist
  in every test database because the revision wrote them. A test asserts them, as DesignAssistant's
  migration-040 test does.
- **`cli upgrade-db --recreate`** stays a live check on the dev stack's database: it drops and
  re-migrates `pilot`.

### 4.5 The row lock, as tests (replacing item 5)

Both tests run on tier 2, with the document born and published first.

**The ingest takes the lock.**

- A second connection holds `SELECT … FROM documents WHERE id = :id FOR UPDATE` in an open
  transaction.
- The ingest then runs on the app, with `lock_timeout` set to 200 ms on its connection. It must
  fail with `LockNotAvailable` (SQLSTATE `55P03`).

The test is deterministic, uses no threads and takes about 0.2 s. On the sidecar, a second `FOR
UPDATE` on a held row was refused with `LockNotAvailable`. If `with_for_update()` is removed from
the ingest, this test fails.

**Two saves serialize.**

1. Two threads, each with its own session on the tier-2 app, ingest two different saves of one
   document from the same base hash.
2. A seam in the ingest holds the first thread inside its transaction once it has taken the lock.
   The seam is a no-op hook after the lock, which the test patches.
3. The test polls `pg_stat_activity` until the second thread's backend shows `wait_event_type =
   'Lock'`, with a timeout. That proves the second save is blocked on the lock, without a sleep.
4. The test releases the first thread. The second then returns, reported stale against the first's
   published hash and merged against the first's text (P4's rules).

Waits use `threading.Event` with a timeout.

Together, the two tests check V19's "two saves of one document never interleave" in every CI
build.

### 4.6 Playwright

- **`global-setup.ts`** stops calling `initialize-sqlite-database.sh`. Instead it:
  - creates `<e2e prefix>_seed` with production's locale;
  - runs `uv run cli load-test-data --yes-i-am-sure` in `backend/`, with `DATABASE_URL` pointing at
    the seed. `handle_load_test_data` runs `upgrade_database(recreate=True)` and then
    `load_test_data_hook` (`backend/app/cli.py:121-163`); on PostgreSQL, that means the revisions
    followed by the seed;
  - publishes the prefix to the workers in an environment variable, as the SQLite path publishes
    `PLAYWRIGHT_SEEDED_SQLITE_DB` today.
- **`fixtures-infrastructure.ts`** copies the seed file per worker today (`:350-370`). Instead, per
  worker, it:
  - creates `<prefix>_w<parallelIndex>` with `TEMPLATE <prefix>_seed`;
  - boots the backend with `DATABASE_URL` set to that database and the small pool (§4.2);
  - drops the database at worker teardown.
- **`process/servers.ts` and `backend/scripts/testing-server.sh`** pass a database URL where they
  pass `--sqlite-db` today. DesignAssistant added `--database-url` to both.
- **A new `global-teardown.ts`** drops the run's databases. `playwright.config.ts` names it; today
  it names only `globalSetup`.
- **The admin operations** come from a port of DesignAssistant's `helpers/pg-admin.ts`, on the npm
  `pg` client (a new dev dependency), with Pilot's names, locale and non-forcing sweep.
- **What falls out of use.** `initialize-sqlite-database.sh` and the SQLite branch of
  `upgrade_database()` are no longer called. Both are template-owned, so leave them in place, unused,
  rather than fight `copier update`.

### 4.7 CI

- **`Jenkinsfile`.** Pass `services: [[name: 'postgres', image: 'postgres:18-trixie', env:
  [POSTGRES_PASSWORD: 'postgres']]]` to `modernApp.test`:
  - The library adds each entry as a container beside the suite in the validation Job's pod
    (JenkinsPipelineUtils `vars/modernApp.groovy`, `jobManifest`), so the suite reaches it at
    `localhost:5432`.
  - Major version 18 matches production (CNPG `18.3-system-trixie`) and the sidecar (18.6, the
    Debian pgdg13 trixie build).
  - The Debian build includes lz4 and ICU. lz4 was verified on the sidecar.
  - A memory request and limit under `resources` are the planner's call.
  - The edit follows `kubecoder:jenkins-pipelines`.
- **`backend/scripts/wait-for-services.py`** is the extension point the suite runner already calls
  before the suites (`tools/suite_runner/local.py:164-173`). It waits up to a minute for
  `TEST_DATABASE_ADMIN_URL` to accept a connection, and fails clearly if it never does. Locally it
  returns at once.
- **No `env:` and no secret** are needed, because the defaults match.
- **`.kubecoder/config.yaml`'s comment** on the `postgres` service ("The test suites never use it
  …") becomes wrong, and changes with this work.

### 4.8 Template ownership

- **pytest's switch needs no template-owned edit.** `backend/tests/conftest.py` is app-owned (it is
  in `_skip_if_exists` in the template's `backend/copier.yml`), and it is the extension point
  CLAUDE.md names for fixtures.
- **Playwright's switch edits template-owned files**: `frontend/tests/support/global-setup.ts`,
  `fixtures-infrastructure.ts`, `process/servers.ts`, `playwright.config.ts` and
  `backend/scripts/testing-server.sh`.
  - Per CLAUDE.md, that is a fix "in this repo, in a commit of its own".
  - CLAUDE.md's list of standing template-owned edits (four today) gains this one, so a `copier
    update` resolves any conflict on these files to this repo's side.
- **Upstream.** ModernAppTemplate still ships SQLite fixtures, and two of its apps have now left
  them. Offering PostgreSQL testing in the template is a card for the operator to open (§6); the
  template is not edited from here.

### 4.9 Rejected alternatives

- **SQLite for unit tests, PostgreSQL for a marked subset.** Two dialects are the problem itself,
  and the dialect hacks of §2.2 would stay.
- **A fresh database per test for everything.** It costs about 70 ms and an app per test, while a
  rollback gives the same isolation for 0.3 ms.
- **`TRUNCATE` between tests instead of cloning.** It costs 23 ms, but it must spare the rows the
  revisions wrote, and a list of tables to spare is one more list to keep in step.
- **testcontainers, or a PostgreSQL started by pytest.** Both need a container runtime the dev
  container does not have, and the environment and CI already provide a server.
- **pytest-xdist.** Not needed at this size. The per-run prefix leaves room for one database per
  worker later.

## 5. What it changes in slice 002 (for the planner)

### 5.1 Where it goes

**Recommendation: make it the plan's first phases, before P1.** P1 writes the first models and the
first revision. While SQLite is still in place, P1 would need `with_variant` on every `bigint` id
and `sqlite_where` on every partial index, and P9's seed would fail on SQLite outright. Those are
workarounds built only to be removed.

Two phases fit naturally:

1. The backend suite and CI (§4.1–§4.5, §4.7).
2. Playwright (§4.6). It must land before P9, and could sit anywhere before it.

A slice of its own ahead of 002 would do the same work, but at the run loop's fixed cost, and 002's
plan would need re-planning anyway.

### 5.2 The plan's text

- **Grounding, "The app today":** "tests run on SQLite in memory through `create_all`" is replaced
  by this design.
- **P1:** "The suites never run a revision" and the route a test holds to the migration's go away.
  The PostgreSQL proof becomes §4.4's schema tests, and stops being a claim in the done-record.
- **P2:** "the PostgreSQL proof (the compression shown on the columns…)" becomes §4.4's
  compression test. "The SQLite databases built from the models" goes away.
- **P6:** "Two saves of one document never interleave" gets the tests of §4.5 instead of item 5's
  one-off proof.
- **P9:** The seed loads on the dev stack's PostgreSQL and on Playwright's PostgreSQL seed.

### 5.3 Its criteria (`verification.json`)

- **V02 stays, now proven by the suite.** The revisions build every test database from empty, and
  the drift and compression tests run in every build. `upgrade-db --recreate` on the dev stack
  stays a live check.
- **V03 is replaced.** Its claim, that the SQLite databases hold the migration's rows, becomes: the
  reference rows and Pilot's User in every test database are the revisions', asserted by a test.
- **V19's last sentence** is checked by §4.5's two tests, in every build.
- **V22:** "and on the SQLite seed Playwright's global setup builds" becomes the PostgreSQL seed.
- **New criteria for the infrastructure phases:**
  - The backend suite and the Playwright harness run on PostgreSQL 18, locally and in CI, and no
    test path builds a SQLite database.
  - Every test database is built by the revisions, with production's locale.
  - Two runs in one environment do not destroy each other's databases, and no run touches `pilot`.

### 5.4 The plan review's findings

- **A2** ("no proof route" for the row lock) is answered by §4.5.
- **"CI has no PostgreSQL"**, which A2 also notes, is answered by §4.7.

## 6. For the operator

- **Upstreaming.** Whether to open a ModernAppTemplate card for PostgreSQL testing in the template
  is your call.
- **The dev database's locale (optional).** The dev database `pilot` is also libc `en_US.utf8`.
  `scripts/init-dev-database.py` could create it with production's locale too. That is a small,
  separate change.

## Appendix: the measurements

- **When and where:** 2026-10-17, in environment `pvginkel-pilotapp-addac6`, through `cexec
  modern-app`.
- **Software:** SQLAlchemy 2.1.4 with psycopg, against the PostgreSQL 18.6 sidecar. The sidecar is
  dev-tuned (128 MB `shared_buffers`, 50 connections) and was not tuned further for tests.
- **Scripts:** in `/work/scratch/pg-bench/`, which is scratch and not in a repo:
  - `pitfalls.py` (§2.2);
  - `timing.py` (§2.5 and the `LockNotAvailable` probe);
  - `create_app_cost.py` (`create_app()`, median over 30 runs);
  - `savepoint.py` (§3.4's check of `after_commit` and rollback on a savepoint-joined session).
