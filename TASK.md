# TASK: aw-transfer-partners-s8-programs-for-partners

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` exposes `PROGRAMS` and `list_partners()` but has no
way to answer "which programs can I transfer to partner X?" -- callers must
hand-roll the lookup. Observed: there is no callable in the module that maps a
set of partner ids back to program names; `grep -n "programs_for_partners"
src/transfer_partners.py` returns nothing, and importing it raises
`AttributeError`.

## Entry point

src/transfer_partners.py (module level, next to `list_partners`)

## Required change

In src/transfer_partners.py, given the top-level PROGRAMS dict (keyed by slug, each value {'name', 'transfers_to'}), add: def programs_for_partners(partner_ids: Iterable[str]) -> List[str]   # names of every PROGRAMS entry whose transfers_to intersects partner_ids -- union across all given partner_ids, SORTED, de-duplicated.

Contract details:
- `partner_ids` may be any iterable of strings (list, tuple, generator); it is
  consumed once and must not raise on an empty input.
- A program qualifies if ANY id in `partner_ids` appears in its `transfers_to`
  list (union / OR semantics -- NOT intersection).
- The result contains the program's `name` value (not its slug), de-duplicated,
  sorted ascending by name.
- Unknown partner ids simply match nothing; an empty or all-unknown input
  yields `[]`.

Behaviour that must NOT change:
- `PROGRAMS` keeps exactly its four entries (`citi_typ`, `capital_one`,
  `bilt`, `wells_fargo`) with the same names and `transfers_to` lists.
- `list_partners()` still returns all four partners sorted by name, each entry
  shaped `{"id": slug, "name": ..., "programs": [...]}`.

## Must contain

- `def programs_for_partners(partner_ids: Iterable[str]) -> List[str]:`
- `from collections.abc import Iterable`

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
This is not about adding bogus assertions for constants; it's about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
