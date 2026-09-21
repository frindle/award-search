# TASK: aw-sched-runner-s15-first-evaluate-passes-fi

## Confirmed defect (observed, not suspected)

`select_results` in `src/scheduled_runner.py` evaluates every result with the
alert's FULL filters dict, including `max_taxes`, against the result's real
taxes value. A result whose taxes exceed `max_taxes` is dropped on that first
evaluation even though the intended flow is to evaluate it tax-blind first and
let a later stage apply the tax cap. Reproduced by calling
`select_results({"filters": {"max_taxes": 5.0}}, [{"taxes": 99.0}])` with a
recording stand-in for `passes_filters`: the recorded filters still contain
`max_taxes` and the result's taxes is its real value, not 0.0.

## Entry point

src/scheduled_runner.py:12 (`select_results`, the `if passes_filters(r, filters):` line)

## Required change

In src/scheduled_runner.py: #   First evaluate passes_filters on a COPY with taxes=0.0 and the filters dict MINUS 'max_taxes'.

Concretely, inside `select_results`, for each result:
- build a copy of the result (the original must not be mutated), set its
  `taxes` to `0.0`;
- evaluate `passes_filters` on that copy with a filters dict that excludes the
  `'max_taxes'` key (all other filter keys pass through unchanged);
- if that first evaluation fails, skip the result; otherwise keep it in the
  output exactly as before (the ORIGINAL result object goes into `kept`).

Behaviour that must NOT change:
- results whose first-pass evaluation passes are still kept, and the original
  (unmodified) result dict is what appears in the returned list;
- a filters dict without `'max_taxes'` behaves identically to before for every
  other key;
- an exception raised by `passes_filters` on one result is still swallowed and
  that result skipped, with remaining results still processed;
- all other functions in the module (`run_cycle`, `search_seats_aero`,
  `get_trip`, `_result_key`, `search_schedule`) are untouched.

## Must contain

- `max_taxes`
- `0.0`
- `passes_filters`

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
