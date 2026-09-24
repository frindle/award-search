# TASK: aw-sched-runner-s25-sleeps-20s-then-forever

## Confirmed defect (observed, not suspected)

`schedule_scheduler()` in `src/scheduled_runner.py` is a bare infinite loop that
only sleeps `(poll_minutes or DEFAULT_POLL_MINUTES) * 60` seconds per tick and
never touches the schedules at all. Reproduced by reading the function: its body
is exactly two lines (`while True:` / `await asyncio.sleep(...)`) -- no call to
`load_schedules()`, no `is_due()` check, no `run_schedule()` dispatch. So a
process started on this entry point polls forever without ever searching or
notifying for any schedule.

## Entry point

src/scheduled_runner.py:142 (`async def schedule_scheduler`)

## Required change

In src/scheduled_runner.py: # sleeps 20s, then forever: load_schedules(), run every schedule where is_due(s) via asyncio.to_thread(run_schedule, s).

Concretely, `schedule_scheduler` must:
1. First `await asyncio.sleep(20)` -- a one-time 20-second startup delay before
   any schedule work happens (this replaces nothing; it precedes the loop).
2. Then loop forever (`while True:`): on each pass call `load_schedules()`, and
   for every schedule `s` where `is_due(s)` is truthy, dispatch
   `await asyncio.to_thread(run_schedule, s)`. Schedules that are not due must
   be skipped (no `run_schedule` call for them). A failure while processing one
   schedule must not kill the loop. After the pass, sleep
   `(poll_minutes or DEFAULT_POLL_MINUTES) * 60` seconds and repeat.

Behaviour that must NOT change:
- The signature stays `async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None`.
- The per-tick poll interval is still `(poll_minutes or DEFAULT_POLL_MINUTES) * 60`
  (e.g. `poll_minutes=1` -> 60s between ticks; default -> 300s).
- All existing module-level code (`select_results`, `run_cycle`, `search_schedule`,
  `notify_hit`, `run_schedule`, etc.) is untouched and keeps working.

## Must contain

- in src/scheduled_runner.py: `await asyncio.sleep(20)`
- in src/scheduled_runner.py: `load_schedules()`
- in src/scheduled_runner.py: `is_due(s)`
- in src/scheduled_runner.py: `asyncio.to_thread(run_schedule, s)`

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
