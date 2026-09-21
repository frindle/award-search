# TASK: aw-sched-routes-s3-from-scheduled-runner-im

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` exposes the scheduled-partners read routes but has no way to trigger a schedule run from the Web UI. Reproduced by importing the module and listing its routes: only `GET /api/scheduled/partners` and `GET /api/scheduled/partners/{code}` exist, and there is no import of `run_schedule` anywhere in the file (`grep -n "scheduled_runner\|run_schedule" src/webui/scheduled_routes.py` returns nothing). The intent for this slice is to wire the runner into the router.

## Entry point

src/webui/scheduled_routes.py:1 (module top -- add the import) and end of file (add the new route after the existing `scheduled_partner` handler).

## Required change

In src/webui/scheduled_routes.py: from ..scheduled_runner import run_schedule.

Concretely, ADD to the existing module (do not remove or rewrite anything already there):
1. The import `from ..scheduled_runner import run_schedule`.
2. A Pydantic request model `RunRequest` with a single optional field `program: str | None = None`.
3. A route handler registered as `@router.post("/run")`, named `scheduled_run(body: RunRequest)`, that:
   - rejects a missing or empty `program` with HTTP 422 and body `{"detail": {"error": "program is required", "code": "invalid_program"}}` (raise `HTTPException(status_code=422, detail={...})`), WITHOUT calling `run_schedule`;
   - otherwise calls `run_schedule(program=body.program)` and returns its result verbatim.

Behaviour that must NOT change:
- `GET /api/scheduled/partners` still returns `{"partners": list_partners()}` with status 200.
- `GET /api/scheduled/partners/{code}` is still case-insensitive, returns the matching partner dict on a hit (200), and raises 404 with detail `{"error": "partner not found", "code": <code>}` on a miss.
- The router keeps its `/api/scheduled` prefix; existing imports (`APIRouter`, `HTTPException`, `list_partners`) remain.

## Must contain

- `from ..scheduled_runner import run_schedule`
- `@router.post("/run")`
- `def scheduled_run(body: RunRequest):`
- `"program is required"`

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
