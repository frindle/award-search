# TASK: aw-sched-routes-s6-parse-csv

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` has no way to turn a comma-separated string
(the form the scheduled-routes UI collects partner/program lists in) into a
clean list of values. Verified by reading the module: it exposes
`scheduled_templates`, `scheduled_page`, `scheduled_partners`,
`scheduled_partner`, and `scheduled_run`, but there is no `parse_csv` helper,
so any caller that needs to split such input has none to call.

## Entry point

src/webui/scheduled_routes.py (module level; add the function after the existing routes)

## Required change

Add a module-level function in `src/webui/scheduled_routes.py`:

```python
def parse_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]
```

Contract:
- `value` is an optional string (or `None`).
- Returns a list of the comma-separated parts, each stripped of surrounding
  whitespace, with empty/whitespace-only fields dropped.
- `None`, `""`, and strings that are only commas/spaces return `[]`.
- Order of the surviving parts is preserved.

Behaviour that must NOT change:
- All existing routes keep working exactly as before: `GET /api/scheduled/templates`,
  `GET /api/scheduled/page/{name}`, `GET /api/scheduled/partners`,
  `GET /api/scheduled/partners/{code}` (404 with the same error shape when not found),
  and `POST /api/scheduled/run` (422 with `{"error": "program is required", ...}` when program missing).
- Existing imports, `RunRequest`, `TEMPLATES`, `init()`, and the router prefix are untouched.

## Must contain

- `def parse_csv(value: Optional[str]) -> List[str]:`
- `from typing import List, Optional`

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
- Prefer falling through to the implicit `return None` over a standalone
  `return None` in an `except:` the tests do not assert.
- If a line genuinely cannot be asserted and cannot be folded, it usually
  should not be a separate line at all -- restructure so it isn't.
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
