# Modern apps

This site holds the conventions every modern app follows. A modern app is a monorepo generated
from ModernAppTemplate: a Flask backend from the backend template, a React frontend from the
frontend template, and the root template's workspace, CI and dev stack around them. The templates
give an app its infrastructure; this guide rules the code the app writes on top of it.

The navigation is the complete list of its pages.

## How the rules read

- **Every rule is a MUST.** Each is stated as a fact about an app's code that a reader can verify
  from the code. Each rule has an id, such as `API-3`, and a link to it is the page's address plus
  `#api-3`.
- **Every rule has its reason.** The reason is written under the rule. A rule does not bend
  because the code would be shorter without it.
- **The template's code is the reference.** Where a rule names a template module, a helper or a
  fixture, the template's current code is its definition: read it there before using it. A page
  ends with a recipe where the rule's code is not obvious from its statement.

## The pages

| Page | What it rules |
| --- | --- |
| [API](api.md) | How the backend's endpoints address resources, run slow work, page lists and document their errors. |
| [Status values](status.md) | Status fields, from the backend's schema to the label the user sees. |
| [Backend code](backend.md) | Measuring time, raising errors, and the failure of a system the app calls. |
| [Readiness](readiness.md) | The readiness check of each system the app depends on. |
| [Server-sent events](sse.md) | Who receives an event, and how the frontend lives with the stream. |
| [Frontend code](frontend.md) | Toasts and downloads. |
| [Testing](testing.md) | Real dependencies, failures, the backend's tests and the testing endpoints. |
| [Playwright](playwright.md) | The frontend's end-to-end specs. |

## Reading it as Markdown

Every page is also published as Markdown, for agents and tools that read Markdown better than HTML:

- [`llms.txt`](https://dev-guides.home/modern-app/llms.txt) — an index of every page, linking each
  page's Markdown copy.
- [`llms-full.txt`](https://dev-guides.home/modern-app/llms-full.txt) — every page's Markdown in
  one file.
