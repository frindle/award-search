# TASK: aw-alert-filters-contract

## Confirmed defect (observed, not suspected)

Two observed symptoms in `src/alert_filters.py`, both reproduced by running the module directly:

1. `passes_filters({"airlines": ["NH", "JL"], "cost": 85000}, {"max_points": 90000})`
   returns **False** even though the result is under the points cap -- and
   `passes_filters({"airlines": ["UA"]}, {"airlines": ["UA", "NH"]})` also returns
   False. The current implementation treats EVERY filter key as an airline list,
   runs both sides through `normalize_airlines()`, and demands exact list
   equality, so numeric caps can never pass and a superset allowlist fails.
2. `describe_filters({"max_points": 90000})` **raises TypeError** ("expected
   string or bytes-like object" / non-string entry) because it pipes every value
   through `normalize_airlines()`.

## Entry point

src/alert_filters.py:31 (`passes_filters`) and src/alert_filters.py:57 (`describe_filters`)

## Required change

Fix passes_filters in src/alert_filters.py to implement the real three-constraint alert filter contract (airline allowlist by intersection, max_points cap, max_taxes cap - each independent, only applied when set, inclusive boundary, fail closed on unknown values), and stop describe_filters from raising TypeError on numeric caps.

The exact contract for `passes_filters(result, filters) -> bool`:

- `filters` is None or empty -> True (no filters).
- Only three keys are constraints: `airlines`, `max_points`, `max_taxes`. Any
  other key in `filters` is IGNORED and must not cause a False.
- **airlines**: if the normalized allowlist (`normalize_airlines(filters['airlines'])`)
  is empty -> constraint not applied. Otherwise pass when at least ONE of the
  result's carriers (normalized the same way) is in the allowlist -- set
  intersection non-empty, NOT list equality. A missing/None/empty
  `result['airlines']` FAILS when an allowlist is set (cannot prove the hit is
  on an allowed carrier).
- **max_points**: if None -> not applied. Otherwise pass when `result['cost']`
  is a number and `result['cost'] <= max_points`. INCLUSIVE: exactly equal to
  the cap PASSES. A missing/None/non-numeric cost FAILS (fail closed).
- **max_taxes**: if None -> not applied. Otherwise pass when `result['taxes']`
  is a number and `result['taxes'] <= max_taxes`. INCLUSIVE: exactly equal to
  the cap PASSES. A missing/None/non-numeric taxes value FAILS (fail closed --
  this is what lets the scheduled_runner two-pass design treat an unavailable
  get_trip as "drop the result").
- All applied constraints must pass (AND). Never raises on odd input; always
  returns a bool.

`describe_filters(filters) -> str` must render numeric caps without crashing,
e.g. `describe_filters({"airlines": ["UA", "NH"], "max_points": 90000,
"max_taxes": 100.0}) == "airlines UA,NH; max_points 90000; max_taxes 100.0"`,
and still return `"(no filters)"` for None/empty.

Behaviour that must NOT change:
- `normalize_airlines()` keeps its exact current behaviour (list/tuple of codes,
  single code string, or None -> uppercase stripped IATA list; non-string
  entries skipped; other types raise TypeError).
- `filter_results(results, filters)` still delegates to `passes_filters` and
  preserves input order.
- Both public signatures stay byte-identical:
  `def passes_filters(result: Dict, filters: Optional[Dict]) -> bool` and
  `def describe_filters(filters: Optional[Dict]) -> str`.

## Must contain

- in src/alert_filters.py: `def passes_filters(result: Dict, filters: Optional[Dict]) -> bool`
- in src/alert_filters.py: `def describe_filters(filters: Optional[Dict]) -> str`
- in src/alert_filters.py: `"airlines"`
- in src/alert_filters.py: `"max_points"`
- in src/alert_filters.py: `"max_taxes"`
- in src/alert_filters.py: `(no filters)`

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
