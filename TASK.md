# TASK: aw-sched-runner-s24-schedule-scheduler

## Confirmed defect (observed, not suspected)

`src/webui/app.py` needs to launch the background scheduler with
`asyncio.create_task(schedule_scheduler())`, but `src/scheduled_runner.py` has
no such name: `from ..scheduled_runner import schedule_scheduler` fails at
import time because the module only defines the per-slice helpers landed so far
(`select_results`, `run_cycle`, `search_schedule`, `notify_hit`,
`run_schedule`). Verified by reading the current module -- there is no
`schedule_scheduler` symbol anywhere in it.

## Entry point

src/scheduled_runner.py:module scope (append after `run_schedule`)

## Required change

In src/scheduled_runner.py: define `async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None` -- the background scheduler coroutine that src/webui/app.py imports as `from ..scheduled_runner import schedule_scheduler` and launches with asyncio.create_task(). THIS SLICE ONLY establishes the coroutine function itself: it must be a real `async def` (not a plain def, not a def returning a coroutine), take a single optional keyword parameter `poll_minutes` defaulting to None, and be importable at module scope. The loop body (sleep 20s, then forever load_schedules()/is_due()/asyncio.to_thread(run_schedule, s), sleeping (poll_minutes or DEFAULT_POLL_MINUTES)*60 per tick) is added by slices s25 and s26 -- do NOT build the full forever-loop here. Keep the body minimal and non-blocking so it can be awaited in a test without hanging.

Behaviour that must NOT change:
- `run_schedule(sched, client=..., notify=False)` still returns the search results list and records `last_hit_count` (and `notified_keys`) on the schedule dict.
- `select_results`, `run_cycle`, `search_schedule`, `notify_hit`, `get_trip` keep their existing signatures and behaviour -- this slice only ADDS a function, it does not touch any of them.

## Must contain

- `async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:`
- `from typing import Dict, List, Optional`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

(A bare bullet checks the default target. To PIN a literal to a specific file --
useful when a fix spans a helper file and the route/wiring that calls it --
prefix the bullet with `in <path>:`, e.g.
`- in app/api/x/route.ts: ` followed by a backtick-quoted token. Then that
token is required in THAT file, not the target.)

## Scope

Only edit `src/scheduled_runner.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
