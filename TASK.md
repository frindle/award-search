# TASK: aw-app-wiring-s6-sched-task-asyncio-creat

## Confirmed defect (observed, not suspected)

`src/webui/app.py`'s `lifespan()` starts only the alert scheduler task; there is
no scheduled-routes scheduler task. Verified by reading the file: `grep -n
create_task src/webui/app.py` shows exactly one hit (the `alert_scheduler` line),
and no `schedule_scheduler` symbol exists anywhere in the module, so the
scheduled-routes wiring has no background loop to run under.

## Entry point

src/webui/app.py:113 (inside `lifespan()`, immediately after the existing
`task = asyncio.create_task(alert_scheduler(...))` line)

## Required change

In src/webui/app.py, inside `lifespan()`, add directly after the existing alert
scheduler task line:

    sched_task = asyncio.create_task(schedule_scheduler())

and define a module-level async stub so that call is valid:

    async def schedule_scheduler():
        """Placeholder for the scheduled-routes scheduler loop (later slice)."""
        return None

Behaviour that must NOT change:
- `lifespan()` still creates and later cancels the existing alert scheduler task
  (`task = asyncio.create_task(alert_scheduler(_alert_search, _alert_notify, interval))`).
- All existing routes, helpers, imports, and module-level state in app.py remain
  untouched.

## Must contain

- `sched_task = asyncio.create_task(schedule_scheduler())`
- `async def schedule_scheduler():`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/webui/app.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The fixture runs `lifespan()` under a spy on `asyncio.create_task` and asserts
both `schedule_scheduler` and `alert_scheduler` are scheduled, so both added
lines carry tested behaviour. Do not add extra untested lines.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
