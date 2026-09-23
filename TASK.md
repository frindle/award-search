# TASK: aw-sched-runner-s22-then-union-the-new-keys

## Confirmed defect (observed, not suspected)

`run_schedule()` in `src/scheduled_runner.py` notifies on every hit but never
records which result keys it has already notified about. Re-running the same
schedule re-notifies the identical award space forever -- there is no dedupe
state at all: `sched` gains `last_checked`, `last_results`, and `last_hit_count`,
but no `notified_keys`. Reproduced by calling `run_schedule` twice with a stubbed
client returning the same results; every run re-fires `notify_hit` for the same
keys, unlike `src/alerts.py:run_alert_check`, which dedupes via `notified_keys`.

## Entry point

src/scheduled_runner.py:`run_schedule()` (the function that ends with
`sched['last_checked'] = datetime.now().isoformat()`)

## Required change

In src/scheduled_runner.py, inside `run_schedule()`: after the notify loop and
before setting `sched['last_checked']`, union the newly returned result keys into
`sched['notified_keys']` (sorted, trimmed to the LAST NOTIFIED_KEYS_CAP).

Exact contract:
- Add a module-level constant `NOTIFIED_KEYS_CAP = 200` near the top of the file.
- In `run_schedule()`, after the existing notify loop and before
  `sched['last_checked'] = ...`:
  - compute `already = set(sched.get("notified_keys") or [])`
  - update it with `_result_key(r)` for every result in this run's results
    (the same `_result_key()` helper the file already defines)
  - write back `sched["notified_keys"] = sorted(already)[-NOTIFIED_KEYS_CAP:]`
- This mirrors the existing idiom in `src/alerts.py:run_alert_check`
  (`alert["notified_keys"] = sorted(already)[-200:]`).

Behaviour that must NOT change:
- `run_schedule()` still returns ALL results from this run, even when
  `notified_keys` is capped.
- The notify loop (and its per-result exception swallowing) is untouched.
- `sched['last_checked']`, `sched['last_results']`, `sched['last_hit_count']`
  are still set exactly as before.
- A `sched` with no `notified_keys` key, or with `notified_keys: None`, must not
  raise -- the new keys are simply recorded.
- All other functions in the file (`select_results`, `run_cycle`,
  `search_schedule`, `notify_hit`, `_result_key`, ...) are unchanged.

## Must contain

- `NOTIFIED_KEYS_CAP = 200`
- `sched["notified_keys"] = sorted(already)[-NOTIFIED_KEYS_CAP:]`

(A bare bullet checks the default target. To PIN a literal to a specific file --
useful when a fix spans a helper file and the route/wiring that calls it --
prefix the bullet with `in <path>:`, e.g.
`- in app/api/x/route.ts: ` followed by a backtick-quoted token. Then that
token is required in THAT file, not the target.)

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
