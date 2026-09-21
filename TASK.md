# TASK: aw-transfer-partners-s6-wells-fargo-wells-fargo

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` defines a top-level `PROGRAMS` dict of credit-card
programs and their airline transfer partners. It currently holds exactly three
entries — `citi_typ`, `capital_one`, `bilt` — and has NO entry for Wells Fargo.
Verified by reading the file: `"wells_fargo"` does not appear anywhere in it, so
any lookup of `PROGRAMS["wells_fargo"]` raises `KeyError`.

## Entry point

src/transfer_partners.py:1 (the top-level `PROGRAMS` dict)

## Required change

In src/transfer_partners.py, add ANOTHER entry to the top-level PROGRAMS dict
(keyed by slug, shape {'name', 'transfers_to'} -- see the entries already in the
file for the pattern): PROGRAMS['wells_fargo'] = {'name': 'Wells Fargo Rewards',
'transfers_to': ['air_canada', 'flying_blue', 'virgin_atlantic']}.

The new entry must be added to the EXISTING dict; do not create a second dict,
do not rename or reorder existing keys, and keep the file valid Python.

Behaviour that must NOT change:
- `PROGRAMS["citi_typ"]` stays exactly `{"name": "Citi ThankYou Points", "transfers_to": ["flying_blue", "jetblue", "qantas", "qatar", "singapore", "turkish", "virgin_atlantic", "etihad", "emirates"]}`.
- `PROGRAMS["capital_one"]` stays exactly `{"name": "Capital One Miles", "transfers_to": ["air_canada", "emirates", "etihad", "finnair", "flying_blue", "qantas", "singapore", "turkish", "virgin_atlantic", "qatar"]}`.
- `PROGRAMS["bilt"]` stays exactly `{"name": "Bilt Rewards", "transfers_to": ["air_canada", "american", "emirates", "flying_blue", "turkish", "united", "virgin_atlantic", "alaska"]}`.
- After the change, `PROGRAMS` has exactly four keys: `citi_typ`, `capital_one`, `bilt`, `wells_fargo`.

## Must contain

- `"wells_fargo"`
- `Wells Fargo Rewards`
- `"transfers_to": ["air_canada", "flying_blue", "virgin_atlantic"]`

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
