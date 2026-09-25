# TASK: aw-sched-routes-s15-post-scheduled-sched-id

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` exposes a legacy `POST /api/scheduled/run` that
takes a program name in the body, but there is NO way to trigger an individual
stored schedule by id. Reproduced: with a schedule registered under id `s1`,
`curl -X POST .../api/scheduled/s1/run` returns 405 Method Not Allowed (no such
route exists), while only the program-based `/run` route responds. The UI's
per-schedule "Run now" action therefore has no endpoint to call.

## Entry point

src/webui/scheduled_routes.py:296 -- the `@router.post("/run")` / `scheduled_run`
route is where schedule execution currently lands; the new per-id route belongs
next to it, reusing the module's existing `SCHEDULES` registry and the already
imported `run_schedule`.

## Required change

Add a route in `src/webui/scheduled_routes.py`:

    POST /api/scheduled/{sched_id}/run   ->   run_schedule(sched) in a threadpool

Exact contract:

- The handler must be `async def` and dispatch the blocking call with
  `await anyio.to_thread.run_sync(run_schedule, schedule)` (add
  `import anyio` at the top of the file). Do NOT call `run_schedule` inline on
  the event loop thread.
- Look up the schedule in the module-level `SCHEDULES` dict by `sched_id`. If it
  is missing, raise `HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})` -- same shape as the other routes in this file. Never a 500.
- Pass the STORED schedule dict (the value from `SCHEDULES[sched_id]`) as the
  single positional argument to `run_schedule`, and return whatever
  `run_schedule` returns, verbatim, as the JSON response body.
- Route order: register the new `{sched_id}/run` route BEFORE the existing
  `/run` route so FastAPI matches it first (the two paths are distinct, but keep
  the per-id route above the legacy one).

Behaviour that must NOT change:
- `POST /api/scheduled/run` with a body `{"program": "..."}` still calls
  `run_schedule(program=...)` and returns its result.
- `POST /api/scheduled/run` without a program still returns 422 with detail
  `{"error": "program is required", "code": "invalid_program"}`.
- All existing routes (`/templates`, `/scheduled/new`, `/scheduled/{sched_id}/edit`,
  `/scheduled/save`, `POST /{sched_id}`, `/{sched_id}/delete`, `/{sched_id}/toggle`,
  `/partners`) keep their current status codes and bodies.

## Must contain

- `@router.post("/{sched_id}/run")`
- `async def scheduled_run_by_id(sched_id: str):`
- `await anyio.to_thread.run_sync(run_schedule, schedule)`
- `"schedule not found"`
- `import anyio`

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
