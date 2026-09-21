# TASK: aw-scheduled-searches-s3-cabins-business-first-pr

## Confirmed defect (observed, not suspected)

`DEFAULT_QUERY` in `src/scheduled_searches.py` carries only a single `"cabin"`
key. There is no way for scheduled searches to declare the set of cabins they
should sweep (`business`, `first`) or the loyalty programs they should query
(`united`, `flying_blue`). Verified by reading the module: `DEFAULT_QUERY` has
exactly four keys (`origin`, `destination`, `date_ranges`, `cabin`) and no
`cabins`/`programs` key exists anywhere in the file, so any consumer of
`build_query()` output cannot see those defaults.

## Entry point

src/scheduled_searches.py:1 -- the `DEFAULT_QUERY` dict literal (lines 1-6).

## Required change

In src/scheduled_searches.py: add the two default keys to `DEFAULT_QUERY`, on
the lines immediately after `"cabin": "business",`:

    'cabins':['business','first'],
    'programs':['united','flying_blue'],

`build_query()` already copies every key of `DEFAULT_QUERY` into its result, so
no other code change is needed -- the new keys must flow through to
`build_query()` output automatically.

Behaviour that must NOT change:
- `DEFAULT_QUERY["origin"] == "JFK"`, `DEFAULT_QUERY["destination"] == "LAX"`,
  `DEFAULT_QUERY["cabin"] == "business"` (singular), and
  `DEFAULT_QUERY["date_ranges"]` stays `[{"start": "2026-03-01", "end": "2026-03-15"}]`.
- `build_query()` with no argument still returns all pre-existing defaults.
- A caller-supplied dict can still override any key, including the new ones:
  `build_query({"cabins": ["economy"], "programs": ["delta"]})` must return
  those exact values for `cabins`/`programs`.
- `_valid_range`, `normalize_date_ranges`, and the date-range fallback logic are
  untouched.

## Must contain

- `'cabins':['business','first'],`
- `'programs':['united','flying_blue'],`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/scheduled_searches.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
