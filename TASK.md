# TASK: aw-alert-filters-s4-filter-results

## Confirmed defect (observed, not suspected)

`src/alert_filters.py` exposes `normalize_airlines()` and `passes_filters(result, filters)` but has no way to apply the filters to a whole result set. Reproduced: `python3 -c "import ast; m=ast.parse(open('src/alert_filters.py').read()); print([n.name for n in m.body if isinstance(n, ast.FunctionDef)])"` prints only `['normalize_airlines', 'passes_filters']` -- there is no `filter_results`, so callers cannot filter a list of results at all.

## Entry point

src/alert_filters.py:31 (end of file, after `passes_filters`)

## Required change

In src/alert_filters.py: def filter_results(results: Iterable[Dict], filters: Optional[Dict]) -> List[Dict].

Contract:
- Returns a NEW list containing exactly the results for which `passes_filters(result, filters)` is True, in their original order.
- A None or empty `filters` means "no filters" and returns every result (same falsy rule passes_filters already uses).
- Accepts any Iterable of dicts as `results`, including a generator; it must be consumed at most once.
- Never raises for a missing filter key in a result -- that is delegated to passes_filters, which fails the match instead of raising.
- The returned list is a fresh object but shares the same dict references (no copying of results).

Behaviour that must NOT change:
- `normalize_airlines()` keeps its exact current behaviour (None -> [], str/tuple coercion, non-string entries skipped, other types raise TypeError).
- `passes_filters(result, filters)` keeps its exact current behaviour (falsy filters pass; missing key fails without raising; normalized IATA comparison per key).

## Must contain

- `def filter_results(results: Iterable[Dict], filters: Optional[Dict]) -> List[Dict]:`
- `from typing import Dict, Iterable, List, Optional`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/alert_filters.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
This is not about adding bogus assertions for constants; it's about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
