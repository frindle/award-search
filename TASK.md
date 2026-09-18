# TASK: aw-sched-runner-s1-from-alert-filters-impor

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` is an unimplemented stub -- its entire body is a
one-line docstring. Verified by reading the file and grepping `src/`: nothing
imports or calls `passes_filters`, so saved alerts are never re-checked on a
cycle and search results are never filtered through each alert's filters.

## Entry point

src/scheduled_runner.py:1 (the whole file is the stub; implement it)

## Required change

Implement `src/scheduled_runner.py` as the scheduled runner for saved alerts,
importing the filter predicate from the existing module instead of
re-implementing filtering:

- Top of file: `from .alert_filters import passes_filters`.
  (`src/alert_filters.py` is provided by the runtime and exposes
  `passes_filters(result, filters) -> bool`: every key in `filters` must equal
  the result's value for that key; an empty filter set keeps everything. Do NOT
  create or edit `alert_filters.py`, and do not define your own
  `passes_filters`.)

- `def select_results(alert, results):` -- return a NEW list containing exactly
  those dicts from `results` (in original order) for which
  `passes_filters(r, filters)` is truthy, where the filter set comes from
  `alert.get("filters") or {}`. A result for which `passes_filters` raises must
  be dropped; that exception must not propagate to the caller.

- `def run_cycle(alerts, search_fn):` -- one check cycle over every alert.
  `alerts` maps id -> alert dict (treat None as empty); `search_fn(alert)`
  returns that alert's raw list of result dicts. Return a dict mapping each
  alert id to its kept results via `select_results`, containing ONLY alerts
  with at least one kept result. An alert whose `search_fn` call raises is
  omitted from the returned dict and must not stop the rest of the cycle.

Behaviour that must NOT change:
- The module imports cleanly as part of package `src` (relative import).
- Filtering decisions are made by `passes_filters`, never re-implemented here.
- Order of kept results is preserved; input alert/result dicts are not mutated.

## Must contain

- `from .alert_filters import passes_filters`
- `def select_results(alert, results):`
- `def run_cycle(alerts, search_fn):`

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
