# TASK: aw-sched-routes-s14-post-scheduled-sched-id

## Confirmed defect (observed, not suspected)

The router in `src/webui/scheduled_routes.py` exposes POST `/api/scheduled/{sched_id}` (edit-save), POST `/api/scheduled/{sched_id}/delete`, and POST `/api/scheduled/save`, but there is NO toggle-enabled route. Observed by importing the module and inspecting `router.routes`: no route with path template `/{sched_id}/toggle` exists, so a client POST to `/api/scheduled/<id>/toggle` gets FastAPI's default 405/404 instead of flipping the schedule's `enabled` flag.

## Entry point

src/webui/scheduled_routes.py:17 (the `router = APIRouter(prefix="/api/scheduled")` declaration; the new route belongs with the other `/{sched_id}` routes, right after `scheduled_delete`)

## Required change

In src/webui/scheduled_routes.py add the MISSING toggle-enabled route. The file's APIRouter has prefix='/api/scheduled' and already has @router.post('/{sched_id}') (edit-save), @router.post('/{sched_id}/delete') and @router.post('/scheduled/save'); there is NO toggle route yet. Add exactly one new route, following the delete route's conventions: @router.post("/{sched_id}/toggle") def scheduled_toggle(sched_id: str). Behaviour: (1) look up schedule = SCHEDULES.get(sched_id); if it is None raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id}) -- byte-for-byte the same 404 shape scheduled_delete/scheduled_edit_save use; (2) otherwise FLIP the record's boolean 'enabled' field: the new value is `not bool(schedule.get("enabled", True))`, so an enabled schedule becomes disabled AND a disabled schedule becomes enabled (both directions must work -- do not hardcode False); (3) write the updated record back into SCHEDULES[sched_id] (upsert), preserving EVERY other key unchanged (id, name, origins, destinations, date_ranges, cabins, programs, transfer_partners, filters, interval_hours, notify_pushover, created_at, last_checked, last_results, notified_keys); (4) return RedirectResponse('/scheduled', status_code=303), exactly as scheduled_delete does. Change NOTHING else in the file: no new imports are needed (HTTPException and RedirectResponse are already imported), and no existing route may be edited.

Behaviour that must NOT change:
- POST `/api/scheduled/{sched_id}/delete` still 404s for an unknown id, deletes the record otherwise, and returns a 303 redirect to `/scheduled`.
- POST `/api/scheduled/{sched_id}` (edit-save) still merges non-null fields, preserves created_at/last_checked/last_results/notified_keys, and returns `{"schedule": ...}`.
- GET routes (`/templates`, `/page/{name}`, `/scheduled/new`, `/scheduled/{sched_id}/edit`, `/partners`, `/partners/{code}`), POST `/scheduled/save` and POST `/run` behave exactly as before.
- The 404 error body for a missing schedule is byte-for-byte `{"detail": {"error": "schedule not found", "sched_id": <id>}}`.

## Must contain

- in src/webui/scheduled_routes.py: `@router.post("/{sched_id}/toggle")`
- in src/webui/scheduled_routes.py: `def scheduled_toggle(sched_id: str):`
- in src/webui/scheduled_routes.py: `not bool(schedule.get("enabled", True))`

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
