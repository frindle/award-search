# TASK: aw-sched-runner-s21-always-sets-sched-last-c

## Confirmed defect (observed, not suspected)

`run_schedule()` in `src/scheduled_runner.py` performs the search and fires
notifications but never records anything on the schedule dict. Observed by
calling it with a fake client: after the call, `sched` still has only its
original keys -- no `last_checked`, no `last_results`, no `last_hit_count`.
So callers (the webui / CLI status views) cannot tell when a schedule was last
checked or what it last returned.

## Entry point

src/scheduled_runner.py:113 (`def run_schedule`)

## Required change

In src/scheduled_runner.py: # ALWAYS sets sched['last_checked'] (datetime.now().isoformat()), sched['last_results']=hits, sched['last_hit_count']=len(hits).

Concretely, `run_schedule(sched, client=None, notify=True)` must set on the
`sched` dict it was given -- before returning:

- `sched['last_checked'] = datetime.now().isoformat()` (a fresh ISO-8601
  timestamp taken at run time)
- `sched['last_results'] = results` (the list returned by `search_schedule`)
- `sched['last_hit_count'] = len(results)`

This must happen ALWAYS -- including when the search returns zero hits and
regardless of the `notify` flag. Add `from datetime import datetime` to the
imports if it is not already present.

Behaviour that must NOT change:
- `run_schedule` still returns exactly the list produced by
  `search_schedule(sched, client=client)`.
- When `notify=True`, `notify_hit(sched, r)` is still attempted for every hit
  (exceptions swallowed); when `notify=False`, no notification is sent.
- All other functions in the module (`select_results`, `run_cycle`,
  `search_seats_aero`, `get_trip`, `_result_key`, `search_schedule`,
  `notify_hit`) are untouched and keep their current behaviour.

## Must contain

- `from datetime import datetime`
- `sched['last_checked'] = datetime.now().isoformat()`
- `sched['last_results'] = results`
- `sched['last_hit_count'] = len(results)`

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
