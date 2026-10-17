# Status values

A status field holds one of a fixed set of values, and the frontend shows each of them. These
rules keep the set exhaustive from the backend's schema to the label the user sees, so that a value
added to the backend fails the frontend's type check until the frontend handles it.

They apply to the statuses of the app's own entities, such as a task's or an order's lifecycle:
not to HTTP status codes, and not to state that only the UI holds.

### STATUS-1 — A status field is a closed type { #status-1 }

A status field in a backend schema MUST be typed with its values: a `Literal[...]` of them, or a
`StrEnum`. It MUST NOT be a plain `str`.

**Why.** Pydantic emits either type as an `enum` in the OpenAPI document, and the frontend's
generated types turn the `enum` into a union of the values. A `str` reaches the frontend as
`string`, and nothing then tells the frontend that a value is new.

### STATUS-2 — The frontend types a status by its generated schema { #status-2 }

Frontend code that takes a status MUST type it from the generated OpenAPI types,
`components['schemas']['<Schema>']['status']` or the generated alias, never as `string`.

**Why.** The generated union is the backend's set of values. Typed as `string`, the code compiles
whatever the backend adds.

### STATUS-3 — A switch over a status ends in a `never` guard { #status-3 }

A `switch` over a status MUST handle every value, and its `default` branch MUST assign the status
to a `never`.

**Why.** With the guard, a value the backend adds is a compile error at every switch that does not
handle it, instead of a missing label at run time. The `default` branch still returns something,
so a response from a newer backend renders while the frontend catches up.

### STATUS-4 — Status labels live in one file { #status-4 }

The mappings from a status to its label, colour or icon MUST live in one module,
`src/lib/utils/status-labels.ts`. A component imports its mapper from there and MUST NOT define a
mapping inline. The template ships no such module: an app creates it with its first mapper.

**Why.** One status shows up in lists, detail pages, badges and filters. With one mapper, a label
changes in one place, and the guard of [STATUS-3](#status-3) points at one switch per status.

## Recipe

The backend schema types the status with its values:

```python
class OrderResponse(BaseModel):
    id: str
    status: Literal["draft", "submitted", "shipped", "cancelled"]
```

`src/lib/utils/status-labels.ts` maps each value, with the guard in `default`:

```ts
import type { components } from '@/lib/api/generated/types';

type OrderStatus = components['schemas']['OrderResponse']['status'];

export function orderStatusLabel(status: OrderStatus): { label: string; color: string } {
  switch (status) {
    case 'draft':
      return { label: 'Draft', color: 'inactive' };
    case 'submitted':
      return { label: 'Submitted', color: 'info' };
    case 'shipped':
      return { label: 'Shipped', color: 'success' };
    case 'cancelled':
      return { label: 'Cancelled', color: 'inactive' };
    default: {
      const _exhaustive: never = status;
      return { label: String(_exhaustive), color: 'inactive' };
    }
  }
}
```
