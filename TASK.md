# TASK: aw-transfer-partners-s5-bilt-bilt-rewards-air-ca

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` defines a top-level `PROGRAMS` dict with exactly two
entries (`citi_typ`, `capital_one`). Verified by importing the module and
inspecting it: `"bilt" in PROGRAMS` is `False` and
`sorted(PROGRAMS)` == `['capital_one', 'citi_typ']`. The Bilt Rewards program
is missing from the transfer-partner data, so any lookup of its partners fails.

## Entry point

src/transfer_partners.py:1 (the top-level `PROGRAMS` dict literal)

## Required change

In src/transfer_partners.py, add ANOTHER entry to the top-level PROGRAMS dict
(keyed by slug, shape {'name', 'transfers_to'} -- see the citi_typ/capital_one
entries already in the file for the pattern):
PROGRAMS['bilt'] = {'name': 'Bilt Rewards', 'transfers_to': ['air_canada',
'american', 'emirates', 'flying_blue', 'turkish', 'united',
'virgin_atlantic', 'alaska']}.

Behaviour that must NOT change:
- `PROGRAMS["citi_typ"]` stays exactly `{"name": "Citi ThankYou Points",
  "transfers_to": ["flying_blue", "jetblue", "qantas", "qatar", "singapore",
  "turkish", "virgin_atlantic", "etihad", "emirates"]}`.
- `PROGRAMS["capital_one"]` stays exactly `{"name": "Capital One Miles",
  "transfers_to": ["air_canada", "emirates", "etihad", "finnair",
  "flying_blue", "qantas", "singapore", "turkish", "virgin_atlantic",
  "qatar"]}`.
- `PROGRAMS` contains exactly the three keys `bilt`, `capital_one`,
  `citi_typ` -- no stray or renamed keys, and the bilt entry must not inherit
  capital_one-only partners (etihad/finnair/qantas/singapore).

## Must contain

- `"bilt": {"name": "Bilt Rewards",`
- `"transfers_to": ["air_canada", "american", "emirates", "flying_blue", "turkish",`
- `"united", "virgin_atlantic", "alaska"]},`

## Scope

Only edit `src/transfer_partners.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The fixture asserts the bilt entry's name, its exact 8-partner list in order,
its length, and that no capital_one-only partner leaked into it; it also pins
both pre-existing entries byte-for-byte. Every line of a correct change is
therefore covered by at least one case -- do not add extra lines (comments,
reordering) beyond the entry itself.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
