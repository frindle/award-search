# TASK: aw-alert-filters-s3-passes-filters

## Confirmed defect (observed, not suspected)

`src/alert_filters.py` currently exposes only `normalize_airlines`; there is no
way to ask whether a search result satisfies a set of filters. Reproduced by
importing the module and calling `passes_filters`: it does not exist
(`AttributeError: module 'target' has no attribute 'passes_filters'`). The
module parses fine, so this is a missing function, not a broken file.

## Entry point

src/alert_filters.py (append after `normalize_airlines`, which stays as-is)

## Required change

Add to `src/alert_filters.py`:

```python
def passes_filters(result: Dict, filters: Optional[Dict]) -> bool:
```

Contract:
- `filters is None` or an empty dict means "no filters" and returns `True`.
- Otherwise EVERY key of `filters` must be present in `result`; a missing key
  returns `False` (never raises).
- For each key, compare the two values as lists of normalized IATA codes using
  the existing `normalize_airlines`: case-insensitive, whitespace-stripped,
  order-sensitive equality. A mismatch on any key returns `False`.
- All keys satisfied -> `True`.

Behaviour that must NOT change:
- `normalize_airlines` keeps its exact current behaviour (None -> [], str ->
  one code, list/tuple of strings -> codes, non-string entries skipped, other
  types raise TypeError). Do not delete or alter it.
- The module still parses and imports cleanly with only stdlib (`typing`).

## Must contain

- `def passes_filters(result: Dict, filters: Optional[Dict]) -> bool:`
- `from typing import Dict, List, Optional`

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
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
