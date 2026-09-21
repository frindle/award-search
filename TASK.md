# TASK: aw-scheduled-searches-s1-id-sched-ab12-name-bay-a

## Confirmed defect (observed, not suspected)

`src/scheduled_searches.py` is a one-line placeholder stub (`"""Stub for
src/scheduled_searches.py -- implement per TASK.md."""`). There is no module-level
registry of scheduled searches and no lookup helper, so nothing downstream can
reference the "Bay Area to Tokyo" schedule. Verified by reading the file: it
contains only that docstring.

## Entry point

`src/scheduled_searches.py:1` (the whole file is the stub).

## Required change

Create `src/scheduled_searches.py` containing a module-level list
`SCHEDULED_SEARCHES` with exactly one entry, and a lookup function
`get_scheduled_search(search_id)`. The single entry must be this dict, in this
key order:

```python
{
    'id': 'sched_ab12',
    'name': 'Bay Area to Tokyo',
    'enabled': True,
    'origin': ['SFO', 'OAK', 'SJC'],
    'destination': ['HND', 'NRT'],
    'cabin': 'business',
}
```

Contract for `get_scheduled_search(search_id)`:
- Returns the dict from `SCHEDULED_SEARCHES` whose `'id'` equals `search_id`.
- Returns `None` (does NOT raise) when no entry has that id.
- `enabled` must be the boolean `True`, not a truthy non-bool like `1`.

Behaviour that must NOT change:
- The module imports cleanly with plain CPython (`import src.scheduled_searches`)
  and defines exactly these two public names; no third-party dependencies.

## Must contain

- `SCHEDULED_SEARCHES`
- `'id': 'sched_ab12'`
- `'name': 'Bay Area to Tokyo'`
- `'enabled': True`
- `def get_scheduled_search(search_id):`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/scheduled_searches.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
