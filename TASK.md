# TASK: aw-alert-filters-s1-filter-dict-airlines-ua

## Confirmed defect (observed, not suspected)

`src/alert_filters.py` is a one-line stub (`"""Stub for src/alert_filters.py -- implement per TASK.md."""`) with no filter definition at all. Verified by reading the file: importing it and looking for `get_filter()` raises `AttributeError`. The alert pipeline needs the canonical airline-alert filter dict, which does not exist yet.

## Entry point

src/alert_filters.py:1 (the whole module is a stub; add the filter here)

## Required change

In src/alert_filters.py: Filter dict: {'airlines': ['UA','NH'], 'max_points': 90000, 'max_taxes': 100.0}.

Concretely: define `get_filter()` in `src/alert_filters.py` that returns exactly this dict:
`{'airlines': ['UA', 'NH'], 'max_points': 90000, 'max_taxes': 100.0}` — airlines list in the order UA then NH, `max_points` the int 90000, `max_taxes` the float 100.0.

Behaviour that must NOT change:
- The module must import cleanly with no side effects (no I/O, no prints).
- Repeated calls to `get_filter()` return an equal dict every time.

## Must contain

- `def get_filter():`
- `'airlines': ['UA', 'NH']`
- `'max_points': 90000`
- `'max_taxes': 100.0`

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
