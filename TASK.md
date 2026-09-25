# TASK: aw-sched-routes-s20-program-choices-a-module

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` has no `PROGRAM_CHOICES`: the module exposes
no list of the seats.aero award programs for the UI to render as choices.
Verified by reading the file -- it defines routes and helpers but no such
module-level constant exists (`grep -n PROGRAM_CHOICES src/webui/scheduled_routes.py`
returns nothing), while the program catalogue already lives in
`config/programs.yml` (14 entries, each with `id` and `name`) and is loaded by
the module's existing `load_programs_config()` import.

## Entry point

src/webui/scheduled_routes.py:36 (module-level state block, next to `TEMPLATES = []`)

## Required change

Add a module-level constant `PROGRAM_CHOICES`: a list of dicts, each with
exactly the keys `'id'` and `'name'`, one entry per seats.aero program in
`config/programs.yml`. Derive it from the existing `load_programs_config()`
import already at the top of the file (do not hardcode a stale subset or
duplicate the YAML by hand). It must be defined at import time, module level.

Behaviour that must NOT change:
- Every existing route keeps working with identical status codes and bodies,
  e.g. `GET /api/scheduled/templates` still returns 200 with body
  `{"templates": []}` before any templates are registered.
- All existing imports, functions, classes, and the two routers (`router`,
  `api_router`) remain untouched.

## Must contain

- `PROGRAM_CHOICES = [`
- `"id"`
- `"name"`
- `load_programs_config()`

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
