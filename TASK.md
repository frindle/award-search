# TASK: aw-transfer-partners-s9-partners-for-program

## Confirmed defect (observed, not suspected)

`src/transfer_partners.py` exposes `list_partners()` and a stubbed
`programs_for_partners()`, but there is no way to look up the transfer partners
for a single program slug. Verified by reading the module: it defines only
`PROGRAMS`, `list_partners`, and `programs_for_partners`; calling
`partners_for_program("citi_typ")` raises `AttributeError`.

## Entry point

src/transfer_partners.py (module level, after `programs_for_partners`)

## Required change

In src/transfer_partners.py, given the top-level PROGRAMS dict (keyed by slug, each value {'name', 'transfers_to'}), add: def partners_for_program(program: str) -> List[str]   # PROGRAMS[program]['transfers_to'] sorted (program is a slug key; unknown slug returns []).

Behaviour that must NOT change:
- `PROGRAMS` keeps its four slugs and their exact `name`/`transfers_to` values.
- `list_partners()` still returns the 4 partner dicts, name-sorted
  (`bilt`, `capital_one`, `citi_typ`, `wells_fargo`).
- `programs_for_partners()` is left exactly as it currently stands (it is a
  stub owned by another slice; do not "fix" or delete it).

## Must contain

- `def partners_for_program(program: str) -> List[str]:`
- `PROGRAMS.get(program)`
- `return []`
- `sorted(info['transfers_to'])`

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
