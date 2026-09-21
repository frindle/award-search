# TASK: aw-sched-runner-s16-against-the-full-filters

## Confirmed defect (observed, not suspected)

`select_results` in `src/scheduled_runner.py` evaluates every candidate with a
hardcoded `taxes = 0.0` and the filters dict MINUS `max_taxes`, so any result
that passes the other filters is kept regardless of its real taxes -- the
`max_taxes` filter is silently never applied, and `r["taxes"]` is left unset on
kept results. Reproduced by calling `select_results({"filters": {"max_taxes": 100}}, [result])`:
a result whose trip carries taxes of 150 is still returned in the kept list.

## Entry point

src/scheduled_runner.py:9 (`def select_results`)

## Required change

In src/scheduled_runner.py, extend select_results: for each result that passes the existing first pass (COPY with taxes=0.0, filters minus max_taxes), call get_trip(r.get('availability_id')) to fetch the real trip. If get_trip returns a trip, build a second candidate with taxes = trip.total_taxes and re-evaluate passes_filters against the FULL filters dict (including max_taxes); only keep the result if this second check passes, and set r['taxes'] = trip.total_taxes on the kept result. If get_trip raises or returns None, leave taxes as None and do NOT keep the result (fail closed -- unknown taxes cannot satisfy a max_taxes filter).

Behaviour that must NOT change:
- The first pass is unchanged: candidate copy with `taxes = 0.0`, filters minus `max_taxes`; results failing it are dropped before any trip fetch happens (`get_trip` is not called for them).
- Results whose trip taxes exceed `max_taxes` are dropped and their `taxes` key stays unset/None (fail closed).
- A raising or None-returning `get_trip` never propagates out of `select_results`; the result is simply not kept.
- The rest of the module (`run_cycle`, `search_seats_aero`, `_TripView`, `get_trip`, `_result_key`, `search_schedule`) and all existing imports are untouched.

## Must contain

- `trip = get_trip(r.get("availability_id"))`
- `second["taxes"] = trip.total_taxes`
- `passes_filters(second, filters)`
- `r["taxes"] = trip.total_taxes`

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
