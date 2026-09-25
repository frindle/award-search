# TASK: aw-app-wiring-s7-imported-as-from-schedul

## Confirmed defect (observed, not suspected)

`src/webui/app.py` defines its own local stub `async def schedule_scheduler()`
(docstring "Placeholder for the scheduled-routes scheduler loop (later slice).",
body `return None`) and `lifespan()` starts it with
`sched_task = asyncio.create_task(schedule_scheduler())`, but after the `yield`
only `task.cancel()` runs -- so on shutdown the real alert task is cancelled
while `sched_task` leaks. Verified by reading the file: the placeholder def at
module scope shadows nothing (there is no import of a real scheduler), and the
shutdown block contains exactly one `.cancel()`.

## Entry point

src/webui/app.py:105 (placeholder `async def schedule_scheduler`) and
src/webui/app.py:117-120 (`lifespan()` shutdown block).

## Required change

In src/webui/app.py, replace the local placeholder scheduler with the real one and clean up its task. Currently app.py defines its own stub `async def schedule_scheduler(): """Placeholder for the scheduled-routes scheduler loop (later slice).""" return None`, and lifespan() starts `sched_task = asyncio.create_task(schedule_scheduler())` but only cancels `task` after the yield, leaking sched_task on shutdown. THREE changes: (1) DELETE the local placeholder `async def schedule_scheduler` definition from app.py; (2) import the real one at module scope as `from ..scheduled_runner import schedule_scheduler`; (3) after the `yield` in lifespan(), cancel sched_task as well as the existing task -- so both `task.cancel()` and `sched_task.cancel()` run on shutdown. Do NOT change any other behaviour in the file; the existing alert_scheduler task keeps working exactly as now.

Behaviour that must NOT change:
- The alert scheduler still starts: `asyncio.create_task(alert_scheduler(_alert_search, _alert_notify, interval))` runs at lifespan entry and `task.cancel()` still runs on shutdown.
- All routes keep their status codes and bodies (e.g. `GET /` -> 200 HTML home page; unknown `/results/{id}` -> 404 with `{"detail": "Search not found"}`; `POST /search` with missing required fields -> 422, never a 500).
- The imported `schedule_scheduler` is the one from `src/scheduled_runner.py` (same object), not another local copy.

## Must contain

- `from ..scheduled_runner import schedule_scheduler`
- `sched_task.cancel()`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/webui/app.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The import and both cancel calls are asserted by the behavioural cases: the
fixture checks that `app.schedule_scheduler is scheduled_runner.schedule_scheduler`,
that the placeholder text is gone, and that lifespan shutdown cancels BOTH
background tasks; the literal check pins the import line. Do not add unrelated
lines.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
