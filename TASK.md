# TASK: aw-transfer-partners-s1-amex-mr-american-express

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` is a one-line placeholder stub with no `PROGRAMS`
data at all. Reproduced by importing the module and observing that
`getattr(module, 'PROGRAMS', None)` is `None` -- there is no program registry
to query for transfer partners yet. This slice creates it, starting with the
American Express Membership Rewards entry.

## Entry point

src/transfer_partners.py:1 (the whole file is a stub; add the top-level dict here)

## Required change

In src/transfer_partners.py: add a top-level PROGRAMS dict keyed by program slug (this is the FIRST entry -- create the dict). PROGRAMS['amex_mr'] = {'name': 'American Express Membership Rewards', 'transfers_to': [...]}: aer_lingus is NOT a valid transfer partner for amex_mr (it must be absent from transfers_to).

Concretely:
- `PROGRAMS` is a module-level dict keyed by program slug.
- The `'amex_mr'` entry has key `'name'` with the exact value
  `'American Express Membership Rewards'`.
- The `'amex_mr'` entry has key `'transfers_to'` holding a non-empty list of
  valid American Express Membership Rewards transfer partner slugs (e.g. hotel
  and airline partners such as Hyatt, Marriott, Hilton, Delta SkyMiles).
- `'aer_lingus'` must NOT appear in `PROGRAMS['amex_mr']['transfers_to']`.

Behaviour that must NOT change:
- The module must import cleanly with no side effects (no I/O at import time).
- `PROGRAMS` stays a plain dict of dicts -- downstream slices will add more
  program slugs to the same dict, so do not wrap it in a class or rename it.

## Must contain

- `PROGRAMS`
- `'amex_mr'`
- `'American Express Membership Rewards'`
- `'transfers_to'`

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
