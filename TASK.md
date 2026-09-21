# TASK: aw-sched-runner-s17-surviving-hits-get-resul

## Confirmed defect (observed, not suspected)

`run_cycle()` in `src/scheduled_runner.py` returns the surviving hits exactly as
the search produced them. Reproduced by calling it with a stub `search_fn`:
every result dict has no `booking_url` key at all (`'booking_url' in r` is
False), so downstream consumers have nothing to deep-link the user from an
alert hit back into seats.aero. The import for `seats_aero_url` already exists
at the top of the module but is never used -- the enrichment step was never
landed.

## Entry point

src/scheduled_runner.py:21 (`run_cycle`)

## Required change

In src/scheduled_runner.py: # surviving hits get result['booking_url'] = seats_aero_url(origin, destination, date, cabin).

Concretely: after `select_results` has produced the kept list for an alert and
it is non-empty, enrich each surviving hit in place before it goes into the
output dict. For every hit that is a dict, set
`result['booking_url'] = seats_aero_url(origin, destination, date, cabin)`
where `origin`, `destination`, `date`, `cabin` are read from THAT result's own
fields (`r.get("origin")`, `r.get("destination")`, `r.get("date")`,
`r.get("cabin")`). A hit missing the `cabin` key must still get a URL (pass
whatever `.get()` returns, i.e. None). Non-dict entries in the kept list are
skipped without raising.

Behaviour that must NOT change:
- `select_results`, `_result_key`, `search_schedule`, `get_trip`,
  `search_seats_aero` and all existing imports keep working exactly as before.
- An alert whose search raises is still skipped, and the cycle continues with
  the remaining alerts (no exception escapes `run_cycle`).
- An alert with no surviving hits does not appear in the returned dict at all.
- Each hit's URL is built from its OWN origin/destination/date/cabin -- two
  different hits must yield two different URLs, never one shared or constant
  value.

## Must contain

- `result['booking_url'] = seats_aero_url(origin, destination, date, cabin)`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/scheduled_runner.py` (the fix) and `test_fixture.py` (add adversarial cases); do not edit `verify.sh` or `TASK.md`.
test_fixture.py is the test fixture -- only ADD adversarial cases there, never weaken existing ones.

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
