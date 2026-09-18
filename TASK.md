# TASK: aw-airport-groups-s1-is-group

## Confirmed defect (observed, not suspected)

`src/airport_groups.py` currently contains only a one-line docstring stub --
there is no `is_group` function at all. Verified by reading the file and
grepping `src/` for `is_group`: zero hits outside the stub's own docstring.
Any caller that needs to tell an airport *group* code (a city code fanning out
to several airports, e.g. NYC = JFK/LGA/EWR) apart from a single-airport code
has nothing to call; the module does not exist as specified.

## Entry point

`src/airport_groups.py:1` -- the whole file is new surface; add the function
and its group table here.

## Required change

In `src/airport_groups.py`, implement exactly this signature:

```python
def is_group(code: str) -> bool:
```

Contract (all of it, or the verify goes red):

- Returns `True` only when `code` names a known airport **group** code. The
  module must expose a mapping named `GROUPS` with at least `"NYC"` mapped to
  its member airports (`"JFK"`, `"LGA"`, `"EWR"`); LON and PAR are fine as
  additional groups, but NYC is required.
- Matching is **case-insensitive**: `is_group("nyc")` must be `True`.
- Matching ignores **surrounding whitespace**: `is_group("  NYC ")` must be
  `True`.
- Single-airport codes are NOT groups: `is_group("JFK")`, `is_group("LAX")`
  must be `False`. Unknown codes (`"ZZZ"`) and the empty string return
  `False`.
- Non-string input (`None`, numbers) returns `False` **without raising**.

Behaviour that must NOT change / must still hold:

- The module imports cleanly with no third-party dependencies (stdlib only).
- `is_group` is pure: no I/O, no mutation of globals, same result on every call.
- No other file in the repo is touched; nothing else in `src/` depends on this
  module yet, so there are no callers to break -- but do not add any.

## Must contain

- `def is_group(code: str) -> bool`
- `GROUPS`
- `"NYC"`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/airport_groups.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

After the job runs, a mutation check flips/deletes each line you changed and
asks the verify to catch it. A changed line whose every mutant survives --
because no test asserts it -- FAILS the gate even when the fix is correct, and
the review never runs. So do NOT emit an isolated, untested line:

- Every group in `GROUPS` should be one that a fixture case can reach; NYC is
  asserted directly, so keep its entry on a single line with its members.
- Prefer falling through to an implicit `return False` over a standalone
  `return None` the tests do not assert (the contract says bool, never None).
- If a line genuinely cannot be asserted and cannot be folded, it usually
  should not be a separate line at all -- restructure so it isn't.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
