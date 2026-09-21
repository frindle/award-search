# TASK: aw-sched-runner-s11-client-none-seatsaerocli

## Confirmed defect (observed, not suspected)

`search_schedule(sched)` called with the default `client=None` raises
`AttributeError: 'NoneType' object has no attribute 'search'`. Reproduced by
importing `src/scheduled_runner.py` and calling `search_schedule({"origin": "JFK"})`:
the body calls `client.search(...)` directly, so a caller that omits `client`
crashes instead of getting a real client. Sibling functions in the same module
(`search_seats_aero`, `get_trip`) already construct `SeatsAeroClient()` when no
client is available; `search_schedule` does not.

## Entry point

src/scheduled_runner.py:73 (`def search_schedule(sched: Dict, client=None, today=None)`)

## Required change

In src/scheduled_runner.py, fix search_schedule(sched, client=None, today=None): currently it calls client.search(...) directly, which raises AttributeError when client is None (the default). Change it to use `client or SeatsAeroClient()` so callers that omit client get a real SeatsAeroClient instance instead of crashing.

Behaviour that must NOT change:
- An explicitly passed `client` is still used as-is; its `.search(...)` result is returned, wrapped in `list(...)`.
- The six arguments are still forwarded to `.search` in the same order: origin, destination, start_date, end_date, cabins, programs (each via `s.get(...)` on the schedule dict).
- A falsy/empty schedule (`{}`) still works and forwards all-None arguments.
- No other function or import in the module is altered.

## Must contain

- `client or SeatsAeroClient()`
- `def search_schedule(sched: Dict, client=None, today=None)`
- `return list((client or SeatsAeroClient()).search(`

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
