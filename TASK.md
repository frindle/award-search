# TASK: aw-app-wiring-s5-app-include-router-sched

## Confirmed defect (observed, not suspected)

The scheduled-searches UI templates (`src/webui/templates/scheduled*.html`) and
the `from . import scheduled_routes` import in `src/webui/app.py` (landed by the
previous slice) are present, but the app never mounts the router: a request to
any `/scheduled*` path is not served by the app's route table. Verified by
inspecting `app.routes` after importing `src.webui.app`: no route registered on
`scheduled_routes.router` appears in the app, because `include_router` was never
called.

## Entry point

src/webui/app.py:104 (the `app = FastAPI(title="Award Search", lifespan=lifespan)` line)

## Required change

In src/webui/app.py: add `app.include_router(scheduled_routes.router)` immediately
after the `app = FastAPI(...)` construction, so every route defined on
`scheduled_routes.router` is mounted on the app.

Behaviour that must NOT change:
- The existing home route still works: `GET /` returns 200 and serves the Award
  Search page (title "Award Search" in the body).
- All other pre-existing routes (`/search`, `/results/{id}`, `/positioning`,
  `/balances`, `/settings`, `/alerts*`) keep their current behaviour.

## Must contain

- `app.include_router(scheduled_routes.router)`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

(A bare bullet checks the default target. To PIN a literal to a specific file --
useful when a fix spans a helper file and the route/wiring that calls it --
prefix the bullet with `in <path>:`, e.g.
`- in app/api/x/route.ts: ` followed by a backtick-quoted token. Then that
token is required in THAT file, not the target.)

## Scope

Only edit `src/webui/app.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
