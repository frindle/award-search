# TASK: aw-sched-routes-s17-get-api-airport-groups-l

## Confirmed defect (observed, not suspected)

The Web UI has no way to fetch the airport code groups. `src/airport_groups.py`
already provides `list_groups()` (a sorted list of `{code, name, airports}`
dicts), but nothing in `src/webui/scheduled_routes.py` exposes it over HTTP: a
request to `GET /api/airport-groups` against the app's routers returns 404.

## Entry point

src/webui/scheduled_routes.py -- the module defines `router = APIRouter(prefix="/api/scheduled")`; the new endpoint must be added here, on an `/api`-prefixed router (the existing router's prefix cannot serve this path).

## Required change

In src/webui/scheduled_routes.py: add a GET route at exactly
`/api/airport-groups` that returns `list_groups()` from `..airport_groups`
verbatim as the JSON response body. Import it alongside the existing relative
imports; define a new router with prefix `/api` (the pre-existing `router` is
prefixed `/api/scheduled`, so mounting on it would produce the wrong path);
register the route on that new router and return the list directly -- no
wrapper object, no extra keys.

Behaviour that must NOT change:
- Every existing route in the module keeps working unchanged, e.g.
  `GET /api/scheduled/templates` still returns `{"templates": []}` with status 200.
- The response body of `/api/airport-groups` is exactly what
  `src.airport_groups.list_groups()` returns: a JSON array (not an object),
  each entry a dict with keys `code`, `name`, `airports`, entries sorted by
  code, e.g. the JFK entry is `{"code": "JFK", "name": "New York (JFK)", "airports": ["JFK"]}`.

## Must contain

- `from ..airport_groups import list_groups`
- `api_router = APIRouter(prefix="/api")`
- `@api_router.get("/airport-groups")`
- `def airport_groups_list():`
- `return list_groups()`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The fixture drives the real router through `fastapi.testclient.TestClient`:
it asserts status 200 AND the exact body from `/api/airport-groups`, checks
the entry shape/order, and pins a regression case on an existing route -- so
every line of the change is exercised. Do not add untested helper lines.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
