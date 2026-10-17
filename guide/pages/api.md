# API

How the backend's endpoints address a resource, run work that takes a while, page a list and
document their errors.

### API-1 — A path identifies a resource by its surrogate key { #api-1 }

An app picks one surrogate key type when it is created, an integer or a UUID, and its tables key
on it. A path parameter that names a resource MUST be that key, as in
`/api/projects/<project_id>`. A path MUST NOT carry a natural key: a name, a slug, an email, or a
code the user chose.

An app does not switch key types later. Changing a primary key is a migration of its own, never a
side effect of other work.

**Why.** A natural value changes, or collides with another, and every link, bookmark and log line
that holds it then names the wrong resource or none. A surrogate key never changes. One key type
per app keeps every route, schema and client the same shape. A UUID also names one resource across
every table and environment, and gives away neither how many rows a table holds nor the ids next
to it, which is what an app weighs when it picks one. The template's task ids are UUIDs.

### API-2 — Work that can take over 2 seconds runs as a task { #api-2 }

An operation whose p95 duration can exceed 2 seconds MUST run as a background task:

- The endpoint starts the task with `TaskService.start_task()` and answers `202` with the task's
  `task_id` at once.
- The task reports its progress and its result as SSE task events, to the user who started it
  ([SSE-3](sse.md#sse-3)).
- The frontend follows the task with `useSSETask` (`src/hooks/use-sse-task.ts`): it passes the
  `task_id` to `subscribeToTask()`, and reads `progress`, `result` and `error`.

**Why.** A request that runs for seconds shows the user nothing while it does, so the user clicks
again and starts the work twice. A proxy or the browser may cut the request off, and the work then
goes on with nobody to report to. A task answers at once, its progress shows the user that the work
is going on, and its result arrives however long it takes. `useSSETask` replays the events that
arrived before it subscribed, so a fast task's events are not lost.

### API-3 — A paged list orders stably { #api-3 }

A paged list MUST order by a unique key last: the sort column, then `id`, in the same direction.

**Why.** When the sort column holds duplicates, the database may return the tied rows in a
different order for each query. A row then repeats on two pages, or is missing from both. With a
unique key last the order is total, so every page's query cuts the same sequence.

### API-4 — A paged list endpoint pages with the template's helpers { #api-4 }

A paged list endpoint MUST:

- take a query schema that subclasses `PaginationQuerySchema` (`app/schemas/common.py`), and adds
  `sort_by` as a `Literal` of the columns it sorts by, with a default;
- sort with `apply_sorting()` (`app/utils/pagination.py`), which adds the `id` tiebreaker of
  [API-3](#api-3);
- answer with the page's items as `data`, and `build_pagination_meta()`'s `PaginationMetaSchema` as
  `meta`, the shape of `PaginatedResponseSchema`.

A sort column that `apply_sorting()` cannot resolve, such as an aggregate, is ordered by hand, with
the model's `id` last.

**Why.** Validation checks `sort_by` against its `Literal` before the value reaches a query, so a
client sorts only by the columns the endpoint offers, and the OpenAPI document lists them.
`PaginationQuerySchema` brings `page` and `per_page` with their bounds (`per_page` at most 100) and
`sort_dir`. Every paged endpoint then takes the same parameters and answers in the same shape, so
the frontend pages every list in one way.

### API-5 — Error responses are documented with `ApiErrorResponseSchema` { #api-5 }

An endpoint's `@api.validate` MUST document every error status the endpoint answers with, with
`ApiErrorResponseSchema` (`app/schemas/common.py`):
`resp=SpectreeResponse(HTTP_200=ProjectResponse, HTTP_404=ApiErrorResponseSchema)`. The error
response itself comes from an exception ([BE-2](backend.md#be-2)).

**Why.** The error handlers answer every exception with one envelope: `error`, `details.message`,
an optional `code` and the `correlationId`. Documented, the envelope is in the OpenAPI document, so
the frontend's generated types hold an error's shape as they hold a success's.

## Recipe

A paged list. The query schema whitelists the sort columns, and the response is `data` and `meta`:

```python
class ProjectListQuery(PaginationQuerySchema):
    sort_by: Literal["name", "created_at"] = Field("name", description="The column to sort by")


class ProjectPage(BaseModel):
    data: list[ProjectResponse]
    meta: PaginationMetaSchema


@projects_bp.route("", methods=["GET"])
@api.validate(
    query=ProjectListQuery,
    resp=SpectreeResponse(HTTP_200=ProjectPage, HTTP_400=ApiErrorResponseSchema),
)
@inject
def list_projects(
    project_service: ProjectService = Provide[ServiceContainer.project_service],
) -> Response:
    query = ProjectListQuery.model_validate(request.args.to_dict())
    projects, total = project_service.list_projects(query)
    page = ProjectPage(
        data=[ProjectResponse.model_validate(project) for project in projects],
        meta=build_pagination_meta(total, query.page, query.per_page, query.sort_by, query.sort_dir),
    )
    return jsonify(page.model_dump(mode="json"))
```

The service sorts through `apply_sorting()`, then cuts the page:

```python
def list_projects(self, query: ProjectListQuery) -> tuple[list[Project], int]:
    total = self.db_session.scalar(select(func.count()).select_from(Project)) or 0
    statement = apply_sorting(select(Project), Project, query.sort_by, query.sort_dir)
    page = statement.offset(query.offset).limit(query.per_page)
    return list(self.db_session.scalars(page)), total
```

An operation that runs as a task answers `202` with what `start_task()` returns:

```python
@projects_bp.route("/<project_id>/export", methods=["POST"])
@api.validate(resp=SpectreeResponse(HTTP_202=TaskStartResponse, HTTP_404=ApiErrorResponseSchema))
@inject
def export_project(
    project_id: str,
    task_service: TaskService = Provide[ServiceContainer.task_service],
) -> tuple[Response, int]:
    auth = get_auth_context()
    started = task_service.start_task(
        ExportProjectTask(),
        caller_subject=auth.subject if auth else None,
        project_id=project_id,
    )
    return jsonify(started.model_dump(mode="json")), 202
```
