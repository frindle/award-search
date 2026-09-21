# TASK: aw-transfer-partners-s4-capital-one-capital-one

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` currently defines `PROGRAMS` with only the s3 entry
(`citi_typ`). Reproduced by importing the module and checking its keys:
`list(PROGRAMS)` returns `['citi_typ']` -- there is no `capital_one` key, so any
consumer looking up Capital One Miles transfer partners gets a `KeyError`.

## Entry point

src/transfer_partners.py:1 (the top-level `PROGRAMS` dict)

## Required change

In src/transfer_partners.py, add ANOTHER entry to the top-level PROGRAMS dict
(keyed by slug, shape {'name', 'transfers_to'} -- see the citi_typ entry from s3
for the pattern already in the file):
PROGRAMS['capital_one'] = {'name': 'Capital One Miles', 'transfers_to': ['air_canada', 'emirates', 'etihad', 'finnair', 'flying_blue', 'qantas', 'singapore', 'turkish', 'virgin_atlantic', 'qatar']}.

Behaviour that must NOT change:
- The existing `citi_typ` entry stays byte-for-byte intact: name
  `'Citi ThankYou Points'` and its original 9-partner `transfers_to` list in the
  original order (`flying_blue, jetblue, qantas, qatar, singapore, turkish,
  virgin_atlantic, etihad, emirates`).
- `PROGRAMS` remains a plain top-level dict of slug -> {'name', 'transfers_to'};
  no new keys beyond the two slugs, and each entry keeps exactly the two keys
  `name` and `transfers_to`.

## Must contain

- `"capital_one"`
- `"Capital One Miles"`
- `"air_canada"`
- `"finnair"`
- `"virgin_atlantic"`
- `"Citi ThankYou Points"`

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
