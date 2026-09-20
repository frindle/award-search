# TASK: aw-sched-runner-s5-from-seats-aero-import-s

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` never imports `SeatsAeroClient`, so the scheduled
runner cannot construct a Seats Aero client at all. Verified by reading the
file: its import block pulls in `.alert_filters`, `.deeplinks`, `.pushover`,
and `.scheduled_searches` only -- there is no reference to `seats_aero` or
`SeatsAeroClient` anywhere in the module, and `grep -n SeatsAeroClient
src/scheduled_runner.py` returns nothing.

## Entry point

src/scheduled_runner.py:4 (the import block; the new import goes with it)

## Required change

In src/scheduled_runner.py: from .seats_aero import SeatsAeroClient. HOW TO PROVE IT (do exactly what s1 did, successfully): stub the imported module in test_fixture.py with a distinctive fake implementation of the imported name, load the TARGET module (src/scheduled_runner.py) with target.__package__ set so the relative import resolves, then assert the imported name is reachable AND correctly bound through target's own namespace by calling it and checking your stub's distinctive return value. Kill test: remove the import line -> AttributeError on target.<name>. Do NOT test unrelated functions (e.g. run_cycle) -- the property under test is only that this one name is imported and correctly bound.

Behaviour that must NOT change:
- The existing imports of `passes_filters`, `seats_aero_url`,
  `send_award_notification`, and the `.scheduled_searches` names stay intact.
- `select_results(alert, results)` still filters via `passes_filters` and skips
  entries that raise.
- `run_cycle(alerts, search_fn)` still returns `{alert_id: kept}` for alerts
  with surviving results and tolerates a raising `search_fn`.

## Must contain

- in src/scheduled_runner.py: `from .seats_aero import SeatsAeroClient`

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
