# TASK: aw-sched-routes-s19-get-api-scheduled-sched

## Confirmed defect (observed, not suspected)

`GET /api/scheduled/{sched_id}/preview` does not exist. Reproduced by driving
the router through `fastapi.testclient.TestClient`: the request returns 404
("Not Found" from Starlette routing, no JSON body), while sibling routes on the
same router (e.g. `GET /api/scheduled/templates`) return 200. There is also no
`effective_programs()` helper in `src/webui/scheduled_routes.py`.

## Entry point

src/webui/scheduled_routes.py:15 (`router = APIRouter(prefix="/api/scheduled")`) -- the new route and helper are added to this existing router/module.

## Required change

In src/webui/scheduled_routes.py: GET  /api/scheduled/{sched_id}/preview -> {'legs': [{'origin','destination','start_date':iso,'end_date':iso}], 'leg_count': n, 'programs': effective_programs(sched)}.

Contract:
- `GET /api/scheduled/{sched_id}/preview` is registered on the existing `router`.
- Unknown `sched_id` -> HTTP 404 with detail `{"error": "schedule not found", "sched_id": <id>}` (same shape as the other routes in this file). Never a 500.
- On success, return exactly: `{"legs": [...], "leg_count": n, "programs": [...]}` where each leg is `{"origin", "destination", "start_date", "end_date"}` -- one leg per (origin x destination x date_range) combination; `start_date`/`end_date` come from the schedule's `date_ranges` entries (`start`/`end`, possibly None); `leg_count == len(legs)`.
- Add a module-level helper `effective_programs(schedule)` returning a list of program ids: the schedule's own non-empty `programs` if set, otherwise every configured program id from `load_programs_config()` (in `src/search/programs/base.py`).

Behaviour that must NOT change:
- All existing routes keep working: `GET /api/scheduled/templates`, `POST /run`, `POST /{sched_id}`, the save/toggle/delete endpoints, and the 404 shapes of existing routes.
- Existing helpers (`normalize_schedule`, `parse_csv`, `parse_date_ranges`, `parse_cap`) are untouched.

## Must contain

- `@router.get("/{sched_id}/preview")`
- `def scheduled_preview(sched_id: str):`
- `"leg_count"`
- `effective_programs`
- `"schedule not found"`

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
