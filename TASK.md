# TASK: aw-sched-routes-s4-init

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` has no way to load the award-program templates
the UI needs: there is no module-level `TEMPLATES`, no `init(templates)` setter,
and no route exposing them. Verified by reading the file as it exists now -- it
ends at the POST /run route and defines nothing template-related (a grep for
`TEMPLATES` across src/ finds no definition anywhere).

## Entry point

src/webui/scheduled_routes.py:34 (end of file, after `scheduled_run`)

## Required change

In src/webui/scheduled_routes.py: def init(templates) -> None:   # sets the module-level TEMPLATES.

Concretely, append to the existing module -- preserving every import and route
already there:
- a module-level `TEMPLATES = []`
- `def init(templates):` that assigns its argument to the module-level
  `TEMPLATES` (via `global TEMPLATES`) and returns None; it REPLACES the list,
  never appends to it
- a GET `/api/scheduled/templates` route returning `{"templates": TEMPLATES}`

Behaviour that must NOT change:
- GET /api/scheduled/partners still returns {"partners": list_partners()}
- GET /api/scheduled/partners/{code} stays case-insensitive and 404s unknown codes with detail {"error": "partner not found", ...}
- POST /api/scheduled/run keeps its RunRequest body, its 422 {"error": "program is required", "code": "invalid_program"} shape for a missing/empty program, and still calls run_schedule(program=...)

## Must contain

- `TEMPLATES = []`
- `def init(templates):`
- `global TEMPLATES`
- `@router.get("/templates")`
- `"templates": TEMPLATES`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

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
