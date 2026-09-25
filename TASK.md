# TASK: aw-sched-routes-s9-get-scheduled-new-templa

## Confirmed defect (observed, not suspected)

`GET /api/scheduled/new` does not exist on the scheduled router. Reproduced by
mounting `src/webui/scheduled_routes.py:router` in a FastAPI TestClient and
requesting `/api/scheduled/new`: it returns 404 while every other route on the
router (`/templates`, `/partners`, ...) works. The edit form template
(`src/webui/templates/scheduled_edit.html`) already exists and expects a
`schedule` context plus `mode == 'new'`, but no route renders it yet, so there
is no "New scheduled search" entry point.

## Entry point

src/webui/scheduled_routes.py:15 (the `router = APIRouter(prefix="/api/scheduled")` the new route must hang off)

## Required change

Add a GET route for `/scheduled/new` to the existing router in
`src/webui/scheduled_routes.py`. Contract, exactly:

- Method/path: `GET /api/scheduled/new` (router prefix is already
  `/api/scheduled`, so decorate with `@router.get("/scheduled/new")`).
- It renders the template `'scheduled_edit.html'` through the module's
  `TEMPLATES.TemplateResponse(...)` idiom (the same one every other render in
  this file uses), NOT a JSON response.
- The context passed to the template must contain:
  - `"request": request` (a FastAPI `Request` parameter on the handler),
  - `"schedule"`: an EMPTY schedule produced by calling
    `normalize_schedule({})`. Add a module-level `normalize_schedule(raw)`
    helper that coerces raw input into the full shape the template reads:
    keys `id`, `name`, `origins`, `destinations`, `date_ranges`, `cabins`,
    `programs`, `transfer_partners`, `filters` (with sub-keys `airlines`,
    `max_points`, `max_taxes`), `interval_hours` (default 6),
    `notify_pushover` (default False), `enabled` (default True). For `{}` the
    result is exactly that empty shape.
  - `"mode"`: `'new'`.
- Do not change any existing route, helper, or import in this file.

Behaviour that must NOT change:
- `GET /api/scheduled/templates` still returns `{"templates": [...]}`.
- `GET /api/scheduled/partners` still returns `{"partners": list_partners()}`.
- `parse_csv`, `parse_date_ranges`, and `parse_cap` keep their exact behaviour.
- The module still imports cleanly (all existing relative imports intact).

## Must contain

- `@router.get("/scheduled/new")`
- `normalize_schedule({})`
- `"scheduled_edit.html"`
- `"mode": "new"`
- `def normalize_schedule(`

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
