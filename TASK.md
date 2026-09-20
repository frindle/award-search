# TASK: aw-sched-runner-s7-seatsaeroclient-get-trip

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` has no way to fetch a single trip for an
availability id. Verified by reading the file and running
`python3 -c "import ast; m=ast.parse(open('src/scheduled_runner.py').read()); print([n.name for n in m.body if isinstance(n, ast.FunctionDef)])"`:
the module exposes `select_results`, `run_cycle`, `search_seats_aero` only --
no `get_trip`. Meanwhile `SeatsAeroClient.get_trip(availability_id)` already
exists in `src/seats_aero.py` (returns a `SeatsAeroTrip | None`) and the client
is already imported at the top of this file, so the runner simply lacks the
wrapper.

## Entry point

src/scheduled_runner.py:31 (end of module; add after `search_seats_aero`)

## Required change

In src/scheduled_runner.py: SeatsAeroClient.get_trip(availability_id) -> SeatsAeroTrip|None with .total_taxes(float), .taxes_currency, .carriers(List[str]).

Concretely: add a module-level function `get_trip(availability_id)` that
constructs the already-imported `SeatsAeroClient`, calls its
`get_trip(availability_id)`, and returns the trip (or None when there is no
trip). The returned object must expose `.total_taxes` as a **float** of
dollars (the client reports cents, so divide by 100), plus `.taxes_currency`
and `.carriers` passed through from the client. If the client raises (e.g.
missing API key) or returns None, `get_trip` must return None -- never raise.

Behaviour that must NOT change:
- The existing imports at the top of the file stay exactly as they are.
- `select_results(alert, results)` still filters via `passes_filters`, skipping
  entries whose filter check raises.
- `run_cycle(alerts, search_fn)` still returns `{alert_id: kept}` for alerts
  with surviving results and skips alerts whose search raises.
- `search_seats_aero(origin, destination, start_date, end_date, cabins, programs)`
  still delegates to `SeatsAeroClient().search(...)`.

## Must contain

- `def get_trip(availability_id):`
- `client.get_trip(availability_id)`
- `float(`
- `/ 100.0`
- `return None`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/scheduled_runner.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
