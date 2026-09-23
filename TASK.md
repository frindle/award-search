# TASK: aw-sched-runner-s19-run-schedule

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` exposes `search_schedule()` and `notify_hit()` but no
entry point that runs a whole schedule: there is nothing to call with one
schedule dict that searches AND notifies. Verified by import:
`python3 -c "import ast; ..."` shows the module defines `search_schedule`,
`notify_hit`, `select_results`, `run_cycle` — and `grep run_schedule src/`
returns no definition, only the missing piece callers need.

## Entry point

src/scheduled_runner.py: end of file (after `notify_hit`)

## Required change

In src/scheduled_runner.py add:

    def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:

Contract:
- Search using the existing `search_schedule(sched, client=client)` helper and
  return its result list unchanged (same dicts, same order). Do not filter or
  mutate results.
- When `notify` is True, call the existing `notify_hit(sched, r)` once for each
  returned result. A notification failure must NOT drop or corrupt any result —
  wrap per-result notification so one bad push cannot lose data.
- When `notify` is False, no notification may be sent at all; results are still
  returned.
- If the client's search itself raises (e.g. API down), let that exception
  propagate — do not swallow it into an empty list.

Behaviour that must NOT change:
- `select_results`, `run_cycle`, `search_seats_aero`, `get_trip`,
  `_result_key`, `search_schedule`, and `notify_hit` keep their exact current
  behaviour; all existing imports stay as they are.

## Must contain

- `def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:`
- `search_schedule(`
- `notify_hit(`

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
