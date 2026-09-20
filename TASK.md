# TASK: aw-airport-groups-s2-expand-codes

## Confirmed defect (observed, not suspected)

`src/airport_groups.py` currently contains only a docstring and defines no
functions at all. Verified by running
`python3 -c "import ast; print([n.name for n in ast.walk(ast.parse(open('src/airport_groups.py').read())) if isinstance(n, ast.FunctionDef)])"`
from the worktree root: it prints `[]`, so any caller of
`expand_codes(...)` fails with `ImportError` / `AttributeError`. The module is
a stub; the function does not exist yet.

## Entry point

src/airport_groups.py:1 (the whole module -- nothing to replace, only to add)

## Required change

In src/airport_groups.py: def expand_codes(codes: Iterable[str]) -> List[str]   # order-preserving dedupe, uppercase output.

Behaviour that must NOT change:
- The function accepts ANY iterable of strings (list, tuple, generator), not
  just lists -- it must not call `len()` or index into the input.
- It returns a plain Python `list` of `str`, never a set/tuple/dict.
- Empty input yields an empty list and does not raise.
- The module stays importable with no side effects (no I/O, no prints).

## Must contain

- `def expand_codes(codes: Iterable[str]) -> List[str]:`
- `from typing import Iterable, List`
- `.upper()`

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
