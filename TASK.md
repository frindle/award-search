# TASK: aw-sched-routes-s16-render-scheduled-result

## Confirmed defect (observed, not suspected)

The scheduled-search UI has no way to view the results of a schedule run.
`src/webui/templates/scheduled_result.html` exists and renders `{{ schedule.name }}`,
iterates `{% for r in results %}` rows (`r.date`, `r.origin`, `r.destination`,
`r.cabin`, `r.source`, `r.airlines`, `r.cost|formatnumber`, `r.taxes`, `r.seats`,
`r.booking_url`) and shows a "No availability matched this schedule's alert limits."
branch when `results` is empty -- but no route in
`src/webui/scheduled_routes.py` ever renders it. Verified by grepping the router:
there is no handler that references `scheduled_result.html`, so any URL for a
schedule's result page 404s while every other scheduled page works.

## Entry point

`src/webui/scheduled_routes.py`: add the missing route next to the existing
`/api/scheduled/{sched_id}/edit` and `/api/scheduled/{sched_id}` handlers (the
router is `APIRouter(prefix="/api/scheduled")`).

## Required change

In src/webui/scheduled_routes.py: render 'scheduled_result.html' with {request, schedule, results}.

Concretely: add a GET route on the existing `router` at path `/{sched_id}/result`.
It must look up the schedule in `SCHEDULES`; if it is missing, raise
`HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})`
(the same shape every other handler in this file uses). Otherwise render
`scheduled_result.html` via `TEMPLATES.TemplateResponse("scheduled_result.html", ...)`
with the context dict containing exactly these three keys: `"request"` (the
incoming `Request`), `"schedule"` (the stored schedule record from `SCHEDULES`),
and `"results"` (`list(schedule.get("last_results") or [])`).

Behaviour that must NOT change:
- Every existing route keeps working, including `GET /api/scheduled/templates`,
  `GET /api/scheduled/page/{name}`, the save/edit/delete/toggle routes and
  `GET /api/scheduled/partners`.
- Unknown schedule ids on any existing route still return their current 404
  shape (`{"error": "schedule not found", ...}`), never a 500.
- The new result route must NOT mutate the stored schedule (no writes to
  `SCHEDULES`).

## Must contain

- `@router.get("/{sched_id}/result")`
- `"scheduled_result.html"`
- `{"request": request, "schedule": schedule, "results": results}`
- `"error": "schedule not found"`

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
