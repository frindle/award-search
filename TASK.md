# TASK: aw-sched-runner-s27-use-module-level-logging

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` has no logging at all. The two swallow-and-continue
paths -- `select_results` (`except Exception: continue`) and `run_cycle`
(`except Exception: continue`) -- drop a result or an entire alert's search on
any error with zero trace: no record, no stderr output. Reproduced by running
those paths against a raising dependency (a `get_trip` that throws for one
availability id; a `search_fn` that raises for one alert): the bad item is
silently skipped and nothing observable happens. The module also never imports
the stdlib `logging`.

## Entry point

src/scheduled_runner.py:1 -- top of module (no `import logging`, no logger);
the silent paths are in `select_results` and `run_cycle`.

## Required change

In src/scheduled_runner.py: Use module-level logging.getLogger(__name__). Stdlib.

Concretely:
- Add `import logging` to the stdlib imports at the top of the file.
- Create a module-level logger bound to the module's own name, e.g.
  `log = logging.getLogger(__name__)`, placed with the other module constants.
- Use that logger in the two silent swallow-and-continue paths so failures are
  observable: log (with context identifying the alert id) before each
  `continue` in `select_results` and in `run_cycle`.

Behaviour that must NOT change:
- `select_results` still returns exactly the results that pass both filter
  passes, with `taxes` set from the trip and a `booking_url` attached; bad
  results are still skipped (not raised).
- `run_cycle` still returns `{alert_id: kept}` for alerts whose search succeeds
  and skips failing alerts without raising.
- `get_trip` still returns `None` when the client raises or has no trip, and a
  `_TripView` with taxes in dollars otherwise.
- No new third-party dependency; stdlib only.

## Must contain

- `import logging`
- `log = logging.getLogger(__name__)`
- `log.exception("select_results: dropping result %r", r.get("availability_id"))`
- `log.exception("run_cycle: search failed for alert %s", alert_id)`

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
