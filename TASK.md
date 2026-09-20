# TASK: aw-sched-runner-s3-from-pushover-import-sen

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py::run_cycle` collects kept award results per alert but
never notifies anyone. Reproduced by reading the module end-to-end: it imports
only `passes_filters`, builds `out[alert_id] = kept`, and returns -- there is no
call to `send_award_notification` (or anything else) anywhere in the file, so a
successful scheduled cycle silently drops every award it finds. The notification
helper already exists at module level in `src/pushover.py` (`send_award_notification`)
and is ready to be wired in; nothing imports it yet.

## Entry point

src/scheduled_runner.py:27 (the `return out` of `run_cycle`, where the kept
results are returned without ever being notified)

## Required change

In src/scheduled_runner.py: from .pushover import send_award_notification.

Wire the notifier into the cycle:

- Add the import at module top level, next to the existing
  `from .alert_filters import passes_filters` line.
- After an alert's results are kept (i.e. only for non-empty `kept`, after
  filtering), send one notification per kept result by calling
  `send_award_notification(...)` with keyword arguments taken from each result:
  `origin=`, `destination=`, `date=`, `program=`, `miles=`, `cabin=`, `seats=`,
  and `booking_url=` (passing the value through, which may be `None`).
- A notification failure must never abort the cycle or raise out of
  `run_cycle`: wrap each send so any exception degrades to a skipped/failed
  notification and the loop continues.

Behaviour that must NOT change:
- `select_results` still filters via `passes_filters`, swallowing per-result
  exceptions, and returns only passing results in order.
- `run_cycle(alerts, search_fn)` still iterates `(alerts or {}).items()`, skips
  alerts whose `search_fn` call raises (no exception escapes), and returns a dict
  mapping alert id -> kept list; alerts with no kept results are absent from the
  returned dict.
- The returned dict is unchanged in shape: notification happens as a side effect,
  it does not alter what `run_cycle` returns.

## Must contain

- `from .pushover import send_award_notification`
- `send_award_notification(`
- `booking_url=`

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
