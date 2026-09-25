# TASK: aw-sched-routes-s12-upserts-then-redirectres

## Confirmed defect (observed, not suspected)

The schedule editor form (`static`/templates `scheduled_edit.html`) posts to
`action="/scheduled/save"`, but no such route exists in the app. Reproduced by
driving the router with FastAPI's TestClient: `POST /api/scheduled/scheduled/save`
returns 405 Method Not Allowed (the path only matches GET routes), so saving a
new or edited schedule is impossible and nothing lands in `SCHEDULES`.

## Entry point

src/webui/scheduled_routes.py -- the router (`router = APIRouter(prefix="/api/scheduled")`)
has no POST handler for `/scheduled/save`; add it alongside the existing
`/scheduled/new`, `/scheduled/{sched_id}/edit` routes.

## Required change

In src/webui/scheduled_routes.py: # upserts, then RedirectResponse('/scheduled?saved=1', status_code=303).

Concretely, add a route `@router.post("/scheduled/save")` (an async handler
taking `request: Request`) that reads the form fields posted by
`scheduled_edit.html`:

- `sched_id` -- blank/absent means CREATE (generate a new id); non-blank means
  UPDATE the existing record in `SCHEDULES`.
- `name`, `origins`, `destinations` (comma-separated CSV strings),
  `range_start` / `range_end` (repeated fields, pair them with the existing
  `parse_date_ranges` helper), repeated checkbox fields `cabins`, `programs`,
  `transfer_partners`.
- `airlines` (CSV), `max_points`, `max_taxes` (caps -- invalid/blank values
  must become `None`, never a 500; use the existing `parse_cap` helper and
  swallow its `ValueError`).
- `interval_hours` (int, default 6 when blank or non-numeric).
- Checkboxes `notify_pushover` and `enabled`: present in the form means True,
  absent means False.

The handler upserts into `SCHEDULES` (new id via `uuid.uuid4()` on create; an
edit must PRESERVE `created_at`, `last_checked`, `last_results`,
`notified_keys` from the existing record) and then returns
`RedirectResponse('/scheduled?saved=1', status_code=303)` -- a 303 See Other,
Location exactly `/scheduled?saved=1`.

Behaviour that must NOT change:
- All existing routes keep working: `GET /templates`, `GET /page/{name}`,
  `GET /scheduled/new`, `GET /scheduled/{sched_id}/edit` (404 for unknown id),
  `POST /{sched_id}` JSON edit, `GET /partners`, `GET /partners/{code}`
  (404 for unknown code), `POST /run` (422 without program).
- The existing helpers (`normalize_schedule`, `parse_csv`, `parse_date_ranges`,
  `parse_cap`) keep their current behaviour.

## Must contain

- `RedirectResponse('/scheduled?saved=1', status_code=303)`
- `@router.post("/scheduled/save")`
- `async def scheduled_save(request: Request):`
- `from starlette.responses import RedirectResponse`

(Note: this environment's FastAPI does not re-export `RedirectResponse`, so it
comes from `starlette.responses`; the existing `from fastapi import ...` line
stays as-is.)

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

After the job runs, a mutation check flips/deletes each line you changed and
asks the verify to catch it. A changed line whose every mutant survives --
because no test asserts it -- FAILS the gate even when the fix is correct, and
the review never runs. So do NOT emit an isolated, untested line:
- Fold an unavoidable constant onto a line the test already exercises. Put a
  `timeout=` / a `daemon=True` flag / a small tuning number on the SAME line as
  a header dict, URL, or argument the fixture checks -- never on its own line.
- Prefer falling through to an implicit `return None` over a standalone
  `return None` in an `except:` the tests do not assert.
- If a line genuinely cannot be asserted and cannot be folded, it usually
  should not be a separate line at all -- restructure so it isn't.
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
