# TASK: aw-sched-routes-s11-preserves-created-at-las

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` has a GET edit page (`/api/scheduled/{sched_id}/edit`)
but NO way to save an edited schedule. The module's `SCHEDULES` store is the only
write surface, and nothing in the file ever updates it: grepping the file for a
POST route that writes `SCHEDULES[...]` finds none (the only POST is `/run`, which
just calls `run_schedule`). So an edit of a schedule cannot be persisted at all --
and any naive save would replace the whole record, wiping the runtime metadata
(`created_at`, `last_checked`, `last_results`, `notified_keys`) that the runner
maintains on the stored record (see how `src/webui/app.py` seeds those exact keys
on alert records and how `src/alerts.py` mutates them).

## Entry point

src/webui/scheduled_routes.py:115 (the existing `@router.post("/run")` route -- the
new save route belongs next to it, after `scheduled_edit`)

## Required change

In src/webui/scheduled_routes.py: add a POST route that saves an edit of an
existing schedule. Contract:

- Route: `POST /api/scheduled/{sched_id}` -- the router already carries the
  `/api/scheduled` prefix (see the existing routes in this file), so decorate with
  `@router.post("/{sched_id}")`, handler named `scheduled_edit_save(sched_id: str, body: EditRequest)`.
- Body model `EditRequest(BaseModel)` with all-optional fields mirroring the shape
  `normalize_schedule()` renders: `name`, `origins`, `destinations`, `date_ranges`,
  `cabins`, `programs`, `transfer_partners`, `filters`, `interval_hours`,
  `notify_pushover`, `enabled`.
- Unknown `sched_id` -> HTTP 404 with detail `{"error": "schedule not found", "sched_id": sched_id}`.
- A submitted (non-None) field replaces the stored value; a missing/None field keeps
  the existing value (partial edits must work).
- PRESERVES created_at/last_checked/last_results/notified_keys from the existing record on an edit:
  after saving, `SCHEDULES[sched_id]` still carries exactly the pre-edit values of those
  four keys, whatever the body said. An empty body (`{}`) leaves the record unchanged.
- On success return HTTP 200 with JSON `{"schedule": normalize_schedule(updated)}`.

Behaviour that must NOT change:
- All existing routes keep working: GET `/templates`, GET `/page/{name}`,
  GET `/scheduled/new`, GET `/scheduled/{sched_id}/edit` (404 shape included),
  GET `/partners`, GET `/partners/{code}`, POST `/run` (422 when `program` missing).
- The helpers `normalize_schedule`, `parse_csv`, `parse_date_ranges`, `parse_cap`,
  `init`, `set_schedules` keep their exact behaviour.

## Must contain

- `@router.post("/{sched_id}")`
- `def scheduled_edit_save(sched_id: str, body: EditRequest):`
- `class EditRequest(BaseModel):`
- `# PRESERVES created_at/last_checked/last_results/notified_keys from the existing record on an edit.`

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The fixture drives the route through fastapi.testclient and asserts both the
response body and the stored record, so every line of the new route is covered:
the 404 branch (unknown id), the field-merge loop (partial + full edits), each of
the four preserved-key assignments -- asserted both against the pre-edit values on
a record that HAS them and for key PRESENCE after saving a record that LACKS them
-- and the 200 response shape. Do not add untested helper lines; keep the
preservation logic inline in `scheduled_edit_save`.

## Loop instruction

Run `bash verify.sh` after every edit and it must print `VERIFY_OK`.
