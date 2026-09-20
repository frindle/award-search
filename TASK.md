# TASK: aw-airport-groups-s3-group-label

## Confirmed defect (observed, not suspected)

`src/airport_groups.py` currently exposes only `expand_codes`; there is no way to
resolve an airport code to its human-readable group label. Reproduced by importing
the module and calling `group_label("JFK")`: it raises `AttributeError: module
'target' has no attribute 'group_label'`. The file parses fine, so this is a
missing function, not a syntax problem.

## Entry point

src/airport_groups.py (module level -- add the new constant and function alongside
the existing `expand_codes`)

## Required change

In src/airport_groups.py: def group_label(code: str) -> str                     # AIRPORT_GROUPS[code]['name'] or the code itself.

Concretely, in `src/airport_groups.py`:

1. Define a module-level mapping `AIRPORT_GROUPS` -- a dict from airport code
   (e.g. `"JFK"`) to an entry dict with at least a `"name"` key holding the
   human-readable label (e.g. `{"name": "New York (JFK)"}`). It must contain at
   least one real group; do not ship it empty.
2. Add:

   ```python
   def group_label(code: str) -> str:
       return AIRPORT_GROUPS[code]['name'] if code in AIRPORT_GROUPS else code
   ```

   i.e. `AIRPORT_GROUPS[code]['name']` when the code is a known group, otherwise
   the code itself. Unknown codes must NOT raise -- they fall through to the
   input unchanged (so `group_label("") == ""`).

Behaviour that must NOT change:
- `expand_codes(codes)` keeps its exact current behaviour: uppercases each code,
  dedupes case-insensitively preserving first-seen order
  (`expand_codes(["jfk", "JFK", "lhr"]) == ["JFK", "LHR"]`).
- The module docstring and existing imports stay intact.

## Must contain

- `def group_label(code: str) -> str`
- `AIRPORT_GROUPS[code]['name']`
- `else code`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/airport_groups.py`; in this refine round `test_fixture.py` may
also be touched (its one dirty line, `CASES -= [` -> `CASES += [`, is a
permitted fix). Do not edit `verify.sh`. `TASK.md` changes are limited to
keeping the scope line and the Must-contain list accurate.

## Keep every changed line exercised (relevance)

After the job runs, a mutation check flips/deletes each line you changed and
asks the verify to catch it. A changed line whose every mutant survives --
because no test asserts it -- FAILS the gate even when the fix is correct, and
the review never runs. So do NOT emit an isolated, untested line:
- Fold an unavoidable constant onto a line the test already exercises. Put a
  `timeout=` / a `daemon=True` flag / a small tuning number on the SAME line as a
  header dict, URL, or argument the fixture checks -- never on its own line.
- Prefer falling through to an implicit `return None` over a standalone
  `return None` in an `except:` the tests do not assert.
- If a line genuinely cannot be asserted and cannot be folded, it usually
  should not be a separate line at all -- restructure so it isn't.
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
