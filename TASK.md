# TASK: aw-transfer-partners-s3-citi-typ-citi-thankyou-p

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` is a stub containing only the docstring
`"""Stub for src/transfer_partners.py -- implement per TASK.md."""`. There is no
data and no lookup function: any consumer asking "which programs transfer into
Citi ThankYou Points?" has nothing to call. Verified by reading the file — it
is 1 line long with no definitions.

## Entry point

src/transfer_partners.py:1 (the whole module must be implemented)

## Required change

Implement `src/transfer_partners.py` as a transfer-partner lookup for Citi
ThankYou Points, exactly this contract:

- A module-level mapping `TRANSFER_POINTS = { ... }` whose keys are the nine
  partner program slugs and whose values are all the string
  `"Citi ThankYou Points"`:
  - `flying_blue`, `jetblue`, `qantas`, `qatar`, `singapore`, `turkish`,
    `virgin_atlantic`, `etihad`, `emirates`
- A function `def get_transfer_points(program):` that returns the mapped value
  for a known program and `None` (never an exception) for anything else —
  unknown slugs, `""`, `None`, or wrong-case input.

Behaviour that must NOT change / must hold:
- The mapping contains EXACTLY those nine keys — no extra programs, none missing.
- Every value is exactly `"Citi ThankYou Points"` (case and spacing matter).
- Lookups are case-sensitive: `"Flying Blue"` does not resolve.
- `get_transfer_points` never raises for degenerate input (`None`, `""`,
  unknown slug) — it returns `None`.

## Must contain

- `TRANSFER_POINTS = {`
- `def get_transfer_points(program):`
- `"Citi ThankYou Points"`
- `"flying_blue": "Citi ThankYou Points",`
- `"jetblue": "Citi ThankYou Points",`
- `"qantas": "Citi ThankYou Points",`
- `"qatar": "Citi ThankYou Points",`
- `"singapore": "Citi ThankYou Points",`
- `"turkish": "Citi ThankYou Points",`
- `"virgin_atlantic": "Citi ThankYou Points",`
- `"etihad": "Citi ThankYou Points",`
- `"emirates": "Citi ThankYou Points",`

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
