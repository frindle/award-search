# TASK: aw-sched-runner-s10-search-schedule

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` has no way to run a single stored schedule against the
Seats Aero client. Verified by reading the module as it exists now: it defines
`select_results`, `run_cycle`, `search_seats_aero`, `get_trip`, and `_result_key`,
and imports from `.scheduled_searches` (including `query_legs`), but there is no
function that takes one schedule dict and returns its search results. Any caller
that wants "run this one schedule" has to hand-roll the client call, so the
runner cannot be driven per-schedule.

## Entry point

src/scheduled_runner.py: end of file (after `_result_key`) -- add the new
function here; also extend the existing `from typing import Dict` line with
`List`.

## Required change

Add to src/scheduled_runner.py: def search_schedule(sched: Dict, client=None, today=None) -> List[Dict].

Contract:
- `sched` is a schedule dict (as stored by `.scheduled_searches`) or None/empty.
  Read its legs defensively with .get(): origin, destination, start_date,
  end_date, cabins, programs. Missing keys become None -- never raise KeyError.
- `client` is an injected search client exposing search(origin, destination,
  start_date=None, end_date=None, cabins=None, programs=None). When client is
  None, construct SeatsAeroClient() (already imported in this module) and use it.
- Forward the six legs positionally to client.search(...) exactly as read from
  sched, and return its result as a list of dicts. Do not wrap or filter the
  results; do not swallow exceptions raised by the client -- let them propagate.
- `today` is accepted for API compatibility with the scheduler's date injection;
  it does not change which legs are forwarded in this slice.

Behaviour that must NOT change:
- select_results, run_cycle, search_seats_aero, get_trip and _result_key keep
  their exact current behaviour (run_cycle still skips alerts whose search_fn
  raises; select_results still drops results that fail passes_filters).
- The existing imports stay; only the typing import gains List.

## Must contain

- `def search_schedule(sched: Dict, client=None, today=None) -> List[Dict]:`
- `from typing import Dict, List`

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
