# TASK: aw-sched-routes-s2-from-transfer-partners-i

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` is a one-line stub (docstring only): it defines no router and exposes no endpoints. Verified by mounting the module in a FastAPI app and requesting `GET /api/scheduled/partners` over HTTP -- the route does not exist, so the Web UI has no way to list the transfer partners that scheduled routes draw from (`src/transfer_partners.py`, which already exists with `list_partners()`).

## Entry point

src/webui/scheduled_routes.py:1 (the stub docstring; the whole module is missing)

## Required change

Implement an APIRouter in src/webui/scheduled_routes.py that serves the transfer partners, importing them from the existing data module:

- `from ..transfer_partners import list_partners` at module top level.
- A module-level router with prefix `/api/scheduled`.
- `GET /api/scheduled/partners` -> 200 with body exactly `{"partners": [...]}` where the list is `list_partners()` -- entries `{"code": ..., "name": ...}`, sorted by code (AA, DL, UA).
- `GET /api/scheduled/partners/{code}` -> 200 with that partner's object when the code matches case-insensitively (`ua` and `UA` both resolve to `{"code": "UA", "name": "United MileagePlus"}`).
- Unknown code -> **404** (not a 500) with body exactly `{"detail": {"error": "partner not found", "code": "<requested code>"}}`.

Behaviour that must NOT change:
- `src/transfer_partners.py` is read-only data; do not modify it or its ordering.
- No other module imports scheduled_routes, so nothing else may break -- but add no side effects (no I/O at import time, no background threads).

## Must contain

- `from ..transfer_partners import list_partners`
- `@router.get("/partners")`
- `def scheduled_partner(code: str)`
- `"partner not found"`

(The gate holds the reference impl against this list. If the verify goes green while one of these is absent from the changed files, the verify does not enforce the spec -- that is a benign verify, caught mechanically.)

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
