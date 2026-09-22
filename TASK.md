# TASK: aw-app-wiring-s4-scheduled-routes-init-te

## Confirmed defect (observed, not suspected)

`src/webui/app.py` imports the scheduled-searches routes module
(`from . import scheduled_routes`, line 34) but never calls its `init()`.
The templates for those routes (`scheduled.html`, `scheduled_edit.html`,
`scheduled_result.html`) exist and link to `/scheduled*` URLs, yet no route is
ever registered because the routes module only registers itself inside
`scheduled_routes.init(templates)` -- which nothing invokes. Verified by grep:
the only occurrence of `scheduled_routes` in app.py is the import line; there
is no call site anywhere in the file.

## Entry point

src/webui/app.py:120 (right after `templates = Jinja2Templates(...)` at line 120)

## Required change

In src/webui/app.py: `scheduled_routes` is already imported (`from . import scheduled_routes`) but nothing calls `scheduled_routes.init(templates)` yet -- add that call once, right after `templates = Jinja2Templates(...)` is constructed (so the routes module receives the same Jinja2Templates instance the rest of app.py uses).

Behaviour that must NOT change:
- The existing `/` home route still renders 200 with the "Award Search" page.
- Unknown search ids on `GET /results/{search_id}` still return 404 with detail `"Search not found"`.
- No other routes, imports, or module-level state are altered; the call is added exactly once and does not change any existing line's behaviour.

## Must contain

- `scheduled_routes.init(templates)`

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
  should not be a separate line at all -- restructure so that it isn't.
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
