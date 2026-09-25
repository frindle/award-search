# TASK: aw-sched-routes-s13-post-scheduled-sched-id

## Confirmed defect (observed, not suspected)

The scheduled-routes router has no way to delete a schedule. `POST /api/scheduled/{sched_id}` exists for editing and `SCHEDULES` is the in-memory store, but there is no route that removes an entry -- verified by reading `src/webui/scheduled_routes.py`: the only mutating routes are `/scheduled/save` (upsert) and `/{sched_id}` (edit). A client POSTing to a delete endpoint gets a 405/404 with no way to remove a schedule.

## Entry point

src/webui/scheduled_routes.py:163 -- the router (`router = APIRouter(prefix="/api/scheduled")`) where the new route is added, next to the existing `@router.post("/{sched_id}")` edit-save handler.

## Required change

In src/webui/scheduled_routes.py: add a module-level function `delete_schedule(sched_id)` that raises `HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})` when the id is not in `SCHEDULES`, otherwise removes it from `SCHEDULES`. Then add route handler `scheduled_delete(sched_id)` on `@router.post("/{sched_id}/delete")` that calls `delete_schedule(sched_id)` and returns `RedirectResponse('/scheduled', status_code=303)`.

Behaviour that must NOT change:
- `POST /api/scheduled/save` still upserts into `SCHEDULES` and 303-redirects to `/scheduled?saved=1`.
- `GET /api/scheduled/templates`, `GET /api/scheduled/partners`, `POST /api/scheduled/run`, the edit-save route, and all helpers (`normalize_schedule`, `parse_csv`, `parse_date_ranges`, `parse_cap`) keep working exactly as before.
- Deleting an unknown id returns 404 (not 500) with detail `{"error": "schedule not found", "sched_id": <id>}`.

## Must contain

- `delete_schedule`
- `@router.post("/{sched_id}/delete")`
- `RedirectResponse('/scheduled', status_code=303)`

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
