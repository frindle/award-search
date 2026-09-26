# TASK: aw-transfer-partners-s10-restore-amex-mr-chase-ur

## Confirmed defect (observed, not suspected)

`PROGRAMS` in `src/transfer_partners.py` currently has only four keys —
`citi_typ`, `capital_one`, `bilt`, `wells_fargo`. The `amex_mr` and `chase_ur`
entries that slices s1 and s2 added are gone: slice s3's change REPLACED the
whole dict instead of adding a key, silently deleting them. Verified by reading
the current file (no `amex_mr`/`chase_ur` keys) and by calling
`target.partners_for_program("amex_mr")`, which returns `[]`.

## Entry point

src/transfer_partners.py:1 — the module-level `PROGRAMS` dict.

## Required change

In src/transfer_partners.py: s3 ('citi_typ...') REPLACED the whole PROGRAMS dict instead of adding a key to it, silently deleting the amex_mr and chase_ur entries s1 and s2 had already added. Restore both entries into the EXISTING PROGRAMS dict -- add these two keys, do not remove or alter citi_typ, capital_one, bilt, or wells_fargo, and do not replace the dict wholesale (that is the exact mistake being corrected here). PROGRAMS['amex_mr'] = {'name': 'American Express Membership Rewards', 'transfers_to': ['hyatt_worldwide', 'marriott_bonvoy', 'hilton_honors', 'delta_sky_miles']}. PROGRAMS['chase_ur'] = {'name': 'Chase Ultimate Rewards', 'transfers_to': ['air_canada', 'american', 'united', 'southwest', 'jetblue', 'british_airways', 'singapore', 'virgin_atlantic']} -- these are the exact values from the original s1/s2 commits (aer_lingus is NOT a valid amex_mr partner).

Behaviour that must NOT change:
- `PROGRAMS` still contains all four pre-existing entries with their exact
  current values (`citi_typ`, `capital_one`, `bilt`, `wells_fargo`).
- `list_partners()` keeps returning the name-sorted list of
  `{id, name, programs}` dicts — now six entries.
- `programs_for_partners(partner_ids)` still returns the sorted names of every
  program whose `transfers_to` intersects the given ids (e.g.
  `["virgin_atlantic"]` must include both restored programs).
- `partners_for_program(program)` still returns the sorted partner list for a
  known program and `[]` for an unknown one, without raising.

## Must contain

- `"American Express Membership Rewards"`
- `"hyatt_worldwide"`
- `"marriott_bonvoy"`
- `"hilton_honors"`
- `"delta_sky_miles"`
- `"Chase Ultimate Rewards"`
- `"southwest"`
- `"british_airways"`

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
