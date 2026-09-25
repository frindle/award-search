# TASK: aw-sched-routes-s8-parse-cap

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` has no `parse_cap`: the module defines
`parse_csv` and `parse_date_ranges` but nothing to parse a cap value from form
input. Verified by reading the file: `grep -n "def parse_" src/webui/
scheduled_routes.py` shows only `parse_csv` and `parse_date_ranges`, and any
attempt to call `parse_cap` raises `AttributeError`.

## Entry point

src/webui/scheduled_routes.py: end of module (after `parse_date_ranges`) -- add the new function here.

## Required change

Add, in `src/webui/scheduled_routes.py`:

```python
def parse_cap(value: Optional[str]) -> Optional[float|int]:
    """Parse a cap value from form input."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        raise ValueError("invalid cap value") from None
    if number.is_integer():
        return int(number)
    return number
```

Contract (exact):
- `None`, `""`, or a whitespace-only string -> return `None` ("no cap"); must NOT raise.
- A whole-number string (`"5"`, `"0"`) -> returned as an **int** (`5`, `0`).
- Any other valid number (`"2.5"`) -> returned as a **float**.
- A non-numeric string (`"abc"`) -> raises **`ValueError`** (not 500, not another exception type).

Behaviour that must NOT change:
- All existing routes keep working: `GET /api/scheduled/templates`, `GET /api/scheduled/page/{name}`, `GET /api/scheduled/partners`, `GET /api/scheduled/partners/{code}` (404 with `{"error": "partner not found", ...}` for unknown codes), `POST /api/scheduled/run` (422 when program missing).
- `parse_csv(" a , b ,,c ")` still returns `["a", "b", "c"]`.
- `parse_date_ranges` pairing semantics are untouched.

## Must contain

- in src/webui/scheduled_routes.py: `def parse_cap(value: Optional[str]) -> Optional[float|int]:`
- in src/webui/scheduled_routes.py: `"invalid cap value"`
- in src/webui/scheduled_routes.py: `number.is_integer()`

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
