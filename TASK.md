# TASK: aw-sched-runner-s26-sleeps-poll-minutes-or-d

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` ends with a stubbed scheduler:

```python
async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:
    pass
```

Reproduced by reading the file and calling it: `await schedule_scheduler(2)`
returns immediately without ever sleeping, so any caller expecting a periodic
poll loop gets no polling at all. There is also no default poll interval
defined anywhere in the module.

## Entry point

src/scheduled_runner.py:139 (`async def schedule_scheduler`)

## Required change

Implement `schedule_scheduler` as an infinite tick loop that, on every tick,
sleeps for `(poll_minutes or DEFAULT_POLL_MINUTES) * 60` seconds using
`await asyncio.sleep(...)`. Add the module-level constant
`DEFAULT_POLL_MINUTES = 5` (minutes). The `or` fallback is required: a falsy
argument (`None`, `0`) must fall back to the default, not sleep for 0.

Contract:
- `poll_minutes` given and truthy -> each tick sleeps `poll_minutes * 60` seconds.
- `poll_minutes` omitted/`None`/falsy -> each tick sleeps `DEFAULT_POLL_MINUTES * 60` = 300 seconds.
- The loop repeats forever (each iteration re-sleeps the same interval).

Behaviour that must NOT change:
- Every existing function and constant in the module (`select_results`,
  `run_cycle`, `search_seats_aero`, `_TripView`, `get_trip`, `_result_key`,
  `search_schedule`, `notify_hit`, `run_schedule`, `NOTIFIED_KEYS_CAP`) keeps
  its exact current behaviour.
- The existing imports stay; only new top-level names are added (`asyncio`
  import, `DEFAULT_POLL_MINUTES`).

## Must contain

- `DEFAULT_POLL_MINUTES = 5`
- `(poll_minutes or DEFAULT_POLL_MINUTES) * 60`
- `await asyncio.sleep((poll_minutes or DEFAULT_POLL_MINUTES) * 60)`
- `async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:`

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
