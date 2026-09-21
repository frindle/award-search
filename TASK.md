# TASK: aw-alert-filters-s2-normalize-airlines

## Confirmed defect (observed, not suspected)

`src/alert_filters.py` is a stub that only contains a docstring -- there is no
`normalize_airlines` at all. Any caller doing `from alert_filters import
normalize_airlines` fails with ImportError, and the alert-filter pipeline has
no way to coerce raw airline filter values (a single code string, a list of
codes, or nothing) into comparable uppercase IATA codes. Reproduced by reading
the file: it is one line, `"""Stub for src/alert_filters.py -- implement per TASK.md."""`.

## Entry point

src/alert_filters.py:1 (whole module -- the function does not exist yet and must be created here).

## Required change

In src/alert_filters.py: def normalize_airlines(value) -> List[str]   # list|str|None -> uppercase stripped IATA codes, [] if none.

Contract:
- `value` may be a `list` (or tuple) of airline code strings, a single string
  code, or `None`.
- Each accepted entry is `.strip()`ped then `.upper()`ed; empty/whitespace-only
  entries are dropped; order is preserved.
- Non-string entries inside a list/tuple are skipped silently.
- `None`, `""`, and whitespace-only strings return `[]` without raising.
- Any other input type (e.g. an int) raises `TypeError`.

Behaviour that must NOT change:
- Already-normalized input passes through unchanged: `["AA", "BA"]` -> `["AA", "BA"]`.
- The function is pure -- no I/O, no mutation of the input list, deterministic order.

## Must contain

- `def normalize_airlines(value) -> List[str]:`
- `from typing import List`
- `"normalize_airlines expects a list, str or None"`

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
