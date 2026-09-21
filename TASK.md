# TASK: aw-alert-filters-s5-describe-filters

## Confirmed defect (observed, not suspected)

`src/alert_filters.py` has no way to render a filter dict as a short human
summary. Reproduced: `python3 -c "import importlib.util; s=importlib.util.spec_from_file_location('t','src/alert_filters.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(hasattr(m,'describe_filters'))"`
prints `False` -- the module exposes `normalize_airlines`, `passes_filters` and
`filter_results` only, so callers building alert text have no summary to show.

## Entry point

src/alert_filters.py: end of file (after `filter_results`) -- add the new
function here; do not touch the existing functions.

## Required change

In src/alert_filters.py: def describe_filters(filters: Optional[Dict]) -> str   # short human summary e.g. 'airlines UA,NH'.

Contract:
- `describe_filters(None)` and `describe_filters({})` return exactly
  `"(no filters)"`.
- Otherwise each key is rendered as `<key> <codes>` where the codes are
  `normalize_airlines(value)` joined with `","`; a value whose normalized code
  list is empty renders just the bare key (no dangling space). Pairs are joined
  in dict insertion order with `"; "`.
- Examples: `{"airlines": ["ua", "NH"]}` -> `"airlines UA,NH"`;
  `{"airlines": []}` -> `"airlines"`;
  `{"airlines": ["UA"], "carriers": ["NH"]}` -> `"airlines UA; carriers NH"`.

Behaviour that must NOT change:
- `normalize_airlines` keeps its exact semantics (None -> [], str wrapped,
  list/tuple filtered to stripped uppercase non-empty strings, other types
  raise TypeError).
- `passes_filters` still returns True for None/empty filters and compares via
  normalized codes.
- `filter_results` still returns the matching results in order.

## Must contain

- `def describe_filters(filters: Optional[Dict]) -> str:`
- `"(no filters)"`

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
