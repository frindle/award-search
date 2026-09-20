# TASK: aw-sched-runner-s4-from-scheduled-searches

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` does not import the scheduled-searches API at all.
Observed by reading the file: its only imports are `passes_filters`,
`seats_aero_url`, and `send_award_notification`; there is no reference to
`scheduled_searches` anywhere in the module, so any code path that needs
`effective_programs`, `is_due`, `load_schedules`, `query_legs`, or
`upsert_schedule` from this runner cannot reach them. Verified with a grep:
`grep -n scheduled_searches src/scheduled_runner.py` returns nothing.

## Entry point

src/scheduled_runner.py:1 (the import block at the top of the module)

## Required change

In src/scheduled_runner.py: add `from .scheduled_searches import effective_programs, is_due, load_schedules, query_legs, upsert_schedule` to the existing import block. HOW TO PROVE IT (do exactly what s1 did, successfully): stub the imported module in test_fixture.py with a distinctive fake implementation of each imported name, load the TARGET module (src/scheduled_runner.py) with target.__package__ set so the relative import resolves, then assert each imported name is reachable AND correctly bound through target's own namespace by calling it and checking your stub's distinctive return value. Kill test: remove the import line -> AttributeError on target.<name>. Do NOT test unrelated functions (e.g. run_cycle) -- the property under test is only that these names are imported and correctly bound.

Behaviour that must NOT change:
- The existing imports (`passes_filters`, `seats_aero_url`, `send_award_notification`) remain present and functional.
- `select_results` and `run_cycle` keep their current behaviour (the fixture does not assert on them, but the module must still parse and import cleanly with them intact).

## Must contain

- in src/scheduled_runner.py: `from .scheduled_searches import effective_programs, is_due, load_schedules, query_legs, upsert_schedule`
- in src/scheduled_runner.py: `effective_programs`
- in src/scheduled_runner.py: `is_due`
- in src/scheduled_runner.py: `load_schedules`
- in src/scheduled_runner.py: `query_legs`
- in src/scheduled_runner.py: `upsert_schedule`

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
