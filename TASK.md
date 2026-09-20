# TASK: aw-sched-runner-s9-result-key

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` has no stable identity for a single search result. The
module already lands `select_results`, `run_cycle`, `search_seats_aero` and
`get_trip` from earlier slices, but nothing in the file can name "this exact
result" so that downstream code (dedup / seen-tracking) can key on it. Observed:
there is no `_result_key` symbol anywhere in the module (`grep _result_key
src/scheduled_runner.py` returns nothing), so any caller needing a per-result
identity has none to call.

## Entry point

src/scheduled_runner.py (append at end of file, after `get_trip`)

## Required change

Add exactly one function:

```python
def _result_key(r: Dict) -> str:
    return "|".join([
        str((r or {}).get("program", "")),
        str((r or {}).get("origin", "")),
        str((r or {}).get("destination", "")),
        str((r or {}).get("date", "")),
        str((r or {}).get("cabin", "")),
    ])
```

Contract:
- Takes a single result dict `r` (may be `{}`, may miss any of the five keys,
  and values may be non-string).
- Returns a `str` that is the pipe-joined concatenation of the stringified
  values of `program`, `origin`, `destination`, `date`, `cabin` in exactly that
  order.
- Missing or absent fields contribute an empty string at their fixed position;
  non-string values are coerced with `str()`.
- Must NOT raise on `{}`, missing keys, or non-string values.

Behaviour that must NOT change:
- The existing imports (`passes_filters`, `seats_aero_url`,
  `send_award_notification`, `SeatsAeroClient`, and the five names from
  `.scheduled_searches`) remain intact at the top of the file.
- `select_results(alert, results)`, `run_cycle(alerts, search_fn)`,
  `search_seats_aero(...)`, `_TripView`, and `get_trip(availability_id)` keep
  their exact current signatures and behaviour.

## Must contain

- `def _result_key(r: Dict) -> str:`
- `"|".join(`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/scheduled_runner.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The five `_result_key` cases in `test_fixture.py` exercise: the full canonical
key, `{}`, a partial dict with only one key present, non-string values coerced
via `str()`, and the return type being `str`. Every line of the new function is
therefore asserted by at least one case. The fixture also asserts that the
module binds `Dict` in its own namespace after exec (the annotation is
evaluated against module globals), so the added `from typing import Dict`
import line is exercised too -- removing it fails the verify.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
