# TASK: aw-sched-routes-s10-get-scheduled-sched-id-e

## Confirmed defect (observed, not suspected)

The scheduled-routes router (`src/webui/scheduled_routes.py`) already serves the
edit template for NEW schedules via `GET /api/scheduled/new` (mode='new'), but
there is no route to open an EXISTING schedule for editing: requesting
`/api/scheduled/{sched_id}/edit` returns 404 from FastAPI's router itself.
Verified by reading the file -- only `/templates`, `/page/{name}`,
`/scheduled/new`, `/partners`, `/partners/{code}` and `POST /run` are declared;
no `{sched_id}` route exists anywhere in the module.

## Entry point

src/webui/scheduled_routes.py:63 (the existing `@router.get("/scheduled/new")` handler -- the new route mirrors it)

## Required change

Add a route to `src/webui/scheduled_routes.py`:

    GET /api/scheduled/{sched_id}/edit   -> same template with the loaded schedule and mode='edit'

Exact contract:
- The router already has `prefix="/api/scheduled"`, so declare the path as
  `/scheduled/{sched_id}/edit` (full URL becomes `/api/scheduled/{sched_id}/edit`).
- Load the schedule for `sched_id` from an in-memory store. Add a module-level
  `SCHEDULES: Dict[str, Dict] = {}` next to `TEMPLATES`, plus a setter
  `set_schedules(schedules)` that replaces it (mirroring how `init(templates)`
  works). The fixture seeds the store through this setter.
- On success render the SAME template as `/scheduled/new`:
  `TEMPLATES.TemplateResponse("scheduled_edit.html", {...})` with context keys
  `request`, `schedule`, `mode`, `programs`, `partners`, `error`.
- `schedule` must be the loaded schedule passed through the existing
  `normalize_schedule(...)` helper (so sparse stored dicts come back in the full
  rendered shape), and `mode` must be `"edit"`. Keep `programs: []`,
  `partners: []`, `error: None` exactly as `/scheduled/new` does.
- Unknown `sched_id`: raise `HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})` -- a clean 404 with that detail shape, never a 500.

Behaviour that must NOT change:
- `GET /api/scheduled/new` still renders `scheduled_edit.html` with mode='new' and the empty normalized schedule.
- `normalize_schedule({})` keeps producing the same full defaulted shape (id None, name "", empty lists, filters {airlines [], max_points None, max_taxes None}, interval_hours 6, notify_pushover False, enabled True).
- The existing `/templates`, `/page/{name}`, `/partners`, `/partners/{code}` and `POST /run` routes keep their current status codes and bodies.

## Must contain

- `@router.get("/scheduled/{sched_id}/edit")`
- `def scheduled_edit(request: Request, sched_id: str):`
- `"mode": "edit"`
- `"schedule not found"`
- `set_schedules`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

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
