# TASK: aw-sched-runner-s8-module-constants-default

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` has no module-level tuning constants. Observed by
reading the file as it exists in this worktree: the module defines only
imports plus `select_results`, `run_cycle`, `search_seats_aero`, `_TripView`,
and `get_trip`. A grep for `DEFAULT_POLL_MINUTES`, `MAX_LEGS_PER_RUN`, and
`NOTIFIED_KEYS_CAP` finds nothing, so any later slice that needs the runner's
default poll interval, per-run leg cap, or notified-keys cap has no single
source of truth to import.

## Entry point

src/scheduled_runner.py:1 (top of module, after the import block)

## Required change

Add exactly three module-level constants near the top of `src/scheduled_runner.py`
(after the existing imports, before `select_results`):

- `DEFAULT_POLL_MINUTES = 15.0` -- a float; this is minutes, not seconds
- `MAX_LEGS_PER_RUN = 60` -- an int cap on legs processed per run
- `NOTIFIED_KEYS_CAP = 500` -- an int cap on stored notified keys

Do NOT change any existing import, function, or class. Do NOT add behaviour,
docstrings beyond what is needed, or other constants. The module must still
parse and all pre-existing names (`select_results`, `run_cycle`,
`search_seats_aero`, `_TripView`, `get_trip`) must remain defined exactly as
before.

Behaviour that must NOT change:
- `select_results(alert, results)` still filters via `passes_filters` and skips
  entries whose filter check raises.
- `run_cycle(alerts, search_fn)` still returns `{alert_id: kept}` for alerts
  with non-empty kept results and swallows per-alert exceptions.
- `search_seats_aero(...)` still delegates to `SeatsAeroClient().search(...)`.
- `get_trip(availability_id)` still returns a `_TripView` (taxes in major
  units) or `None` on any failure.

## Must contain

- `DEFAULT_POLL_MINUTES = 15.0`
- `MAX_LEGS_PER_RUN = 60`
- `NOTIFIED_KEYS_CAP = 500`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/scheduled_runner.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

The fixture asserts each constant's exact value AND its type, so all three new
lines are individually covered: a mutant that drops the `.0`, changes any
number, or reorders nothing-but-renames fails at least one case. Do not add
any other lines -- an untested extra line would fail the mutation check.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
