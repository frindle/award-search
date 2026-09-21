# TASK: aw-app-wiring-v2

## Confirmed defect (observed, not suspected)

The scheduled-award-search feature exists as a separate module (`src/webui/scheduled_routes.py`, landing from the sibling `aw-sched-routes` slice; its templates already exist in this worktree under `src/webui/templates/`) but is NOT wired into the FastAPI app: `grep -n "sched" src/webui/app.py` shows no import of `scheduled_routes`, no router mount, and the `lifespan` handler starts only the existing `alert_scheduler` task. Observed via `TestClient`: no `/api/scheduled*` route exists on `app.routes`.

## Entry point

src/webui/app.py:105 (the `lifespan` asynccontextmanager) and src/webui/app.py:118 (`app = FastAPI(...)`), plus the import block at lines 27-34.

## Required change

Wire the new scheduled-award-search feature into the existing FastAPI app in src/webui/app.py: mount the scheduled_routes APIRouter, hand it this app's Jinja2Templates instance, and start the scheduled-search background loop alongside the existing alert_scheduler. Nothing already in the file may change behaviour.

Concretely, add exactly these three things (in any order that keeps the module valid):
1. After `from ..settings import load_settings, save_settings`, import the feature: `from ..webui.scheduled_routes import create_router, scheduled_search_loop`.
2. Immediately after this app's `templates = Jinja2Templates(...)` line, build and mount the router with THIS app's templates instance: `scheduled_routes = create_router(templates)` then `app.include_router(scheduled_routes)`.
3. In `lifespan`, right after the existing `task = asyncio.create_task(alert_scheduler(_alert_search, _alert_notify, interval))` line, start the background loop: `scheduled_task = asyncio.create_task(scheduled_search_loop())`, and cancel it on shutdown with `scheduled_task.cancel()` next to the existing `task.cancel()`.

Behaviour that must NOT change:
- The existing `alert_scheduler` task still starts in `lifespan` and is cancelled on shutdown.
- All pre-existing routes (`/`, `/search`, `/results/{id}`, `/positioning*`, `/balances`, `/settings*`, `/alerts*`) keep their paths, methods, status codes and response shapes (e.g. `GET /api/alerts/<unknown>/results` still returns 404).
- The app's own `Jinja2Templates` instance (`templates`) is the one handed to `create_router`.

## Must contain

- `from ..webui.scheduled_routes import create_router, scheduled_search_loop`
- `scheduled_routes = create_router(templates)`
- `app.include_router(scheduled_routes)`
- `scheduled_task = asyncio.create_task(scheduled_search_loop())`
- `scheduled_task.cancel()`

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
