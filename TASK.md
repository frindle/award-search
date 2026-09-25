# TASK: aw-sched-routes-s18-get-api-transfer-partner

## Confirmed defect (observed, not suspected)

`GET /api/transfer-partners` is not served at all. Reproduced by mounting the
existing `api_router` from `src/webui/scheduled_routes.py` in a FastAPI app and
hitting it with TestClient: the route returns 404 (no matching path), while the
sibling slice's `GET /api/airport-groups` works. The module already imports
`list_partners` (`from ..transfer_partners import list_partners`) but never
exposes it on a top-level `/api` route -- only under the `/api/scheduled`
prefix as `/partners`.

## Entry point

src/webui/scheduled_routes.py:26 (the `@api_router.get("/airport-groups")` block, where the new sibling route belongs)

## Required change

Add one GET route to the existing top-level `api_router` (prefix `/api`) in
`src/webui/scheduled_routes.py`:

- `GET /api/transfer-partners` -> returns `list_partners()` directly. The
  response body must be exactly what `list_partners()` returns -- a bare JSON
  array of partner objects, NOT wrapped in an object like `{"partners": [...]}`
  (that wrapper shape belongs to the existing `/api/scheduled/partners` route).

Behaviour that must NOT change:
- `GET /api/airport-groups` still returns `list_groups()` with status 200.
- Every other route on `router` (`/api/scheduled/*`) and `api_router` keeps its
  current behaviour; no existing import, function, or class is removed or
  altered.

## Must contain

- `@api_router.get("/transfer-partners")`
- `def transfer_partners_list():`
- `return list_partners()`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The fixture drives the new route through TestClient and asserts both the 200
status and the exact response body, so all three lines of the new handler are
exercised; no untested standalone lines should be introduced.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
