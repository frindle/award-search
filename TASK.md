# TASK: aw-transfer-partners-s7-list-partners

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` currently defines only the `PROGRAMS` dict and exposes
no way to enumerate partners. Reproduced by importing the module and calling
`list_partners()`: it raises `AttributeError: module 'target' has no attribute
'list_partners'`. The data (slug -> {'name', 'transfers_to'}) is present; only
the accessor function is missing.

## Entry point

src/transfer_partners.py:1 (module top level, after the existing `PROGRAMS` dict)

## Required change

In src/transfer_partners.py, given the top-level PROGRAMS dict (keyed by slug, each value {'name', 'transfers_to'}) built by the earlier slices, add: def list_partners() -> List[Dict]   # one dict per PROGRAMS entry: {'id': slug, 'name': PROGRAMS[slug]['name'], 'programs': PROGRAMS[slug]['transfers_to']}, sorted by name.

Behaviour that must NOT change:
- The existing `PROGRAMS` dict stays byte-for-byte intact: same four slugs
  (`citi_typ`, `capital_one`, `bilt`, `wells_fargo`), same `name` values, same
  `transfers_to` lists in the same order.
- Each returned entry's `programs` list preserves the exact order of that slug's
  `transfers_to` (e.g. for `citi_typ`, `jetblue` is still second).

## Must contain

- `def list_partners() -> List[Dict]:`
- `"id": slug`
- `sorted(partners, key=lambda partner: partner["name"])`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/transfer_partners.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
