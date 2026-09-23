# TASK: aw-sched-runner-s18-notify-hit

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` has no way to notify a user when a scheduled search
hits award space. Verified by reading the module: it defines `search_schedule`,
`select_results`, `run_cycle`, etc., and imports `send_award_notification` from
`.pushover` (line 4) but never calls it -- there is no function in the file that
sends a notification for a hit result. `grep -n "notify_hit" src/scheduled_runner.py`
returns nothing, so any caller of `scheduled_runner.notify_hit` fails with
`AttributeError`.

## Entry point

src/scheduled_runner.py:104 (end of module -- the new function is appended after `search_schedule`)

## Required change

Add to `src/scheduled_runner.py`:

```python
def notify_hit(sched: Dict, r: Dict) -> None   # calls send_award_notification(origin,destination,date,program=r['source'],miles=r['cost'],cabin,seats,booking_url).
```

Exact contract:
- `notify_hit(sched: Dict, r: Dict) -> None` -- returns nothing.
- It must call the already-imported `send_award_notification(origin, destination, date, program=..., miles=..., cabin=..., seats=..., booking_url=...)`.
- `origin`, `destination`, and `date` come from the schedule dict `sched` (keys `"origin"`, `"destination"`, `"date"`).
- `program` comes from `r["source"]`; `miles` comes from `r["cost"]`; `cabin`, `seats`, and `booking_url` come from `r`.
- Missing keys / empty dicts must not raise -- pass the missing values through as-is (e.g. via `.get`).

Behaviour that must NOT change:
- All existing functions (`select_results`, `run_cycle`, `search_seats_aero`,
  `_TripView`, `get_trip`, `_result_key`, `search_schedule`) keep their exact
  signatures and behaviour; no imports are removed or renamed.
- The module still parses and imports cleanly with its existing relative imports.

## Must contain

- `def notify_hit(sched: Dict, r: Dict) -> None`
- `send_award_notification(`
- `"source"`
- `"cost"`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

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
