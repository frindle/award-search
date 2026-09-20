# TASK: aw-sched-runner-s2-from-deeplinks-import-se

## Confirmed defect (observed, not suspected)

The scheduled runner (`src/scheduled_runner.py`) returns bare result dicts from
`run_cycle`, so downstream consumers have no booking deep link to hand the user.
Observed by importing `src.scheduled_runner`: there is no function that attaches
a seats.aero URL to results, and the module does not import anything from
`.deeplinks` (which already provides `seats_aero_url`). The webui builds this
link itself (`src/webui/app.py:100`) by calling `seats_aero_url` directly -- the
runner path has no equivalent.

## Entry point

src/scheduled_runner.py:24 (end of module, after `run_cycle`)

## Required change

In src/scheduled_runner.py: from .deeplinks import seats_aero_url.

Add a function `booking_links(alert, results)` that returns NEW result dicts
(each augmented with a `"booking_url"` key) where the URL is built by calling
`seats_aero_url(origin, destination, departure_date, cabin)` with values taken
from the alert: `alert.get("origin", "")`, `alert.get("destination", "")`,
`alert.get("date", "")`, and `alert.get("cabin", "economy")`.

Contract:
- `booking_links(None, None)` must not raise; it returns one dict whose
  `booking_url` is the all-empty seats.aero URL with the default cabin.
- Non-dict results are wrapped as `{"result": r}` before linking.
- Input result dicts are NEVER mutated -- callers get fresh dicts (do not do
  `r["booking_url"] = ...`).
- The alert's keys are read via `.get` with the defaults above; a missing key
  must never raise KeyError.

Behaviour that must NOT change:
- `select_results(alert, results)` still filters each result through
  `passes_filters`, swallowing per-result exceptions and returning only kept
  results (e.g. cabin filter keeps only matching cabins).
- `run_cycle(alerts, search_fn)` still maps alert_id -> kept results, skips an
  alert when its `search_fn` raises or nothing is kept, and tolerates a None
  alerts mapping.

## Must contain

- `from .deeplinks import seats_aero_url`
- `def booking_links(alert, results):`
- `alert.get("cabin", "economy")`

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
