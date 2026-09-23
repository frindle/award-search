# TASK: aw-sched-runner-s23-always-calls-upsert-sche

## Confirmed defect (observed, not suspected)

`run_schedule()` in `src/scheduled_runner.py` mutates the schedule dict in
memory (`notified_keys`, `last_checked`, `last_results`, `last_hit_count`) and
returns the hits, but never persists it: `upsert_schedule` is imported from
`.scheduled_searches` (line 9) yet has zero call sites in this file. Verified by
grep -- the only occurrence of `upsert_schedule` in the module is the import.
Consequence observed: after a cycle runs, the stored schedule still shows its
pre-cycle state; dedupe keys and last-checked timestamps are lost on restart.

## Entry point

src/scheduled_runner.py:130 (the `return results` at the end of `run_schedule`, line 116)

## Required change

In src/scheduled_runner.py: # ALWAYS calls upsert_schedule(sched) before returning hits.

Concretely: inside `run_schedule()`, after all bookkeeping fields
(`notified_keys`, `last_checked`, `last_results`, `last_hit_count`) have been
written to `sched` and immediately before the final `return results`, call
`upsert_schedule(sched)` so every cycle -- hits or not, notify success or
failure -- persists its state.

Behaviour that must NOT change:
- `run_schedule()` still returns exactly the list of hit dicts from
  `search_schedule` (same objects, same order).
- Zero-hit cycles return `[]` and do not raise.
- A notification failure (`notify_hit` raising) is still swallowed per-hit;
  hits are still returned and the cycle completes.
- The bookkeeping fields keep their exact shape: `notified_keys` sorted and
  capped at `NOTIFIED_KEYS_CAP`, `last_checked` an ISO timestamp string,
  `last_results` the hit list, `last_hit_count` its length.

## Must contain

- `upsert_schedule(sched)`
- `def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:`

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
