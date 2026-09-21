# TASK: aw-transfer-partners-s2-use-air-canada-american

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` defines `PROGRAMS` with only the `amex_mr` entry;
there is no `chase_ur` key at all. Reproduced by importing the module and
checking `'chase_ur' in PROGRAMS` -> False. The registry therefore cannot serve
Chase Ultimate Rewards transfer partners (air_canada, american) that later
slices depend on.

## Entry point

src/transfer_partners.py:3 (the `PROGRAMS = {` dict literal -- the new entry is added inside it)

## Required change

In src/transfer_partners.py: the top-level PROGRAMS dict already exists (added by s1, shape {'name': str, 'transfers_to': [partner_slug, ...]}). Add ANOTHER entry: PROGRAMS['chase_ur'] = {'name': 'Chase Ultimate Rewards', 'transfers_to': [...]}. The transfers_to list MUST include the partner slugs air_canada and american (exactly these spellings, not aliases like 'aeroplan' or 'aa'), plus other plausible Chase UR airline transfer partners, e.g. united, southwest, jetblue, british_airways, singapore, virgin_atlantic. Do not touch any other PROGRAMS entry.

Behaviour that must NOT change:
- The existing `amex_mr` entry stays byte-for-byte intact (name and its four
  transfer partners).
- `PROGRAMS` remains a plain top-level dict of `{slug: {'name': str, 'transfers_to': [str, ...]}}`.

## Must contain

- in src/transfer_partners.py: `'chase_ur'`
- in src/transfer_partners.py: `'Chase Ultimate Rewards'`
- in src/transfer_partners.py: `'air_canada'`
- in src/transfer_partners.py: `'american'`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

(A bare bullet checks the default target. To PIN a literal to a specific file --
useful when a fix spans a helper file and the route/wiring that calls it --
prefix the bullet with `in <path>:`, e.g.
`- in app/api/x/route.ts: ` followed by a backtick-quoted token. Then that
token is required in THAT file, not the target.)

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
