# TASK: scheduled_routes

## Confirmed defect (observed, not suspected)

`src/webui/app.py:34` imports "scheduled_routes", but `src/webui/scheduled_routes.py` does not exist -> ImportError on app import. Reproduced by attempting to import the webui package; the module file is absent while the templates it must back (`scheduled.html`, `scheduled_edit.html`, `scheduled_result.html`) already exist in `src/webui/templates/`.

## Entry point

`src/webui/scheduled_routes.py:1` (the whole module is missing; create it).

## Required change

Create `src/webui/scheduled_routes.py`: an `APIRouter` plus `init(templates)` that stores the Jinja2Templates instance, backing the existing scheduled.html / scheduled_edit.html / scheduled_result.html templates. The router must serve:

- `GET /scheduled` -> renders `scheduled.html` (list of schedules; 200).
- `POST /scheduled/save` -> validates input; invalid airport codes or malformed date ranges re-render the edit form with an error message (NOT a 500); valid payloads persist and redirect to `/scheduled?saved=1`.
- Unknown schedule ids on edit/toggle/delete/run must not 500 -- redirect to the list with an error marker.

Behaviour that must NOT change:
- Existing app routes (`/`, `/search`, `/alerts`, ...) keep working; the module imports cleanly and exposes `router` and `init`.
- Invalid input never produces a 500 from these routes.

## Must contain

- `router = APIRouter()`
- `def init(templates: Jinja2Templates) -> None:`
- `@router.get("/scheduled"`
- `scheduled.html`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
