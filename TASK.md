# TASK: aw-sched-routes-s1-from-airport-groups-impo

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` currently exposes only the transfer-partner
routes (`/api/scheduled/partners`, `/api/scheduled/partners/{code}`). There is
no way to list airport groups or expand a group into its airport codes through
the scheduled-routes API: `GET /api/scheduled/groups` and
`GET /api/scheduled/groups/{name}` do not exist (verified by reading the file --
only two routes are registered on the router). The data module
`src/airport_groups.py` with `list_groups()` / `expand_codes(name)` is also
absent from the tree.

## Entry point

src/webui/scheduled_routes.py:3 (the import block, where the new import lands)

## Required change

In src/webui/scheduled_routes.py: add `from ..airport_groups import list_groups, expand_codes`
and two routes on the existing router:

- `GET /api/scheduled/groups` -> 200 with body `{"groups": [{"name": <str>, "codes": [<str>, ...]}, ...]}` -- one entry per group from `list_groups()`, each expanded via `expand_codes(name)`.
- `GET /api/scheduled/groups/{name}` -> 200 with the group's name and its codes (case-insensitive match, consistent with the existing partner lookup); unknown group -> **404** (not a 500) with an error detail.

The data module `src/airport_groups.py` must provide `list_groups()` (group
names) and `expand_codes(name)` (codes for a known name, case-insensitive;
`None` for unknown). Create it if absent -- the fixture does NOT stub it, so it
must exist on disk.

Behaviour that must NOT change:
- `GET /api/scheduled/partners` still returns 200 with `{"partners": [...]}` from `list_partners()`.
- `GET /api/scheduled/partners/{code}` is still case-insensitive and still 404s (with an error detail) for unknown codes.

## Must contain

- in src/webui/scheduled_routes.py: `from ..airport_groups import list_groups, expand_codes`
- in src/webui/scheduled_routes.py: `/groups`
- in src/webui/scheduled_routes.py: `expand_codes`
- in src/airport_groups.py: `def list_groups():`
- in src/airport_groups.py: `def expand_codes(name):`

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
(You may also create the data module `src/airport_groups.py` that the import requires.)
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
