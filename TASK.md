# TASK: aw-airport-groups-s4-list-groups

## Confirmed defect (observed, not suspected)

`src/airport_groups.py` exposes `AIRPORT_GROUPS`, `expand_codes()` and
`group_label()`, but there is no way to enumerate the registry as structured
data. Verified by importing the module: `hasattr(module, "list_groups")` is
`False`, so any caller that wants `[{'code':..,'name':..,'airports':[..]}]`
must hand-roll it from the dict.

## Entry point

src/airport_groups.py (module level -- add a new function next to `group_label`)

## Required change

In src/airport_groups.py: def list_groups() -> List[Dict]                       # [{'code':..,'name':..,'airports':[..]}] sorted by code.

Contract, exactly:
- Returns a `List[Dict]` with one entry per key of the module-level
  `AIRPORT_GROUPS` registry.
- Each entry is a dict with EXACTLY three keys: `"code"` (the group's IATA
  code), `"name"` (the value of that group's `"name"` field in
  `AIRPORT_GROUPS`), and `"airports"` (a list containing the single code).
- The list is sorted by `"code"` ascending. Sorting must come from the codes,
  not from dict insertion order -- a group added last with an alphabetically
  first code must still appear first in the result.
- `list_groups()` must be pure: it must not mutate `AIRPORT_GROUPS` or any of
  its nested dicts.

Behaviour that must NOT change:
- `expand_codes(["jfk", "LHR"])` still returns `["JFK", "LHR"]` (uppercases,
  dedupes, preserves first-seen order).
- `group_label("JFK")` still returns `"New York (JFK)"`, and an unknown code
  is returned unchanged.
- The existing `AIRPORT_GROUPS` entries (`"JFK"` -> `"New York (JFK)"`,
  `"LHR"` -> `"London (LHR)"`) are untouched.

## Must contain

- `def list_groups() -> List[Dict]:`
- `sorted(AIRPORT_GROUPS)`
- `"airports"`

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
